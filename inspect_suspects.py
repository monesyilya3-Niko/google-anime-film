# -*- coding: utf-8 -*-
"""聚焦 Shot_007 / 017 / 177：primary 字段 vs upload_instruction 的 ① 槽位。"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
CACHE = Path(__file__).resolve().parent / "source" / "audit"
J180 = CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json"
shots = {s["shot_number"]: s for s in json.loads(J180.read_text(encoding="utf-8"))}

for n in (7, 17, 177):
    s = shots[n]
    print("=" * 86)
    print(f"Shot_{n:03d}")
    print("=" * 86)
    for k in ("primary_image_key", "primary_image_path", "primary_cloud_filename",
              "primary_drive_file_id", "first_frame_cloud_filename", "first_frame_drive_file_id"):
        print(f"  {k}: {s.get(k)}")
    for k in ("upload_instruction", "cloud_dispatch_command_zh"):
        t = str(s.get(k, ""))
        i = t.find("①")
        print(f"\n  --- {k} ① 槽位 ---")
        print("  " + t[i:i + 420].replace("\n", " "))
    print()
