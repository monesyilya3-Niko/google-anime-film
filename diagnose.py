# -*- coding: utf-8 -*-
"""追查：三个待确认的疑点。"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
V16 = next(d for d in list(ROOT.iterdir()) + list((ROOT/"source").iterdir())
            if d.is_dir() and d.name.startswith("《"))
ASSETS = next(d for d in ROOT.iterdir() if d.is_dir() and d.name.startswith("40"))
S180 = json.load(open(next(V16.glob("*180Shots.json")), encoding="utf-8"))
S120 = json.load(open(next(V16.glob("*120Shots.json")), encoding="utf-8"))
assets = {f.name for f in ASSETS.glob("*.jpg")}


def num(s):
    return s.get("shot_number", s.get("manus_15s_number"))


def sid(s):
    return s.get("shot_id", s.get("manus_15s_id"))


def img(s):
    return (s.get("primary_image_path") or s.get("primary_cloud_filename") or "").strip()


print("=" * 78)
print("疑点 1：120 镜的幕次划分（从数据自己推，别用 180 镜的区间）")
print("=" * 78)
for name, S in (("180镜", S180), ("120镜", S120)):
    trans = []
    prev = None
    for s in S:
        a = (s.get("act") or "").strip()
        if a != prev:
            trans.append((num(s), a))
            prev = a
    print(f"  {name}: {len(trans)} 段")
    for n, a in trans:
        print(f"     从第 {n:3d} 镜起 → {a}")

print()
print("=" * 78)
print("疑点 2：OST 乐章 → 曲目（每镜只取第一次，去重）")
print("=" * 78)
for name, S in (("180镜", S180), ("120镜", S120)):
    per = defaultdict(Counter)
    for s in S:
        pz = (s.get("prompt_zh") or "").strip()
        m = re.search(r"乐章([IVX]+)\s*·\s*([^\s—]+)\s*—\s*(.+?)\s*（", pz)
        if m:
            per[m.group(1)][m.group(3).strip()] += 1
        else:
            m2 = re.search(r"乐章([IVX]+)\s*·\s*([^\s—]+)\s*—\s*([^\s（(]+)", pz)
            per[m2.group(1) if m2 else "?"][m2.group(3).strip() if m2 else "(未解析)"] += 1
    print(f"  {name}:")
    for ch in sorted(per):
        items = ", ".join(f"{k}({v})" for k, v in per[ch].most_common())
        print(f"     乐章{ch}: {items}")

print()
print("=" * 78)
print("疑点 3：禁面部锁 —— Shot_012 到底有没有")
print("=" * 78)
s12 = next(s for s in S180 if num(s) == 12)
pz = s12.get("prompt_zh", "")
for key in ("严禁出现任何人物", "禁挂人物", "无面部出镜", "纯实景", "严禁出现", "面部"):
    print(f"   prompt_zh 含 '{key}': {key in pz}")
for key in ("严禁出现任何人物", "禁挂人物", "无面部出镜", "纯实景"):
    print(f"   audio_cue  含 '{key}': {key in (s12.get('audio_cue') or '')}")
print(f"   primary_image_path: {img(s12)}")
print("   --- 铁律2 段 ---")
m = re.search(r"【铁律2[^】]*】(.{0,600})", pz, re.S)
print("   " + (m.group(1)[:600] if m else "(无铁律2)"))
print("   --- 铁律4 段（前 900 字）---")
m = re.search(r"【铁律4[^】]*】(.{0,900})", pz, re.S)
print("   " + (m.group(1)[:900] if m else "(无铁律4)"))

print()
print("=" * 78)
print("疑点 4：图号不一致的 39 处")
print("=" * 78)
bad = []
for s in S180:
    p = img(s)
    key = (s.get("primary_image_key") or "").strip()
    m = re.search(r"图(\d+\.\d+)", p)
    if m and key:
        k = key.replace("图", "").replace(" ", "")
        if m.group(1) != k:
            bad.append((sid(s), key, p))
for sid_, k, p in bad[:15]:
    print(f"   {sid_}: key='{k}'  file='{p}'")
print(f"   共 {len(bad)} 处")
# 反向：文件里的图号 vs 镜头 scene
print()
print("   抽查：这些镜头的 scene_title 与文件图号对得上吗")
for sid_, k, p in bad[:6]:
    s = next(x for x in S180 if sid(x) == sid_)
    print(f"     {sid_}: scene={s.get('scene_number')} {str(s.get('scene_title'))[:52]}")
