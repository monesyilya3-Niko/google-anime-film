# -*- coding: utf-8 -*-
"""把 15s 判定所需信息写入 UTF-8 文件，避免控制台编码/截断。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api  # noqa: E402

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
OUT = ROOT / "inspect_15s_out.txt"
TOTAL = "1_37tPXPYlTmguorlPZfMvVPCr8Og3Z_7q92mCva-g5Y"
OLD_NAME = "04_图3.1_Scene01_暮冬之雪与春雨之窗_3840x2160_4K.jpg"
OLD_ID = "1pkU017WSHLc7v3EAFPCO7y1gqmSWoVNv"

j120 = json.loads((CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json").read_text(encoding="utf-8"))
j180 = json.loads((CACHE / "cloud_current" / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json").read_text(encoding="utf-8"))

lines = []

lines.append("=" * 88)
lines.append("A. 120 轨 Manus15s_005（原始 JSON 字段）")
lines.append("=" * 88)
hits = [s for s in j120 if s.get("manus_15s_id") == "Manus15s_005"]
lines.append(f"命中条数：{len(hits)}")
for n, s in enumerate(hits):
    lines.append(f"\n--- 第 {n+1} 条 ---")
    for k in sorted(s.keys()):
        if any(x in k for x in ("primary", "first_frame", "end_frame", "source", "timecode", "manus_15s_id", "duration", "frame_range")):
            v = s.get(k)
            lines.append(f"  {k} ({type(v).__name__}): {json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else repr(v)}")

lines.append("\n" + "=" * 88)
lines.append("B. 180 轨 Shot_007 manus_15s_mapping（原始类型）")
lines.append("=" * 88)
s7 = next(s for s in j180 if s["shot_number"] == 7)
m = s7.get("manus_15s_mapping")
lines.append(f"type={type(m).__name__}")
lines.append(json.dumps(m, ensure_ascii=False, indent=1) if not isinstance(m, str) else repr(m))


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


lines.append("\n" + "=" * 88)
lines.append("C. Act1 15s 段（含 Manus15s_005 的块）")
lines.append("=" * 88)
act1 = gdoc_text("1JAcgxtBjt88n81zMbkxWxbaMVOaZWzNrcdI9i940z20")
idx = []
start = 0
while True:
    i = act1.find("Manus15s_005", start)
    if i < 0:
        break
    idx.append(i)
    start = i + 1
lines.append(f"Manus15s_005 出现位置：{idx}")
for i in idx:
    lines.append(f"\n--- 位置 {i} 前后关键行 ---")
    seg = act1[max(0, i - 1200):i + 1200]
    for ln in seg.splitlines():
        if any(x in ln for x in ("主母带", "首帧", "尾帧", "Manus15s_005", "Shot_007", "Shot_008", "参考槽")):
            lines.append(f"  {ln[:260]}")

lines.append("\n" + "=" * 88)
lines.append("D. 总控表 Shot_007 段")
lines.append("=" * 88)
tt = gdoc_text(TOTAL)
start = 0
n = 0
while True:
    i = tt.find("Shot_007", start)
    if i < 0:
        break
    n += 1
    lines.append(f"\n--- 第 {n} 处，位置 {i} ---")
    seg = tt[max(0, i - 300):i + 1000]
    lines.append(seg)
    start = i + 1

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"written {OUT} ({OUT.stat().st_size}B)")
