# -*- coding: utf-8 -*-
"""调试 run 索引与候选句位置。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
DOC = "1JAcgxtBjt88n81zMbkxWxbaMVOaZWzNrcdI9i940z20"
OLD_NAME = "04_图3.1_Scene01_暮冬之雪与春雨之窗_3840x2160_4K.jpg"
OLD_ID = "1pkU017WSHLc7v3EAFPCO7y1gqmSWoVNv"

doc = api(f"https://docs.googleapis.com/v1/documents/{DOC}")
runs = []


def walk(elems, depth=0):
    for el in elems:
        if "paragraph" in el:
            for e in el["paragraph"].get("elements", []):
                if "textRun" in e:
                    runs.append(e["textRun"])
        elif "table" in el:
            for row in el["table"].get("tableRows", []):
                for cell in row.get("tableCells", []):
                    walk(cell.get("content", []), depth + 1)


walk(doc.get("body", {}).get("content", []))

# 按 startIndex 排序，检查是否连续
runs_sorted = sorted(runs, key=lambda r: r.get("startIndex", 0))
print("首 run:", runs_sorted[0].get("startIndex"), repr(runs_sorted[0].get("content", "")[:40]))
print("末 run:", runs_sorted[-1].get("startIndex"), runs_sorted[-1].get("endIndex"))
gaps = 0
prev_end = runs_sorted[0].get("endIndex")
for r in runs_sorted[1:]:
    s = r.get("startIndex")
    if s > prev_end:
        gaps += 1
        if gaps <= 5:
            print(f"  gap: {prev_end} → {s} ({s - prev_end})")
    prev_end = max(prev_end, r.get("endIndex"))
print(f"总 gaps {gaps}")

# 找 startIndex 在 77000-78500 的 run
print("\n附近 runs：")
for r in runs_sorted:
    s, e = r.get("startIndex"), r.get("endIndex")
    if 77000 <= s <= 78500:
        print(f"  [{s},{e}) {r.get('content','')!r}")

# 直接定位包含 Shot_006_LastFrame 且后续有 04_ 的 run
print("\n包含 Shot_006_LastFrame.png 的 run：")
for r in runs_sorted:
    c = r.get("content", "")
    if "Shot_006_LastFrame.png" in c:
        print(f"  [{r.get('startIndex')},{r.get('endIndex')}) {c!r}")
