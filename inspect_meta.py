# -*- coding: utf-8 -*-
"""修复前元数据核对：V19 目录内文件 ID/MIME、待重画包两个文本文件、180 JSON 往返排版测试。"""
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, list_in  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

V19 = "103fzTVsi34QCz6hkpHTzR7RJNsTmZgN-"
PACK = "1o6sBhOJJBfVcMJttU7YxzsCCixGdFao0"
J180 = "15fC3MHNYCklvPmdmZsLba6uiqVGYhOgA"

print("=" * 86)
print("1. V19 目录")
print("=" * 86)
for name, f in sorted(list_in(V19).items()):
    print(f"  {f['id']}  {f['mimeType']:<52} {int(f.get('size', 0)):>9}B  {name}")

print("\n" + "=" * 86)
print("2. 待重画包")
print("=" * 86)
for name, f in sorted(list_in(PACK).items()):
    print(f"  {f['id']}  {f['mimeType']:<40} {int(f.get('size', 0)):>9}B  {name}")

print("\n" + "=" * 86)
print("3. 180 JSON 元数据")
print("=" * 86)
meta = api(f"https://www.googleapis.com/drive/v3/files/{J180}"
           "?fields=id,name,mimeType,size,md5Checksum&supportsAllDrives=true")
for k, v in meta.items():
    print(f"  {k}: {v}")

print("\n" + "=" * 86)
print("4. JSON 往返排版测试（indent=1, ensure_ascii=False）")
print("=" * 86)
CACHE = Path(__file__).resolve().parent / "source" / "audit"
p = CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json"
raw = p.read_text(encoding="utf-8")
obj = json.loads(raw)
out = json.dumps(obj, ensure_ascii=False, indent=1)
print(f"  原文字节 {len(raw.encode('utf-8'))}  重排字节 {len(out.encode('utf-8'))}")
print(f"  原文末尾换行: {raw.endswith(chr(10))}  重排末尾换行: {out.endswith(chr(10))}")
print(f"  完全一致: {out == raw}")
if out != raw:
    import difflib
    diff = list(difflib.unified_diff(raw.splitlines(), out.splitlines(), n=1, lineterm=""))
    print(f"  差异行数 {len(diff)}，前 40 行：")
    for ln in diff[:40]:
        print("   ", ln[:160])
