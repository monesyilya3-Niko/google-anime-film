# -*- coding: utf-8 -*-
"""体检 D：引用计数、帧号连续性、27 号依赖、字段数、V17 子目录、重画包 23 张名单。"""
import json
import re
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, fresh_token, list_in  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

CACHE = Path(__file__).resolve().parent / "source" / "audit"
F180 = CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json"
F120 = CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json"
ASSETS = "1aRc6-MNuk7wsd1OFhjZPMQGXck-OIpxG"
V17 = "1gOkAIAs2gY3uXK48R1VCwTiuagMpTOXG"
PACK = "1o6sBhOJJBfVcMJttU7YxzsCCixGdFao0"


def ids_in(v):
    """从任意值里抽取 Drive 文件 ID（只认母带库真实 ID 更稳，这里先全抽）。"""
    blob = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    return set(re.findall(r"\b1[A-Za-z0-9_-]{32}\b", blob))


assets = {f["name"]: f["id"] for f in list_in(ASSETS).values()}
asset_ids = set(assets.values())
by_id = {v: k for k, v in assets.items()}

print("=" * 84)
print("D1. 引用计数（README 声称 395 个真实引用 / 40 个 ID 被 395 个分镜锁定）")
print("=" * 84)
grand = Counter()
for tag, path in (("180", F180), ("120", F120)):
    shots = json.loads(path.read_text(encoding="utf-8"))
    prim = Counter()
    aux = Counter()
    frame = Counter()
    for s in shots:
        prim[s.get("primary_drive_file_id", "")] += 1
        for x in ids_in(s.get("auxiliary_cloud_assets", "")):
            aux[x] += 1
        for k in ("first_frame_drive_file_id", "end_frame_drive_file_id"):
            for x in ids_in(s.get(k, "")):
                frame[x] += 1
    real_prim = {k: v for k, v in prim.items() if k in asset_ids}
    real_aux = {k: v for k, v in aux.items() if k in asset_ids}
    real_frame = {k: v for k, v in frame.items() if k in asset_ids}
    print(f"  {tag} 轨：主母带 {len([k for k in prim if k])} 个ID / {sum(prim.values())} 处"
          f"（真实命中 {len(real_prim)} 个ID / {sum(real_prim.values())} 处）")
    print(f"        辅助槽位 真实命中 {len(real_aux)} 个ID / {sum(real_aux.values())} 处；"
          f"首尾帧槽位 真实命中 {len(real_frame)} 个ID / {sum(real_frame.values())} 处")
    grand.update(real_prim)
    grand.update(real_aux)
    grand.update(real_frame)
print(f"  两轨合计：真实引用 {sum(grand.values())} 处，涉及母带 {len(grand)} 张")
print(f"  未被任何一轨引用的母带：{sorted(set(assets) - {by_id[i] for i in grand})}")

print("\n" + "=" * 84)
print("D2. 帧号连续性（README 声称 43,200 帧精确闭环）")
print("=" * 84)
for tag, path in (("180", F180), ("120", F120)):
    shots = json.loads(path.read_text(encoding="utf-8"))
    spans, bad = [], []
    for s in shots:
        m = re.match(r"(\d+)[–-](\d+)", str(s.get("frame_range", "")))
        if not m:
            bad.append((s.get("shot_number") or s.get("manus_15s_number"), s.get("frame_range")))
            continue
        spans.append((int(m.group(1)), int(m.group(2))))
    gaps = [(a[1] + 1, b[0]) for a, b in zip(spans, spans[1:]) if b[0] != a[1] + 1]
    print(f"  {tag} 轨：{len(spans)} 段，首 {spans[0]}，末 {spans[-1]}，断口 {len(gaps)}，异常 {len(bad)}")
    print(f"     末帧 = {spans[-1][1]}（43,200 = {'✔' if spans[-1][1] == 43200 else '✘'}）")

print("\n" + "=" * 84)
print("D3. 27 号母带（掌心剧情字）被哪些镜引用")
print("=" * 84)
mid = assets["27_图3.22_Scene22_次年早春融雪窗边左手托左掌写下DBX与YXP_3840x2160_4K.jpg"]
for tag, path in (("180", F180), ("120", F120)):
    shots = json.loads(path.read_text(encoding="utf-8"))
    hits = [s.get("shot_number") or s.get("manus_15s_number") for s in shots
            if s.get("primary_drive_file_id") == mid]
    print(f"  {tag} 轨：{len(hits)} 处 → 镜 {hits}")

print("\n" + "=" * 84)
print("D4. 字段数（README 声称 180 轨 40 字段/镜）")
print("=" * 84)
for tag, path in (("180", F180), ("120", F120)):
    shots = json.loads(path.read_text(encoding="utf-8"))
    cnt = Counter()
    for s in shots:
        for k in s:
            cnt[k] += 1
    full = sum(1 for v in cnt.values() if v == len(shots))
    print(f"  {tag} 轨：字段名 {len(cnt)} 种，全镜齐备 {full} 种，非全员字段 {sorted(k for k, v in cnt.items() if v != len(shots))}")

print("\n" + "=" * 84)
print("D5. V17 目录结构与重画包 23 张名单")
print("=" * 84)
v17 = list_in(V17)
print("  V17 顶层：")
for n, f in sorted(v17.items()):
    kind = "DIR " if f.get("mimeType") == "application/vnd.google-apps.folder" else "FILE"
    print(f"     {kind} {int(f.get('size', 0)) // 1024:>6}KB  {n}")
pack = list_in(PACK)
print("  重画包顶层：")
for n, f in sorted(pack.items()):
    kind = "DIR " if f.get("mimeType") == "application/vnd.google-apps.folder" else "FILE"
    print(f"     {kind} {int(f.get('size', 0)) // 1024:>6}KB  {n}")
orig = list_in(pack["母带原图"]["id"])
marks = list_in(pack["区域标注图"]["id"])
print(f"  母带原图 {len(orig)} 张 / 区域标注图 {len(marks)} 张 / 同名对应 {len(set(orig) & set(marks))}")
print("  23 张底图清单：")
for n in sorted(orig):
    print(f"     {n}")
