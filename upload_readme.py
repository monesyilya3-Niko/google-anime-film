# -*- coding: utf-8 -*-
"""收尾：把总入口 README 上传到工程总库根目录，并回读校验。"""
import hashlib
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, fresh_token, upload_binary  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

ROOT_ID = "1ya8IwwmFgLWCSE9i_sihtXyTmdW4R528"
SRC = Path(__file__).resolve().parent / "00_README_工程总入口与交接说明.md"
NAME = SRC.name

data = SRC.read_bytes()
local_md5 = hashlib.md5(data).hexdigest()
print(f"本地：{NAME}  {len(data):,} 字节  md5={local_md5}")


def root_children():
    q = urllib.parse.quote(f"'{ROOT_ID}' in parents and trashed=false")
    url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
           "&fields=files(id,name,mimeType,size,md5Checksum)&pageSize=100"
           "&supportsAllDrives=true")
    return api(url).get("files", [])


def upload_media(parent, file_id):
    """用 media 更新既有文件内容（保持 ID 与名称）。"""
    req = urllib.request.Request(
        f"https://www.googleapis.com/upload/drive/v3/files/{file_id}"
        "?uploadType=media&supportsAllDrives=true&fields=id,name,size,md5Checksum,mimeType",
        data=data, method="PATCH",
        headers={"Authorization": api.__globals__["H"]["Authorization"],
                 "Content-Type": "text/markdown; charset=UTF-8"})
    with urllib.request.urlopen(req, timeout=180) as r:
        import json as _json
        return _json.loads(r.read().decode("utf-8"))


existing = [f for f in root_children() if "README" in f["name"].upper()]
if existing:
    f = existing[0]
    print(f"已存在同名文件，改为原地更新内容：{f['name']}  {f['id']}")
    res = upload_media(ROOT_ID, f["id"])
else:
    res = api("https://www.googleapis.com/drive/v3/files"
              "?fields=id,name,size,md5Checksum,mimeType",
              data=__import__("json").dumps({"name": NAME, "parents": [ROOT_ID]},
                                            ensure_ascii=False).encode(),
              method="POST", ctype="application/json; charset=UTF-8")
    print(f"已创建条目：{res['id']}")
    res = upload_binary(NAME, SRC, ROOT_ID)
    # upload_binary 只回 id/name，补一次元信息
    res = api(f"https://www.googleapis.com/drive/v3/files/{res['id']}"
              "?fields=id,name,size,md5Checksum,mimeType&supportsAllDrives=true")

print(f"云端：{res['name']}  {int(res.get('size', 0)):,} 字节  md5={res.get('md5Checksum')}"
      f"  mime={res.get('mimeType')}  id={res['id']}")
print(f"md5 一致？{'✔ 一致' if res.get('md5Checksum') == local_md5 else '✘ 不一致'}")

print("\n=== 根目录最终结构 ===")
for f in root_children():
    kind = "DIR " if f["mimeType"].endswith("folder") else "FILE"
    print(f"  [{kind}] {f['name']}   {int(f.get('size', 0))//1024}KB   {f['id']}")
