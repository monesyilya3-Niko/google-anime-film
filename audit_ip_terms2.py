# -*- coding: utf-8 -*-
"""精确统计：提示词/运镜层 vs 文件名/指令层的 IP 残留。"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
CACHE = Path(__file__).resolve().parent / "source" / "audit"
FILES = {
    "180": CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json",
    "120": CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json",
}
TERMS = ["小樱粉色星之杖", "白猫吊坠", "茶百道", "Cardcaptor Sakura", "white cat charm", "Hello Kitty", "Kitty"]
PROMPT_KEYS = {"prompt_zh", "prompt_en", "motion_zh", "motion_en"}

for tag, path in FILES.items():
    shots = json.loads(path.read_text(encoding="utf-8"))
    print("=" * 90)
    print(f"{tag} 轨：{len(shots)} 条")
    print("=" * 90)
    for term in TERMS:
        prompt_c = Counter()
        meta_c = Counter()
        shots_hit = []
        for s in shots:
            label = s.get("shot_id") or s.get("manus_15s_id") or str(s.get("shot_number") or s.get("manus_15s_number"))
            n = 0
            for k, v in s.items():
                if not isinstance(v, str) or term not in v:
                    continue
                c = v.count(term)
                n += c
                (prompt_c if k in PROMPT_KEYS else meta_c)[k] += c
            if n:
                shots_hit.append((label, n))
        total = sum(prompt_c.values()) + sum(meta_c.values())
        if not total:
            continue
        print(f"\n【{term}】总 {total} 处")
        print(f"  提示词/运镜层 {sum(prompt_c.values())}：{dict(prompt_c)}")
        print(f"  文件名/指令层 {sum(meta_c.values())}：{dict(meta_c)}")
        print(f"  镜头：{shots_hit}")

    # 英文上下文样例
    print("\n" + "-" * 90)
    print("英文 IP 片段样例")
    print("-" * 90)
    seen = set()
    for s in shots:
        for k in ("prompt_en", "motion_en"):
            v = s.get(k, "")
            for term in ("Cardcaptor Sakura", "white cat charm", "Hello Kitty", "Kitty"):
                i = v.find(term)
                if i >= 0:
                    frag = v[max(0, i - 90):i + 110]
                    if frag[:50] in seen:
                        continue
                    seen.add(frag[:50])
                    print(f"  {s.get('shot_id') or s.get('manus_15s_id')}.{k}: …{frag}…")
                    if len(seen) >= 8:
                        break
            if len(seen) >= 8:
                break
        if len(seen) >= 8:
            break
    print()
