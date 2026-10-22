# -*- coding: utf-8 -*-
"""Act1 中 Shot_007 旧挂载句定点替换。默认 dry-run，--apply 执行。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
DOC = "1JAcgxtBjt88n81zMbkxWxbaMVOaZWzNrcdI9i940z20"
OLD_NAME = "04_图3.1_Scene01_暮冬之雪与春雨之窗_3840x2160_4K.jpg"
NEW_NAME = "01c_图0.1_上幅16x9_星河苍穹与双色彗星终幕空镜_3840x2160_4K.jpg"
OLD_ID = "1pkU017WSHLc7v3EAFPCO7y1gqmSWoVNv"
NEW_ID = "16S3Lyt2Lbf8uyU8JMy6zUayKY87aSQHT"
APPLY = "--apply" in sys.argv

OLD = (f"截取前镜第240帧末帧 `Shot_006_LastFrame.png` 作为 0.0s 首帧（100%像素锚定），"
       f"同时挂载云端母带 `{OLD_NAME}` (`File ID: {OLD_ID}`，Weight=0.55) 防长链画质漂移")
NEW = OLD.replace(OLD_NAME, NEW_NAME).replace(OLD_ID, NEW_ID)


def doc_text():
    doc = api(f"https://docs.googleapis.com/v1/documents/{DOC}")
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


before = doc_text()
print(f"文档 {DOC} 字符数 {len(before)}")
print(f"旧句出现 {before.count(OLD)} 次；04_图3.1 共 {before.count(OLD_NAME)} 次；1pkU017 共 {before.count(OLD_ID)} 次")
assert before.count(OLD) == 1, "旧句不唯一，终止"
i = before.find(OLD)
print(f"位置 {i}，上下文：…{before[max(0, i - 60):i + len(OLD) + 60]}…")

if not APPLY:
    print("\nDRY-RUN：未写入。加 --apply 执行。")
    raise SystemExit(0)

resp = api(f"https://docs.googleapis.com/v1/documents/{DOC}:batchUpdate",
           data=__import__("json").dumps({"requests": [{
               "replaceAllText": {
                   "containsText": {"text": OLD, "matchCase": True},
                   "replaceText": NEW,
               }}]}).encode(),
           method="POST", ctype="application/json; charset=UTF-8")
changed = resp.get("replies", [{}])[0].get("replaceAllText", {}).get("occurrencesChanged")
print(f"occurrencesChanged = {changed}")
assert changed == 1

after = doc_text()
print(f"写后字符数 {len(after)}（变化 {len(after) - len(before):+d}）")
print(f"旧句 {after.count(OLD)} 次；新句 {after.count(NEW)} 次")
print(f"04_图3.1 {after.count(OLD_NAME)} 次；1pkU017 {after.count(OLD_ID)} 次")
assert after.count(OLD) == 0
assert after.count(NEW) == 1
assert after.count(OLD_NAME) == before.count(OLD_NAME) - 1
assert after.count(OLD_ID) == before.count(OLD_ID) - 1
assert after == before.replace(OLD, NEW), "全文不等于预期替换结果"
print("✔ Act1 已修复：全文等于「原全文仅替换该句」，无其他改动")
