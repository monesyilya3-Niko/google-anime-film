# -*- coding: utf-8 -*-
"""清掉上传脚本产生的 0KB 空占位，并回读 README 校验内容。"""
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

ROOT_ID = "1ya8IwwmFgLWCSE9i_sihtXyTmdW4R528"
STRAY = "1lcUi9-JG7rJo0TWkaUleJYpKYFgpHIU5"   # 空占位
REAL = "1ZSZ-suR1vPyw37EgFLEEtTledCsy7hga"     # 真 README

# 1) 回读真 README 内容
req = urllib.request.Request(
    f"https://www.googleapis.com/drive/v3/files/{REAL}?alt=media&supportsAllDrives=true",
    headers={"Authorization": api.__globals__["H"]["Authorization"]})
with urllib.request.urlopen(req, timeout=180) as r:
    back = r.read()
print(f"回读 {len(back):,} 字节  md5={hashlib.md5(back).hexdigest()}")
head = back.decode("utf-8").splitlines()
print("前 3 行：")
for line in head[:3]:
    print("   " + line)
print(f"末行：{head[-1][:120]}")

local = (Path(__file__).resolve().parent / "00_README_工程总入口与交接说明.md").read_bytes()
print(f"与本地一致？{'✔ 一致' if back == local else '✘ 不一致'}")

# 2) 空占位移入回收站（可 30 天内恢复；为上传脚本误建）
api(f"https://www.googleapis.com/drive/v3/files/{STRAY}?supportsAllDrives=true",
    data=json.dumps({"trashed": True}).encode(), method="PATCH",
    ctype="application/json; charset=UTF-8")
print(f"\n空占位 {STRAY} 已移入回收站")

# 3) 根目录终态
q = urllib.parse.quote(f"'{ROOT_ID}' in parents and trashed=false")
url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
       "&fields=files(id,name,mimeType,size,md5Checksum)&pageSize=100&supportsAllDrives=true")
kids = api(url).get("files", [])
print(f"\n=== 根目录终态（{len(kids)} 项）===")
for f in kids:
    kind = "DIR " if f["mimeType"].endswith("folder") else "FILE"
    print(f"  [{kind}] {f['name']}   {int(f.get('size', 0))//1024}KB   {f['id']}")
