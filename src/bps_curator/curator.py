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


def curate(requested, master, add_mandatory=True, profile=None, availability=None):
    """Matching dinormalisasi; output kode standar master.

    availability: {partisi: [kode]} variabel yang benar-benar ada di file
    data (None = anggap semua kamus tersedia, perilaku lama). Variabel
    kamus yang tak ada di data mana pun -> result["unavailable"]; partisi
    kamus tanpa data -> result["unavailable_partitions"].
    """
    idx = {normalize_code(v["code"]): v for v in master["variables"]}
    avail = None
    if availability is not None:
        avail = {p: {normalize_code(c) for c in codes} for p, codes in availability.items()}

    def is_available(code_norm, partition):
        return avail is None or (partition in avail and code_norm in avail[partition])

    def available_anywhere(code_norm, partitions):
        return avail is None or any(is_available(code_norm, p) for p in partitions)

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
            if mu not in have and mu in idx and available_anywhere(mu, idx[mu]["partitions"]):
                have.add(mu)
                found.append(idx[mu])
                mandatory_added.append(idx[mu]["code"])
    grouped = {}
    for v in found:
        for p in v["partitions"]:
            if is_available(normalize_code(v["code"]), p):
                grouped.setdefault(p, []).append(v["code"])
    for p in grouped:
        grouped[p] = sorted(set(grouped[p]))
    unavailable, unavailable_partitions = [], []
    if avail is not None:
        have_codes = {normalize_code(v["code"]) for v in found}
        for v in found:
            vn = normalize_code(v["code"])
            if not available_anywhere(vn, v["partitions"]) and v["code"] not in unavailable:
                unavailable.append(v["code"])
        for v in master["variables"]:
            for p in v["partitions"]:
                if p not in avail and p not in unavailable_partitions:
                    unavailable_partitions.append(p)
        unavailable_partitions.sort()
    return {"found": found, "missing": missing,
            "mandatory_added": mandatory_added, "grouped": grouped,
            "unavailable": unavailable,
            "unavailable_partitions": unavailable_partitions,
            "availability": ({p: sorted(avail[p]) for p in avail}
                             if avail is not None else None)}


def _readme_table(vars_sorted, available=None):
    """Tabel teks: nomor + kode + label + partisi, semua kolom rata.

    available: {partisi: [kode]} overlay data; bila ada, kolom Partisi
    hanya tampilkan partisi yang benar-benar ada datanya.
    """
    items = sorted(vars_sorted, key=lambda x: x["code"])

    def show_parts(v):
        parts = v["partitions"]
        if available is not None:
            parts = [p for p in parts if p in available]
        return ", ".join(parts)

    w_no = len(str(len(items)))
    w_code = max([len("Kode")] + [len(v["code"]) for v in items])
    w_label = max([len("Label")] + [len(v["label"]) for v in items])
    head = (f"{'No.':<{w_no + 2}}  {'Kode':<{w_code}}  "
            f"{'Label':<{w_label}}  Partisi")
    lines = [head, "-" * len(head)]
    for i, v in enumerate(items, 1):
        lines.append(f"[{i:0{w_no}d}]  {v['code']:<{w_code}}  "
                     f"{v['label']:<{w_label}}  {show_parts(v)}")
    return lines


def generate_readme(curated, master):
    """README pemetaan: wajib vs request user, beserta label + partisi. Format TXT."""
    unavailable = set(curated.get("unavailable", []))
    available = curated.get("availability")
    mset = {normalize_code(x) for x in get_mandatory_list(master)}
    w_vars = [v for v in curated["found"]
              if normalize_code(v["code"]) in mset and v["code"] not in unavailable]
    req_vars = [v for v in curated["found"]
                if normalize_code(v["code"]) not in mset and v["code"] not in unavailable]
    bar = "-" * 70
    L = ["=" * 70,
         f"Kurasi {master.get('survey_id', '')} {master.get('period', '')}".rstrip(),
         "=" * 70,
         f"Ditemukan: {len(curated['found'])} | Hilang: {len(curated['missing'])} "
         f"| Wajib ditambah: {len(curated['mandatory_added'])}",
         "",
         bar,
         f"Variabel wajib ({len(w_vars)})",
         bar]
    if w_vars:
        L += _readme_table(w_vars, available)
        if curated["mandatory_added"]:
            L.append(f"  (ditambahkan otomatis: {', '.join(sorted(curated['mandatory_added']))})")
    elif get_mandatory_list(master):
        L.append("  Tidak ada variabel wajib dalam hasil.")
    else:
        L.append("  Tidak ada (master tanpa variabel wajib).")
    L += ["",
          bar,
          f"Variabel request user ({len(req_vars)})",
          bar]
    if req_vars:
        L += _readme_table(req_vars, available)
    else:
        L.append("  Tidak ada.")
    L += ["",
          bar,
          f"Tidak ditemukan ({len(curated['missing'])})",
          bar]
    for m in curated["missing"]:
        L.append(f"  - {m}")
    if not curated["missing"]:
        L.append("  Tidak ada.")
    L += ["",
          bar,
          f"Tidak tersedia di data ({len(curated.get('unavailable', []))})",
          bar]
    if curated.get("unavailable"):
        by_code = {v["code"]: v for v in curated["found"]}
        for c in curated["unavailable"]:
            lbl = by_code[c]["label"] if c in by_code else ""
            L.append(f"  - {c}" + (f" | {lbl}" if lbl else ""))
        if curated.get("unavailable_partitions"):
            L.append(f"  (partisi tanpa data: {', '.join(curated['unavailable_partitions'])})")
    else:
        L.append("  Tidak ada.")
    return "\n".join(L).rstrip() + "\n"


def generate_do(curated, master):
    lines = [f"* Auto-generated {master.get('survey_id', '')} {master.get('period', '')}".rstrip(),
             f"* Found: {len(curated['found'])}, Missing: {len(curated['missing'])}"]
    if curated["missing"]:
        lines.append(f"* WARNING missing: {', '.join(curated['missing'])}")
    if curated.get("unavailable"):
        lines.append(f"* WARNING tidak tersedia di data: {', '.join(curated['unavailable'])}")
    if curated.get("unavailable_partitions"):
        for p in curated["unavailable_partitions"]:
            lines.append(f"* NOTE {p}: tidak tersedia di data")
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
