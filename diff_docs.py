# -*- coding: utf-8 -*-
"""02/04 修改前后逐行 diff。"""
import difflib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
base = Path(__file__).resolve().parent / "source" / "audit"
fix = Path(__file__).resolve().parent / "docs_fix"

for name, fn in (("02", "02_4K母带画面修订清单_V19.md"), ("04", "04_未完成事项清单_V19.md")):
    a = (base / fn).read_text(encoding="utf-8").splitlines()
    b = (fix / (name + ".md")).read_text(encoding="utf-8").splitlines()
    print("=" * 90)
    print(name)
    print("=" * 90)
    d = list(difflib.unified_diff(a, b, fromfile="原", tofile="新", n=1, lineterm=""))
    if not d:
        print("  （无变化）")
    for ln in d:
        print(ln)
    print()
