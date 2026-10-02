# -*- coding: utf-8 -*-
"""
生成「法语科目发音练习」离线单文件 HTML —— Henri 法语男声版。

音频方案：edge-tts 调用微软神经网络语音 fr-FR-HenriNeural（法国标准男声），
          逐条下载 MP3 并以 base64 内嵌进 HTML，实现完全离线播放。

关于 ffmpeg：原脚本用 ffmpeg 把音频压到 32kbps/22.05kHz/单声道。
            实测 edge-tts 原生输出已是 24kHz 单声道 64kbps MPEG2，编码本身足够精简，
            ffmpeg 仅能再省约 10-20% 体积，不值得为此增加一个外部依赖，故跳过。

依赖：edge-tts、openpyxl
用法：python make_offline_html.py
      FORCE_RESYNTH=1 python make_offline_html.py   # 清空缓存全量重合成
"""
import asyncio
import base64
import hashlib
import json
import os
import re
import shutil
import time

import edge_tts
import openpyxl

XLSX = '用于发音练习的科目表.xlsx'
TEMPLATE = 'template.html'
OUT = '法语科目发音练习_离线版.html'
CACHE = '_audio_cache'          # 音频缓存目录，重跑时直接复用，避免重复联网

VOICE = 'fr-FR-HenriNeural'     # 法国法语标准男声
RATE = '-10%'                   # 稍慢，便于跟读

VOICE_EN = 'en-GB-RyanNeural'   # 英式英语男声
RATE_EN = '-5%'                 # 英文稍慢，便于辨听

# 九大类的标题（SYSCOHADA révisé 官方类名），用于树形目录顶层标题行的展示与发音。
# 键须与 Excel「cat」列完全一致；值为 (法文标题, 英文标题)。
CAT_TITLES = {
    '1 长期资源':      ("Comptes de ressources durables", "Long-term resources accounts"),
    '2 固定资产':      ("Comptes d'actifs immobilisés", "Fixed assets accounts"),
    '3 存货':          ("Comptes de stocks", "Inventory accounts"),
    '4 往来方':        ("Comptes de tiers", "Third-party accounts"),
    '5 资金':          ("Comptes de trésorerie", "Cash and treasury accounts"),
    '6 费用':          ("Comptes de charges", "Expense accounts"),
    '7 收入':          ("Comptes de produits", "Revenue accounts"),
    '8 HAO非经常性':   ("Comptes hors activités ordinaires (HAO)", "Non-ordinary activities (HAO)"),
    '9 承诺与管理会计': ("Comptes des engagements et comptabilité de gestion",
                        "Commitments and management accounting"),
}

CONCURRENCY = 8                 # 并发合成数
RETRY = 3


# ---------- 1. 读取数据 ----------
def load_rows():
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb['科目表']
    fields = ('code', 'level', 'parent', 'fr', 'zh', 'en', 'cat', 'bal')
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        r = r[:8]
        if not r[3] or not str(r[3]).strip():
            continue
        item = {k: (str(v).strip() if v is not None else '') for k, v in zip(fields, r)}
        item['level'] = int(item['level']) if item['level'].isdigit() else 0
        rows.append(item)
    wb.close()
    return apply_en_fix(rows)


def apply_en_fix(rows):
    """应用 en_fix.py 的英文译名修订。

    背景：Excel 英文列存在两类缺陷——
      ① 大量子科目直接沿用父科目的笼统英文（1011~1018 全都是
         "Share capital — called up and paid"），未按法文本义翻译；
      ② 部分条目错译（如 451 与非洲机构的业务 被译成了"国际组织"）。
    en_fix.py 是按法文含义逐条重译的结果，此处统一套用，
    未收录的条目则剥离英文列中冗余的「— 中文译文」尾巴。
    """
    from en_fix import FIX, strip_cn
    n_fix = n_tail = 0
    for r in rows:
        if r['code'] in FIX:
            if r['en'] != FIX[r['code']]:
                n_fix += 1
            r['en'] = FIX[r['code']]
        else:
            s = strip_cn(r['en'])
            if s != r['en']:
                n_tail += 1
                r['en'] = s
    print(f'英文译名修订 {n_fix} 条，剥离中文尾巴 {n_tail} 条')
    return rows


