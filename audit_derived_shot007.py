# -*- coding: utf-8 -*-
"""扫描 V19 所有派生文档中的 Shot_007 旧挂载文案。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, list_in  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
V19 = "103fzTVsi34QCz6hkpHTzR7RJNsTmZgN-"
OLD_NAME = "04_图3.1_Scene01_暮冬之雪与春雨之窗_3840x2160_4K.jpg"
OLD_ID = "1pkU017WSHLc7v3EAFPCO7y1gqmSWoVNv"


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


for name, f in sorted(list_in(V19).items()):
    mt = f["mimeType"]
    if mt == "application/vnd.google-apps.document":
        t = gdoc_text(f["id"])
    elif mt.startswith("text/"):
        t = api(f"https://www.googleapis.com/drive/v3/files/{f['id']}?alt=media&supportsAllDrives=true", raw=True).decode("utf-8")
    else:
        continue
    if "Shot_007" not in t:
        continue
    print("=" * 86)
    print(f"{name}")
    print(f"  字符数 {len(t)}  Shot_007 {t.count('Shot_007')} 次  旧ID {t.count(OLD_ID)} 次  旧名 {t.count(OLD_NAME)} 次")
    # 找 Shot_007 之后 1500 字内是否出现旧 ID
    start = 0
    while True:
        i = t.find("Shot_007", start)
        if i < 0:
            break
        seg = t[i:i + 1600]
        if OLD_ID in seg or OLD_NAME in seg:
            print(f"  ✘ 位置 {i} 的 Shot_007 段含旧引用")
            j = seg.find(OLD_ID) if OLD_ID in seg else seg.find(OLD_NAME)
            print(f"     …{seg[max(0, j - 100):j + 120]}…")
        start = i + 1
