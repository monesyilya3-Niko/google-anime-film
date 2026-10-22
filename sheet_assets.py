# -*- coding: utf-8 -*-
"""40 张 4K 母带的审片墙：拼图 + 尺寸核对。

用法:
  python sheet_assets.py            拼总览墙（8 列）
  python sheet_assets.py 2          只看第 2 页
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
ASSETS = next(d for d in list(ROOT.iterdir()) + list((ROOT/"source").iterdir())
            if d.is_dir() and d.name.startswith("40"))

files = sorted(ASSETS.glob("*.jpg"))
print(f"母带 {len(files)} 张\n")

# ── 尺寸 / 比例体检 ──
print(f"{'文件名':<64} {'尺寸':>14} {'比例':>8}")
print("-" * 92)
bad_ratio = []
for f in files:
    with Image.open(f) as im:
        w, h = im.size
    r = w / h
    tag = ""
    if abs(r - 16 / 9) > 0.01 and abs(r - 1916 / 2160) > 0.01 and abs(r - 2880 / 3840) > 0.01:
        tag = "  ← 比例异常"
        bad_ratio.append((f.name, w, h))
    print(f"{f.name:<64} {w:>6}x{h:<7} {r:>8.3f}{tag}")
print()
if bad_ratio:
    print("比例异常:", bad_ratio)

# ── 拼图 ──
PAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 1
PER = 20
pages = (len(files) + PER - 1) // PER
chunk = files[(PAGE - 1) * PER: PAGE * PER]
COLS = 4
TW, TH = 460, 300
rows = (len(chunk) + COLS - 1) // COLS
out = Image.new("RGB", (COLS * TW, rows * TH), (12, 14, 18))
d = ImageDraw.Draw(out)
try:
    fnt = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 13)
except Exception:
    fnt = ImageFont.load_default()

for i, f in enumerate(chunk):
    with Image.open(f) as im:
        im = im.convert("RGB")
        iw, ih = im.size
        s = min(TW / iw, (TH - 34) / ih)
        im = im.resize((max(1, int(iw * s)), max(1, int(ih * s))), Image.LANCZOS)
    cx = (i % COLS) * TW
    cy = (i // COLS) * TH
    ox = cx + (TW - im.width) // 2
    oy = cy + 30
    out.paste(im, (ox, oy))
    d.rectangle([cx, cy, cx + TW - 1, cy + TH - 1], outline=(46, 52, 62))
    d.text((cx + 6, cy + 7), f"{i + (PAGE - 1) * PER + 1:02d} {f.name[:34]}", fill=(190, 200, 215), font=fnt)
    d.text((cx + 6, cy + TH - 20), f"{iw}x{ih}", fill=(120, 132, 148), font=fnt)

p = ROOT / f"assets_sheet_p{PAGE}.jpg"
out.save(p, quality=90)
print(f"审片墙 P{PAGE}/{pages} -> {p}")
