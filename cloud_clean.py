# -*- coding: utf-8 -*-
"""云端清理：
1) 删除根目录的 _Trash_待清空历史废弃旧版（V12-V15 废弃稿，60+ 个文件）
2) 删除根目录游离的 母带台账_40张.md（V17 目录里已有正式版 gdoc + csv）
3) 检查全盘是否还有其它游离项
"""
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, list_in, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

ROOT_LEVEL = "root"

# 1) 根目录列出
q = urllib.parse.quote("'root' in parents and trashed=false")
url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
       "&fields=files(id,name,mimeType,size)&pageSize=100"
       "&supportsAllDrives=true&includeItemsFromAllDrives=true")
root = api(url).get("files", [])
print("根目录现有:")
for f in root:
    print(f"   [{'DIR ' if f['mimeType'].endswith('folder') else 'FILE'}] "
          f"{f['name'][:70]}  {f['id']}")


def purge_folder(fid, name):
    n = 0
    for f in list_in(fid).values():
        api(f"https://www.googleapis.com/drive/v3/files/{f['id']}?supportsAllDrives=true",
            method="DELETE")
        n += 1
    api(f"https://www.googleapis.com/drive/v3/files/{fid}?supportsAllDrives=true",
        method="DELETE")
    print(f"   ✗ 已删目录「{name}」及其中 {n} 个文件")


# 2) 删废弃目录
for f in root:
    if f["name"].startswith("_Trash_"):
        purge_folder(f["id"], f["name"])

# 3) 删根目录游离台账
for f in root:
    if f["name"] == "母带台账_40张.md":
        api(f"https://www.googleapis.com/drive/v3/files/{f['id']}?supportsAllDrives=true",
            method="DELETE")
        print("   ✗ 已删根目录游离文件:", f["name"])

# 4) 复查
q = urllib.parse.quote("'root' in parents and trashed=false")
url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
       "&fields=files(id,name,mimeType,size)&pageSize=100"
       "&supportsAllDrives=true&includeItemsFromAllDrives=true")
root2 = api(url).get("files", [])
print("\n清理后根目录:")
for f in root2:
    print(f"   [{'DIR ' if f['mimeType'].endswith('folder') else 'FILE'}] {f['name'][:70]}")
print(f"共 {len(root2)} 项（应为 2：V16 总库 + V17 修复版）")
