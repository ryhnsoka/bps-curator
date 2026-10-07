"""Kurasi request -> grouping per partisi -> do-file Stata (hanya keep)."""
from .normalize import normalize_code


def get_mandatory_list(master, profile=None):
    m = master.get("mandatory", [])
    if isinstance(m, dict):
        if profile and profile in m:
            return m[profile]
        union, seen = [], set()
        for vals in m.values():
            for v in vals:
                if normalize_code(v) not in seen:
                    seen.add(normalize_code(v))
                    union.append(v)
        return union
    return m


def curate(requested, master, add_mandatory=True, profile=None):
    """Matching dinormalisasi; output kode standar master."""
    idx = {normalize_code(v["code"]): v for v in master["variables"]}
    found, missing, seen = [], [], set()
    for r in requested:
        key = normalize_code(r)
        if key in idx and key not in seen:
            seen.add(key)
            found.append(idx[key])
        elif key not in idx:
            missing.append(r)
    mandatory_added = []
    if add_mandatory:
        have = {normalize_code(v["code"]) for v in found}
        for m in get_mandatory_list(master, profile):
            mu = normalize_code(m)
            if mu not in have and mu in idx:
                have.add(mu)
                found.append(idx[mu])
                mandatory_added.append(idx[mu]["code"])
    grouped = {}
    for v in found:
        for p in v["partitions"]:
            grouped.setdefault(p, []).append(v["code"])
    for p in grouped:
        grouped[p] = sorted(set(grouped[p]))
    return {"found": found, "missing": missing,
            "mandatory_added": mandatory_added, "grouped": grouped}


def generate_readme(curated, master):
    """README pemetaan: wajib vs request user, beserta label + partisi."""
    by_code = {v["code"]: v for v in curated["found"]}
    madd = set(curated["mandatory_added"])
    req_vars = [v for v in curated["found"] if v["code"] not in madd]
    w_vars = [by_code[c] for c in curated["mandatory_added"] if c in by_code]
    L = [f"# Kurasi {master.get('survey_id', '')} {master.get('period', '')}".rstrip(),
         f"- Found: {len(curated['found'])}, Missing: {len(curated['missing'])}",
         ""]
    L.append(f"## Variabel wajib ({len(w_vars)})")
    if w_vars:
        L += ["| Kode | Label | Partisi |", "|---|---|---|"]
        for v in sorted(w_vars, key=lambda x: x["code"]):
            L.append(f"| {v['code']} | {v['label']} | {', '.join(v['partitions'])} |")
    elif get_mandatory_list(master):
        L.append("Semua variabel wajib sudah termasuk dalam request (tidak ada tambahan).")
    else:
        L.append("Tidak ada (master tanpa variabel wajib).")
    L += ["", f"## Variabel request user ({len(req_vars)})"]
    if req_vars:
        L += ["| Kode | Label | Partisi |", "|---|---|---|"]
        for v in sorted(req_vars, key=lambda x: x["code"]):
            L.append(f"| {v['code']} | {v['label']} | {', '.join(v['partitions'])} |")
    else:
        L.append("Tidak ada.")
    L += ["", f"## Tidak ditemukan ({len(curated['missing'])})"]
    L += [f"- {m}" for m in curated["missing"]] or ["Tidak ada."]
    return "\n".join(L).rstrip() + "\n"


def generate_do(curated, master):
    lines = [f"* Auto-generated {master.get('survey_id', '')} {master.get('period', '')}".rstrip(),
             f"* Found: {len(curated['found'])}, Missing: {len(curated['missing'])}"]
    if curated["missing"]:
        lines.append(f"* WARNING missing: {', '.join(curated['missing'])}")
    lines.append("")
    mandatory_set = {normalize_code(m) for m in get_mandatory_list(master)}
    multi = len(curated["grouped"]) > 1
    parts = []
    for p, varlist in sorted(curated["grouped"].items()):
        if [v for v in varlist if normalize_code(v) not in mandatory_set] or not multi:
            parts.append(p)
        else:
            lines.append(f"* SKIP {p}: hanya berisi variabel wajib")
    for p in parts:
        lines += [f"* --- {p} ---", f"keep {' '.join(curated['grouped'][p])}", ""]
    if multi and not parts:
        p0 = sorted(curated["grouped"])[0]
        lines += [f"* NOTE semua request adalah variabel wajib -> pakai {p0}",
                  f"* --- {p0} ---", f"keep {' '.join(curated['grouped'][p0])}", ""]
    return "\n".join(lines).rstrip() + "\n"
