# -*- coding: utf-8 -*-
"""统计 180/120 JSON 中第三方 IP 词的字段分布与镜头范围。"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
CACHE = Path(__file__).resolve().parent / "source" / "audit"
FILES = {
    "180": CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json",
    "120": CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json",
}
TERMS = ["小樱粉色星之杖", "白猫吊坠", "茶百道", "星之杖", "白猫", "Kitty", "Sakura", "cat charm", "wand"]

for tag, path in FILES.items():
    shots = json.loads(path.read_text(encoding="utf-8"))
    print("=" * 88)
    print(f"{tag} 轨：{len(shots)} 条")
    print("=" * 88)
    print("字段名：", sorted(shots[0].keys()))
    for term in TERMS:
        by_field = Counter()
        by_shot = []
        for s in shots:
            n = 0
            for k, v in s.items():
                if isinstance(v, str) and term in v:
                    by_field[k] += v.count(term)
                    n += v.count(term)
            if n:
                by_shot.append((s.get("shot_number"), n))
        total = sum(by_field.values())
        if not total:
            continue
        print(f"\n【{term}】总计 {total} 处")
        print(f"  字段分布：{dict(by_field)}")
        print(f"  镜头：{by_shot}")
        # 样例
        shown = 0
        for s in shots:
            for k, v in s.items():
                if isinstance(v, str) and term in v and shown < 2:
                    i = v.find(term)
                    print(f"  样例 Shot_{s.get('shot_number'):03d}.{k}: …{v[max(0,i-80):i+80]}…")
                    shown += 1
    print()
