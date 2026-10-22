# -*- coding: utf-8 -*-
"""把 12 张修好的母带 + 台账 + 整理总结上传到云端 V17 目录。

- 旧候选稿目录清空并改名
- 修好的母带以 FIX_ 前缀单独存放，**不替换真母带**（等人工确认后再原地提升）
"""
import json
import sys
import urllib.parse
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, list_in, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

V17 = "1gOkAIAs2gY3uXK48R1VCwTiuagMpTOXG"
ROOT = Path(__file__).resolve().parent
GEN = ROOT / "gen_out"
V17DIR = ROOT / "v17"

FIXED = ["03_", "03b_", "06_", "06a_", "06b_", "07_", "10_", "18_", "18a_",
         "23_", "26_", "27_"]
OLD_CAND = "1fuzd3UjUJ5Sz7P5LeoFA-tD1090JtSME"
NEW_CAND = "母带去字修订稿_待人工确认 (2026-10-20)"


def get_or_create_folder(name, parent):
    q = urllib.parse.quote(f"'{parent}' in parents and name = '{name}' and trashed=false")
    url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
           "&fields=files(id,name,mimeType)&pageSize=10"
           "&supportsAllDrives=true&includeItemsFromAllDrives=true")
    for f in api(url).get("files", []):
        if f["mimeType"] == "application/vnd.google-apps.folder":
            return f["id"]
    body = json.dumps({"name": name, "mimeType": "application/vnd.google-apps.folder",
                       "parents": [parent]}).encode()
    return api("https://www.googleapis.com/drive/v3/files?supportsAllDrives=true",
               data=body, method="POST",
               ctype="application/json; charset=UTF-8")["id"]


def upload_binary(name, path, parent):
    data = path.read_bytes()
    b = uuid.uuid4().hex
    meta = json.dumps({"name": name, "parents": [parent]}, ensure_ascii=False)
    head = (f"--{b}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{meta}\r\n"
            f"--{b}\r\nContent-Type: image/jpeg\r\n\r\n").encode()
    tail = f"\r\n--{b}--".encode()
    return api("https://www.googleapis.com/upload/drive/v3/files"
               "?uploadType=multipart&supportsAllDrives=true&fields=id,name,size",
               data=head + data + tail, method="POST",
               ctype=f"multipart/related; boundary={b}")


def create_gdoc(name, text, parent):
    doc = api("https://docs.googleapis.com/v1/documents",
              data=json.dumps({"title": name}).encode(), method="POST",
              ctype="application/json; charset=UTF-8")
    did = doc["documentId"]
    old = api(f"https://www.googleapis.com/drive/v3/files/{did}"
              f"?fields=parents&supportsAllDrives=true").get("parents", [])
    rm = "&removeParents=" + urllib.parse.quote(old[0], safe="") if old else ""
    api(f"https://www.googleapis.com/drive/v3/files/{did}"
        f"?addParents={parent}{rm}&supportsAllDrives=true&fields=id,name,parents",
        data=json.dumps({"name": name}).encode(), method="PATCH",
        ctype="application/json; charset=UTF-8")
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


# ── 1) 清掉旧候选稿目录 ──
print("清理旧候选稿目录:", OLD_CAND)
for f in list_in(OLD_CAND).values():
    api(f"https://www.googleapis.com/drive/v3/files/{f['id']}?supportsAllDrives=true",
        method="DELETE")
    print("   ✗ 已删:", f["name"][:60])
api(f"https://www.googleapis.com/drive/v3/files/{OLD_CAND}?supportsAllDrives=true",
    method="DELETE")
print("   ✗ 旧目录已删")

# ── 2) 新目录 + 12 张修好的母带 ──
CAND = get_or_create_folder(NEW_CAND, V17)
print(f"\n新目录: {NEW_CAND}  ({CAND})")
have = set(list_in(CAND).keys())
n = 0
for pref in FIXED:
    src = next((p for p in sorted(GEN.glob(pref + "*.jpg"))), None)
    if not src:
        print("   ! 本地缺:", pref)
        continue
    name = "FIX_" + src.name
    if name in have:
        print("   – 已存在:", name[:62])
        continue
    r = upload_binary(name, src, CAND)
    n += 1
    print(f"   OK {name[:66]}  {int(r.get('size', 0)) // 1024} KB")
print(f"新增 {n} 张")

# ── 3) 文档：台账 + 整理总结（覆盖旧版）──
for fn in ("母带台账_40张.md", "02_4K母带画面修订清单_V17.md"):
    p = V17DIR / fn
    if not p.exists():
        continue
    old = list_in(V17).get(fn)
    if old:
        api(f"https://www.googleapis.com/drive/v3/files/{old['id']}?supportsAllDrives=true",
            method="DELETE")
        print("   删旧版:", fn)
    did = create_gdoc(fn, p.read_text(encoding="utf-8"), V17)
    print("   OK [gdoc]", fn, did)

csv = V17DIR / "母带台账_40张.csv"
if csv.exists():
    old = list_in(V17).get(csv.name)
    if old:
        api(f"https://www.googleapis.com/drive/v3/files/{old['id']}?supportsAllDrives=true",
            method="DELETE")
    upload_binary(csv.name, csv, V17)
    print("   OK [csv]", csv.name)

print("\nV17 目录:", len(list_in(V17)), "项 | 修好母带目录:", len(list_in(CAND)), "张")
