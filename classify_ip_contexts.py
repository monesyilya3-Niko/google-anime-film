# -*- coding: utf-8 -*-
"""把 IP 词出现上下文分类为：台词 / 文件名引用 / 负向禁止 / 视觉描述。"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
OUT = ROOT / "inspect_ip_classify.txt"
FILES = {
    "180": CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json",
    "120": CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json",
}
PROMPT_KEYS = ("prompt_zh", "prompt_en", "motion_zh", "motion_en")
TERMS = ("小樱粉色星之杖", "白猫吊坠", "茶百道", "Kitty", "Hello Kitty",
         "Cardcaptor Sakura", "white cat charm")


def classify(frag):
    if any(x in frag for x in ("「", "」", "VO）", "VO)", "台词", "Audio Cue", "独白")):
        return "dialogue"
    if any(x in frag for x in (".jpg", ".png", "File ID", "云端4K母带", "母带（", "母带(")):
        return "filename"
    if any(x in frag for x in ("严禁", "禁止", "negative", "Negative")):
        return "negative"
    return "visual"


lines = []
for tag, path in FILES.items():
    shots = json.loads(path.read_text(encoding="utf-8"))
    lines.append("=" * 100)
    lines.append(f"{tag} 轨 · IP 词上下文分类")
    lines.append("=" * 100)
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
                    frag = v[max(0, i - 140):i + 160].replace("\n", " ")
                    cat = classify(frag)
                    by_cat[cat] += 1
                    samples.setdefault(cat, [])
                    if len(samples[cat]) < 2:
                        samples[cat].append(f"[{label}.{k}] …{frag}…")
                    start = i + 1
        if not by_cat:
            continue
        lines.append(f"\n### {term}  总计 {sum(by_cat.values())}")
        lines.append(f"  {dict(by_cat)}")
        for cat, items in samples.items():
            lines.append(f"  --- {cat} ---")
            for it in items:
                lines.append(f"    {it}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"written {OUT} ({OUT.stat().st_size}B)")
