# -*- coding: utf-8 -*-
"""定位 Act1 中 Shot_007 专属旧句：唯一性 + run 结构 + 精确索引。"""
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


def walk(elems):
    for el in elems:
        if "paragraph" in el:
            for e in el["paragraph"].get("elements", []):
                if "textRun" in e:
                    runs.append(e["textRun"])
        elif "table" in el:
            for row in el["table"].get("tableRows", []):
                for cell in row.get("tableCells", []):
                    walk(cell.get("content", []))


walk(doc.get("body", {}).get("content", []))
print(f"textRun 数：{len(runs)}")

# 用 run 的 startIndex 还原全文（UTF-16 索引空间）
full = []
pos = 0
for r in runs:
    s = r.get("startIndex", 0)
    if s > pos:
        full.append("\x00" * (s - pos))
        pos = s
    c = r.get("content", "")
    full.append(c)
    pos += len(c.encode("utf-16-le")) // 2
text = "".join(full)

cand = (f"截取前镜第240帧末帧 `Shot_006_LastFrame.png` 作为 0.0s 首帧（100%像素锚定），"
        f"同时挂载云端母带 `{OLD_NAME}` (`File ID: {OLD_ID}`，Weight=0.55) 防长链画质漂移")
print(f"候选句长度 {len(cand)}（UTF-16 {len(cand.encode('utf-16-le')) // 2}）")
print(f"候选句出现次数：{text.count(cand)}")

i = text.find(cand)
print(f"首次位置（UTF-16 单位）：{i}")
if i >= 0:
    print(f"前 100 字符：{text[max(0, i - 100):i]!r}")
    print(f"后 100 字符：{text[i + len(cand):i + len(cand) + 100]!r}")

print("\n" + "=" * 86)
print("覆盖该句的 textRun")
print("=" * 86)
start, end = i, i + len(cand.encode("utf-16-le")) // 2
for n, r in enumerate(runs):
    rs, re_ = r.get("startIndex", 0), r.get("endIndex", 0)
    if re_ <= start or rs >= end:
        continue
    c = r.get("content", "")
    st = r.get("textStyle", {})
    print(f"\nrun#{n} [{rs},{re_}) len={re_ - rs} style={json.dumps(st, ensure_ascii=False)}")
    print(f"  {c!r}")
