# -*- coding: utf-8 -*-
"""勘察：180 总表 CSV 的块结构 + Shot_007 行；120 总表行数；Act1 中 Shot_007 调取指令的唯一性。"""
import csv
import io
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
CACHE = Path(__file__).resolve().parent / "source" / "audit"


def load(pattern):
    p = next(CACHE.glob(pattern))
    return list(csv.reader(io.StringIO(p.read_text(encoding="utf-8-sig"))))


t180 = load("export_*180*.csv")
t120 = load("export_*120*.csv")

print("=" * 84)
print("1. 180 总表结构")
print("=" * 84)
print(f"  行数 {len(t180)}  列数 {len(t180[0])}")
for ri in (0, 1, 2, 7, 8, 180, 181, 182, 183, len(t180) - 2, len(t180) - 1):
    if 0 <= ri < len(t180):
        r = t180[ri]
        print(f"  行{ri + 1}: 列数={len(r)} 首列={(r[0][:40] if r else '')!r} 次列={(r[1][:30] if len(r) > 1 else '')!r}")

print("\n" + "=" * 84)
print("2. 180 总表 Shot_007 行（按 shot_number == 7 找）")
print("=" * 84)
for ri, r in enumerate(t180):
    if r and r[0].strip() == "7":
        print(f"  行{ri + 1}：")
        for ci in (0, 1, 15, 17, 26, 27, 31, 32, 33, 39):
            print(f"     {ci:>2} {t180[0][ci]}: {r[ci][:180]}")
        break

print("\n" + "=" * 84)
print("3. 120 总表结构")
print("=" * 84)
print(f"  行数 {len(t120)}  列数 {len(t120[0])}")
for ri in (0, 1, 2, len(t120) - 1):
    r = t120[ri]
    print(f"  行{ri + 1}: [{r[0]!r}, {r[1]!r}]")

print("\n" + "=" * 84)
print("4. Act1 中 '04_图3.1' 出现次数与 Shot_007 上下文唯一串")
print("=" * 84)
act1 = (CACHE / "export_Act1_Shots_001_027_第一幕_起_序破_Manus(540子镜24fps关键帧版)_V19.md.md").read_text(encoding="utf-8")
print(f"  04_图3.1 出现 {act1.count('04_图3.1')} 次")
print(f"  1pkU017 出现 {act1.count('1pkU017')} 次")
# 找到 Shot_007 的调取指令段
i = act1.find("Shot_007 (01:00–01:10")
print(f"  Shot_007 指令段位置 {i}")
seg = act1[i:i + 700] if i >= 0 else ""
print(seg.replace("\\_", "_")[:700])
# 检查目标短语在全文中是否唯一
target = "同时挂载云端母带 \\`04_图3.1_Scene01_暮冬之雪与春雨之窗_3840x2160_4K.jpg\\` (\\`File ID: 1pkU017WSHLc7v3EAFPCO7y1gqmSWoVNv\\`，Weight=0.55) 防长链画质漂移"
print(f"\n  目标短语原始出现次数：{act1.count(target)}")
# 转义形式也可能是 \` 
alt = target.replace("\\`", "`")
print(f"  非转义形式出现次数：{act1.count(alt)}")