def norm(fr: str) -> str:
    """朗读文本规范化：科目名中的逗号只表并列，统一为自然停顿。"""
    t = fr.replace(';', ',')
    t = re.sub(r'\s*,\s*', ', ', t)
    t = re.sub(r'\s{2,}', ' ', t)
    return t.strip(' ,')


# 中文/全角字符（英文列中混排的中文译文，朗读时应剔除）
_CJK = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f\uff00-\uffef]+')


def norm_en(en: str) -> str:
    """英文朗读文本规范化。

    Excel 的英文列大量采用「英文 — 中文译文」的混排格式，
    直接朗读会把中文一并读出。此处剥离中文，并清理残留的破折号与空格。
    """
    t = _CJK.sub(' ', en)
    t = re.sub(r'\s*[-–—]\s*$', '', t)      # 去掉结尾悬空的连接符
    t = re.sub(r'^[\s\-–—]+', '', t)         # 去掉开头悬空的连接符
    t = re.sub(r'\s{2,}', ' ', t)
    return t.strip(' -–—,')


# ---------- 2. 音频合成 ----------
def cache_name(text: str, lang: str = 'fr') -> str:
    """用「语言 + 内容哈希」作文件名，稳定、天然去重，且法/英互不覆盖。"""
    return hashlib.md5((lang + '\x00' + text).encode('utf-8')).hexdigest() + '.mp3'


async def synth_all(texts, voice=VOICE, rate=RATE, conv=norm, lang='fr', label='法语'):
    os.makedirs(CACHE, exist_ok=True)
    todo = [t for t in texts if not os.path.exists(os.path.join(CACHE, cache_name(t, lang)))]
    reused = len(texts) - len(todo)

    if reused:
        print(f'[{label}] 复用缓存 {reused} 条，待合成 {len(todo)} 条')
    if not todo:
        return 0, []

    sem = asyncio.Semaphore(CONCURRENCY)
    failures = []
    lock = asyncio.Lock()
    counter = {'n': 0}
    total = len(todo)
    t0 = time.time()

    async def one(text):
        path = os.path.join(CACHE, cache_name(text, lang))
        async with sem:
            for attempt in range(RETRY):
                try:
                    await edge_tts.Communicate(conv(text), voice=voice, rate=rate).save(path)
                    if os.path.exists(path) and os.path.getsize(path) > 0:
                        break
                except Exception:
                    await asyncio.sleep(1.5 * (attempt + 1))
            else:
                async with lock:
                    failures.append(text)
                return
        async with lock:
            counter['n'] += 1
            n = counter['n']
            if n % 25 == 0 or n == total:
                el = time.time() - t0
                eta = el / n * (total - n)
                print(f'  进度 {n}/{total}  ({n/total*100:.0f}%)  已用 {el:.0f}s  预计剩余 {eta:.0f}s')

    await asyncio.gather(*[one(t) for t in todo])
    return counter['n'], failures


# ---------- 3. 组装 HTML ----------
def b64_of(text, lang):
    p = os.path.join(CACHE, cache_name(text, lang))
    if not os.path.exists(p):
        return None
    with open(p, 'rb') as f:
        return 'data:audio/mpeg;base64,' + base64.b64encode(f.read()).decode()


def build_cats(rows):
    """按数据中首次出现的顺序生成九大类标题条目（供模板渲染顶层标题行）。"""
    cats, seen = [], set()
    for r in rows:
        c = r['cat']
        if not c or c in seen:
            continue
        seen.add(c)
        fr, en = CAT_TITLES.get(c, ('', ''))
        zh = c.split(' ', 1)[1] if ' ' in c else c
        cats.append({
            'cat': c, 'fr': fr, 'zh': zh, 'en': en,
            'say': norm(fr), 'sayEn': norm_en(en),
        })
    return cats


