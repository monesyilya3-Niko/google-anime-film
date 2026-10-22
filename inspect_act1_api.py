# -*- coding: utf-8 -*-
"""提取 Act1 Google Doc 全文（含表格），定位 Shot_007 的旧挂载句并判断唯一性。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
DOC = "1JAcgxtBjt88n81zMbkxWxbaMVOaZWzNrcdI9i940z20"
OLD_NAME = "04_图3.1_Scene01_暮冬之雪与春雨之窗_3840x2160_4K.jpg"
OLD_ID = "1pkU017WSHLc7v3EAFPCO7y1gqmSWoVNv"

doc = api(f"https://docs.googleapis.com/v1/documents/{DOC}")


def collect(elems, out):
    for el in elems:
        if "paragraph" in el:
            for e in el["paragraph"].get("elements", []):
                if "textRun" in e:
                    out.append(e["textRun"].get("content", ""))
        elif "table" in el:
            for row in el["table"].get("tableRows", []):
                for cell in row.get("tableCells", []):
                    collect(cell.get("content", []), out)


parts = []
collect(doc.get("body", {}).get("content", []), parts)
text = "".join(parts)
print(f"文档标题：{doc.get('title')}")
print(f"提取字符数：{len(text)}")
print(f"04_图3.1 出现 {text.count(OLD_NAME)} 次；1pkU017 出现 {text.count(OLD_ID)} 次")

print("\n" + "=" * 86)
print("所有 04_图3.1 出现位置及上下文")
print("=" * 86)
start = 0
n = 0
while True:
    i = text.find(OLD_NAME, start)
    if i < 0:
        break
    n += 1
    a, b = max(0, i - 260), min(len(text), i + 200)
    ctx = text[a:b].replace("\n", " ")
    # 找最近的 Shot_xxx
    import re
    shots = re.findall(r"Shot_\d{3}", text[max(0, i - 600):i])
    print(f"\n[{n}] 位置 {i}  最近 Shot 标记 {shots[-1] if shots else '?'}")
    print(f"    …{ctx}…")
    start = i + 1

print("\n" + "=" * 86)
print("Shot_007 调取指令段（从文档定位）")
print("=" * 86)
i = text.find("Shot_007 (01:00–01:10")
if i < 0:
    i = text.find("Shot_007")
print(f"位置 {i}")
print(text[i:i + 900].replace("\n", " "))

# 候选唯一句：从 "同时挂载云端母带" 到 "防长链画质漂移"
print("\n" + "=" * 86)
print("候选句出现次数")
print("=" * 86)
for cand in [
    f"同时挂载云端母带 `{OLD_NAME}` (`File ID: {OLD_ID}`，Weight=0.55) 防长链画质漂移",
    f"同时挂载云端母带 `{OLD_NAME}`",
    f"`{OLD_NAME}` (`File ID: {OLD_ID}`，Weight=0.55) 防长链画质漂移",
]:
    print(f"  {text.count(cand)} 次  |  {cand[:90]}…")
