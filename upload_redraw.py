# -*- coding: utf-8 -*-
"""上传 V17 新增的两个目录：
  V17_未完成清单                 -> 04_未完成事项清单_V17.md
  V17_待重画_23张_含原图与提示词  -> 母带原图/ + 区域标注图/ + 重画提示词.md + 重画清单.csv
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
PACK = ROOT / "redraw_pack"
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
    b = uuid.uuid4().hex
    meta = json.dumps({"name": name, "parents": [parent]}, ensure_ascii=False)
    head = (f"--{b}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{meta}\r\n"
            f"--{b}\r\nContent-Type: image/jpeg\r\n\r\n").encode()
    tail = f"\r\n--{b}--".encode()
    return api("https://www.googleapis.com/upload/drive/v3/files"
               "?uploadType=multipart&supportsAllDrives=true&fields=id,name,size",
               data=head + data + tail, method="POST",
               ctype=f"multipart/related; boundary={b}")


def upload_any(name, path, parent):
    if path.suffix.lower() in (".jpg", ".jpeg"):
        return upload_binary(name, path, parent)
    return upload_binary(name, path, parent)


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


# ── 1) 未完成清单 ──
F1 = get_or_create_folder("V17_未完成清单 (2026-10-21)", V17)
p = V17DIR / "04_未完成事项清单_V17.md"
old = list_in(F1).get(p.name)
if old:
    api(f"https://www.googleapis.com/drive/v3/files/{old['id']}?supportsAllDrives=true",
        method="DELETE")
did = create_gdoc(p.name, p.read_text(encoding="utf-8"), F1)
print("OK [gdoc] 未完成事项清单 ->", F1, did)

# ── 2) 待重画包 ──
F2 = get_or_create_folder("V17_待重画_23张_含原图与提示词 (2026-10-21)", V17)
print("OK 目录:", F2)
for sub, files in (("母带原图", sorted((PACK / "母带原图").glob("*.jpg"))),
                   ("区域标注图", sorted((PACK / "区域标注图").glob("*.jpg")))):
    sid = get_or_create_folder(sub, F2)
    have = set(list_in(sid).keys())
    n = 0
    for f in files:
        if f.name in have:
            continue
        upload_binary(f.name, f, sid)
        n += 1
    print(f"   OK {sub}/  {n} 个新文件（共 {len(files)}）")

for fn in ("重画提示词.md", "重画清单.csv"):
    f = PACK / fn
    if not f.exists():
        continue
    old = list_in(F2).get(fn)
    if old:
        api(f"https://www.googleapis.com/drive/v3/files/{old['id']}?supportsAllDrives=true",
            method="DELETE")
    upload_binary(fn, f, F2)
    print("   OK", fn)

print("\nV17 目录:", len(list_in(V17)), "项")
print("未完成清单:", len(list_in(F1)), "项")
print("待重画包:", len(list_in(F2)), "项")
