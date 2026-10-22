# -*- coding: utf-8 -*-
"""把 V17 修复结果回写到 Google Drive。

在 V16 工程总库下新建子文件夹「V17_深度体检修复版」，内容与原工程同构：
  - 两个结构化清单（.json，二进制文件）
  - 7 卷 Act 分镜手册 + 总控调取指令总表 → **原生 Google 文档**（与 V16 同格式）
  - 3 份新增交付件 → 原生 Google 文档
V16 原有文件一律不动，40 张 4K 母带一个字节不改。

用法: python upload_v17.py [--dry]
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
# 云端原图不再在本地留副本（用 pull_v16.py 拉回），所以这里不做强制目录查找
_V16_CANDS = [d for d in ROOT.iterdir() if d.is_dir() and d.name.startswith("《")]
_SRC = ROOT / "source"
if _SRC.is_dir():
    _V16_CANDS += [d for d in _SRC.iterdir() if d.is_dir() and d.name.startswith("《")]
V16_DIR = _V16_CANDS[0] if _V16_CANDS else None
V17_OUT = ROOT / "v17_out"
V17_DOCS = ROOT / "v17"
CONF = Path(os.environ["APPDATA"]) / "rclone" / "rclone.conf"

V16_FOLDER_NAME_FRAG = "\u5168\u6848\u5de5\u7a0b\u603b\u5e93"          # 全案工程总库
NEW_FOLDER = "V17_深度体检修复版 (2026-10-19)"


def fresh_token():
    from datetime import datetime, timedelta
    from urllib.parse import urlencode
    txt = CONF.read_text(encoding="utf-8")
    blk = re.search(r"(?ms)^\[gdrive2\](.*?)(?=^\[|\Z)", txt).group(1)
    tk = json.loads(re.search(r"token = (\{.*?\})", blk).group(1))
    exp = tk.get("expiry")
    still_valid = False
    if exp:
        try:
            e = datetime.fromisoformat(str(exp))
            if e.tzinfo is None:
                e = e.replace(tzinfo=datetime.now().astimezone().tzinfo)
            still_valid = e > datetime.now(e.tzinfo) + timedelta(minutes=3)
        except Exception:
            # rclone 有时写 unix 时间戳
            try:
                still_valid = float(exp) > time.time() + 180
            except Exception:
                still_valid = False
    if still_valid:
        return tk["access_token"]
    data = urlencode({
        "client_id": re.search(r"client_id = (\S+)", blk).group(1),
        "client_secret": re.search(r"client_secret = (\S+)", blk).group(1),
        "refresh_token": tk["refresh_token"], "grant_type": "refresh_token"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=60) as r:
        j = json.loads(r.read().decode("utf-8"))
    tk["access_token"] = j["access_token"]
    tk["expiry"] = j.get("expiry", "")
    CONF.write_text(txt.replace(blk, re.sub(r"token = \{.*?\}",
                                           "token = " + json.dumps(tk, ensure_ascii=False),
                                           blk, flags=re.S)), encoding="utf-8")
    return j["access_token"]


TOKEN = fresh_token()
H = {"Authorization": "Bearer " + TOKEN}


def refresh(force=True):
    """强制刷新 access token，并同步模块级 H（api() 用的是模块全局）。"""
    global TOKEN, H
    if force:
        from datetime import datetime, timedelta
        txt = CONF.read_text(encoding="utf-8")
        blk = re.search(r"(?ms)^\[gdrive2\](.*?)(?=^\[|\Z)", txt).group(1)
        tk = json.loads(re.search(r"token = (\{.*?\})", blk).group(1))
        tk["expiry"] = ""            # 逼下一次 fresh_token 走刷新分支
        CONF.write_text(txt.replace(blk, re.sub(r"token = \{.*?\}",
                                               "token = " + json.dumps(tk, ensure_ascii=False),
                                               blk, flags=re.S)), encoding="utf-8")
    TOKEN = fresh_token()
    H = {"Authorization": "Bearer " + TOKEN}
    return TOKEN


def api(url, data=None, method=None, ctype=None, raw=False, retries=4):
    headers = dict(H)
    if ctype:
        headers["Content-Type"] = ctype
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                b = r.read()
            return b if raw else (json.loads(b.decode("utf-8")) if b.strip() else {})
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:400]
            if e.code in (500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise SystemExit(f"API 失败 {e.code}: {method or 'GET'} {url[:110]}\n  {body}")
        except (urllib.error.URLError, OSError) as e:
            last = e
            if attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise SystemExit(f"网络失败（已重试 {retries} 次）: {method or 'GET'} {url[:90]}\n  {e}")
    raise SystemExit(f"API 失败: {last}")


def list_in(folder):
    q = urllib.parse.quote(f"'{folder}' in parents and trashed=false")
    url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
           "&fields=files(id,name,mimeType,size)&pageSize=200"
           "&supportsAllDrives=true&includeItemsFromAllDrives=true")
    return {f["name"]: f for f in api(url).get("files", [])}


def find_folder(frag):
    q = urllib.parse.quote(f"name contains '{frag}' and trashed=false")
    url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
           "&fields=files(id,name,mimeType)&pageSize=20&supportsAllDrives=true"
           "&includeItemsFromAllDrives=true")
    for f in api(url).get("files", []):
        if f["mimeType"] == "application/vnd.google-apps.folder":
            return f
    return None


def create_folder(name, parent):
    body = json.dumps({
        "name": name, "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent]}).encode()
    return api("https://www.googleapis.com/drive/v3/files?supportsAllDrives=true",
               data=body, method="POST",
               ctype="application/json; charset=UTF-8")


def upload_binary(name, path, parent):
    data = path.read_bytes()
    boundary = uuid.uuid4().hex
    meta = json.dumps({"name": name, "parents": [parent]}, ensure_ascii=False)
    head = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
            f"{meta}\r\n--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n").encode()
    tail = f"\r\n--{boundary}--".encode()
    body = head + data + tail
    return api(f"https://www.googleapis.com/upload/drive/v3/files"
               f"?uploadType=multipart&supportsAllDrives=true&fields=id,name",
               data=body, method="POST",
               ctype=f"multipart/related; boundary={boundary}")


def create_gdoc(name, text, parent):
    """建原生 Google 文档并灌入内容（分块 insertText，绕开 100KB/请求上限）。"""
    doc = api("https://docs.googleapis.com/v1/documents",
              data=json.dumps({"title": name}).encode(), method="POST",
              ctype="application/json; charset=UTF-8")
    did = doc["documentId"]
    # 移到目标文件夹 + 改名
    api(f"https://www.googleapis.com/drive/v3/files/{did}"
       f"?addParents={parent}&supportsAllDrives=true&fields=id,name,parents",
       data=json.dumps({"name": name}).encode(),
       method="PATCH", ctype="application/json; charset=UTF-8")
    # 新建文档自带一个空段，正文直接插在 index 1（末尾换行保留，正好是段分隔）
    CH = 90000
    idx = 1
    i = 0
    while i < len(text):
        chunk = text[i:i + CH]
        api(f"https://docs.googleapis.com/v1/documents/{did}:batchUpdate",
            data=json.dumps({"requests": [
                {"insertText": {"location": {"index": idx}, "text": chunk}}]}).encode(),
            method="POST", ctype="application/json; charset=UTF-8")
        idx += len(chunk)
        i += CH
    return did


def doc_text(did):
    try:
        d = api(f"https://docs.googleapis.com/v1/documents/{did}")
        out = []
        for p in d.get("body", {}).get("content", []):
            for e in p.get("paragraph", {}).get("elements", []):
                out.append(e.get("textRun", {}).get("content", ""))
        return "".join(out)
    except Exception:
        return ""


def doc_text_len(did):
    return len(doc_text(did))


def main():
    dry = "--dry" in sys.argv
    v16 = find_folder(V16_FOLDER_NAME_FRAG)
    if not v16:
        print("找不到 V16 工程总库")
        return
    print(f"V16 工程总库: {v16['name']}  ({v16['id']})")

    if dry:
        print("\n[DRY] 将要上传:")
        for p in sorted(FIXED.glob("*.json")) if (FIXED := ROOT / "fixed").exists() else []:
            print("  [json]", p.name)
        for p in sorted(V17_OUT.glob("*.md")):
            print("  [gdoc]", p.name)
        for p in sorted(V17_DOCS.glob("*.md")):
            print("  [gdoc]", p.name)
        return

    # 复用同名文件夹（重跑不要重复建）
    existing = None
    q = urllib.parse.quote(f"'{v16['id']}' in parents and name = '{NEW_FOLDER}' and trashed=false")
    url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
           "&fields=files(id,name,mimeType)&pageSize=10&supportsAllDrives=true"
           "&includeItemsFromAllDrives=true")
    hits = [f for f in api(url).get("files", [])
            if f["mimeType"] == "application/vnd.google-apps.folder"]
    if hits:
        folder = hits[0]
        print(f"复用文件夹: {folder['name']}  ({folder['id']})")
    else:
        folder = create_folder(NEW_FOLDER, v16["id"])
        print(f"新建文件夹: {folder['name']}  ({folder['id']})")
    print()
    have = list_in(folder["id"])

    n = 0
    replace = "--replace" in sys.argv
    for p in sorted((ROOT / "fixed").glob("*.json")):
        if p.name in have:
            if not replace:
                print(f"  – [json] {p.name[:60]} 已存在，跳过")
                continue
            api(f"https://www.googleapis.com/drive/v3/files/{have[p.name]['id']}"
                f"?supportsAllDrives=true", method="DELETE")
            print(f"  ↻ [json] {p.name[:60]} 覆盖旧版")
        r = upload_binary(p.name, p, folder["id"])
        n += 1
        print(f"  ✓ [json] {p.name[:66]}  ({p.stat().st_size/1024:.0f} KB)  id={r['id']}")

    for p in sorted(V17_OUT.glob("*.md")) + sorted(V17_DOCS.glob("*.md")):
        if p.name in have:
            txt = p.read_text(encoding="utf-8")
            if not replace:
                print(f"  – [gdoc] {p.name[:60]} 已存在，跳过")
                continue
            cur = doc_text(have[p.name]["id"])
            # 云端必须与本地等价：长度相当，且本地有的关键标记云端也要有
            same = (len(cur) >= len(txt) * 0.98
                    and ("画面内严禁出现任何文字" not in txt
                         or "画面内严禁出现任何文字" in cur))
            if same:
                print(f"  = [gdoc] {p.name[:56]} 云端已是最新版，跳过")
                continue
            api(f"https://www.googleapis.com/drive/v3/files/{have[p.name]['id']}"
                f"?supportsAllDrives=true", method="DELETE")
            print(f"  ↻ [gdoc] {p.name[:60]} 覆盖旧版")
        txt = p.read_text(encoding="utf-8")
        did = create_gdoc(p.name, txt, folder["id"])
        n += 1
        print(f"  ✓ [gdoc] {p.name[:66]}  ({len(txt)/1024:.0f} KB)  id={did}")

    print(f"\n共上传 {n} 个文件到「{NEW_FOLDER}」")
    print(f"链接: https://drive.google.com/drive/folders/{folder['id']}")


if __name__ == "__main__":
    main()
