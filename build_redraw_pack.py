# -*- coding: utf-8 -*-
"""构建「待重画」交付包：
  母带原图/      23 张待重画母带的 4K 原图（直接喂 ChatGPT）
  区域标注图/    同一张图 + 200px 坐标网格（让 ChatGPT 精确定位要改的部位）
  重画提示词.md  逐张：问题 / 区域 / 完整提示词
  重画清单.csv   机器可读清单
  未完成事项清单.md  全部未完成项（含非图片部分）
"""
import csv
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from redraw_prompts import REDRAW, PREFIX  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
SRC = next(d for d in list(ROOT.iterdir()) + list((ROOT / "source").iterdir())
            if d.is_dir() and d.name.startswith("40"))
PACK = ROOT / "redraw_pack"
for sub in ("母带原图", "区域标注图"):
    (PACK / sub).mkdir(parents=True, exist_ok=True)

FONT_CN = ImageFont.truetype("C:/Windows/Fonts/simsun.ttc", 17)
FONT_NUM = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 15)


def grid_map(im, boxes, title, out):
    """在原图上叠 200px 网格 + 红色问题框。"""
    W, H = im.size
    tw = 1500
    sc = tw / W
    c = im.resize((tw, int(H * sc)), Image.LANCZOS).convert("RGB")
    d = ImageDraw.Draw(c)
    for x in range(0, W + 1, 200):
        px = int(x * sc)
        d.line([(px, 0), (px, c.height)], fill=(0, 170, 220))
        if x % 400 == 0:
            d.text((px + 3, 3), str(x), fill=(0, 235, 255), font=FONT_NUM)
    for y in range(0, H + 1, 200):
        py = int(y * sc)
        d.line([(0, py), (c.width, py)], fill=(0, 170, 220))
        if y % 400 == 0:
            d.text((3, py + 3), str(y), fill=(0, 235, 255), font=FONT_NUM)
    for (x1, y1, x2, y2) in boxes:
        p1 = (int(x1 * sc), int(y1 * sc))
        p2 = (int(x2 * sc), int(y2 * sc))
        d.rectangle([p1, p2], outline=(255, 60, 60), width=5)
    d.rectangle([0, 0, c.width - 1, 28], fill=(0, 0, 0))
    d.text((6, 5), f"{title}    网格=200px  蓝线=坐标  红框=问题区域",
           fill=(255, 220, 60), font=FONT_CN)
    c.save(out, quality=92)


def parse_box(s):
    if not s.startswith("("):
        return None
    try:
        return tuple(int(v) for v in s.strip("()").split(","))
    except Exception:
        return None


rows = []
md = ["# 《暮冬念春》待重画母带 · 逐张提示词（V17）", "",
      f"共 **{len(REDRAW)}** 张待重画。目录：",
      "`母带原图/`（4K 原图，直接喂 ChatGPT 作参考图）· "
      "`区域标注图/`（同一张图 + 200px 坐标网格 + 红框问题区域）· "
      "`重画清单.csv`", "",
      "**统一前缀（每一张都带）**", "", "```", PREFIX, "```", "",
      "---", ""]

for pref, info in REDRAW.items():
    src = next((p for p in sorted(SRC.glob(pref + "*.jpg"))), None)
    if not src:
        print("缺源图:", pref)
        continue
    im = Image.open(src).convert("RGB")
    # 复制原图
    (PACK / "母带原图" / src.name).write_bytes(src.read_bytes())
    # 区域标注图
    boxes = [b for b in (parse_box(i[1]) for i in info["issues"]) if b]
    grid_map(im, boxes, f"{pref} {im.size}", PACK / "区域标注图" / src.name)

    md.append(f"## {pref} — {src.name}")
    md.append("")
    md.append(f"*画幅 {im.size[0]}×{im.size[1]}　|　分级 {info['grade']}*")
    md.append("")
    md.append("**要改什么**")
    md.append("")
    for i, (desc, loc, act) in enumerate(info["issues"], 1):
        md.append(f"{i}. {desc}　—　位置：{loc}")
    md.append("")
    md.append("**提示词（整段复制）**")
    md.append("")
    md.append("```")
    md.append(PREFIX)
    md.append("")
    md.append(info["prompt"])
    md.append("```")
    md.append("")
    rows.append(dict(
        母带=pref, 文件名=src.name, 画幅=f"{im.size[0]}x{im.size[1]}",
        分级=info["grade"], 问题数=len(info["issues"]),
        问题=" / ".join(i[0] for i in info["issues"]),
        区域=" | ".join(f"{i[1]}" for i in info["issues"]),
        提示词=(PREFIX + "\n" + info["prompt"]).replace("\n", " "),
    ))
    print(f"  {pref}  {im.size}  {len(info['issues'])} 处问题")

(PACK / "重画提示词.md").write_text("\n".join(md), encoding="utf-8")
with open(PACK / "重画清单.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"\n交付包 -> {PACK}")
for p in sorted(PACK.rglob("*")):
    if p.is_file():
        print(f"   {p.relative_to(PACK)}  {p.stat().st_size//1024} KB")
