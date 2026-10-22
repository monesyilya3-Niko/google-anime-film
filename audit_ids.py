# -*- coding: utf-8 -*-
"""体检 G：README §8 File ID 逐个解析 + 01/03/导演全案关键声明抽查。"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

IDS = [
    "1ya8IwwmFgLWCSE9i_sihtXyTmdW4R528",
    "1aRc6-MNuk7wsd1OFhjZPMQGXck-OIpxG",
    "103fzTVsi34QCz6hkpHTzR7RJNsTmZgN-",
    "1gOkAIAs2gY3uXK48R1VCwTiuagMpTOXG",
    "1rg9BXm_-0YpqrLlIMAH38hQbzBPc2XeE",
    "17klUmU7h2FIrsT4D0FBQrN2AojBfYHUb",
    "1_37tPXPYlTmguorlPZfMvVPCr8Og3Z_7q92mCva-g5Y",
    "1aUbH2mqNruj1qKoFUn-L7auKlR-H6e2mNRTCrN0mA5Y",
    "15fC3MHNYCklvPmdmZsLba6uiqVGYhOgA",
    "10Oq8OAWJpqRMc-ze2TGqRHJY_hDkoul1DHXUpPYtwoY",
    "1I8dAlyoGJUS4H3QUqd1Y0lJ9oVwFk9Ab",
    "1l81Tpwrc71RS4m1Wk7tQa84gA8LxrlLlFEEJsZLh-Uc",
]

print("=" * 84)
print("G1. README §8 File ID 解析")
print("=" * 84)
for i in IDS:
    try:
        f = api(f"https://www.googleapis.com/drive/v3/files/{i}?fields=id,name,mimeType,size&supportsAllDrives=true")
        print(f"  {i}  {f['mimeType']:<42} {int(f.get('size', 0)) // 1024:>5}KB  {f['name']}")
    except Exception as e:  # noqa: BLE001
        print(f"  {i}  ERROR {e}")

print("\n" + "=" * 84)
print("G2. 01 / 03 文档关键声明抽查")
print("=" * 84)
LOCAL = Path(__file__).resolve().parent / "source" / "audit"
t01 = next(LOCAL.glob("01_*.md")).read_text(encoding="utf-8")
for kw in ("9 曲", "致敬轨", "可商用", "111.9", "-4.5", "侧链", "基频"):
    hit = kw in t01
    print(f"  01 含「{kw}」：{'✔' if hit else '✘'}")
print(f"  01 曲目条目（### / | 曲）：{len(re.findall(r'^### ', t01, re.M))} 个三级标题")

t03 = next(LOCAL.glob("03_*.md")).read_text(encoding="utf-8")
for kw in ("勘误", "V19"):
    print(f"  03 含「{kw}」：{'✔' if kw in t03 else '✘'}")

print("\n" + "=" * 84)
print("G3. 导演全案导出件：章节数与镜头表")
print("=" * 84)
p = Path(__file__).resolve().parent / "source" / "audit" / "export_暮冬念春_导演全案与分镜制作手册_V19.md.md"
txt = p.read_text(encoding="utf-8")
heads = re.findall(r"^#+\s*(.+)$", txt, re.M)
print(f"  章节标题 {len(heads)} 条：")
for h in heads[:20]:
    print(f"     {h[:70]}")
print(f"  含 Shot\\_（转义）次数：{len(re.findall(r'Shot\\\\_', txt))}；含 Shot_ 次数：{len(re.findall(r'Shot_', txt))}")
