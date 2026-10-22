# -*- coding: utf-8 -*-
"""导出 IP 词的提示词上下文（写 UTF-8 文件，供 Phase 2 映射设计）。"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
OUT = ROOT / "inspect_ip_contexts.txt"
FILES = {
    "180": CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json",
    "120": CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json",
}
PROMPT_KEYS = ("prompt_zh", "prompt_en", "motion_zh", "motion_en")
TERMS = ("小樱粉色星之杖", "白猫吊坠", "茶百道", "Kitty",
         "Cardcaptor Sakura", "white cat charm", "Hello Kitty")

lines = []
for tag, path in FILES.items():
    shots = json.loads(path.read_text(encoding="utf-8"))
    lines.append("=" * 100)
    lines.append(f"{tag} 轨 · 提示词/运镜层 IP 上下文")
    lines.append("=" * 100)
    for term in TERMS:
        lines.append(f"\n### {term}")
        seen = set()
        count = 0
        for s in shots:
            label = s.get("shot_id") or s.get("manus_15s_id")
            for k in PROMPT_KEYS:
                v = s.get(k, "")
                if not isinstance(v, str) or term not in v:
                    continue
                for m in re.finditer(re.escape(term), v):
                    i = m.start()
                    frag = v[max(0, i - 140):i + 160].replace("\n", " ")
                    key = frag[:80]
                    if key in seen:
                        continue
                    seen.add(key)
                    count += 1
                    lines.append(f"  [{label}.{k}] …{frag}…")
        lines.append(f"  （去重后 {count} 条上下文）")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"written {OUT} ({OUT.stat().st_size}B)")
