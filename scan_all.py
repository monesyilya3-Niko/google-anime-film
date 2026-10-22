# -*- coding: utf-8 -*-
"""剩余母带全幅扫描：每张 950px 宽缩览，人工确认是否还有屏内文字。"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
SRC = next(d for d in list(ROOT.iterdir()) + list((ROOT / "source").iterdir())
            if d.is_dir() and d.name.startswith("40"))
OUT = ROOT / "gen_out"

GROUPS = [
    ["06_", "09_", "20_", "21_", "05_", "05a_"],
    ["05b_", "01_", "24_", "29_", "04_", "08_"],
    ["12_", "14_", "16_", "17_", "19_", "22_"],
    ["25_", "28_", "02_", "03a_", "11_", "13_"],
    ["18b_", "15_", "07_", "06_", "10_", "23_"],
]

CW = 950     # 单格宽
COLS = 2


def build(group, idx):
    tiles = []
    for pref in group:
        f = next((p for p in sorted(SRC.glob(pref + "*.jpg"))), None)
        if not f:
            continue
        im = Image.open(f).convert("RGB")
        h = int(im.height * CW / im.width)
        t = im.resize((CW, h), Image.LANCZOS)
        d = ImageDraw.Draw(t)
        d.rectangle([0, 0, CW - 1, 24], fill=(0, 0, 0))
        d.text((4, 6), f"{pref}  {im.size}", fill=(255, 220, 60))
        tiles.append(t)
    if not tiles:
        return
    rh = max(t.height for t in tiles)
    rows = (len(tiles) + COLS - 1) // COLS
    canvas = Image.new("RGB", (CW * COLS + 8, rh * rows + 8 * rows), (8, 8, 10))
    for i, t in enumerate(tiles):
        r, c = divmod(i, COLS)
        canvas.paste(t, (c * (CW + 8), r * (rh + 8)))
    p = OUT / f"scanall_{idx}.jpg"
    canvas.save(p, quality=90)
    print("->", p.name, canvas.size)


if __name__ == "__main__":
    for i, g in enumerate(GROUPS, 1):
        build(g, i)
