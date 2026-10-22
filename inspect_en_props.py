# -*- coding: utf-8 -*-
"""查英文侧书签/吊坠表达，确定 Phase 2 英文映射。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
OUT = ROOT / "inspect_en_props.txt"
FILES = {
    "180": CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json",
    "120": CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json",
}
PROMPT_KEYS = ("prompt_zh", "prompt_en", "motion_zh", "motion_en")
TERMS = (
    "pink winged star-comet", "star-comet charm", "bookmark", "wooden bookmark",
    "comet pendant", "brass comet", "winged star", "star wand", "magic wand",
    "white cat charm", "cat charm", "charm",
)

lines = []
for tag, path in FILES.items():
    shots = json.loads(path.read_text(encoding="utf-8"))
    lines.append("=" * 80)
    lines.append(f"{tag} 轨（仅英文/通用）")
    lines.append("=" * 80)
    for term in TERMS:
        total = 0
        samples = []
        for s in shots:
            label = s.get("shot_id") or s.get("manus_15s_id")
            for k in ("prompt_en", "motion_en"):
                v = s.get(k, "")
                if not isinstance(v, str):
                    continue
                c = v.count(term)
                if c:
                    total += c
                    if len(samples) < 3:
                        i = v.find(term)
                        samples.append(f"[{label}.{k}] …{v[max(0, i-90):i+130]}…".replace("\n", " "))
        if total:
            lines.append(f"\n### {term}: {total} 次")
            for smp in samples:
                lines.append(f"  {smp}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"written {OUT} ({OUT.stat().st_size}B)")
