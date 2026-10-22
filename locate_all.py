# -*- coding: utf-8 -*-
"""把所有待修文字区域拼成一张对照图（每块带坐标网格），一次读出所有像素框。

用法: python locate_all.py
输出: gen_out/locate_all.jpg
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
SRC = next(d for d in list(ROOT.iterdir()) + list((ROOT / "source").iterdir())
            if d.is_dir() and d.name.startswith("40"))
OUT = ROOT / "gen_out"
OUT.mkdir(exist_ok=True)

# (前缀, 比例框, 标签)
TILES = [
    ("07_", (0.28, 0.18, 0.80, 0.55), "07_notebook"),
    ("27_", (0.30, 0.55, 0.78, 0.95), "27_palm"),
    ("18_", (0.00, 0.02, 0.26, 0.30), "18_screen"),
    ("18a_", (0.00, 0.02, 0.30, 0.30), "18a_screen"),
    ("13_", (0.02, 0.28, 0.36, 0.70), "13_desk"),
    ("06a_", (0.30, 0.18, 0.78, 0.58), "06a_card"),
    ("03b_", (0.16, 0.42, 0.62, 0.88), "03b_tee"),
    ("10_", (0.55, 0.55, 0.90, 0.95), "10_tee"),
    ("21_", (0.45, 0.30, 0.90, 0.75), "21_laptop"),
    ("26_", (0.55, 0.45, 0.95, 0.90), "26_cup"),
]

TW, TH = 600, 380
cols = 2
rows = (len(TILES) + cols - 1) // cols
canvas = Image.new("RGB", (cols * TW, rows * TH), (10, 10, 12))
d = ImageDraw.Draw(canvas)

for i, (pref, (x0, y0, x1, y1), label) in enumerate(TILES):
    src = next((p for p in sorted(SRC.glob(pref + "*.jpg"))), None)
    if not src:
        continue
    im = Image.open(src).convert("RGB")
    W, H = im.size
    box = (int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H))
    crop = im.crop(box)
    sc = min(TW / crop.width, (TH - 26) / crop.height)
    crop = crop.resize((int(crop.width * sc), int(crop.height * sc)), Image.LANCZOS)
    tile = Image.new("RGB", (TW, TH), (18, 18, 22))
    td = ImageDraw.Draw(tile)
    for gx in range(0, crop.width, max(1, int(100 * sc))):
        td.line([(gx, 0), (gx, crop.height)], fill=(0, 200, 255))
        td.text((gx + 2, 2), str(int(box[0] + gx / sc)), fill=(0, 235, 255))
    for gy in range(0, crop.height, max(1, int(100 * sc))):
        td.line([(0, gy), (crop.width, gy)], fill=(0, 200, 255))
        td.text((2, gy + 2), str(int(box[1] + gy / sc)), fill=(0, 235, 255))
    tile.paste(crop, (0, 24))
    td.text((6, 5), label, fill=(255, 220, 120))
    canvas.paste(tile, ((i % cols) * TW, (i // cols) * TH))

p = OUT / "locate_all.jpg"
canvas.save(p, quality=93)
print("->", p)
