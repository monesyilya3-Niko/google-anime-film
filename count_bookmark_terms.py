# -*- coding: utf-8 -*-
"""精确统计书签相关短语在四个 prompt/motion 字段中的出现次数。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
FILES = {
    "180": CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json",
    "120": CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json",
}
TERMS = [
    "Cardcaptor Sakura",
    "Cardcaptor Sakura pink winged star-comet charm",
    "Cardcaptor Sakura golden-winged pink winged star-comet charm",
    "pink-and-gold winged star-comet charm",
    "winged star-comet charm",
    "粉金星翼彗星书签挂坠",
    "粉金星翼彗星挂坠",
    "粉金星翼",
    "小樱粉色星之杖",
]
KEYS = ("prompt_zh", "prompt_en", "motion_zh", "motion_en")

for tag, path in FILES.items():
    shots = json.loads(path.read_text(encoding="utf-8"))
    print("=" * 60)
    print(tag)
    for term in TERMS:
        total = 0
        per_key = {k: 0 for k in KEYS}
        shots_with = 0
        for s in shots:
            hit = False
            for k in KEYS:
                c = s.get(k, "").count(term)
                if c:
                    per_key[k] += c
                    total += c
                    hit = True
            if hit:
                shots_with += 1
        print(f"{term!r}: total={total} shots={shots_with} per_key={per_key}")
