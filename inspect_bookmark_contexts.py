# -*- coding: utf-8 -*-
"""检查“粉金星翼彗星书签挂坠”与“星翼彗星”的上下文，判定是否与 05 木书签同一道具。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
OUT = ROOT / "inspect_bookmark_contexts.txt"
FILES = {
    "180": CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json",
    "120": CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json",
}
PROMPT_KEYS = ("prompt_zh", "prompt_en", "motion_zh", "motion_en")
TERMS = ("粉金星翼彗星书签挂坠", "星翼彗星", "书签挂坠")

lines = []
for tag, path in FILES.items():
    shots = json.loads(path.read_text(encoding="utf-8"))
    lines.append("=" * 100)
    lines.append(f"{tag} 轨")
    lines.append("=" * 100)
    for term in TERMS:
        lines.append(f"\n### {term}")
        seen = set()
        n = 0
        for s in shots:
            label = s.get("shot_id") or s.get("manus_15s_id")
            for k in PROMPT_KEYS:
                v = s.get(k, "")
                if not isinstance(v, str):
                    continue
                for m in re.finditer(re.escape(term), v):
                    i = m.start()
                    frag = v[max(0, i - 160):i + 200].replace("\n", " ")
                    key = frag[:100]
                    if key in seen:
                        continue
                    seen.add(key)
                    n += 1
                    if n <= 12:
                        lines.append(f"  [{label}.{k}] …{frag}…")
        lines.append(f"  （去重后 {n} 条）")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"written {OUT} ({OUT.stat().st_size}B)")
