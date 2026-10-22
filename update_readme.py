# -*- coding: utf-8 -*-
"""把本地修订版 README 覆盖到云端同一 File ID，并回读校验 md5。"""
import hashlib
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

ROOT = Path(__file__).resolve().parent
LOCAL = ROOT / "00_README_工程总入口与交接说明.md"
FID = "1ZSZ-suR1vPyw37EgFLEEtTledCsy7hga"
data = LOCAL.read_bytes()

# 1) 覆盖内容（media upload，保留 File ID）
api(f"https://www.googleapis.com/upload/drive/v3/files/{FID}?uploadType=media&supportsAllDrives=true",
    data=data, method="PATCH", ctype="text/markdown; charset=utf-8")

# 2) 元数据
meta = api(f"https://www.googleapis.com/drive/v3/files/{FID}"
           "?fields=id,name,size,md5Checksum,mimeType,modifiedTime&supportsAllDrives=true")
print(f"云端：{meta['name']}")
print(f"  类型 {meta['mimeType']}  体积 {int(meta['size'])}B  修改 {meta['modifiedTime']}")
print(f"  云端 md5 {meta['md5Checksum']}")

# 3) 回读
back = api(f"https://www.googleapis.com/drive/v3/files/{FID}?alt=media&supportsAllDrives=true", raw=True)
local_md5 = hashlib.md5(data).hexdigest()
back_md5 = hashlib.md5(back).hexdigest()
print(f"本地 {len(data)}B  md5 {local_md5}")
print(f"回读 {len(back)}B  md5 {back_md5}")
print(f"一致性：{'✔ 完全一致' if local_md5 == back_md5 == meta['md5Checksum'] else '✘ 不一致'}")
