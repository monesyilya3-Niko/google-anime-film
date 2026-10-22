# -*- coding: utf-8 -*-
"""核查 panda/ChaPanda/Kitty 是否落在负向提示或台词内。"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
OUT = ROOT / "inspect_panda_classify.txt"
FILES = {
    "180": CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json",
    "120": CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json",
}
PROMPT_KEYS = ("prompt_zh", "prompt_en", "motion_zh", "motion_en")
TERMS = ("panda", "ChaPanda", "Kitty", "熊猫", "奶茶杯", "mirror")


def classify(frag):
    if any(x in frag for x in ("「", "」", "（VO", "(VO", "台词", "Audio Cue", "独白")):
        return "dialogue"
    if any(x in frag for x in (".jpg", ".png", "File ID")):
        return "filename"
    if any(x in frag for x in ("严禁", "禁止", "strictly NO", "no brand", "No brand", "negative")):
        return "negative"
    return "visual"


lines = []
for tag, path in FILES.items():
    shots = json.loads(path.read_text(encoding="utf-8"))
    lines.append("=" * 90)
    lines.append(f"{tag} 轨 · panda/Kitty 分类")
    lines.append("=" * 90)
    for term in TERMS:
        by_cat = Counter()
        samples = {}
        for s in shots:
            label = s.get("shot_id") or s.get("manus_15s_id")
            for k in PROMPT_KEYS:
                v = s.get(k, "")
                if not isinstance(v, str) or term not in v:
                    continue
                start = 0
                while True:
                    i = v.find(term, start)
                    if i < 0:
                        break
                    frag = v[max(0, i - 130):i + 150].replace("\n", " ")
                    cat = classify(frag)
                    by_cat[cat] += 1
                    samples.setdefault(cat, [])
                    if len(samples[cat]) < 2:
                        samples[cat].append(f"[{label}.{k}] …{frag}…")
                    start = i + 1
        if not by_cat:
            continue
        lines.append(f"\n### {term}  总计 {sum(by_cat.values())}  {dict(by_cat)}")
        for cat in ("dialogue", "negative", "filename"):
            for it in samples.get(cat, []):
                lines.append(f"  --- {cat} ---")
                lines.append(f"    {it}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"written {OUT} ({OUT.stat().st_size}B)")
