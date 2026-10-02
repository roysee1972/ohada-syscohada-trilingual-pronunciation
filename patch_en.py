# -*- coding: utf-8 -*-
"""修补「法语科目发音练习_离线版.html」的英文列：
1) 应用 en_fix.py 的译名修订表；
2) 剥离英文列中冗余的「— 中文译文」尾巴（中文列已单独展示）；
3) 为新出现的英文朗读文本合成 en-GB-RyanNeural 音频并内嵌；
4) 剪掉不再使用的旧英文音频，控制体积。

用法：python patch_en.py [--dry]
"""
import asyncio
import base64
import hashlib
import json
import os
import re
import shutil
import sys
import time

import edge_tts

BASE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(BASE, '法语科目发音练习_离线版.html')
CACHE = os.path.join(BASE, '_audio_cache')
VOICE_EN = 'en-GB-RyanNeural'
RATE_EN = '-5%'
CONCURRENCY = 8
RETRY = 3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from en_fix import FIX, strip_cn  # noqa: E402

_CJK = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f\uff00-\uffef]+')


def norm_en(en: str) -> str:
    t = _CJK.sub(' ', en)
    t = re.sub(r'\s*[-–—]\s*$', '', t)
    t = re.sub(r'^[\s\-–—]+', '', t)
    t = re.sub(r'\s{2,}', ' ', t)
    return t.strip(' -–—,')


def cache_name(text, lang='en'):
    return hashlib.md5((lang + '\x00' + text).encode('utf-8')).hexdigest() + '.mp3'


# ---------- 读取现有 HTML 中的四大 JSON ----------
def load_consts(src, name):
    m = re.search(r'^const %s\s*=\s*(.*);\s*$' % name, src, re.M)
    if not m:
        raise SystemExit('未找到 const %s' % name)
    return json.loads(m.group(1)), m


src = open(HTML, encoding='utf-8').read()
DATA, mD = load_consts(src, 'DATA')
AUDIO, mA = load_consts(src, 'AUDIO')
AUDIO_EN, mE = load_consts(src, 'AUDIO_EN')
CATS, mC = load_consts(src, 'CATS')
print('读取：条目 %d，类目 %d，法语音频 %d，原英文音频 %d'
      % (len(DATA), len(CATS), len(AUDIO), len(AUDIO_EN)))

# ---------- 1+2. 应用译名修订 & 剥离中文尾巴 ----------
changed_fix = changed_tail = 0
for d in DATA:
    code = d['code']
    if code in FIX:
        new_en = FIX[code]
        if d['en'] != new_en:
            changed_fix += 1
        d['en'] = new_en
    else:
        stripped = _CJK.sub(' ', d['en'])
        stripped = re.sub(r'\s*[-–—]\s*$', '', stripped)
        stripped = re.sub(r'\s{2,}', ' ', stripped).strip(' -–—,')
        if stripped and stripped != d['en']:
            changed_tail += 1
            d['en'] = stripped
    d['sayEn'] = norm_en(d['en'])

print('译名修订 %d 条，剥离中文尾巴 %d 条' % (changed_fix, changed_tail))

# ---------- 3. 需要哪些英文音频 ----------
need = [d['sayEn'] for d in DATA if d['sayEn']]
need += [c['sayEn'] for c in CATS if c.get('sayEn')]
need = list(dict.fromkeys(need))
missing = [t for t in need if t not in AUDIO_EN]
print('需要英文朗读文本 %d 条，其中缺音频 %d 条' % (len(need), len(missing)))

DRY = '--dry' in sys.argv
if DRY:
    # 自检：修订后法文不同却仍同英文的组
    import collections
    g = collections.defaultdict(list)
    for d in DATA:
        g[d['en']].append(d)
    bad = [(k, v) for k, v in g.items()
           if len(v) > 1 and len(set(x['fr'] for x in v)) > 1]
    print('残留「法文不同却同英文」组：%d' % len(bad))
    for k, v in bad[:30]:
        print('   %s -> %s' % (k[:52], [x['code'] for x in v]))
    raise SystemExit(0)


