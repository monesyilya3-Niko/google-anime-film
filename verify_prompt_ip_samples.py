# -*- coding: utf-8 -*-
"""Phase 2 关键镜头逐条目检：应用映射但不写文件，打印改前/改后片段。"""
import json
from collections import Counter
from pathlib import Path

import fix_prompt_ip as f

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
OUT = ROOT / "verify_prompt_ip_samples.txt"
FILES = {
    "180": CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json",
    "120": CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json",
}
CASES = [
    ("180", "Shot_021", "prompt_zh", ("粉金星翼", "白猫吊坠")),
    ("180", "Shot_021", "prompt_en", ("Cardcaptor Sakura", "white cat charm")),
    ("180", "Shot_030", "prompt_zh", ("小樱粉色星之杖",)),
    ("180", "Shot_037", "prompt_en", ("Kitty Mirror Lock", "ChaPanda")),
    ("180", "Shot_041", "prompt_en", ("Kitty mirror",)),
    ("180", "Shot_058", "prompt_en", ("Cardcaptor Sakura",)),
    ("180", "Shot_135", "prompt_zh", ("熊猫保温", "熊猫杯")),
    ("180", "Shot_135", "prompt_en", ("panda thermal", "panda cup")),
    ("180", "Shot_136", "prompt_zh", ("熊猫保温套",)),
    ("180", "Shot_150", "prompt_en", ("panda-logo cups",)),
    ("120", "Manus15s_103", "prompt_en", ("ChaPanda",)),
    ("120", "Manus15s_091", "prompt_zh", ("熊猫保温",)),
]

lines = []
for tag, label, key, terms in CASES:
    shots = json.loads(FILES[tag].read_text(encoding="utf-8"))
    s = next((x for x in shots if (x.get("shot_id") or x.get("manus_15s_id")) == label), None)
    if s is None:
        lines.append(f"[{tag} {label}] 未找到")
        continue
    old = s.get(key, "")
    new = f.apply_field(old, f.build_mappings("05"), Counter())
    lines.append("=" * 100)
    lines.append(f"[{tag} {label}.{key}]")
    for term in terms:
        i = old.find(term)
        if i < 0:
            lines.append(f"  -- 原字段未找到 {term}")
            continue
        j = new.find(term)
        lines.append(f"  ### {term}")
        lines.append(f"  改前：…{old[max(0, i-140):i+240]}…")
        # 改后按新词定位
        for _, o, t in f.build_mappings("05"):
            if o == term:
                k = new.find(t[:24])
                if k >= 0:
                    lines.append(f"  改后：…{new[max(0, k-140):k+260]}…")
                break
        else:
            lines.append(f"  改后：…{new[max(0, i-140):i+240]}…")
    lines.append("")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"written {OUT} ({OUT.stat().st_size}B)")
