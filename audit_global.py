# -*- coding: utf-8 -*-
"""体检 F：395 引用的真实口径、V18 目录 24 件、全库散落/重复/0KB 扫描。"""
import json
import re
import sys
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, list_in, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
ASSETS = "1aRc6-MNuk7wsd1OFhjZPMQGXck-OIpxG"
V19 = "103fzTVsi34QCz6hkpHTzR7RJNsTmZgN-"
V17 = "1gOkAIAs2gY3uXK48R1VCwTiuagMpTOXG"
PACK = "1o6sBhOJJBfVcMJttU7YxzsCCixGdFao0"
V18 = "1bMyJPEwrfUsnzLhO7soamlvFEVHxkGwy"
V17_TODO = None
ROOTID = "1ya8IwwmFgLWCSE9i_sihtXyTmdW4R528"

assets = list_in(ASSETS)
asset_ids = set(f["id"] for f in assets.values())
by_id = {f["id"]: n for n, f in assets.items()}

print("=" * 84)
print("F1. “395 个真实图片引用”的机器复算（按出现次数，不去重）")
print("=" * 84)
tot = Counter()
for tag, fname in (("180", "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json"),
                   ("120", "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json")):
    shots = json.loads((CACHE / fname).read_text(encoding="utf-8"))
    prim = aux = frame = 0
    for s in shots:
        if s.get("primary_drive_file_id") in asset_ids:
            prim += 1
        aux += sum(1 for m in re.findall(r"\b1[A-Za-z0-9_-]{32}\b", str(s.get("auxiliary_cloud_assets", "")))
                   if m in asset_ids)
        for k in ("first_frame_drive_file_id", "end_frame_drive_file_id"):
            frame += sum(1 for m in re.findall(r"\b1[A-Za-z0-9_-]{32}\b", str(s.get(k, ""))) if m in asset_ids)
    print(f"  {tag} 轨：主母带 {prim} + 辅助 {aux} + 首尾帧 {frame} = {prim + aux + frame}")
    tot[tag] = (prim, aux, frame)
s = sum(v[0] for v in tot.values()), sum(v[1] for v in tot.values()), sum(v[2] for v in tot.values())
print(f"  合计：主母带 {s[0]} + 辅助 {s[1]} + 首尾帧 {s[2]} = {sum(s)}")
print(f"  若只算 主母带+首尾帧 = {s[0] + s[2]}（与 395 对照）")

print("\n" + "=" * 84)
print("F2. V18 精修目录 24 件（V18_FIX_ 12 + FIX_ 12）")
print("=" * 84)
v18 = list_in(V18)
for n, f in sorted(v18.items()):
    tag = "V18" if n.startswith("V18_FIX_") else ("旧FIX" if n.startswith("FIX_") else "其他")
    print(f"  [{tag}] {int(f.get('size', 0)) // 1024:>5}KB  {n}")
print(f"  合计 {len(v18)} 件；V18_FIX_ {sum(1 for n in v18 if n.startswith('V18_FIX_'))}，"
      f"FIX_ {sum(1 for n in v18 if n.startswith('FIX_'))}")

print("\n" + "=" * 84)
print("F3. 全库扫描：0 字节 / 重名")
print("=" * 84)
folders = {
    "根": ROOTID, "V19": V19, "V17": V17, "母带库": ASSETS, "重画包": PACK, "V18": V18,
}
all_files = []
for label, fid in folders.items():
    d = list_in(fid)
    for n, f in d.items():
        if f.get("mimeType") == "application/vnd.google-apps.folder":
            continue
        all_files.append((label, n, f))
        if int(f.get("size", 0)) == 0:
            print(f"  ! 0 字节：{label} / {n} ({f['id']})")
# 子目录递归一层
for fid in (PACK, V17):
    for n, f in list_in(fid).items():
        if f.get("mimeType") == "application/vnd.google-apps.folder":
            for n2, f2 in list_in(f["id"]).items():
                all_files.append((n, n2, f2))
                if int(f2.get("size", 0)) == 0:
                    print(f"  ! 0 字节：{n} / {n2} ({f2['id']})")
print(f"  非目录文件合计 {len(all_files)} 件")
byname = defaultdict(list)
for label, n, f in all_files:
    byname[n].append((label, f))
dups = {n: v for n, v in byname.items() if len(v) > 1}
print(f"  同名文件 {len(dups)} 组：")
for n, v in sorted(dups.items()):
    print(f"     {n[:60]:62s} {[(x[0], x[1].get('size')) for x in v]}")

print("\n" + "=" * 84)
print("F4. 重画包内 23 张“母带原图”与母带库现版的同版/过期（复核）")
print("=" * 84)
pack_root = list_in(PACK)
orig = list_in(pack_root["母带原图"]["id"])
for n, f in sorted(orig.items()):
    m = assets.get(n)
    same = m and m.get("size") == f.get("size")
    print(f"  {'同版' if same else '过期'} {n[:58]:60s} 包{int(f['size']) // 1024:>5}KB 库{int(m['size']) // 1024 if m else 0:>5}KB")
