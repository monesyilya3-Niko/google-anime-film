# -*- coding: utf-8 -*-
"""把母带候选去字稿 + 台账 + 整理总结上传到云端 V17 目录。

候选稿用 CANDIDATE_ 前缀单独存放，**不替换真母带**（除已定稿的 05a/05b）。
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
    boundary = uuid.uuid4().hex
    meta = json.dumps({"name": name, "parents": [parent]}, ensure_ascii=False)
    head = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
            f"{meta}\r\n--{boundary}\r\nContent-Type: image/jpeg\r\n\r\n").encode()
    tail = f"\r\n--{boundary}--".encode()
    return api("https://www.googleapis.com/upload/drive/v3/files"
               f"?uploadType=multipart&supportsAllDrives=true&fields=id,name,size",
               data=head + data + tail, method="POST",
               ctype=f"multipart/related; boundary={boundary}")


def create_gdoc(name, text, parent):
    doc = api("https://docs.googleapis.com/v1/documents",
              data=json.dumps({"title": name}).encode(), method="POST",
              ctype="application/json; charset=UTF-8")
    did = doc["documentId"]
    old_parents = api(f"https://www.googleapis.com/drive/v3/files/{did}"
                      f"?fields=parents&supportsAllDrives=true").get("parents", [])
    rm = "&removeParents=" + urllib.parse.quote(old_parents[0], safe="") if old_parents else ""
    api(f"https://www.googleapis.com/drive/v3/files/{did}"
        f"?addParents={parent}{rm}&supportsAllDrives=true&fields=id,name,parents",
        data=json.dumps({"name": name}).encode(),
        method="PATCH", ctype="application/json; charset=UTF-8")
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


# ── 1) 候选去字稿（独立文件夹）──
CAND = get_or_create_folder("母带候选去字稿_待人工确认 (2026-10-20)", V17)
have = set(list_in(CAND).keys())
n = 0
for p in sorted(GEN.glob("*.jpg")):
    if p.name.startswith("02_") or p.name in ("after_10.jpg", "detext_compare.jpg", "cmp_02.jpg", "locate_all.jpg",
                  "18b_grid.jpg", "preview.png", "preview_edit.png", "02_图2.1")
        continue
    name = "CANDIDATE_" + p.name
    if name in have:
        print("  – 已存在，跳过:", name[:56])
        continue
    r = upload_binary(name, p, CAND)
    n += 1
    print(f"  OK {name[:62]}  {int(r.get('size',0))//1024} KB")
print(f"候选稿文件夹: {CAND}  新增 {n}")

# ── 2) 台账 + 整理总结（原生 Google 文档）──
for fn in ("母带台账_40张.md",):
    p = V17DIR / fn
    if p.exists():
        did = create_gdoc(fn, p.read_text(encoding="utf-8"), V17)
        print("  OK [gdoc]", fn, did)

# 02_ 修订清单：覆盖上传（内容已更新）
p = V17DIR / "02_4K母带画面修订清单_V17.md"
old = list_in(V17).get("02_4K母带画面修订清单_V17.md")
if old:
    api(f"https://www.googleapis.com/drive/v3/files/{old['id']}?supportsAllDrives=true",
        method="DELETE")
    print("  删旧版 02_")
if p.exists():
    did = create_gdoc(p.name, p.read_text(encoding="utf-8"), V17)
    print("  OK [gdoc]", p.name, did)

# ── 3) 母带台账 CSV 也上传一份（可下载/筛选）──
csv = V17DIR / "母带台账_40张.csv"
if csv.exists():
    r = upload_binary(csv.name, csv, V17)
    print("  OK [csv]", csv.name, r["id"])

print("\nV17 目录现有:", len(list_in(V17)), "个文件")
