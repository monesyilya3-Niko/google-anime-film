# -*- coding: utf-8 -*-
"""全量一致性审计：每条镜的 名称↔ID、upload_instruction 挂载 ID、首/尾帧名称↔ID。"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import list_in, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

CACHE = Path(__file__).resolve().parent / "source" / "audit"
ASSETS = "1aRc6-MNuk7wsd1OFhjZPMQGXck-OIpxG"
assets = {f["id"]: n for n, f in list_in(ASSETS).items()}
name2id = {n: i for i, n in assets.items()}

FILES = {
    "180": "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json",
    "120": "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json",
}

ID_RE = re.compile(r"\b1[A-Za-z0-9_-]{32}\b")


def basename(p):
    return str(p).replace("\\", "/").split("/")[-1].strip()


def first_id(text):
    m = ID_RE.search(str(text))
    return m.group(0) if m else None


for tag, fname in FILES.items():
    shots = json.loads((CACHE / fname).read_text(encoding="utf-8"))
    print("=" * 86)
    print(f"{tag} 轨：{len(shots)} 条")
    print("=" * 86)
    issues = []
    for s in shots:
        sid = s.get("shot_id") or s.get("manus_15s_id") or str(s.get("shot_number"))
        pid = s.get("primary_drive_file_id", "")
        pc = s.get("primary_cloud_filename", "")
        pp = basename(s.get("primary_image_path", ""))
        pk = s.get("primary_image_key", "")
        if pc and pp and pp != pc:
            issues.append((sid, "primary_image_path ≠ primary_cloud_filename", pp, pc))
        if pc and name2id.get(pc) and pid and name2id[pc] != pid:
            issues.append((sid, "primary_cloud_filename ↔ ID 不符", pc, pid))
        if pid and pid not in assets:
            issues.append((sid, "primary_drive_file_id 不在母带库", pid, ""))
        u = first_id(s.get("upload_instruction", ""))
        d = first_id(s.get("cloud_dispatch_command_zh", ""))
        if pid and u and u != pid:
            issues.append((sid, "upload_instruction 首个 ID ≠ primary ID", u, assets.get(u, "?")))
        if pid and d and d != pid:
            issues.append((sid, "cloud_dispatch 首个 ID ≠ primary ID", d, assets.get(d, "?")))
        ffn = s.get("first_frame_cloud_filename", "")
        ffi = s.get("first_frame_drive_file_id", "")
        if ffn and name2id.get(ffn) and ffi and name2id[ffn] != ffi:
            issues.append((sid, "first_frame 名称↔ID 不符", ffn, ffi))
        efn = s.get("end_frame_cloud_filename", "")
        efi = s.get("end_frame_drive_file_id", "")
        if efn and name2id.get(efn) and efi and name2id[efn] != efi:
            issues.append((sid, "end_frame 名称↔ID 不符", efn, efi))
    if not issues:
        print("  ✔ 无错配")
    for it in issues:
        print(f"  ✘ {it[0]:>8}  {it[1]}")
        print(f"        A = {it[2]}")
        print(f"        B = {it[3]}")
    print(f"  小计 {len(issues)} 条\n")
