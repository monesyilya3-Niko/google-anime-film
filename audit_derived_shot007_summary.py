# -*- coding: utf-8 -*-
"""V19 派生文档 Shot_007 段残留复核（紧凑输出，写 UTF-8 文件）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, list_in  # noqa: E402

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "audit_derived_shot007_summary.txt"
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


lines = []
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
    # 逐个 Shot_007，截到下一个 Shot_008 或 600 字
    flags = []
    start = 0
    while True:
        i = t.find("Shot_007", start)
        if i < 0:
            break
        j = t.find("Shot_008", i)
        seg = t[i:j if j > 0 else i + 700]
        has_name = OLD_NAME in seg
        has_id = OLD_ID in seg
        if has_name or has_id:
            flags.append((i, has_name, has_id, seg[:220].replace("\n", " ")))
        start = i + 1
    lines.append(f"{name}\n  chars={len(t)} Shot_007={t.count('Shot_007')} 段内残留={len(flags)}")
    for i, hn, hi, prev in flags:
        lines.append(f"    @{i} name={hn} id={hi} | {prev}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"written {OUT} ({OUT.stat().st_size}B)")
