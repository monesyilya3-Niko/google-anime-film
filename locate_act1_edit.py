# -*- coding: utf-8 -*-
"""定位 Act1 中 Shot_007 专属旧句：唯一性 + ParagraphElement run 结构 + 精确索引。"""
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

runs = []  # (startIndex, endIndex, content, textStyle)


def walk(elems):
    for el in elems:
        if "paragraph" in el:
            for e in el["paragraph"].get("elements", []):
                if "textRun" in e:
                    runs.append((e.get("startIndex"), e.get("endIndex"),
                                 e["textRun"].get("content", ""),
                                 e["textRun"].get("textStyle", {})))
        elif "table" in el:
            for row in el["table"].get("tableRows", []):
                for cell in row.get("tableCells", []):
                    walk(cell.get("content", []))


walk(doc.get("body", {}).get("content", []))
print(f"textRun 数：{len(runs)}")

runs = [r for r in runs if r[0] is not None]
runs.sort(key=lambda r: r[0])
print(f"首 run {runs[0][0]}，末 run {runs[-1][1]}")

# 用索引还原全文（UTF-16 单位）
full = []
pos = 0
for s, e, c, st in runs:
    if s > pos:
        full.append("\x00" * (s - pos))
        pos = s
    full.append(c)
    pos = e
text = "".join(full)
print(f"全文长度（含 gap 占位）：{len(text)}")

cand = (f"截取前镜第240帧末帧 `Shot_006_LastFrame.png` 作为 0.0s 首帧（100%像素锚定），"
        f"同时挂载云端母带 `{OLD_NAME}` (`File ID: {OLD_ID}`，Weight=0.55) 防长链画质漂移")
print(f"候选句出现次数：{text.count(cand)}")
i = text.find(cand)
print(f"位置：{i}")
print(f"前 80：{text[max(0, i - 80):i]!r}")
print(f"后 80：{text[i + len(cand):i + len(cand) + 80]!r}")

# 检查覆盖的 run（按 UTF-16 长度计算候选句 end）
cand_u16 = len(cand.encode("utf-16-le")) // 2
start, end = i, i + cand_u16
print(f"UTF-16 区间 [{start},{end})  长度 {cand_u16}")

print("\n覆盖的 runs：")
for n, (s, e, c, st) in enumerate(runs):
    if e <= start or s >= end:
        continue
    print(f"\nrun#{n} [{s},{e}) len={e - s}")
    print(f"  style={json.dumps(st, ensure_ascii=False)}")
    print(f"  content={c!r}")
