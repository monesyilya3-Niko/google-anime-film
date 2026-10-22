# -*- coding: utf-8 -*-
"""打印工程总库根目录元信息与现有 README，作为上传前置检查。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

ROOT_ID = "1ya8IwwmFgLWCSE9i_sihtXyTmdW4R528"
meta = api(f"https://www.googleapis.com/drive/v3/files/{ROOT_ID}"
           "?fields=id,name,mimeType,owners(emailAddress),shared,capabilities(canAddChildren),webViewLink"
           "&supportsAllDrives=true")
print("根目录：")
for k, v in meta.items():
    print(f"  {k} = {v}")

import urllib.parse  # noqa: E402
q = urllib.parse.quote(f"'{ROOT_ID}' in parents and trashed=false")
url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
       "&fields=files(id,name,mimeType,size)&pageSize=100&supportsAllDrives=true")
print("\n根目录现有子项：")
for f in api(url).get("files", []):
    print(f"  - {f['name']}  [{f['mimeType']}]  {int(f.get('size',0))//1024}KB  {f['id']}")
