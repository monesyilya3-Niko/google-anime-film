# -*- coding: utf-8 -*-
"""诊断 熊猫保温杯套 映射为何未生效。"""
import json
from pathlib import Path
import fix_prompt_ip as f

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
path = CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json"
shots = json.loads(path.read_text(encoding="utf-8"))
s = next(x for x in shots if x.get("shot_id") == "Shot_135")
v = s["prompt_zh"]
print("原始包含 熊猫保温杯套:", v.count("熊猫保温杯套"), "熊猫保温套:", v.count("熊猫保温套"))
mappings = f.build_mappings("05")
for name, old, new in mappings:
    if "熊猫保温" in old:
        print("映射:", name, repr(old), "->", repr(new), "命中:", v.count(old))
# 逐步应用，看在哪一步被掩码
masked, store = f.mask(v)
print("掩码后包含 熊猫保温杯套:", masked.count("熊猫保温杯套"), "掩码段数:", len(store))
for i, seg in enumerate(store):
    if "熊猫保温" in seg:
        print("掩码段含熊猫保温:", i, seg[:200])
new = f.apply_field(v, mappings, __import__("collections").Counter())
print("替换后包含 熊猫保温杯套:", new.count("熊猫保温杯套"), "熊猫保温套:", new.count("熊猫保温套"))
i = new.find("熊猫保温")
print("替换后上下文:", new[max(0, i-120):i+160] if i >= 0 else "无")