def build(rows, cat_items):
    payload = [{
        'code': r['code'], 'level': r['level'], 'fr': r['fr'],
        'zh': r['zh'], 'en': r['en'], 'cat': r['cat'],
        'say': norm(r['fr']),
        'sayEn': norm_en(r['en']),
    } for r in rows]

    # 法语音频：按「朗读文本」索引，多条科目共用一个音频
    audio, covered = {}, 0
    for r in payload:
        url = b64_of(r['fr'], 'fr')
        if not url:
            continue
        covered += 1
        if r['say'] not in audio:
            audio[r['say']] = url

    # 英文音频：必须用与合成时相同的键（即清洗后的文本 sayEn），
    # 不能用英文原文，否则含中文混排的条目会因 hash 不符而查不到音频。
    audio_en, covered_en = {}, 0
    for r in payload:
        key = r['sayEn']
        if not key:
            continue
        url = b64_of(key, 'en')
        if not url:
            continue
        covered_en += 1
        if key not in audio_en:
            audio_en[key] = url

    # 大类标题的法/英音频（键与前端朗读文本一致，即规范化后的 say / sayEn）
    for c in cat_items:
        if c['say']:
            url = b64_of(c['fr'], 'fr')
            if url and c['say'] not in audio:
                audio[c['say']] = url
        if c['sayEn']:
            url = b64_of(c['sayEn'], 'en')
            if url and c['sayEn'] not in audio_en:
                audio_en[c['sayEn']] = url

    tmpl = open(TEMPLATE, encoding='utf-8').read()
    doc = (tmpl
           .replace('__DATA__', json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
           .replace('__CATS__', json.dumps(cat_items, ensure_ascii=False, separators=(',', ':')))
           .replace('__AUDIO_EN__', json.dumps(audio_en, ensure_ascii=False, separators=(',', ':')))
           .replace('__AUDIO__', json.dumps(audio, ensure_ascii=False, separators=(',', ':'))))

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(doc)
    return len(payload), len(audio), covered, len(audio_en), covered_en


# ---------- 主流程 ----------
async def main():
    if os.environ.get('FORCE_RESYNTH') == '1':
        shutil.rmtree(CACHE, ignore_errors=True)
        print('已清空缓存，全量重新合成')

    rows = load_rows()
    print(f'读取科目 {len(rows)} 条')

    uniq = list(dict.fromkeys(r['fr'] for r in rows))
    print(f'唯一法文短语 {len(uniq)} 条 → 语音 {VOICE}')
    _, fail_fr = await synth_all(uniq, VOICE, RATE, norm, 'fr', '法语')

    # 英文列存在「英文 — 中文译文」混排，先清洗再合成（clean 后为空则跳过）
    uniq_en = list(dict.fromkeys(norm_en(r['en']) for r in rows if norm_en(r['en'])))
    print(f'唯一英文短语 {len(uniq_en)} 条 → 语音 {VOICE_EN}')
    _, fail_en = await synth_all(uniq_en, VOICE_EN, RATE_EN, norm_en, 'en', '英语')

    # 大类标题的法 / 英音频
    cat_items = build_cats(rows)
    cat_fr = [c['fr'] for c in cat_items if c['say']]
    cat_en = [c['sayEn'] for c in cat_items if c['sayEn']]
    _, fail_cfr = await synth_all(cat_fr, VOICE, RATE, norm, 'fr', '法语类目')
    _, fail_cen = await synth_all(cat_en, VOICE_EN, RATE_EN, norm_en, 'en', '英语类目')

    for label, fails in (('法语', fail_fr + fail_cfr), ('英语', fail_en + fail_cen)):
        if fails:
            print(f'\n⚠ {label} 有 {len(fails)} 条合成失败（浏览器会回退到内置语音）：')
            for t in fails[:5]:
                print('   ', t[:70])

    n_items, n_audio, covered, n_audio_en, covered_en = build(rows, cat_items)
    size = os.path.getsize(OUT)
    # 分母应是「有法文/英文可读的条目数」，而非去重后的音频段数
    den_fr = sum(1 for r in rows if norm(r['fr']))
    den_en = sum(1 for r in rows if norm_en(r['en']))

    print()
    print('=' * 52)
    print(f'  条目数    : {n_items}')
    print(f'  法语音频  : {n_audio} 段 · 覆盖 {covered}/{den_fr} '
          f'({covered/den_fr*100:.1f}%)')
    print(f'  英语音频  : {n_audio_en} 段 · 覆盖 {covered_en}/{den_en} '
          f'({covered_en/den_en*100:.1f}%)')
    print(f'  输出文件  : {OUT}')
    print(f'  文件体积  : {size/1024/1024:.1f} MB')
    print('=' * 52)


if __name__ == '__main__':
    asyncio.run(main())
