# -*- coding: utf-8 -*-
"""对齐 120 轨 Manus15s_005 / 180 轨 Shot_007 的 15s 映射 / Act1 15s 段 / 总控表。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, list_in  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
CACHE = Path(__file__).resolve().parent / "source" / "audit"
V19 = "103fzTVsi34QCz6hkpHTzR7RJNsTmZgN-"
TOTAL = "1_37tPXPYlTmguorlPZfMvVPCr8Og3Z_7q92mCva-g5Y"
OLD_NAME = "04_图3.1_Scene01_暮冬之雪与春雨之窗_3840x2160_4K.jpg"

j120 = json.loads((CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json").read_text(encoding="utf-8"))
j180 = json.loads((CACHE / "cloud_current" / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json").read_text(encoding="utf-8"))

print("=" * 88)
print("120 轨 Manus15s_005")
print("=" * 88)
for s in j120:
    if s.get("manus_15s_id") == "Manus15s_005":
        for k in ("manus_15s_id", "source_10s_shots", "primary_cloud_filename", "primary_drive_file_id",
                  "first_frame_cloud_filename", "first_frame_drive_file_id",
                  "end_frame_cloud_filename", "end_frame_drive_file_id", "timecode"):
            print(f"  {k}: {s.get(k)}")
        break

print("\n" + "=" * 88)
print("180 轨 Shot_007 的 manus_15s_mapping")
print("=" * 88)
s7 = next(s for s in j180 if s["shot_number"] == 7)
print(f"  {s7.get('manus_15s_mapping')}")

print("\n" + "=" * 88)
print("Act1 15s 段（位置 409913 前后）")
print("=" * 88)


def gdoc_text(did):
    doc = api(f"https://docs.googleapis.com/v1/documents/{did}")
    parts = []

    def walk(elems):
        for el in elems:
            if "paragraph" in el:
                for e in el["paragraph"].get("elements", []):
                    if "textRun" in e:
                        parts.append(e["textRun"].get("content", ""))
            elif "table" in el:
                for row in el["table"].get("tableRows", []):
                    for cell in row.get("tableCells", []):
                        walk(cell.get("content", []))

    walk(doc.get("body", {}).get("content", []))
    return "".join(parts)


act1 = gdoc_text("1JAcgxtBjt88n81zMbkxWxbaMVOaZWzNrcdI9i940z20")
i = act1.find("Manus15s_005")
while i >= 0:
    print(f"\n--- 位置 {i} ---")
    print(act1[max(0, i - 500):i + 1600])
    i = act1.find("Manus15s_005", i + 1)

print("\n" + "=" * 88)
print("总控表 Shot_007 段")
print("=" * 88)
tt = gdoc_text(TOTAL)
start = 0
while True:
    i = tt.find("Shot_007", start)
    if i < 0:
        break
    print(f"\n--- 位置 {i} ---")
    print(tt[max(0, i - 350):i + 1100])
    start = i + 1
