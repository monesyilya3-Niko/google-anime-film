# -*- coding: utf-8 -*-
"""按比例裁切母带局部并画坐标网格，用来读出精确像素框。

用法: python crop.py <文件名前缀> <x0> <y0> <x1> <y1> [标签]
     比例 0..1；输出 gen_out/crop_<标签>.png
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

pref, x0, y0, x1, y1 = sys.argv[1], *[float(v) for v in sys.argv[2:6]]
label = sys.argv[6] if len(sys.argv) > 6 else "crop"

src = next((p for p in sorted(SRC.glob(pref + "*.jpg"))), None)
if not src:
    raise SystemExit("找不到 " + pref)
im = Image.open(src).convert("RGB")
W, H = im.size
box = (int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H))
crop = im.crop(box)
target_w = 1200
sc = target_w / crop.width
crop = crop.resize((int(crop.width * sc), int(crop.height * sc)), Image.LANCZOS)
d = ImageDraw.Draw(crop)
step = 100
for gx in range(0, crop.width, step):
    d.line([(gx, 0), (gx, crop.height)], fill=(0, 190, 255), width=1)
    d.text((gx + 3, 3), str(int(box[0] + gx / sc)), fill=(0, 230, 255))
for gy in range(0, crop.height, step):
    d.line([(0, gy), (crop.width, gy)], fill=(0, 190, 255), width=1)
    d.text((3, gy + 3), str(int(box[1] + gy / sc)), fill=(0, 230, 255))
p = OUT / f"crop_{label}.png"
crop.save(p)
print(f"{src.name}")
print(f"  源框 {box}  缩放 {sc:.2f}x  -> {p.name}")
