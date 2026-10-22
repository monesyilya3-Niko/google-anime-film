# -*- coding: utf-8 -*-
"""全量校验：Phase 2 映射前后，文件名、台词、字面茶百道必须逐字段完全一致。"""
import json
import re
from collections import Counter
from pathlib import Path

import fix_prompt_ip as f

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
OUT = ROOT / "verify_prompt_ip_protected.txt"
FILES = {
    "180": CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json",
    "120": CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json",
}
MAPPINGS = f.build_mappings("05")

lines = []
for tag, path in FILES.items():
    shots = json.loads(path.read_text(encoding="utf-8"))
    filenames_old, filenames_new = [], []
    dialogue_old, dialogue_new = [], []
    tea_old = tea_new = 0
    kitty_fn_old = kitty_fn_new = 0
    changed = 0
    for s in shots:
        label = s.get("shot_id") or s.get("manus_15s_id")
        for k in f.ALLOWED_FIELDS:
            old = s.get(k)
            if not isinstance(old, str):
                continue
            new = f.apply_field(old, MAPPINGS, Counter())
            if new != old:
                changed += 1
            fo = f.FILENAME_RE.findall(old)
            fn = f.FILENAME_RE.findall(new)
            do = f.DIALOGUE_RE.findall(old)
            dn = f.DIALOGUE_RE.findall(new)
            filenames_old.extend(fo)
            filenames_new.extend(fn)
            dialogue_old.extend(do)
            dialogue_new.extend(dn)
            tea_old += old.count("茶百道")
            tea_new += new.count("茶百道")
            kitty_fn_old += sum(x.count("Kitty") for x in fo)
            kitty_fn_new += sum(x.count("Kitty") for x in fn)
            if fo != fn:
                lines.append(f"  ✘ 文件名变化 [{tag} {label}.{k}]")
            if do != dn:
                lines.append(f"  ✘ 台词变化 [{tag} {label}.{k}]")
            if old.count("茶百道") != new.count("茶百道"):
                lines.append(f"  ✘ 茶百道字面变化 [{tag} {label}.{k}]")

    lines.append("=" * 80)
    lines.append(f"{tag} 轨 · 保护对象全量校验（{changed} 字段被修改）")
    lines.append("=" * 80)
    lines.append(f"  文件名 token：改前 {len(filenames_old)} / 改后 {len(filenames_new)}  完全一致={filenames_old == filenames_new}")
    lines.append(f"  含 Kitty 的文件名 token：改前 {kitty_fn_old} / 改后 {kitty_fn_new}")
    lines.append(f"  台词「…」段：改前 {len(dialogue_old)} / 改后 {len(dialogue_new)}  完全一致={dialogue_old == dialogue_new}")
    lines.append(f"  字面茶百道：改前 {tea_old} / 改后 {tea_new}")
    lines.append("")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
print(f"written {OUT} ({OUT.stat().st_size}B)")
