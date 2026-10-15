"""Lapisan data: path proyek, seed DB, loader JSON, query + audit log.

Catatan multi-user: setiap query tulis/baca berat membuka koneksi SQLite
sendiri (timeout 30 dtk, mode WAL) — tidak ada koneksi global yang dipakai
bersama antar-sesi/thread. session_state tetap terisolasi per pengunjung
oleh Streamlit.
"""
import importlib.util
import json
import sqlite3
from pathlib import Path

import streamlit as st

from bps_curator.normalize import normalize_code

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output"
DB_PATH = ROOT / "bps.db"
_TIMEOUT = 30


def _ensure_seeded():
    """Bangun bps.db via db/seed.py bila belum ada (tanpa hack sys.path global)."""
    spec = importlib.util.spec_from_file_location("bps_seed", ROOT / "db" / "seed.py")
    seed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed)
    seed.seed(str(DB_PATH), str(OUT_DIR))


@st.cache_resource
def ensure_db():
    """Pastikan DB ada + WAL aktif. Kembalikan path DB (bukan koneksi bersama)."""
    if not DB_PATH.exists():
        _ensure_seeded()
    con = sqlite3.connect(DB_PATH, timeout=_TIMEOUT)
    try:
        con.execute("PRAGMA journal_mode=WAL;")
    finally:
        con.close()
    return str(DB_PATH)


def get_conn():
    """Koneksi pendek per panggilan — aman dipakai lintas thread/sesi."""
    con = sqlite3.connect(DB_PATH, timeout=_TIMEOUT)
    con.row_factory = sqlite3.Row
    return con


@st.cache_data
def load_catalog():
    return json.loads((OUT_DIR / "catalog.json").read_text(encoding="utf-8"))


@st.cache_data
def load_master_vars(json_file):
    return json.loads((OUT_DIR / json_file).read_text(encoding="utf-8"))


@st.cache_data
def load_availability():
    p = OUT_DIR / "availability.json"
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    return {(e.get("survey_id", ""), e.get("period", "")): e
            for e in data.get("masters", [])}


@st.cache_data
def load_documents():
    """Pemetaan (survei, periode) -> kuesioner/layout di Drive (hyperlink)."""
    import csv
    rows = {}
    with (ROOT / "data" / "dokumen.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[(r["survey"], r["period"])] = r
    return rows


def search_variables(qf, ql, limit=200):
    """Cari variabel per kode-fold/label (koneksi pendek, aman konkuren)."""
    con = get_conn()
    try:
        return list(con.execute(
            "SELECT m.survey_id, m.period, v.code, v.label FROM variables v "
            "JOIN masters m ON m.drive_id = v.master_id "
            "WHERE v.fold LIKE '%' || ? || '%' OR LOWER(v.label) LIKE '%' || ? || '%'"
            " ORDER BY m.survey_id, m.period, v.code LIMIT ?",
            (qf, ql, limit)))
    finally:
        con.close()


def get_master_drive_id(survey_id, period):
    con = get_conn()
    try:
        row = con.execute("SELECT drive_id FROM masters WHERE survey_id = ? AND period = ?",
                          (survey_id, period)).fetchone()
        return row["drive_id"] if row else ""
    finally:
        con.close()


def log_request(master_id, profile, req, curated):
    con = get_conn()
    try:
        cur = con.execute("INSERT INTO requests(master_id, profile, note) VALUES (?, ?, '')",
                          (master_id, profile or ""))
        rid = cur.lastrowid
        for r in req:
            con.execute("INSERT OR IGNORE INTO request_items(request_id, code_raw, code_norm, status)"
                        " VALUES (?, ?, ?, ?)",
                        (rid, r, normalize_code(r),
                         "missing" if r in curated["missing"] else "found"))
        con.commit()
        return rid
    finally:
        con.close()
