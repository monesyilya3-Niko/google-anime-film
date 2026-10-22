# -*- coding: utf-8 -*-
"""拉取《暮冬念春》工程总库云端最终结构（根目录递归），作为 README 底稿。"""
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

ROOT_ID = "1ya8IwwmFgLWCSE9i_sihtXyTmdW4R528"  # 全案工程总库根目录
OUT = Path(__file__).resolve().parent
MAX_DEPTH = 3

FOLDER_MIME = "application/vnd.google-apps.folder"


def children(folder):
    q = urllib.parse.quote(f"'{folder}' in parents and trashed=false")
    url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
           "&fields=files(id,name,mimeType,size,modifiedTime)&pageSize=300"
           "&orderBy=folder,name&supportsAllDrives=true&includeItemsFromAllDrives=true")
    return api(url).get("files", [])


def walk(folder, depth=0):
    items = []
    for f in children(folder):
        node = {
            "id": f["id"],
            "name": f["name"],
            "type": "folder" if f["mimeType"] == FOLDER_MIME else "file",
            "size": int(f.get("size", 0)),
            "modified": f.get("modifiedTime", ""),
        }
        if node["type"] == "folder" and depth < MAX_DEPTH:
            node["children"] = walk(f["id"], depth + 1)
        items.append(node)
    return items


def render(nodes, depth=0):
    lines = []
    for n in nodes:
        pad = "    " * depth
        if n["type"] == "folder":
            sub = n.get("children", [])
            lines.append(f"{pad}- **{n['name']}/**  `{n['id']}`  ({len(sub)} 项)")
            lines.extend(render(sub, depth + 1))
        else:
            kb = n["size"] / 1024
            lines.append(f"{pad}- {n['name']}  `{n['id']}`  {kb:,.0f} KB")
    return lines


tree = walk(ROOT_ID)
data = {"root_id": ROOT_ID, "pulled_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "tree": tree}
(OUT / "cloud_structure_final.json").write_text(
    json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
md = ["# 云端最终结构（拉取快照）", "",
      f"- 根目录 ID：`{ROOT_ID}`",
      f"- 拉取时间：{data['pulled_at']}", "",
      *render(tree)]
(OUT / "cloud_structure_final.md").write_text("\n".join(md), encoding="utf-8")
print("\n".join(render(tree)))
print(f"\n共 {sum(1 for _ in render(tree))} 行；已写入 cloud_structure_final.md / .json")
