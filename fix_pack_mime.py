# -*- coding: utf-8 -*-
"""修复待重画包两个文本文件的 MIME：内容字节不变，仅改 Content-Type。

重画清单.csv  image/jpeg → text/csv
重画提示词.md image/jpeg → text/markdown
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

FILES = [
    ("1Q-__fB7O7-RCa0SLs-D1ZyRKkWxpyQTq", "重画清单.csv", "text/csv",
     "9802b2b2cf8a535e3ef8747d1d93e304"),
    ("1_csUuNdGNrJXsNDz-OIg7U5bIIkMIaFr", "重画提示词.md", "text/markdown",
     "b6f0ac2b16915bf849ff2ba491d5babc"),
]

for fid, name, mime, expect_md5 in FILES:
    print("=" * 80)
    print(name)
    before = api(f"https://www.googleapis.com/drive/v3/files/{fid}"
                 "?fields=id,name,mimeType,size,md5Checksum&supportsAllDrives=true")
    print(f"  修复前 mime={before['mimeType']} size={before['size']} md5={before.get('md5Checksum')}")
    data = api(f"https://www.googleapis.com/drive/v3/files/{fid}?alt=media&supportsAllDrives=true", raw=True)
    md5 = hashlib.md5(data).hexdigest()
    print(f"  下载 {len(data)}B md5={md5}")
    assert md5 == expect_md5, f"内容 md5 不符：{md5} != {expect_md5}"

    r = api(f"https://www.googleapis.com/upload/drive/v3/files/{fid}"
            "?uploadType=media&supportsAllDrives=true&fields=id,name,mimeType,size,md5Checksum",
            data=data, method="PATCH", ctype=mime)
    print(f"  上传返回 mime={r.get('mimeType')} size={r.get('size')} md5={r.get('md5Checksum')}")

    after = api(f"https://www.googleapis.com/drive/v3/files/{fid}"
                "?fields=id,name,mimeType,size,md5Checksum&supportsAllDrives=true")
    print(f"  回读 mime={after['mimeType']} size={after['size']} md5={after.get('md5Checksum')}")
    assert after["mimeType"] == mime, after["mimeType"]
    assert after["md5Checksum"] == expect_md5, after["md5Checksum"]
    again = api(f"https://www.googleapis.com/drive/v3/files/{fid}?alt=media&supportsAllDrives=true", raw=True)
    assert again == data, "回读字节不一致"
    print("  ✔ MIME 已修，内容字节完全一致")
