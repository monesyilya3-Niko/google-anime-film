# -*- coding: utf-8 -*-
"""06_ 是 06a_ + 06b_ 的拼接主母带 —— 用修好的两半重拼 06_。

先做像素级对应关系校验（06_ 左半 == 06a_ ? 右半 == 06b_ ?），
确认后把修复后的 06a_/06b_ 贴回 06_ 对应区域，保留 06_ 自身的接缝与画幅。
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
SRC = next(d for d in list(ROOT.iterdir()) + list((ROOT / "source").iterdir())
            if d.is_dir() and d.name.startswith("40"))
OUT = ROOT / "gen_out"

f06 = next(p for p in sorted(SRC.glob("06_*.jpg")))
f6a = next(p for p in sorted(SRC.glob("06a_*.jpg")))
f6b = next(p for p in sorted(SRC.glob("06b_*.jpg")))

base = Image.open(f06).convert("RGB")
a = Image.open(f6a).convert("RGB")
b = Image.open(f6b).convert("RGB")
W, H = base.size
wa, wb = a.width, b.width
print(f"06_ {base.size} | 06a_ {a.size} | 06b_ {b.size}")

# 找 06b_ 在 06_ 中的最佳横向偏移
gb = np.asarray(b.convert("L"), np.float32)
best = None
for off in range(W - wb - 2, W - wb + 6):
    if off < 0:
        continue
    seg = np.asarray(base.crop((off, 0, off + wb, H)).convert("L"), np.float32)
    d = float(np.abs(seg - gb).mean())
    if best is None or d < best[1]:
        best = (off, d)
print(f"06b_ 最佳横向偏移 = {best[0]}  平均差 = {best[1]:.2f}")

# 找 06a_ 在 06_ 中的最佳横向偏移
ga = np.asarray(a.convert("L"), np.float32)
besta = None
for off in range(-4, 8):
    if off < 0:
        continue
    seg = np.asarray(base.crop((off, 0, off + wa, H)).convert("L"), np.float32)
    d = float(np.abs(seg - ga).mean())
    if besta is None or d < besta[1]:
        besta = (off, d)
print(f"06a_ 最佳横向偏移 = {besta[0]}  平均差 = {besta[1]:.2f}")

# 用修复后的两半重拼
fixed_a = Image.open(OUT / f6a.name).convert("RGB")
fixed_b = Image.open(OUT / f6b.name).convert("RGB")
res = base.copy()
res.paste(fixed_a, (besta[0], 0))
res.paste(fixed_b, (best[0], 0))
dst = OUT / f06.name
res.save(dst, quality=96, subsampling=0)
print("重拼 ->", dst.name, res.size)

# 校验
seg_new = np.asarray(res.crop((best[0], 0, best[0] + wb, H)).convert("L"), np.float32)
seg_old = np.asarray(base.crop((best[0], 0, best[0] + wb, H)).convert("L"), np.float32)
print(f"右半改动幅度 = {float(np.abs(seg_new - seg_old).mean()):.2f}")
