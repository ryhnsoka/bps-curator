"""Loader definisi variabel dari output/definitions/*.json.

Hasil: {(survey_id, period): {kode: {kind, ref, text, source}}}
kind: 'definisi' (dokumen konsep) | 'soal' (kuesioner) | 'konteks' (jangkar teks)
"""
import json
from pathlib import Path


def _norm_code(s):
    import re
    return re.sub(r"[^A-Z0-9]", "", str(s or "").strip().upper())


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
                bucket.setdefault(_norm_code(t), {
                    "kind": "definisi", "ref": code, "text": txt, "source": src})
        for code, val in (d.get("mapped", {}) or {}).items():
            if not isinstance(val, dict):
                continue
            if "teks" in val:
                kind, ref = "soal", val.get("soal", "")
            else:
                kind, ref = "konteks", ""
            bucket.setdefault(_norm_code(code), {
                "kind": kind, "ref": ref, "text": val.get("teks") or val.get("konteks", ""),
                "source": src})
    return out


def definitions_for(definitions, survey_id, period):
    return definitions.get((survey_id or "", period or ""), {})
