"""Parser universal master BPS.

Sumber wajib berlapis: sheet '.' -> fallback sel kuning (FFFFFF00 dkk) -> kosong.
Sheet kamus terdeteksi otomatis dari header berisi 'Variabel' + 'Partisi'.
"""
import json
import re
from pathlib import Path

import openpyxl

from .normalize import normalize_code

YELLOW_FILLS = {"FFFFFF00", "FFFFFF99", "FFFFFFCC", "FFFFEB9C", "FFFFF2CC"}


def find_kamus_sheet(wb):
    """Return (sheet_name, header_row_idx, col_map). Kolom ganda -> kemunculan pertama."""
    for sn in wb.sheetnames:
        ws = wb[sn]
        rows = list(ws.iter_rows(min_row=1, max_row=8, values_only=True))
        for ri, r in enumerate(rows):
            vals = [str(c).strip() if c is not None else "" for c in r]
            low = [v.lower() for v in vals]
            if "variabel" in low and any("partisi" in v for v in low):
                # blok kamus = kolom 'Variabel' yang punya 'Partisi' di kanannya;
                # Label/Tipe/Partisi = kemunculan pertama di kanan blok itu
                # (kamus bisa di kiri ex Jabo, atau kanan ex SAK)
                var_idx = [i for i, v in enumerate(low) if v == "variabel"]
                iv = next((i for i in var_idx if any("partisi" in v for v in low[i:])), var_idx[0])

                def right(names):
                    for i in range(iv + 1, len(low)):
                        if low[i] in names:
                            return i
                    return None

                return sn, ri, {
                    "variabel": iv,
                    "label": right(["label"]),
                    "tipe": right(["tipe data", "tipe", "type"]),
                    "partisi": next((i for i in range(iv + 1, len(low)) if "partisi" in low[i]), None),
                }
    raise ValueError(f"Kamus (Variabel+Partisi) tidak ditemukan: {wb.sheetnames}")


def parse_dot_sheet(wb, kamus_codes=None):
    """Return [] | list | {profil: list}. Token disaring ke kode kamus."""
    if "." not in wb.sheetnames:
        return []
    ws = wb["."]
    rows = list(ws.iter_rows(values_only=True))
    cleaned = [[str(c).strip() for c in r if c not in (None, "")] for r in rows]
    cleaned = [r for r in cleaned if r]
    if not cleaned:
        return []
    kmap = {}
    if kamus_codes:
        for c in kamus_codes:
            kmap.setdefault(normalize_code(c), c)

    def keep(tokens):
        if not kmap:
            return tokens
        out, seen = [], set()
        for t in tokens:
            k = normalize_code(t)
            if k in kmap and k not in seen:
                seen.add(k)
                out.append(kmap[k])
        return out

    if len(cleaned) == 1 and len(cleaned[0]) == 1:
        return keep(cleaned[0][0].split())
    if all(len(r) == 2 and len(r[0].split()) == 1 and len(r[1].split()) == 1 for r in cleaned):
        return keep([r[0] for r in cleaned])
    if all(len(r) == 1 and len(r[0].split()) == 1 for r in cleaned):
        return keep([r[0] for r in cleaned])
    profiles, single = {}, []
    for r in cleaned:
        if len(r) == 2 and len(r[0].split()) == 1 and len(r[1].split()) > 1:
            profiles[r[0]] = keep(r[1].split())
        elif len(r) == 1 and len(r[0].split()) > 1:
            single.extend(r[0].split())
        else:
            toks = []
            for cell in r:
                toks.extend(cell.split())
            single.extend(toks)
    if profiles:
        return {k: v for k, v in profiles.items() if v}
    return keep(single)


def scan_yellow_mandatory(xlsx_path, kamus_codes, kamus_sheet=None):
    """Pindai sel kuning hanya di sheet kamus (max 3000x40)."""
    wb = openpyxl.load_workbook(xlsx_path, read_only=False, data_only=True)
    umap = {}
    for c in kamus_codes:
        umap.setdefault(normalize_code(c), c)
    found, seen = [], set()
    sheets = [kamus_sheet] if kamus_sheet in wb.sheetnames else [s for s in wb.sheetnames if s != "."]
    for sn in sheets:
        ws = wb[sn]
        max_r = min(ws.max_row or 0, 3000)
        max_c = min(ws.max_column or 0, 40)
        for row in ws.iter_rows(min_row=1, max_row=max_r, max_col=max_c):
            for cell in row:
                f = cell.fill
                if not f or f.patternType in (None, "none"):
                    continue
                if str(getattr(f.start_color, "rgb", "") or "").upper() not in YELLOW_FILLS:
                    continue
                val = str(cell.value or "").strip()
                if not val or " " in val:
                    continue
                key = normalize_code(val)
                if key in umap and key not in seen:
                    seen.add(key)
                    found.append(umap[key])
    wb.close()
    return found


def parse_master(xlsx_path, survey_id="", period=""):
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    sn, hri, cmap = find_kamus_sheet(wb)
    rows = list(wb[sn].iter_rows(values_only=True))
    vi, li, ti, pi = cmap["variabel"], cmap["label"], cmap["tipe"], cmap["partisi"]
    variables = []
    for r in rows[hri + 1:]:
        def g(i):
            return r[i] if i is not None and i < len(r) else None

        code = g(vi)
        if not code or not str(code).strip():
            continue
        code = str(code).strip()
        if code.lower() in ("variabel", "no"):
            continue
        part_raw = str(g(pi) or "").strip()
        try:
            partitions = json.loads(part_raw.replace("'", '"'))
            if isinstance(partitions, str):
                partitions = [partitions]
        except Exception:
            partitions = [p for p in re.findall(r"[\w]+", part_raw) if p.lower() != "no"]
        variables.append({
            "code": code,
            "label": str(g(li) or "").strip(),
            "type": str(g(ti) or "").strip().lower(),
            "partitions": partitions,
        })
    mandatory = parse_dot_sheet(wb, [v["code"] for v in variables])
    wb.close()
    if not mandatory:
        try:
            yellow = scan_yellow_mandatory(xlsx_path, [v["code"] for v in variables], kamus_sheet=sn)
        except Exception:
            yellow = []
        if yellow:
            mandatory = yellow
    return {
        "survey_id": survey_id,
        "period": period,
        "source_file": Path(xlsx_path).name,
        "kamus_sheet": sn,
        "n_variables": len(variables),
        "partitions": sorted({p for v in variables for p in v["partitions"]}),
        "mandatory": mandatory,
        "variables": variables,
    }
