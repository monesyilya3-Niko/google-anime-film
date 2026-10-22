// 用本地 CDP Chrome 走完 rclone 的 OAuth 授权流程（浏览器级 CDP）
// 用法: node oauth_consent.mjs <authUrl> [port] [outPrefix]
import fs from 'node:fs';

const url = process.argv[2];
const port = process.argv[3] || '9333';
const prefix = process.argv[4] || 'consent';
if (!url) { console.error('need url'); process.exit(1); }

const ver = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json();
console.log('浏览器:', ver.Browser);

const ws = new WebSocket(ver.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r, { once: true }));

let id = 0;
const pend = new Map();
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); }
});
function rpc(method, params = {}, sessionId) {
  const i = ++id;
  const msg = { id: i, method, params };
  if (sessionId) msg.sessionId = sessionId;
  ws.send(JSON.stringify(msg));
  return new Promise(r => pend.set(i, r));
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

const ct = await rpc('Target.createTarget', { url: 'about:blank' });
const tid = ct.result.targetId;
const at = await rpc('Target.attachToTarget', { targetId: tid, flatten: true });
const sid = at.result.sessionId;
console.log('新标签:', tid);

await rpc('Page.enable', {}, sid);
await rpc('Runtime.enable', {}, sid);
await rpc('Page.navigate', { url }, sid);
await sleep(3500);

async function evaluate(expr) {
  const r = await rpc('Runtime.evaluate',
    { expression: expr, returnByValue: true, awaitPromise: true }, sid);
  return r.result?.result?.value;
}
async function shot(name) {
  const r = await rpc('Page.captureScreenshot', { format: 'png' }, sid);
  if (r.result?.data) fs.writeFileSync(`${name}.png`, Buffer.from(r.result.data, 'base64'));
}
async function clickAt(p) {
  for (const type of ['mousePressed', 'mouseReleased']) {
    await rpc('Input.dispatchMouseEvent',
      { type, x: p.x, y: p.y, button: 'left', clickCount: 1 }, sid);
  }
}

async function clickAccount(email) {
  // 优先「文本正好等于该邮箱」的最小元素；且必须不含另一个账号的邮箱。
  const js = `(() => {
    const want = ${JSON.stringify(email)};
    const other = ['monesyilya3@gmail.com','nikoaa666666@gmail.com'].filter(e => e !== want);
    const all = [...document.querySelectorAll('div,span,a,li,p')];
    const ok = e => {
      const s = (e.textContent || '').trim();
      if (!s.includes(want)) return false;
      if (other.some(o => s.includes(o))) return false;
      const b = e.getBoundingClientRect();
      return b.width > 20 && b.height > 8;
    };
    let hit = all.find(e => (e.textContent||'').trim() === want && ok(e));
    if (!hit) {
      const cands = all.filter(ok);
      cands.sort((a,b) => {
        const ra=a.getBoundingClientRect(), rb=b.getBoundingClientRect();
        return (ra.width*ra.height) - (rb.width*rb.height);
      });
      hit = cands[0];
    }
    if (!hit) return null;
    hit.scrollIntoView({block:'center'});
    const b = hit.getBoundingClientRect();
    return {x: b.x + b.width/2, y: b.y + b.height/2, text: (hit.textContent||'').trim().slice(0,40)};
  })()`;
  const p = await evaluate(js);
  if (!p) return false;
  await clickAt(p);
  console.log('  已选账号:', p.text.replace(/\n/g, ' '));
  return true;
}

async function clickText(needle) {
  const js = `(() => {
    const t = ${JSON.stringify(needle)};
    const all = [...document.querySelectorAll('body *')];
    const hits = all.filter(e => {
      const s = (e.innerText || e.value || e.getAttribute('aria-label') || e.title || '').trim();
      if (!s || !s.includes(t)) return false;
      if (e.children.length > 0 && s.split('\\n').length > 2) return false;
      return true;
    });
    if (!hits.length) return null;
    hits.sort((a, b) => {
      const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
      return (ra.width*ra.height) - (rb.width*rb.height);
    });
    const el = hits[0];
    el.scrollIntoView({block: 'center'});
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return null;
    return {x: r.x + r.width/2, y: r.y + r.height/2, text: (el.innerText||el.value||'').trim().slice(0,40)};
  })()`;
  const p = await evaluate(js);
  if (!p) return false;
  await clickAt(p);
  console.log('  已点击:', p.text.replace(/\n/g, ' '));
  return true;
}

async function fillEmail(email) {
  const js = `(() => {
    const el = document.querySelector('#identifierId')
             || document.querySelector('input[name=identifier]')
             || document.querySelector('input[type=email]');
    if (!el) return null;
    const setter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype, 'value').set;
    setter.call(el, ${JSON.stringify(email)});
    el.dispatchEvent(new Event('input', {bubbles: true}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
    el.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true, key: 'a'}));
    el.focus();
    const b = el.getBoundingClientRect();
    return {x: b.x + b.width/2, y: b.y + b.height/2, v: el.value};
  })()`;
  const p = await evaluate(js);
  if (!p) return false;
  await clickAt(p);
  await sleep(700);
  const v = await evaluate(`(document.querySelector('#identifierId')||{}).value || ''`);
  console.log('  已填邮箱:', email, '-> 框内值长度', (v || '').length);
  return (v || '').length > 5;
}

const ACCOUNT = 'nikoaa666666@gmail.com';
// 不要用 '继续' 这类通用词，会误点「继续前往 xxx」
const BTNS = ['允许', 'Allow', '同意', '我同意', 'Accept', '知道了',
              '下一步', 'Next', '使用其他账号'];

for (let i = 0; i < 12; i++) {
  const info = await evaluate(`({url: location.href, title: document.title,
      body: (document.body ? document.body.innerText : '').slice(0, 500)})`);
  const u = info?.url || '';
  console.log(`\n[${i + 1}] ${u.slice(0, 120)}`);
  console.log('    ', (info?.body || '').replace(/\s*\n\s*/g, ' | ').slice(0, 250));

  if (u.startsWith('http://127.0.0.1:53682')) {
    console.log('=> 已回到 rclone 回调页，授权完成');
    await shot(`${prefix}_done`);
    break;
  }
  await shot(`${prefix}_${i + 1}`);

  let clicked = false;
  if (/signin\/identifier/.test(u)) {
    // 邮箱页：直接填邮箱
    if (await fillEmail(ACCOUNT)) {
      await sleep(1200);
      clicked = await clickText('下一步');
    }
  } else if (/accountchooser/.test(u)) {
    clicked = await clickAccount(ACCOUNT);
  }
  if (!clicked) {
    for (const t of BTNS) {
      if (await clickText(t)) { clicked = true; break; }
    }
  }
  if (!clicked) console.log('    (无可点项)');
  await sleep(2800);
}

const final = await evaluate(`({url: location.href})`);
console.log('\n最终 URL:', (final?.url || '').slice(0, 160));
ws.close();