async def synth(texts):
    os.makedirs(CACHE, exist_ok=True)
    todo = [t for t in texts
            if not os.path.exists(os.path.join(CACHE, cache_name(t)))]
    print('缓存命中 %d，实际合成 %d 条' % (len(texts) - len(todo), len(todo)))
    if not todo:
        return []
    sem = asyncio.Semaphore(CONCURRENCY)
    fails = []
    lock = asyncio.Lock()
    cnt = {'n': 0}
    total = len(todo)
    t0 = time.time()

    async def one(text):
        path = os.path.join(CACHE, cache_name(text))
        async with sem:
            for attempt in range(RETRY):
                try:
                    await edge_tts.Communicate(
                        text, voice=VOICE_EN, rate=RATE_EN).save(path)
                    if os.path.exists(path) and os.path.getsize(path) > 0:
                        break
                except Exception:
                    await asyncio.sleep(1.5 * (attempt + 1))
            else:
                async with lock:
                    fails.append(text)
                return
        async with lock:
            cnt['n'] += 1
            if cnt['n'] % 50 == 0 or cnt['n'] == total:
                el = time.time() - t0
                print('  合成 %d/%d (%.0f%%) 已用 %.0fs'
                      % (cnt['n'], total, cnt['n'] / total * 100, el))

    await asyncio.gather(*[one(t) for t in todo])
    return fails


fails = asyncio.run(synth(missing))
if fails:
    print('⚠ 合成失败 %d 条：' % len(fails))
    for t in fails[:10]:
        print('   ', t[:70])


def b64(text):
    p = os.path.join(CACHE, cache_name(text))
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        return None
    with open(p, 'rb') as f:
        return 'data:audio/mpeg;base64,' + base64.b64encode(f.read()).decode()


NEW_EN = {}
lost = []
for t in need:
    if t in AUDIO_EN:
        NEW_EN[t] = AUDIO_EN[t]
    else:
        u = b64(t)
        if u:
            NEW_EN[t] = u
        else:
            lost.append(t)
print('新英文音频 %d 段（原 %d 段），缺失 %d'
      % (len(NEW_EN), len(AUDIO_EN), len(lost)))

miss_items = sum(1 for d in DATA if d['sayEn'] and d['sayEn'] not in NEW_EN)
print('条目级英文音频覆盖：%d / %d' % (
    sum(1 for d in DATA if d['sayEn'] and d['sayEn'] in NEW_EN),
    sum(1 for d in DATA if d['sayEn'])))
if miss_items:
    print('⚠ 无音频条目 %d' % miss_items)

# ---------- 写回 ----------
def dumps(o):
    return json.dumps(o, ensure_ascii=False, separators=(',', ':'))


bak = os.path.join(BASE, '法语科目发音练习_离线版 - 备份1002.html')
if not os.path.exists(bak):
    shutil.copy2(HTML, bak)
    print('已备份 → %s' % os.path.basename(bak))

def rebuild():
    s = open(HTML, encoding='utf-8').read()
    parts = []
    idx = 0
    for name in ('DATA', 'AUDIO', 'AUDIO_EN', 'CATS'):
        m = re.search(r'^const %s\s*=\s*(.*);\s*$' % name, s, re.M)
        parts.append((m, name))
    for m, name in reversed(parts):
        payload = {'DATA': DATA, 'AUDIO': AUDIO,
                   'AUDIO_EN': NEW_EN, 'CATS': CATS}[name]
        s = s[:m.start(1)] + dumps(payload) + s[m.end(1):]
    return s


out = rebuild()
with open(HTML, 'w', encoding='utf-8') as f:
    f.write(out)
print('已写回 %s（%.1f MB）' % (os.path.basename(HTML),
                               os.path.getsize(HTML) / 1024 / 1024))
