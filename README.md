# OHADA / SYSCOHADA 法语会计科目 · 中法英三语离线发音练习

> 一个 **单文件 HTML**（下载即可用，双击打开，无需联网、无需安装）：
> **1351 条** OHADA/SYSCOHADA 会计科目，**中文 · 法文 · 英文**三语对照，
> 每一条都能听到**离线内嵌的法语音频**和**英文音频**。

- 工具本体：[Releases 下载 `ohada-syscohada-pronunciation-offline.html`](https://github.com/roysee1972/ohada-syscohada-trilingual-pronunciation/releases/latest/download/ohada-syscohada-pronunciation-offline.html)（约 58 MB，下载后双击打开）
- 在线体验（GitHub Pages 首页）：<https://roysee1972.github.io/ohada-syscohada-trilingual-pronunciation/>
- 只要数据不要界面：[`data/ohada_accounts_trilingual.csv`](data/ohada_accounts_trilingual.csv)（1351 行，130 KB）

[English](#english) · [Français](#français)

---

## 一、这个工具是给谁用的

服务对象是**在 OHADA 法语区从事财务、会计、审计工作的中国人**（刚果金、科特迪瓦、塞内加尔、喀麦隆、贝宁、马里、布基纳法索等 17 个成员国），以及需要用法语处理会计业务的工程、商务、翻译人员。

它要解决的是一个很具体、很常见的痛点：

| 场景 | 困境 |
|---|---|
| 看当地报表、凭证、账套 | 科目是法语的，认识单词但**念不出来**，和同事口头对不上 |
| 开会、查账、和当地会计沟通 | 想说"应收账款减值"，**不知道法语怎么说** |
| 用法语报出科目号 | 对方听得懂，自己却**不敢开口** |
| 查词典 / 查 PDF 科目表 | 只有文字，**没有发音**；且只有法语，**没有中文** |
| 在矿区、工地、出差途中 | **没网**，在线翻译和在线 TTS 全部失效 |

**核心目的**：把"看得懂"推进到"听得懂、说得出"——用**耳朵**把 SYSCOHADA 科目表装进脑子里，
并且能在**中文（理解）— 法文（工作语言）— 英文（国际准则术语）**之间自由对齐。

---

## 二、数据范围

- 依据 **SYSCOHADA révisé**（OHADA 统一会计制度修订版）科目表
- **1351 条**科目，覆盖 **9 大类**（1 长期资源 ～ 9 承诺与管理会计）
- 层级完整：**二级 85 条 / 三级 431 条 / 四级 835 条**，最细到四级子科目
- 每一条都带：科目号 · 级次 · 上级科目 · 法文名 · 中文名 · 英文名 · 所属大类

| 大类 | 条数 | 大类 | 条数 |
|---|---|---|---|
| 1 长期资源 | 156 | 6 费用 | 258 |
| 2 固定资产 | 298 | 7 收入 | 119 |
| 3 存货 | 74 | 8 HAO 非经常性 | 55 |
| 4 往来方 | 235 | 9 承诺与管理会计 | 58 |
| 5 资金 | 98 | | |

---

## 三、主要特点

**1. 真正的离线，不依赖任何网络或语音包**
1351 条科目的法语发音（1196 段 MP3）与英文发音（1263 段 MP3）**全部以 base64 内嵌在这一个 HTML 文件里**。
不需要联网，不需要系统安装法语语音包，拷到 U 盘、发到手机上都能用。
（Windows 常见的"Web Speech API 找不到法语就念成英语"的问题，在这里不存在。）

**2. 三语对照，一次对齐三个世界**
- **中文**：让你真正理解这个科目在讲什么（`已认购已催缴未实缴股本`）
- **法文**：当地账套上的原文，工作现场要用（`Capital souscrit, appelé, non versé`）
- **英文**：国际财务语境下的标准术语（`Share capital subscribed, called up, not paid`）

**3. 法英双发音，可对照听**
每行两个按钮：圆形 ▶ 读法语（微软神经网络语音 `fr-FR-HenriNeural`），方形 `EN` 读英语（英式男声 `en-GB-RyanNeural`）。
法语稍慢（−10%）、英语稍慢（−5%），便于跟读辨音。

**4. 子科目英文按法文本义逐条翻译，不是复制父科目**
这是本项目花力气最多的地方。原始数据中 **1017 条**子科目直接沿用了父科目的笼统英文，
例如 2911～2919（开发费用 / 专利 / 软件 / 商标 / 商誉 …… 减值）的英文全是同一句
`Impairment — intangible assets`；现已逐条按法文含义重译（见 `en_fix.py`，共 1089 条修订）。

**5. 树形结构，和真实账套层级一致**
大类 → 二级 → 三级 → 四级，逐级折叠展开，折叠状态记在本地。

**6. 连续朗读：整类"磨耳朵"**
点「连续朗读」自动展开全部层级并从第一条读到底，适合通勤、做家务时当背景音反复听。

**7. 四档语速**（0.7× / 0.85× / 1.0× / 1.15×），用 `playbackRate` 变速，不重新编码、不失真。

**8. 搜索与筛选**
按大类筛选；关键词可同时搜**法文 / 中文 / 英文 / 科目号**。搜到明细科目时会自动补齐它的各级父标题，不会丢上下文。

**9. 键盘流操作**
`↑` `↓` 选条目，`←` 读法文，`→` 读英文，`Enter` 折叠/展开，`Esc` 停止，空格键重听。
适合不便于一直点鼠标的场景。

**10. 纯静态、零依赖**
单个 `.html` 文件。没有构建、没有后端、没有 CDN、没有外部字体，断网环境下行为完全一致。

---

## 四、怎么用

1. 下载 `ohada-syscohada-pronunciation-offline.html`（约 58 MB，即仓库根目录那个大文件）
2. 双击用浏览器打开（Chrome / Edge / Firefox 均可）
3. 点任意一行听法语，点 `EN` 听英文

文件较大是因为把 2459 段语音都塞进去了——这正是"能离线"的代价。
如果只想拿到三语对照文字，用 `data/ohada_accounts_trilingual.csv` 就够了，不必下载 58 MB。

---

## 五、自己重新生成 / 二次开发

```bash
pip install edge-tts openpyxl
```

| 文件 | 作用 |
|---|---|
| `ohada-syscohada-pronunciation-offline.html` | **成品**：单文件离线工具（58 MB，已内嵌双语语音） |
| `index.html` | 仓库首页 / GitHub Pages 落地页（轻量，不含语音） |
| `data/ohada_accounts_trilingual.csv` | 1351 条三语对照纯数据（科目号 / 级次 / 法文 / 中文 / 英文） |
| `用于发音练习的科目表.xlsx` | 源数据（科目号/级次/上级科目/法文/中文/英文/大类） |
| `template.html` | 页面模板（含 `__DATA__` `__AUDIO__` `__AUDIO_EN__` `__CATS__` 四个占位符） |
| `make_offline_html.py` | 全量重建：读 Excel → edge-tts 合成法英双语音频 → base64 内嵌 → 输出单文件 HTML |
| `en_fix.py` | 英译名修订表（1089 条）+ 中文尾巴剥离工具 |
| `patch_en.py` | 增量修补：只改英文列并重合成英文音频，法文音频原样保留（支持 `--dry` 自检） |
| `_smoke.js` | 端到端测试：最小 DOM 桩执行真实脚本，断言点 ▶/EN 真的触发播放 |

```bash
python make_offline_html.py            # 全量重建
python patch_en.py --dry               # 只自检英文重复，不改文件
FORCE_RESYNTH=1 python make_offline_html.py   # 清空音频缓存全量重合成
```

音频缓存在 `_audio_cache/`（按 `语言 + 文本` 的 MD5 命名，天然去重），重跑时自动复用。

---

## 六、和已有项目的区别

检索 GitHub 后，现有的 OHADA/SYSCOHADA 开源项目大致是两类，和本项目不重叠：

- **科目数据 / SDK 类**（`ohadakit`、PHP `plan-comptable-syscohada`、Odoo `l10n_*_syscohada` 等）：
  面向开发者，提供查询、校验、导入导出。语言为 **法 / 英 / 葡 / 西**，**无中文**；不含发音，也不是给人直接用的界面。
- **法语学习类**（法语发音练习 Web App、Anki 音频生成器等）：面向通用生活词汇，
  **不含会计科目**，也**不含中文**。

目前没有检索到同时具备 **OHADA 完整科目表 + 中法英三语 + 离线内嵌双语语音** 的现成工具，这是本项目存在的理由。

---

## 七、许可

- **代码**（`make_offline_html.py` / `patch_en.py` / `en_fix.py` / `template.html` / `_smoke.js`）采用 **MIT**，见 `LICENSE`。
- **科目数据**整理自 OHADA/SYSCOHADA révisé 公开科目表；中文与英文译文为本项目翻译整理，可自由使用与勘误。
- **音频**由 Microsoft Edge TTS（`fr-FR-HenriNeural` / `en-GB-RyanNeural`）合成，仅供学习交流使用。

译文难免有误，欢迎提 Issue 指正——尤其是法文术语与中文会计惯用译名的对应关系。

---

<a name="english"></a>
## English

A **single-file, fully offline HTML** tool: **1351** OHADA/SYSCOHADA chart-of-accounts entries,
presented **trilingually (Chinese · French · English)**, each with **embedded French audio**
(`fr-FR-HenriNeural`) and **English audio** (`en-GB-RyanNeural`).

Built for Chinese-speaking finance and accounting professionals working in the 17 OHADA member states
(DR Congo, Côte d'Ivoire, Senegal, Cameroon, Benin, …) who can read French account labels but cannot
say them out loud — and who often work without reliable internet.

Highlights: zero network dependency (2459 MP3 clips embedded as base64); hierarchical tree matching
the real chart (levels 2–4); per-account English translated from the French meaning rather than copied
from the parent (1089 corrections in `en_fix.py`); continuous playback for passive listening;
4 speed levels; search across French/Chinese/English/account code; full keyboard control.

Related existing projects are either developer SDKs (French/English/Portuguese/Spanish, no Chinese,
no audio) or general French-learning apps (no accounting content). Nothing found combines a complete
OHADA chart with Chinese-French-English trilingual display and offline embedded audio.

<a name="français"></a>
## Français

Un **fichier HTML unique, entièrement hors ligne** : **1351** comptes du plan comptable
OHADA/SYSCOHADA révisé, en **trilingue (chinois · français · anglais)**, avec la **prononciation
audio intégrée** de chaque libellé en français (`fr-FR-HenriNeural`) et en anglais (`en-GB-RyanNeural`).

Conçu pour les professionnels chinois de la finance et de la comptabilité travaillant dans les 17 États
membres de l'OHADA (RD Congo, Côte d'Ivoire, Sénégal, Cameroun, Bénin, …) : ils savent lire les
libellés français mais n'osent pas les prononcer, et travaillent souvent sans connexion fiable.

Points forts : aucune dépendance réseau (2459 clips MP3 intégrés en base64) ; arborescence fidèle au
plan officiel (niveaux 2 à 4) ; libellés anglais traduits du sens français compte par compte
(1089 corrections dans `en_fix.py`) ; lecture continue pour l'écoute passive ; 4 vitesses ;
recherche multilingue ; navigation clavier complète.
