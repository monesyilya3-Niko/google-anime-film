# -*- coding: utf-8 -*-
"""核对母带库 40 张与 V18 去字定稿 24 张的 md5：确认哪些修复真正合入（同名同 ID 内容替换）。"""
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

ASSETS = "1aRc6-MNuk7wsd1OFhjZPMQGXck-OIpxG"
V18 = "1bMyJPEwrfUsnzLhO7soamlvFEVHxkGwy"


def listing(folder):
    q = urllib.parse.quote(f"'{folder}' in parents and trashed=false")
    url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
           "&fields=files(id,name,size,md5Checksum,createdTime,modifiedTime)"
           "&pageSize=300&supportsAllDrives=true&includeItemsFromAllDrives=true")
    return api(url).get("files", [])


masters = listing(ASSETS)
v18 = listing(V18)
m_by_num = {}
for f in masters:
    m = re.match(r"(\d{2}[a-c]?)_", f["name"])
    if m:
        m_by_num[m.group(1)] = f

print(f"母带 {len(masters)} 张 / V18 目录 {len(v18)} 项\n")
print(f"{'编号':<6}{'母带 ID':<36}{'母带 md5':<34}{'V18 对应':<10}{'一致?':<8}说明")
for f in sorted(v18, key=lambda x: x["name"]):
    m = re.match(r"V18_FIX_(\d{2}[a-c]?)_", f["name"]) or re.match(r"FIX_(\d{2}[a-c]?)_", f["name"])
    if not m:
        continue
    num = m.group(1)
    master = m_by_num.get(num)
    if not master:
        print(f"{num:<6}{'—':<36}{'—':<34}{'有':<10}{'—':<8}母带库无此编号")
        continue
    same = master.get("md5Checksum") == f.get("md5Checksum")
    tag = "相同" if same else "不同"
    print(f"{num:<6}{master['id']:<36}{str(master.get('md5Checksum'))[:32]:<34}"
          f"{f['name'][:8]:<10}{tag:<8}母带{int(master.get('size',0))//1024}KB vs "
          f"此件{int(f.get('size',0))//1024}KB  created={f.get('createdTime','')[:19]}"
          f"{'  <== 内容已合入' if same else ''}")

print("\n=== 母带库逐张 md5（供对照）===")
for num, f in sorted(m_by_num.items()):
    print(f"  {num:<5}{str(f.get('md5Checksum'))[:32]:<34}{int(f.get('size',0))//1024:>6}KB  "
          f"mod={f.get('modifiedTime','')[:19]}")
