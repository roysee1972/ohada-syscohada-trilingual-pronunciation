// 端到端冒烟：用最小 DOM 桩执行真实脚本，断言点击 ▶ / EN 会调用 Audio.play()
const fs = require('fs');
const html = fs.readFileSync('法语科目发音练习_离线版.html', 'utf8');
const js = html.match(/<script>([\s\S]*)<\/script>/)[1];

let plays = [];
class Audio {
  constructor(src) { this.src = src; }
  play() { plays.push(this.src); return Promise.resolve(); }
  pause() {}
}
global.Audio = Audio;
global.speechSynthesis = { cancel(){}, getVoices(){return []}, speak(){} };
global.SpeechSynthesisUtterance = class { constructor(t){this.text=t} };
const localStorage = { getItem: () => null, setItem: () => {} };

function mkEl(id) {
  const el = {
    id, _html: '', value: '', textContent: '', disabled: false,
    dataset: {}, handlers: {},
    classList: { add(){}, remove(){}, toggle(){}, contains(){return false} },
    addEventListener(t, fn) { this.handlers[t] = fn; },
    querySelectorAll: () => [],
    querySelector: () => null,
    closest: () => null,
    scrollIntoView(){},
  };
  Object.defineProperty(el, 'innerHTML', { get(){return el._html}, set(v){el._html=v} });
  return el;
}
const els = {};
for (const id of ['list','cat','q','rate','stat','stop','playAll','fold']) els[id] = mkEl(id);
els.rate.value = '1';
els.cat.value = '__all';   // init() 写入的是 innerHTML，桩不会自动选中默认值

global.document = {
  getElementById: id => els[id] || mkEl(id),
  querySelectorAll: () => [],
  addEventListener(){},
};
global.window = { addEventListener(){} };
global.localStorage = localStorage;
global.Intl = Intl;

new Function(js)();

// 1) 渲染是否产出内容
const out = els.list.innerHTML;
console.log('渲染 HTML 长度:', out.length);
console.log('包含科目行 .item :', /class="row item/.test(out));
console.log('包含 EN 按钮 :', /class="play en"/.test(out));
console.log('条目统计栏:', els.stat.innerHTML.replace(/<[^>]+>/g, ''));

// 2) 从渲染结果里取一行，构造假 row，触发点击
const m = out.match(/<div class="row item[^>]*data-say="([^"]*)"[^>]*data-say-en="([^"]*)"/);
if (!m) { console.log('✗ 未能从渲染结果解析出科目行'); process.exit(1); }
const sayFr = m[1].replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>');
const sayEn = m[2].replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>');
console.log('样本法文:', sayFr.slice(0, 46));
console.log('样本英文:', sayEn.slice(0, 46));

const enBtn = { classList:{add(){},remove(){},contains(){return false}} };
const frBtn = { classList:{add(){},remove(){},contains(){return false}} };
const row = {
  dataset: { say: sayFr, sayEn },
  classList: { add(){}, remove(){}, contains(){ return false } },
  querySelector: sel => (sel === '.play.en' ? enBtn : frBtn),
};
const click = els.list.handlers['click'];
if (!click) { console.log('✗ 未捕获到 click 处理器'); process.exit(1); }

const evtEn = { target: { closest: s => (s === '.play.en' ? enBtn : (s === '.row' ? row : null)) } };
const evtFr = { target: { closest: s => (s === '.play:not(.en)' ? frBtn : (s === '.row' ? row : null)) } };

plays = [];
click(evtEn);
const okEn = plays.length === 1 && plays[0].startsWith('data:audio/mpeg;base64,');
console.log('点 EN  → play 次数', plays.length, okEn ? '✓ 英文音频已播放' : '✗');

plays = [];
click(evtFr);
const okFr = plays.length === 1 && plays[0].startsWith('data:audio/mpeg;base64,');
console.log('点 ▶   → play 次数', plays.length, okFr ? '✓ 法文音频已播放' : '✗');

// 3) 英文/法文音频确实是两段不同的音频
plays = []; click(evtEn); const a1 = plays[0];
plays = []; click(evtFr); const a2 = plays[0];
console.log('法/英音频不同:', a1 !== a2 ? '✓' : '✗');
process.exit(okEn && okFr && a1 !== a2 ? 0 : 1);
