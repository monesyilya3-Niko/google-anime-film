# -*- coding: utf-8 -*-
"""检查本地修图工具链：cv2 / numpy / scipy / 可用中文字体。"""
import importlib.util as u
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
for m in ("cv2", "numpy", "scipy", "PIL"):
    print(f"  {m:8s}: {bool(u.find_spec(m))}")

print("\n可用中文字体（用于重绘「暮冬」等字）:")
FD = Path("C:/Windows/Fonts")
picks = []
for p in sorted(FD.glob("*.tt*")):
    n = p.name.lower()
    if any(k in n for k in ("simsun", "simhei", "msyh", "deng", "song", "kai", "fangsong")):
        picks.append((p.name, p.stat().st_size))
for n, s in picks[:14]:
    print(f"  {n:32s} {s/1024:.0f} KB")
print(f"  合计 {len(picks)} 个候选")
