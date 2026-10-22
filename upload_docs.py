# -*- coding: utf-8 -*-
"""上传修订后的 02/04，回读校验，并同步 source/audit 本地副本。"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
FIX = ROOT / "docs_fix"
ZCODE = ROOT / "source" / "audit"

DOCS = [
    ("1YA7cNT0jJwTY5MtvSkqn34tTl6bTgvEW", "02_4K母带画面修订清单_V19.md", FIX / "02.md"),
    ("17klUmU7h2FIrsT4D0FBQrN2AojBfYHUb", "04_未完成事项清单_V19.md", FIX / "04.md"),
]

for fid, name, path in DOCS:
    data = path.read_bytes()
    md5 = hashlib.md5(data).hexdigest()
    print("=" * 84)
    print(name)
    print(f"  本地修订件 {len(data)}B md5={md5}")
    cur = api(f"https://www.googleapis.com/drive/v3/files/{fid}?alt=media&supportsAllDrives=true", raw=True)
    print(f"  云端当前 {len(cur)}B md5={hashlib.md5(cur).hexdigest()}")
    orig = (ZCODE / name).read_bytes()
    print(f"  本地原稿 {len(orig)}B md5={hashlib.md5(orig).hexdigest()}  与云端同={orig == cur}")
    assert cur == orig, "云端与本地原稿不一致，终止"

    r = api(f"https://www.googleapis.com/upload/drive/v3/files/{fid}"
            "?uploadType=media&supportsAllDrives=true&fields=id,name,mimeType,size,md5Checksum",
            data=data, method="PATCH", ctype="text/markdown")
    print(f"  上传返回 {r.get('size')}B mime={r.get('mimeType')} md5={r.get('md5Checksum')}")
    assert r.get("md5Checksum") == md5

    back = api(f"https://www.googleapis.com/drive/v3/files/{fid}?alt=media&supportsAllDrives=true", raw=True)
    assert back == data
    print("  ✔ 云端回读字节一致")

    # 同步本地副本
    (ZCODE / name).write_bytes(data)
    synced = (ZCODE / name).read_bytes()
    assert synced == data
    print(f"  ✔ zcode 本地副本已同步 md5={hashlib.md5(synced).hexdigest()}")
