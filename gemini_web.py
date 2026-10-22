# -*- coding: utf-8 -*-
"""用 Gemini 网页版（本地 Chrome + CDP）做图像生成/改图。

流程：上传参考图 → 输入指令 → 发送 → 等待出图 → 下载到本地。

用法:
  python gemini_web.py <参考图路径|无> "<指令>" <输出目录> [轮询秒数]
"""
import base64
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
CDP = "http://127.0.0.1:9222"


def rpc(ws, method, params=None, _id=[0]):
    _id[0] += 1
    mid = _id[0]
    out = {}

    def on_msg(ev):
        m = json.loads(ev.data)
        if m.get("id") == mid and "result" in out:
            return
        if m.get("id") == mid:
            out["result"] = m.get("result", {})
            out["error"] = m.get("error")

    ws.addEventListener("message", on_msg)
    ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    t0 = time.time()
    while "result" not in out and "error" not in out and time.time() - t0 < 60:
        time.sleep(0.05)
    ws.removeEventListener("message", on_msg)
    if "error" in out and out["error"]:
        raise RuntimeError(f"{method}: {out['error']}")
    return out.get("result", {})


def connect():
    import http.client
    ts = json.loads(urllib.request.urlopen(f"{CDP}/json", timeout=10).read())
    page = next((t for t in ts if t["type"] == "page"), None)
    if not page:
        raise SystemExit("没有可用的 page target")
    import websocket  # noqa
    return page


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return
    ref = sys.argv[1]
    instr = sys.argv[2]
    outdir = Path(sys.argv[3])
    outdir.mkdir(parents=True, exist_ok=True)
    timeout = int(sys.argv[4]) if len(sys.argv) > 4 else 300

    # 用 node 里的 WebSocket（Node 24 自带全局 WebSocket），避免装依赖
    node_script = r"""
const fs=require('fs');
(async()=>{
  const [ref,instr,outdir,timeout,mode]=process.argv.slice(2);
  const ts=await (await fetch('http://127.0.0.1:9222/json')).json();
  let page=ts.find(t=>t.type==='page');
  if(!page){
    await fetch('http://127.0.0.1:9222/json/new?'+encodeURIComponent('https://gemini.google.com/app'),{method:'PUT'});
    await new Promise(r=>setTimeout(r,3000));
    const ts2=await (await fetch('http://127.0.0.1:9222/json')).json();
    page=ts2.find(t=>t.type==='page');
    if(!page){ console.log('NO_PAGE'); process.exit(1); }
  }
  const ws=new WebSocket(page.webSocketDebuggerUrl);
  await new Promise(r=>ws.addEventListener('open',r,{once:true}));
  let id=0; const pend=new Map();
  ws.addEventListener('message',e=>{const m=JSON.parse(e.data); if(m.id&&pend.has(m.id)){pend.get(m.id)(m); pend.delete(m.id);}});
  const rpc=(method,params={})=>new Promise(res=>{const i=++id; pend.set(i,res); ws.send(JSON.stringify({id:i,method,params}));});
  const ev=async(expr)=>{const r=await rpc('Runtime.evaluate',{expression:expr,returnByValue:true,awaitPromise:true});
    if(r.result?.exceptionDetails) throw new Error(r.result.exceptionDetails.exception?.description||'eval err');
    return r.result?.result?.value;};
  const log=(...a)=>console.log(...a);
  try{
    await rpc('Page.enable'); await rpc('Runtime.enable'); await rpc('DOM.enable');

    // 1) 上传参考图
    if(ref!=='NONE'){
      const doc=await rpc('DOM.getDocument',{depth:-1});
      const q=await rpc('DOM.querySelector',{nodeId:doc.root.nodeId,selector:'input[type=file]'});
      if(!q.nodeId) { log('NO_FILE_INPUT'); }
      else{
        await rpc('DOM.setFileInputFiles',{files:[ref],nodeId:q.nodeId});
        log('UPLOADED', ref);
        await new Promise(r=>setTimeout(r,2500));
      }
    }

    // 2) 输入指令
    const PROMPT_SEL = 'rich-textarea, [contenteditable="true"], textarea.input-area, .ql-editor';
    const focusExpr = `(() => {
      const cands=[...document.querySelectorAll('rich-textarea, [contenteditable=\\"true\\"]')]
        .filter(e=>e.getBoundingClientRect().width>0);
      if(!cands.length) return 'NO_EDITOR';
      const e=cands[cands.length-1];
      e.scrollIntoView({block:'center'});
      const r=e.getBoundingClientRect();
      e.focus();
      return JSON.stringify({x:r.left+r.width/2, y:r.top+r.height/2, tag:e.tagName});
    })()`;
    const fi = await ev(focusExpr);
    log('EDITOR', fi);
    if(typeof fi==='string' && fi.startsWith('{')){
      const o=JSON.parse(fi);
      await rpc('Input.dispatchMouseEvent',{type:'mousePressed',x:o.x,y:o.y,button:'left',clickCount:1,buttons:1});
      await rpc('Input.dispatchMouseEvent',{type:'mouseReleased',x:o.x,y:o.y,button:'left',clickCount:1,buttons:0});
      await rpc('Input.insertText',{text:instr});
      log('TYPED', instr.length, 'chars');
    }
    await new Promise(r=>setTimeout(r,800));

    // 3) 发送（Enter）
    await rpc('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13,text:'\r'});
    await rpc('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13});
    log('SENT');

    // 4) 轮询出图
    const t0=Date.now();
    let got=null;
    while(Date.now()-t0 < timeout*1000){
      await new Promise(r=>setTimeout(r,4000));
      const st=await ev(`(() => {
        const imgs=[...document.querySelectorAll('img')].filter(i=>{
          const r=i.getBoundingClientRect(); return r.width>200 && r.height>200 && i.naturalWidth>400;
        });
        const last=imgs[imgs.length-1];
        const stop=document.body.innerText.includes('停止生成')||document.body.innerText.includes('Stop');
        return JSON.stringify({n:imgs.length, src:last?last.src:null, w:last?last.naturalWidth:0, h:last?last.naturalHeight:0, stop});
      })()`);
      let o={}; try{o=JSON.parse(st)}catch(e){}
      if(o.src && !o.stop){ got=o.src; log('IMAGE', o.w+'x'+o.h); break; }
      if(o.stop) log('...generating');
    }
    if(!got){ log('TIMEOUT_NO_IMAGE'); process.exit(2); }

    // 5) 下载
    const b64 = await ev(`(async()=>{
      const r=await fetch(${JSON.stringify(got)});
      const b=await r.arrayBuffer();
      let s=''; const u=new Uint8Array(b);
      for(let i=0;i<u.length;i+=0x8000) s+=String.fromCharCode.apply(null,u.subarray(i,i+0x8000));
      return btoa(s);
    })()`);
    if(!b64){ log('DOWNLOAD_FAIL'); process.exit(3); }
    const ext = (o.w>=o.h) ? 'png' : 'png';
    const fp = outdir + '/gemini_out.' + ext;
    require('fs').writeFileSync(fp, Buffer.from(b64,'base64'));
    log('SAVED', fp, Math.round(Buffer.from(b64,'base64').length/1024)+'KB');
  }catch(e){ log('ERR', e.message); process.exit(1); }
  ws.close();
})();
"""
    import subprocess
    node = shutil_which = None
    node_exe = "node"
    tmp = Path(os.environ.get("TEMP", ".")) / "_gemini_web_driver.js"
    tmp.write_text(node_script, encoding="utf-8")
    r = subprocess.run([node_exe, str(tmp), ref, instr, str(outdir), str(timeout)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout)
    if r.stderr.strip():
        print("STDERR:", r.stderr[:600])


if __name__ == "__main__":
    main()
