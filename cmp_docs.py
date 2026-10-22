# -*- coding: utf-8 -*-
"""对比：JSON 里的锁脸挂载 vs 文档里写的锁脸槽。"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
V16 = next(d for d in list(ROOT.iterdir()) + list((ROOT/"source").iterdir())
            if d.is_dir() and d.name.startswith("《"))
FIXED = ROOT / "fixed"

aux = {}
for p in FIXED.glob("*180Shots.json"):
    for s in json.load(open(p, encoding="utf-8")):
        aux[s["shot_id"]] = [a.get("filename", "") for a in (s.get("auxiliary_cloud_assets") or [])]

pat = re.compile(r"^\* 辅助锁脸槽（Weight=[\d.]+）：(.*)$", re.M)
docs = {}
for d in sorted(V16.glob("Act*.txt")):
    for m in pat.finditer(d.read_text(encoding="utf-8")):
        docs.setdefault(d.name, []).append(m.group(1))

print("文档里的辅助锁脸槽条目数（按文件）:")
for k, v in docs.items():
    print(f"  {k[:40]}: {len(v)}")

# 取第一个 Act 的条目，按出现顺序和 shot 顺序对齐
d1 = next(V16.glob("Act1*.txt"))
text = d1.read_text(encoding="utf-8")
items = pat.findall(text)
sids = re.findall(r"^(Shot_\d{3})\s*\|", text, re.M)
print(f"\nAct1: 文档锁脸槽 {len(items)} 条 vs 镜头块 {len(sids)} 个")

same = diff = 0
for sid, line in zip(sids, items):
    j = set(aux.get(sid, []))
    d = set(re.findall(r"(\d{2}[a-z]?_图[\d.]+[^\s(]*?\.jpg)", line))
    if j == d:
        same += 1
    else:
        diff += 1
        if diff <= 6:
            print(f"  ✗ {sid}")
            print(f"      JSON: {sorted(x[:10] for x in j)}")
            print(f"      DOC : {sorted(x[:10] for x in d)}")
print(f"\n一致 {same} / 不一致 {diff}")

# 文档里带男主基准的条数
cnt = 0
for line in items:
    if re.search(r"0?3[ab]?_图2\.2", line):
        cnt += 1
print(f"Act1 文档里挂了男主基准的条目: {cnt}/{len(items)}")

# 总表的结构
tt = next(V16.glob("*总控调取指令总表.txt")).read_text(encoding="utf-8")
print("\n--- 总表里含 Shot_ 的行样例 ---")
n = 0
for l in tt.split("\n"):
    if "Shot_0" in l:
        print("  ", l[:130])
        n += 1
        if n >= 6:
            break
print("总表里 Shot_ 出现次数:", tt.count("Shot_"))
