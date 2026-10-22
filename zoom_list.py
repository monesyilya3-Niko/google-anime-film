# -*- coding: utf-8 -*-
"""高分辨率定点目视 v2：宽松框，确认文字真实边界。"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
SRC = next(d for d in list(ROOT.iterdir()) + list((ROOT / "source").iterdir())
            if d.is_dir() and d.name.startswith("40"))
OUT = ROOT / "gen_out"

PRESETS = {
    "r2": [
        ("18_", (80, 140, 720, 330), "18_poster"),
        ("18_", (1480, 760, 2020, 930), "18_phone"),
        ("18_", (900, 930, 2000, 1130), "18_dash"),
        ("18_", (0, 0, 1920, 1080), "18_TL"),
        ("18_", (1920, 0, 3840, 1080), "18_TR"),
        ("18a_", (0, 0, 1920, 1080), "18a_TL"),
        ("18a_", (0, 1080, 1916, 2160), "18a_BL"),
        ("18b_", (0, 0, 1916, 1080), "18b_TL"),
        ("26_", (2330, 1310, 2640, 1460), "26_tea"),
        ("27_", (1780, 1600, 2240, 1840), "27_palm"),
        ("06a_", (1200, 1890, 1470, 2060), "06a_card"),
        ("10_", (1360, 530, 1700, 680), "10_screen"),
    ],
    "r3": [
        ("03_", (2520, 1860, 3220, 2140), "03_tee"),
        ("03b_", (600, 1860, 1300, 2140), "03b_tee"),
        ("06b_", (840, 1190, 1070, 1450), "06b_card"),
        ("07_", (800, 1410, 1210, 1550), "07_nbL"),
        ("07_", (2750, 1410, 3140, 1550), "07_nbR"),
        ("23_", (1790, 1320, 2110, 1470), "23_cup"),
        ("23_", (990, 1590, 1360, 1900), "23_tee"),
        ("18_", (0, 1080, 1920, 2160), "18_BL"),
        ("18_", (1920, 1080, 3840, 2160), "18_BR"),
        ("18a_", (0, 1080, 1916, 2160), "18a_BL2"),
    ],
}


def build(cases, outname, target_w=700):
    tiles = []
    for pref, box, label in cases:
        f = next((p for p in sorted(SRC.glob(pref + "*.jpg"))), None)
        if not f:
            continue
        im = Image.open(f).convert("RGB")
        crop = im.crop(box)
        sc = min(3.0, target_w / max(crop.width, 1))
        c = crop.resize((max(1, int(crop.width * sc)), max(1, int(crop.height * sc))),
                        Image.LANCZOS)
        d = ImageDraw.Draw(c)
        d.rectangle([0, 0, c.width - 1, 22], fill=(0, 0, 0))
        d.text((4, 5), f"{label}  {box}", fill=(255, 220, 60))
        tiles.append(c)
    if not tiles:
        raise SystemExit("empty")
    W = max(t.width for t in tiles)
    H = sum(t.height + 6 for t in tiles)
    canvas = Image.new("RGB", (W, H), (8, 8, 10))
    y = 0
    for t in tiles:
        canvas.paste(t, (0, y))
        y += t.height + 6
    p = OUT / outname
    canvas.save(p, quality=93)
    print("->", p, canvas.size)


if __name__ == "__main__":
    preset = sys.argv[1] if len(sys.argv) > 1 else "r2"
    outname = sys.argv[2] if len(sys.argv) > 2 else f"zoom_{preset}.jpg"
    build(PRESETS[preset], outname)
