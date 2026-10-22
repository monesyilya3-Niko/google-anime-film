# -*- coding: utf-8 -*-
"""修复前勘察：180 JSON 的排版/Shot_007 相关字段；180 总表 CSV 的 Shot_007 行；Act1 的 Shot_007 段。"""
import csv
import io
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
J180 = CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json"

raw = J180.read_text(encoding="utf-8")
print("=" * 84)
print("1. 180 JSON 原始排版")
print("=" * 84)
print(f"  体积 {len(raw.encode('utf-8'))}B  行数 {raw.count(chr(10)) + 1}")
print(f"  前 160 字符：{raw[:160]!r}")
print(f"  含缩进换行（\\n  + 空格）：{'是' if re.search(r'\\n\\s+\\S', raw) else '否'}")

shots = json.loads(raw)
s7 = next(s for s in shots if s.get("shot_number") == 7)
print("\n" + "=" * 84)
print("2. Shot_007 对象里所有含 04_图3.1 / 01c 的字段")
print("=" * 84)
for k, v in s7.items():
    sv = str(v)
    if "04_图3.1" in sv or "01c_图0.1" in sv:
        print(f"  {k}:")
        for m in re.finditer(r"04_图3\.1|01c_图0\.1", sv):
            a, b = max(0, m.start() - 70), min(len(sv), m.end() + 70)
            print(f"     …{sv[a:b].replace(chr(10), ' ')}…")
print(f"\n  Shot_007 键数 {len(s7)}")

print("\n" + "=" * 84)
print("3. 180 总表 CSV：表头与 Shot_007 行")
print("=" * 84)
csv_path = CACHE / "export_暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜全量总表_180Shots_V19.csv"
rows = list(csv.reader(io.StringIO(csv_path.read_text(encoding="utf-8-sig"))))
print(f"  CSV 行数 {len(rows)}  列数 {len(rows[0])}")
print("  表头：")
for i, h in enumerate(rows[0]):
    print(f"     {i:>2} {h}")
# 找到含 Shot_007 的行
for ri, r in enumerate(rows):
    if r and any("Shot_007" in c for c in r):
        print(f"\n  Shot_007 在 CSV 第 {ri + 1} 行：")
        for ci, c in enumerate(r):
            if c.strip():
                print(f"     {ci:>2} {rows[0][ci] if ci < len(rows[0]) else '?'}: {c[:150]}")
        break

print("\n" + "=" * 84)
print("4. Act1 导出件里的 Shot_007 段")
print("=" * 84)
act1 = (CACHE / "export_Act1_Shots_001_027_第一幕_起_序破_Manus(540子镜24fps关键帧版)_V19.md.md").read_text(encoding="utf-8")
idx = act1.find("Shot_007")
print(f"  首次出现位置 {idx}")
seg = act1[max(0, idx - 400):idx + 1200]
print(seg.replace("\\_", "_")[:2000])
