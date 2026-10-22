# -*- coding: utf-8 -*-
"""扫描 gdrive2 账号全盘，找出「已知目录之外」的散落文件（= 可以清掉的残留）。"""
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

KNOWN = {
    "1ya8IwwmFgLWCSE9i_sihtXyTmdW4R528": "V16 全案总库",
    "1aRc6-MNuk7wsd1OFhjZPMQGXck-OIpxG": "4K 母带库",
    "1gOkAIAs2gY3uXK48R1VCwTiuagMpTOXG": "V17 修复版",
    "1bMyJPEwrfUsnzLhO7soamlvFEVHxkGwy": "母带去字修订稿_待人工确认",
}

print("=== gdrive2 全盘逐层扫描 ===\n")
seen = set()
queue = [("root", None)]
strays = []
count = 0
while queue:
    label, parent = queue.pop(0)
    if parent is None:
        q = urllib.parse.quote("'root' in parents and trashed=false")
    else:
        q = urllib.parse.quote(f"'{parent}' in parents and trashed=false")
    url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
           "&fields=files(id,name,mimeType,size,parents,trashed)&pageSize=300"
           "&supportsAllDrives=true&includeItemsFromAllDrives=true")
    files = api(url).get("files", [])
    for f in files:
        count += 1
        if f["id"] in seen:
            continue
        seen.add(f["id"])
        is_dir = f["mimeType"].endswith("folder")
        tag = "DIR " if is_dir else "FILE"
        print(f"  [{tag}] {f['name'][:66]:68s} {int(f.get('size', 0))//1024:>6} KB"
              f"   <- {label}")
        if is_dir:
            queue.append((f["name"][:40], f["id"]))
        else:
            # 散落文件：不在任何已知目录下
            in_known = any(f["id"] == k for k in KNOWN)
            parents = f.get("parents", [])
            if not in_known:
                strays.append(f)
    print()

print("=" * 72)
print(f"总计 {count} 个对象，{len(strays)} 个散落文件（不在已知目录下）")
for f in strays:
    print(f"  ? {f['name'][:66]}  {f['id']}")
