# -*- coding: utf-8 -*-
"""统计现有原创道具/品牌残留词，确保 Phase 2 不造第三套表达。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
OUT = ROOT / "inspect_term_counts.txt"
FILES = {
    "180": CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json",
    "120": CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json",
}
PROMPT_KEYS = ("prompt_zh", "prompt_en", "motion_zh", "motion_en")
TERMS = (
    "粉金星翼彗星书签挂坠", "彗星书签", "星翼彗星", "黄铜色小彗星吊坠", "小彗星吊坠",
    "素面银镜", "无字纯色奶茶杯", "纯色奶茶杯", "米白杯身", "纯色杯套",
    "star-wing comet", "comet bookmark", "brass comet", "plain silver",
    "plain solid-color", "off-white cup", "tasseled wooden bookmark",
    "小樱粉色星之杖", "白猫吊坠", "Cardcaptor Sakura", "white cat charm",
    "Kitty mirror", "Kitty Mirror", "pink Kitty mirror", "Kitty 化妆镜", "Hello Kitty",
    "panda", "ChaPanda", "熊猫杯", "熊猫标志", "熊猫保温杯套",
)

lines = []
for tag, path in FILES.items():
    shots = json.loads(path.read_text(encoding="utf-8"))
    lines.append("=" * 80)
    lines.append(f"{tag} 轨")
    lines.append("=" * 80)
    for term in TERMS:
        total = 0
        fields = 0
        for s in shots:
            for k in PROMPT_KEYS:
                v = s.get(k, "")
                if isinstance(v, str) and term in v:
                    total += v.count(term)
                    fields += 1
        if total:
            lines.append(f"  {term}: {total} 次 / {fields} 字段")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"written {OUT} ({OUT.stat().st_size}B)")
