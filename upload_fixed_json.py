# -*- coding: utf-8 -*-
"""上传 Shot_007 修复后的 180 JSON，并做字节/逐镜回读验证。"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
FID = "15fC3MHNYCklvPmdmZsLba6uiqVGYhOgA"
FIXED = Path(__file__).resolve().parent / "fixed" / "180Shots_V19_shot007fix.json"
CUR = (Path(__file__).resolve().parent / "source" / "audit" / "cloud_current" /
       "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json")

data = FIXED.read_bytes()
md5 = hashlib.md5(data).hexdigest()
print(f"本地修复件 {len(data)}B md5={md5}")

before_meta = api(f"https://www.googleapis.com/drive/v3/files/{FID}"
                  "?fields=id,name,mimeType,size,md5Checksum&supportsAllDrives=true")
print(f"上传前云端 {before_meta['size']}B md5={before_meta.get('md5Checksum')}")

r = api(f"https://www.googleapis.com/upload/drive/v3/files/{FID}"
        "?uploadType=media&supportsAllDrives=true&fields=id,name,mimeType,size,md5Checksum",
        data=data, method="PATCH", ctype="application/json")
print(f"上传返回 {r.get('size')}B mime={r.get('mimeType')} md5={r.get('md5Checksum')}")
assert r.get("md5Checksum") == md5

after = api(f"https://www.googleapis.com/drive/v3/files/{FID}?alt=media&supportsAllDrives=true", raw=True)
print(f"回读 {len(after)}B md5={hashlib.md5(after).hexdigest()}")
assert after == data, "回读字节与本地修复件不一致"

new = json.loads(after.decode("utf-8"))
old = json.loads(CUR.read_text(encoding="utf-8"))
assert len(new) == len(old) == 180
diffs = []
for a, b in zip(old, new):
    if a != b:
        changed = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
        diffs.append((a["shot_number"], sorted(changed)))
print(f"与上传前逐镜差异：{diffs}")
assert diffs == [(7, ["cloud_dispatch_command_zh", "primary_image_path", "upload_instruction"])]

s7 = new[6]
print("\nShot_007 回读：")
for k in ("primary_image_path", "primary_cloud_filename", "primary_drive_file_id"):
    print(f"  {k} = {s7[k]}")
for k in ("upload_instruction", "cloud_dispatch_command_zh"):
    print(f"  {k}: 01c 名 {s7[k].count('01c_图0.1')} 次 / 16S3Lyt2 {s7[k].count('16S3Lyt2')} 次 / 旧名 {s7[k].count('04_图3.1')} 次 / 旧ID {s7[k].count('1pkU017')} 次")
print("\n✔ 180 JSON 已修复并回读验证")
