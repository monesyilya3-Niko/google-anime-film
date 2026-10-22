# -*- coding: utf-8 -*-
"""检查重画包两个文本文件的真实 MIME 与内容完整性。"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, list_in, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

ROOT = Path(__file__).resolve().parent
PACK = "1o6sBhOJJBfVcMJttU7YxzsCCixGdFao0"
pack = list_in(PACK)
for name, local in (("重画清单.csv", ROOT / "redraw_pack" / "重画清单.csv"),
                    ("重画提示词.md", ROOT / "redraw_pack" / "重画提示词.md")):
    f = pack[name]
    b = api(f"https://www.googleapis.com/drive/v3/files/{f['id']}?alt=media&supportsAllDrives=true", raw=True)
    lb = local.read_bytes()
    print(f"{name}")
    print(f"  云端 MIME {f['mimeType']}  体积 {len(b)}B  md5 {hashlib.md5(b).hexdigest()}")
    print(f"  本地      体积 {len(lb)}B  md5 {hashlib.md5(lb).hexdigest()}  同版 {'✔' if b == lb else '✘'}")
    print(f"  首行：{b[:90].decode('utf-8', 'replace').replace(chr(10), ' | ')}")
