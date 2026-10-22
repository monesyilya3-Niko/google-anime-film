# -*- coding: utf-8 -*-
"""用还活着的 gdrive（monesyilya3@gmail.com）token 查一下：
   暮冬念春项目文件是否共享到了这个账号下。
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
CONF = Path(os.environ["APPDATA"]) / "rclone" / "rclone.conf"
txt = CONF.read_text(encoding="utf-8")
blk = re.search(r"(?ms)^\[gdrive\](.*?)(?=^\[|\Z)", txt).group(1)
tk = json.loads(re.search(r"token = (\{.*?\})", blk).group(1))
H = {"Authorization": "Bearer " + tk["access_token"]}


def api(url):
    req = urllib.request.Request(url, headers=H)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


for q in ("name contains '暮冬' and trashed=false",
          "name contains '母带' and trashed=false",
          "name contains 'V16' and trashed=false",
          "name contains 'assets_4k' and trashed=false"):
    u = ("https://www.googleapis.com/drive/v3/files?q=" + urllib.parse.quote(q)
         + "&fields=files(id,name,parents,owners(emailAddress),shared)&pageSize=50"
         "&supportsAllDrives=true&includeItemsFromAllDrives=true"
         "&corpora=allDrives")
    try:
        res = api(u).get("files", [])
    except Exception as e:
        print("查询失败:", e)
        continue
    print(f"\n[q] {q}  -> {len(res)} 条")
    for f in res[:12]:
        owners = ",".join(o.get("emailAddress", "") for o in f.get("owners", []))
        print(f"   {f['name'][:60]:62s} owners={owners[:40]} shared={f.get('shared')}")
