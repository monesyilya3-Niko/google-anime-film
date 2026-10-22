# -*- coding: utf-8 -*-
"""列出关键目录子项的 mimeType，判定云文档形态（Google 原生 vs 二进制）。"""
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

TARGETS = {
    "ROOT 1ya8...": "1ya8IwwmFgLWCSE9i_sihtXyTmdW4R528",
    "V17 1gOk...": "1gOkAIAs2gY3uXK48R1VCwTiuagMpTOXG",
    "V19 103f...": "103fzTVsi34QCz6hkpHTzR7RJNsTmZgN-",
}
for label, fid in TARGETS.items():
    q = urllib.parse.quote(f"'{fid}' in parents and trashed=false")
    url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
           "&fields=files(id,name,mimeType,size,createdTime,modifiedTime,md5Checksum)"
           "&pageSize=300&orderBy=name&supportsAllDrives=true&includeItemsFromAllDrives=true")
    print(f"=== {label} ===")
    for f in api(url).get("files", []):
        mt = f["mimeType"].replace("application/vnd.google-apps.", "G/").replace(
            "application/vnd.openxmlformats-officedocument.", "OOXML/")
        idlen = len(f["id"])
        print(f"  {f['name'][:70]:72s} {mt:34s} {int(f.get('size',0))//1024:>6}KB  id{idlen:>3}  {f.get('modifiedTime','')[:10]}")
    print()
