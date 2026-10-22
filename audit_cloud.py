# -*- coding: utf-8 -*-
"""云端深度交叉核对 A：
- 清单里每个 primary_drive_file_id 是否真实存在、名字是否对得上、size 是否一致
- auxiliary_cloud_assets 里的锁脸基准是否都存在
- 主母带引用是否与母带库实际文件一致
- 全云 0 字节 / 异常大小文件扫描
"""
import json
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, list_in, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

ASSETS = "1aRc6-MNuk7wsd1OFhjZPMQGXck-OIpxG"
V17 = "1gOkAIAs2gY3uXK48R1VCwTiuagMpTOXG"
V16 = "1ya8IwwmFgLWCSE9i_sihtXyTmdW4R528"
CAND = "1bMyJPEwrfUsnzLhO7soamlvFEVHxkGwy"
REDRAW = "1o6sBhOJJBfVcMJttU7YxzsCCixGdFao0"

problems = []


def check(cond, msg):
    if not cond:
        problems.append(msg)
    return cond


# ── 1) 母带库真实清单 ──
assets = {f["name"]: f for f in list_in(ASSETS).values()}
print(f"母带库 {len(assets)} 张")
for n, f in sorted(assets.items()):
    sz = int(f.get("size", 0))
    check(sz > 100_000, f"母带体积异常/0字节: {n} ({sz}B)")

# ── 2) 180/120 清单核对 ──
local_fixed = ROOT_FIXED = Path(__file__).resolve().parent / "fixed"
for tag, fname in (("180镜", "180Shots.json"), ("120镜", "120Shots.json")):
    p = next(local_fixed.glob(f"*{fname}"), None)
    if not p:
        print(f"!! 本地找不到 {fname}")
        continue
    shots = json.load(open(p, encoding="utf-8"))
    print(f"\n=== {tag}  {len(shots)} 镜 ===")

    nums = [s.get("shot_number", s.get("manus_15s_number")) for s in shots]
    check(nums == list(range(1, len(shots) + 1)), f"{tag} 编号不连续")

    # 主母带：文件名 + File ID（用一次拉取的全量映射做 O(1) 校验，避免逐镜发 API）
    by_id = {f["id"]: (n, f) for n, f in assets.items()}
    bad_name, bad_id, miss_file, size_mismatch = 0, 0, 0, 0
    used = Counter()
    for s in shots:
        fn = s.get("primary_cloud_filename") or s.get("primary_image_path") or ""
        fid = s.get("primary_drive_file_id") or ""
        base = Path(fn).name
        if not base:
            continue
        used[base] += 1
        if base not in assets:
            miss_file += 1
            if miss_file <= 3:
                problems.append(f"{tag} 镜{s.get('shot_number')} 主母带不在母带库: {base}")
            continue
        if fid:
            hit = by_id.get(fid)
            if hit is None:
                bad_id += 1
                if bad_id <= 3:
                    problems.append(f"{tag} 镜{s.get('shot_number')} FileID 不在母带库: {fid[:20]}…")
            elif hit[0] != base:
                bad_name += 1
                if bad_name <= 3:
                    problems.append(f"{tag} FileID 名字不符: 清单 {base[:36]} / 云端 {hit[0][:36]}")
            elif int(hit[1].get("size", 0)) != int(assets[base].get("size", 0)):
                size_mismatch += 1
    print(f"  主母带引用 {sum(used.values())} 次，覆盖 {len(used)} 张母带")
    print(f"  母带不存在 {miss_file} | FileID 指向母带库外 {bad_id} | 名字不符 {bad_name} | size 不符 {size_mismatch}")

    # 锁脸基准（辅助资产）
    aux_missing, aux_names = 0, Counter()
    for s in shots:
        for a in (s.get("auxiliary_cloud_assets") or []):
            fn = a.get("filename") or a.get("primary_cloud_filename") or ""
            if not fn:
                continue
            aux_names[fn] += 1
            if fn not in assets:
                aux_missing += 1
                if aux_missing <= 3:
                    problems.append(f"{tag} 锁脸基准不在母带库: {fn[:50]}")
    print(f"  锁脸基准引用 {sum(aux_names.values())} 次，涉及 {len(aux_names)} 张；母带库缺 {aux_missing}")

    # 场次一致性：同一场戏的镜头是否都指向同一张母带
    scene_map = {}
    for s in shots:
        sc = s.get("scene_id") or s.get("scene") or s.get("scene_number")
        fn = Path(s.get("primary_cloud_filename") or s.get("primary_image_path") or "").name
        if sc is not None and fn:
            scene_map.setdefault(sc, set()).add(fn)
    multi = {k: v for k, v in scene_map.items() if len(v) > 1}
    print(f"  场次数 {len(scene_map)}；同一场次引用多张母带的: {len(multi)}")
    for k, v in list(multi.items())[:5]:
        print(f"     场次 {k}: {[x[:26] for x in v]}")

# ── 3) 全云 0 字节 / 异常文件 ──
print("\n=== 全云 0 字节扫描 ===")
for label, fid in (("V16", V16), ("V17", V17), ("母带库", ASSETS),
                   ("去字修订稿", CAND), ("待重画包", REDRAW)):
    items = list_in(fid)
    zeros = [n for n, f in items.items()
             if not f["mimeType"].endswith("folder") and int(f.get("size", 0)) == 0]
    print(f"  {label:10s} {len(items):>3} 项，0 字节 {len(zeros)}")
    for z in zeros[:3]:
        problems.append(f"{label} 存在 0 字节文件: {z[:50]}")

# ── 4) 去字修订稿 12 张是否与待重画包互斥 ──
cand = {n for n in list_in(CAND) if n.startswith("FIX_")}
red = set()
for sub, f in list_in(REDRAW).items():
    if f["mimeType"].endswith("folder"):
        red |= set(list_in(f["id"]))
overlap = {n for n in cand if any(n[4:] in r for r in red)}
print(f"\n去字修订稿 {len(cand)} 张；待重画包原图 {len([r for r in red if r.endswith('.jpg')])} 张；交集 {len(overlap)}")
for o in list(overlap)[:6]:
    print("   交集:", o[:60])

print("\n" + "=" * 72)
if problems:
    print(f"发现 {len(problems)} 个问题：")
    for x in problems[:40]:
        print("  ✗", x)
else:
    print("云端交叉核对：无问题")
