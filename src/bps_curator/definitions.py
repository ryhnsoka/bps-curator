"""Loader definisi variabel dari output/definitions/*.json.

Hasil: {(survey_id, period): {kode: {kind, ref, text, source}}}
kind: 'definisi' (dokumen konsep) | 'soal' (kuesioner) | 'konteks' (jangkar teks)
"""
import json
from pathlib import Path


def _norm_code(s):
    import re
    return re.sub(r"[^A-Z0-9]", "", str(s or "").strip().upper())


def _raw_code(s):
    return str(s or "").strip().upper()


def _put(bucket, code, entry):
    """Simpan di bawah kode apa adanya + alias tanpa tanda baca.

    Kode master IMK mengandung underscore (mis. B10_1001) sedangkan
    prakerja memakai kode polos (R51A), jadi keduanya harus bisa dicari.
    """
    raw = _raw_code(code)
    if not raw:
        return
    bucket.setdefault(raw, entry)
    norm = _norm_code(raw)
    if norm and norm != raw:
        bucket.setdefault(norm, entry)


def load_definitions(def_dir):
    def_dir = Path(def_dir)
    out = {}
    if not def_dir.is_dir():
        return out
    for fp in sorted(def_dir.glob("*.json")):
        if fp.name == "index.json":
            continue
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        key = (d.get("survey_id", ""), d.get("period", ""))
        bucket = out.setdefault(key, {})
        src = d.get("source", fp.name)
        q2c = d.get("map_question_to_codes", {}) or {}
        c2q = {}
        for q, codes in q2c.items():
            for c in codes or []:
                c2q[_norm_code(c)] = q
        for code, val in (d.get("definitions", {}) or {}).items():
            if isinstance(val, str):
                txt = val
            elif isinstance(val, dict):
                txt = val.get("teks") or val.get("text") or val.get("konteks") or ""
            else:
                continue
            if code in q2c:
                targets = q2c[code]
            elif code.upper().startswith("R"):
                targets = [code]
            else:
                targets = ["R" + code]
            for t in targets:
                _put(bucket, t, {"kind": "definisi", "ref": code,
                                 "text": txt, "source": src})
        for code, val in (d.get("mapped", {}) or {}).items():
            if not isinstance(val, dict):
                continue
            if "teks" in val:
                kind, ref = "soal", val.get("soal", "")
            else:
                kind, ref = "konteks", ""
            _put(bucket, code, {"kind": kind, "ref": ref,
                                "text": val.get("teks") or val.get("konteks", ""),
                                "source": src})
    return out


def definitions_for(definitions, survey_id, period):
    return definitions.get((survey_id or "", period or ""), {})


#: Cakupan minimum agar seksi definisi ditampilkan di UI. Di bawah ini
#: peta hasil eksplorasi yang belum tervalidasi, jadi lebih baik disembunyikan.
MIN_COVERAGE = 0.15


def master_definitions(definitions, master, min_coverage=MIN_COVERAGE):
    """Definisi untuk variabel master, atau {} bila cakupannya di bawah ambang.

    Mengembalikan (lookup, info) dengan lookup memakai kode master apa adanya.
    """
    bucket = definitions_for(definitions, master.get("survey_id", ""),
                             master.get("period", ""))
    codes = [v["code"] for v in master.get("variables", [])]
    lookup = {c: bucket[c] for c in codes if c in bucket}
    coverage = len(lookup) / len(codes) if codes else 0.0
    info = {"n_total": len(codes), "n_mapped": len(lookup), "coverage": coverage}
    if not codes or coverage < min_coverage:
        return {}, info
    return lookup, info
