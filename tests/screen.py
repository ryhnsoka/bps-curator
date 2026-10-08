"""Screening cepat 34 master JSON: partisi, wajib, duplikat fold."""
import json, glob
from pathlib import Path
from collections import Counter
import sys
sys.path.insert(0, "src")
from bps_curator.normalize import normalize_code

issues, total_vars = [], 0
files = sorted(glob.glob("output/master_*.json"))
print(f"file: {len(files)}")
for f in files:
    p = Path(f)
    if p.name == "master_inventory.json":
        continue
    m = json.loads(p.read_text(encoding="utf-8"))
    vars_ = m["variables"]
    total_vars += len(vars_)
    parts = set(m["partitions"])
    for v in vars_:
        if not v["partitions"]:
            issues.append(f"{p.name}: {v['code']} tanpa partisi")
        for pt in v["partitions"]:
            if pt not in parts:
                issues.append(f"{p.name}: {v['code']} partisi tak dikenal {pt}")
    counts = Counter(p for v in vars_ for p in v["partitions"])
    for pt in parts:
        if counts[pt] == 0:
            issues.append(f"{p.name}: partisi kosong {pt}")
    folds = Counter(normalize_code(v["code"]) for v in vars_)
    for k, n in folds.items():
        if n > 1:
            issues.append(f"{p.name}: fold ganda {k} x{n}")
    mand = m.get("mandatory", [])
    profs = mand.items() if isinstance(mand, dict) else [("", mand)]
    for prof, codes in profs:
        for c in codes:
            if normalize_code(c) not in folds:
                issues.append(f"{p.name}: wajib {c} (profil {prof}) tak ada di kamus")
print(f"total variabel: {total_vars}")
print(f"temuan: {len(issues)}")
for i in issues[:40]:
    print(" -", i)
