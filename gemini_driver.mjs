// Gemini 网页版驱动 v2
//   上传参考图：优先 CDP 拖拽投喂（Input.dispatchDragEvent 带 files），
//                失败则回落到 CDP 文件选择器拦截
//   生成：新建对话 -> 输入指令 -> 发送 -> 等本轮新图 -> 点「下载完整尺寸」落盘
// 用法: node gemini_driver.mjs <参考图路径|NONE> "<指令>" <输出目录> [超时秒]
import fs from 'node:fs';

const [ref, instr, outdir, timeoutArg] = process.argv.slice(2);
const timeout = parseInt(timeoutArg || '300', 10);
const log = (...a) => console.log(...a);
fs.mkdirSync(outdir, { recursive: true });

const ts = await (await fetch('http://127.0.0.1:9222/json')).json();
let page = ts.find(t => t.type === 'page');
if (!page) {
  await fetch('http://127.0.0.1:9222/json/new?' +
    encodeURIComponent('https://gemini.google.com/app'), { method: 'PUT' });
  await new Promise(r => setTimeout(r, 4000));
  const ts2 = await (await fetch('http://127.0.0.1:9222/json')).json();
  page = ts2.find(t => t.type === 'page');
  if (!page) { log('NO_PAGE'); process.exit(1); }
}

const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r, { once: true }));

