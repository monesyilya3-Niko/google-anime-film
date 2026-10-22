# -*- coding: utf-8 -*-
"""清理云端残留的测试文件，并核对两个账号的完整性。"""
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, list_in, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

# 1) 找所有 _agent* / _wtest* 残留
for remote, folder in (("gdrive2", "1gOkAIAs2gY3uXK48R1VCwTiuagMpTOXG"),):
    pass

V16_FOLDER = "1ya8IwwmFgLWCSE9i_sihtXyTmdW4R528"
ASSETS_FOLDER = "1aRc6-MNuk7wsd1OFhjZPMQGXck-OIpxG"
V17_FOLDER = "1gOkAIAs2gY3uXK48R1VCwTiuagMpTOXG"

for label, fid in (("V16 全案", V16_FOLDER), ("V17 修复版", V17_FOLDER),
                   ("母带库", ASSETS_FOLDER)):
    q = urllib.parse.quote(f"'{fid}' in parents and trashed=false")
    url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
           "&fields=files(id,name,mimeType,size)&pageSize=300"
           "&supportsAllDrives=true&includeItemsFromAllDrives=true")
    files = api(url).get("files", [])
    junk = [f for f in files if "_agent" in f["name"] or "_wtest" in f["name"]
             or f["name"].startswith("_tmp_")]
    print(f"{label}: {len(files)} 个文件" + (f"，其中残留 {len(junk)}" if junk else "，无残留"))
    for f in junk:
        api(f"https://www.googleapis.com/drive/v3/files/{f['id']}?supportsAllDrives=true",
            method="DELETE")
        print(f"   ✗ 已删: {f['name']}")

# 2) 全盘搜 _agent
q = urllib.parse.quote("name contains '_agent' and trashed=false")
url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
       "&fields=files(id,name,size)&pageSize=50&supportsAllDrives=true"
       "&includeItemsFromAllDrives=true")
hits = api(url).get("files", [])
print(f"\n全盘 _agent 残留: {len(hits)}")
for f in hits:
    api(f"https://www.googleapis.com/drive/v3/files/{f['id']}?supportsAllDrives=true",
        method="DELETE")
    print(f"   ✗ 已删: {f['name']} ({f.get('size')} B)")

# 3) 母带库最终核对
files = list_in(ASSETS_FOLDER)
print(f"\n母带库最终: {len(files)} 个文件")
