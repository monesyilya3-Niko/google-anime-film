# -*- coding: utf-8 -*-
"""打印 panda-logo cups 原始上下文。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
FILES = {
    "180": CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json",
    "120": CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json",
}
for tag, path in FILES.items():
    shots = json.loads(path.read_text(encoding="utf-8"))
    for s in shots:
        label = s.get("shot_id") or s.get("manus_15s_id")
        for k in ("prompt_en", "motion_en"):
            v = s.get(k, "")
            if "panda-logo cups" in v:
                i = v.find("panda-logo cups")
                print(f"[{tag} {label}.{k}] …{v[max(0, i-260):i+100]}…")
