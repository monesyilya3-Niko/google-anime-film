# -*- coding: utf-8 -*-
"""导出杯身/Kitty 视觉描述的精确上下文，供 Phase 2 正则设计。"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
OUT = ROOT / "inspect_cup_kitty.txt"
FILES = {
    "180": CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json",
    "120": CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json",
}
PROMPT_KEYS = ("prompt_zh", "prompt_en", "motion_zh", "motion_en")
TERMS = ("ChaPanda", "panda", "熊猫", "奶茶杯", "Kitty", "化妆镜", "mirror")

lines = []
for tag, path in FILES.items():
    shots = json.loads(path.read_text(encoding="utf-8"))
    lines.append("=" * 100)
    lines.append(f"{tag} 轨 · 杯身/Kitty 视觉上下文")
    lines.append("=" * 100)
    for term in TERMS:
        lines.append(f"\n### {term}")
        seen = set()
        count = 0
        for s in shots:
            label = s.get("shot_id") or s.get("manus_15s_id")
            for k in PROMPT_KEYS:
                v = s.get(k, "")
                if not isinstance(v, str):
                    continue
                for m in re.finditer(re.escape(term), v):
                    i = m.start()
                    frag = v[max(0, i - 110):i + 140].replace("\n", " ")
                    # 只保留含视觉/动作线索的片段，滤掉纯文件名
                    if ".jpg" in frag and term not in ("Kitty",):
                        continue
                    key = frag[:90]
                    if key in seen:
                        continue
                    seen.add(key)
                    count += 1
                    if count <= 6:
                        lines.append(f"  [{label}.{k}] …{frag}…")
        lines.append(f"  （去重后 {count} 条）")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"written {OUT} ({OUT.stat().st_size}B)")
