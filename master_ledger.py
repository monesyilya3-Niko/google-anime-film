# -*- coding: utf-8 -*-
"""生成《暮冬念春》4K 母带台账（CSV + Markdown）。

台账 = 40 张母带逐张的：图号 / 场次 / 尺寸 / 被哪些镜头引用 / 已知问题 / 状态 / 处置
数据源：云端拉下来的 40 张母带 + 修复后的 180Shots.json / 120Shots.json
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
SRC = next(d for d in list(ROOT.iterdir()) + list((ROOT / "source").iterdir())
            if d.is_dir() and d.name.startswith("40"))
OUT = ROOT / "v17"
OUT.mkdir(exist_ok=True)

from master_issues import ISSUES, TEXT_ITEMS  # noqa: E402


def key_of(name):
    m = re.match(r"^(\d{2}[a-z]?)_", name)
    return m.group(1) if m else name[:3]


def fig_of(name):
    m = re.search(r"图(\d+\.\d+[a-z]?)", name)
    return m.group(1) if m else ""


def main():
    assets = sorted(SRC.glob("*.jpg"))
    # 引用关系
    refs = defaultdict(list)
    for pat in ("fixed/*180Shots.json", "fixed/*120Shots.json"):
        for p in ROOT.glob(pat):
            for s in json.load(open(p, encoding="utf-8")):
                fn = (s.get("primary_image_path") or s.get("primary_cloud_filename") or "")
                if fn:
                    refs[fn].append(s.get("shot_id") or s.get("manus_15s_id"))

    rows = []
    for f in assets:
        k = key_of(f.name)
        with Image.open(f) as im:
            w, h = im.size
        used = refs.get(f.name, [])
        grade, issue, action = ISSUES.get(k + "_", ("?", "未审", "待定"))
        txt = TEXT_ITEMS.get(k + "_", [])
        rows.append(dict(
            key=k, name=f.name, fig=fig_of(f.name),
            size=f"{w}x{h}", ratio=("16:9" if abs(w / h - 16 / 9) < .01 else
                                    "8:9" if abs(w / h - 1916 / 2160) < .01 else "3:4"),
            mb=round(f.stat().st_size / 1048576, 2),
            refs=len(used),
            first_ref=(used[0] if used else ""),
            last_ref=(used[-1] if used else ""),
            grade=grade, issue=issue, action=action,
            screen_text=(" | ".join(f"{t[0]} @{t[1]} [{t[2]}]" for t in txt)
                         if txt else ""),
        ))

    # CSV
    csvp = OUT / "母带台账_40张.csv"
    with open(csvp, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("台账 CSV ->", csvp.name)

    # Markdown
    grade_c = Counter(r["grade"] for r in rows)
    md = ["# 《暮冬念春》4K 母带台账（40 张）· V17", "",
          f"云端母带库 `40幅真4K超清主母带与单屏子母带 (assets_4k_all)`（Folder ID `1aRc6-MNuk7wsd1OFhjZPMQGXck-OIpxG`）", "",
          "## 总览", "",
          f"- 母带总数 **{len(rows)}**（16:9 主母带 30 张 / 8:9 子母带 9 张 / 3:4 封面 1 张）",
          f"- 被 180/120 镜清单引用的 **{sum(1 for r in rows if r['refs'])}** 张，"
          f"未被引用的 **{sum(1 for r in rows if not r['refs'])}** 张（封面/宣发备选）",
          f"- 问题分级：`A1` 屏内文字 **{grade_c.get('A1',0)+grade_c.get('A1/A2',0)+grade_c.get('A1/A2',0)}** 处"
          f" · `A2` 借用 IP **{grade_c.get('A2',0)+grade_c.get('A1/A2',0)}** 处"
          f" · `B` 画面与承诺不符 **{sum(v for k,v in grade_c.items() if k.startswith('B'))}** 处",
          f"- 需重绘 **{sum(1 for r in rows if '需重画' in r['action'])}** 张 · "
          f"已去字/已修 **{sum(1 for r in rows if '已修' in r['action'])}** 张", "",
          "## 逐张台账", "",
          "| # | 图号 | 尺寸 | 比例 | MB | 被引用镜头 | 首个引用 | 分级 | 屏内文字（4K 绝对坐标） | 处置 |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        md.append(f"| {i:02d} | {r['fig']} | {r['size']} | {r['ratio']} | {r['mb']} | "
                  f"{r['refs']} | {r['first_ref']} | {r['grade']} | "
                  f"{r['screen_text'] or '—'} | {r['action']} |")
    mdp = OUT / "母带台账_40张.md"
    mdp.write_text("\n".join(md), encoding="utf-8")
    print("台账 MD  ->", mdp.name)

    # 控制台摘要
    print("\n分级分布:", dict(grade_c))
    print("待重绘:", [r["name"][:26] for r in rows if "需重画" in r["action"]])
    print("已修  :", [r["name"][:26] for r in rows if "已修" in r["action"]])
    print("无问题:", [r["name"][:26] for r in rows if r["grade"] == "—"])


if __name__ == "__main__":
    main()