let seq = 0;
const pend = new Map();
const chooser = { pending: [] };
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); }
  if (m.method === 'Page.fileChooserOpened') { chooser.pending.push(m.params); log('FILE_CHOOSER'); }
});
const rpc = (method, params = {}) => new Promise((res, rej) => {
  const id = ++seq;
  pend.set(id, m => (m.error ? rej(new Error(method + ': ' + JSON.stringify(m.error))) : res(m.result || {})));
  ws.send(JSON.stringify({ id, method, params }));
});
const ev = async expr => {
  const r = await rpc('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || 'eval error');
  return r.result?.value;
};
const sleep = ms => new Promise(r => setTimeout(r, ms));

const PROMPT_POS = `(() => {
  const cands=[...document.querySelectorAll('rich-textarea,[contenteditable="true"],textarea')]
    .filter(e=>{const r=e.getBoundingClientRect();return r.width>120&&r.height>10;});
  if(!cands.length) return null;
  const e=cands[cands.length-1];
  e.scrollIntoView({block:'center'});
  const r=e.getBoundingClientRect();
  return {x:Math.round(r.left+r.width/2), y:Math.round(r.top+r.height/2)};
})()`;

try {
  await rpc('Page.enable');
  await rpc('Runtime.enable');
  await rpc('DOM.enable');
  try { await rpc('Page.setInterceptFileChooserDialog', { enabled: true }); } catch {}

  // ── 0) 全新对话 ──
  await rpc('Page.navigate', { url: 'https://gemini.google.com/app' });
  await sleep(6000);
  log('FRESH', await ev('location.href'));

  const pos = await ev(PROMPT_POS);
  if (!pos) { log('NO_EDITOR'); process.exit(1); }
  log('PROMPT_POS', JSON.stringify(pos));

  // ── 1) 上传参考图 ──
  let uploaded = false;
  if (ref !== 'NONE') {
    // 1a) 拖拽投喂
    try {
      const files = JSON.stringify([ref]);
      for (const type of ['dragEnter', 'dragOver', 'drop']) {
        await rpc('Input.dispatchDragEvent', {
          type, x: pos.x, y: pos.y,
          data: { items: [], files: [ref], dragOperationsMask: 1 },
        });
        await sleep(400);
      }
      await sleep(2500);
      const has = await ev(`(() => {
        const t=document.body.innerText;
        const imgs=[...document.querySelectorAll('img')].filter(i=>i.naturalWidth>200);
        return JSON.stringify({n:imgs.length, hasName:${files}.some(f=>t.includes(f.split(/[\\\\/]/).pop().slice(0,12)))});
      })()`);
      log('DROP', has);
      if (has && String(has).includes('"n":0') === false) uploaded = true;
    } catch (e) { log('DROP_ERR', e.message); }

    // 1b) 回落到菜单 → 上传文件 → CDP 选择器
    if (!uploaded) {
      await ev(`(() => {
        const b=[...document.querySelectorAll('button')].find(e=>(e.getAttribute('aria-label')||'')==='上传和工具');
        if(b) b.click(); return 1; })()`);
      await sleep(1500);
      await ev(`(() => {
        const mi=[...document.querySelectorAll('[role=menuitem],mat-menu-item')];
        const hit=mi.find(e=>/上传文件|上传图片|图库|Google 相册|从 Drive|插入图片/.test((e.innerText||'')));
        if(hit){hit.click(); return 'CLICKED';} return 'NO_ITEM'; })()`);
      for (let i = 0; i < 30 && !chooser.pending.length; i++) await sleep(300);
      if (chooser.pending.length) {
        const p = chooser.pending.shift();
        await rpc('DOM.setFileInputFiles', {
          files: [ref],
          ...(p.backendNodeId != null ? { backendNodeId: p.backendNodeId } : {}),
        });
        uploaded = true;
        log('UPLOADED_VIA_CHOOSER');
      } else log('CHOOSER_FAIL');
      await sleep(3000);
    } else log('UPLOADED_VIA_DROP');
  }

  // ── 2) 输入指令 ──
  await ev(PROMPT_POS);
  await rpc('Input.dispatchMouseEvent', { type: 'mousePressed', x: pos.x, y: pos.y, button: 'left', clickCount: 1, buttons: 1 });
  await rpc('Input.dispatchMouseEvent', { type: 'mouseReleased', x: pos.x, y: pos.y, button: 'left', clickCount: 1, buttons: 0 });
  await rpc('Input.insertText', { text: instr });
  log('TYPED', instr.length, 'chars');
  await sleep(1500);

  // 发送前记录已有图
  const beforeList = await ev("[...document.querySelectorAll('img')].map(i=>i.src)");
  const beforeJson = JSON.stringify(beforeList);

  // ── 3) 发送 ──
  const sent = await ev(`(() => {
    const b=[...document.querySelectorAll('button')].filter(e=>/^(发送|Send)$/.test((e.getAttribute('aria-label')||e.innerText||'').trim()))
      .filter(e=>{const r=e.getBoundingClientRect();return r.width>0;});
    if(b.length){ b[b.length-1].click(); return 'BTN'; }
    return 'ENTER';
  })()`);
  log('SEND', sent, 'uploaded=' + uploaded);
  if (sent === 'ENTER') {
    await rpc('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13, text: '\r' });
    await rpc('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13 });
  }

  // ── 4) 轮询本轮新图（以「下载完整尺寸」按钮出现为完成标志）──
  const t0 = Date.now();
  let src = null, dim = null;
  while (Date.now() - t0 < timeout * 1000) {
    await sleep(4000);
    const st = await ev(`(() => {
      const before=${beforeJson};
      const imgs=[...document.querySelectorAll('img')].filter(i=>{
        const r=i.getBoundingClientRect(); return r.width>150&&r.height>150&&i.naturalWidth>400;});
      const fresh=imgs.filter(i=>!before.includes(i.src));
      const l=fresh.length?fresh[fresh.length-1]:null;
      const dl=[...document.querySelectorAll('button')].filter(b=>/下载完整尺寸/.test(b.getAttribute('aria-label')||'')).length;
      return JSON.stringify({n:fresh.length,src:l?l.src:null,w:l?l.naturalWidth:0,h:l?l.naturalHeight:0,dl});
    })()`);
    let o = {}; try { o = JSON.parse(st); } catch {}
    if (o.src && o.dl > 0) { src = o.src; dim = o; log('IMAGE', o.w + 'x' + o.h); break; }
    if (o.n) log('...waiting', o.n);
  }
  if (!src) { log('TIMEOUT_NO_IMAGE'); process.exit(2); }

  // ── 5) 下载 ──
  let buf = null, saved = null;
  try { await rpc('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: outdir, eventsEnabled: true }); } catch {}
  const dclick = await ev(`(() => {
    const b=[...document.querySelectorAll('button')].filter(e=>/下载完整尺寸/.test(e.getAttribute('aria-label')||''));
    if(!b.length) return 'NO_DL_BTN';
    b[b.length-1].click(); return 'CLICKED';
  })()`);
  log('DL_BTN', dclick);
  if (dclick === 'CLICKED') {
    for (let i = 0; i < 60; i++) {
      await sleep(500);
      const fs2 = fs.readdirSync(outdir).filter(f => !f.endsWith('.crdownload'));
      if (fs2.length) { saved = outdir + '/' + fs2[0]; buf = fs.readFileSync(saved); break; }
    }
  }
  if (!buf) {
    const urlJson = JSON.stringify(src);
    const b64 = await ev(`(async()=>{ try{
      const r=await fetch(${urlJson}); const b=await r.arrayBuffer();
      let s=''; const u=new Uint8Array(b);
      for(let i=0;i<u.length;i+=0x8000) s+=String.fromCharCode.apply(null,u.subarray(i,i+0x8000));
      return btoa(s);}catch(e){return 'ERR:'+e.message;} })()`);
    if (b64 && !String(b64).startsWith('ERR')) buf = Buffer.from(b64, 'base64');
  }
  if (!buf) { log('DOWNLOAD_FAIL'); process.exit(3); }
  const ext = (saved && /\.png$/i.test(saved)) ? 'png' : (saved && /\.jpe?g$/i.test(saved)) ? 'jpg' : 'png';
  const fp = outdir + '/gemini_out.' + ext;
  fs.writeFileSync(fp, buf);
  log('SAVED', fp, Math.round(buf.length / 1024) + 'KB', (dim ? dim.w + 'x' + dim.h : ''));
} catch (e) {
  log('ERR', e.message);
  process.exit(1);
}
ws.close();
