"""BPS Curator — Lab Digital FEB Undip. Tone emas-putih situs utama lab."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import json
import re
import sqlite3

import streamlit as st

from bps_curator.curator import curate, generate_do, generate_readme, get_mandatory_list
from bps_curator.normalize import normalize_code

OUT_DIR = ROOT / "output"
DB_PATH = ROOT / "bps.db"

GOLD, GOLD_DARK, INK, MUTED, LINE, PANEL = "#B8860B", "#8F6A08", "#111827", "#6B7280", "#E5E7EB", "#F4F5F7"

CSS = f"""
<style>
.block-container {{ max-width: 1100px; padding-top: 1.2rem; }}
[data-testid="stAppViewContainer"] {{ background: {PANEL}; }}
.hero {{
  background: linear-gradient(135deg, #C9970D 0%, #B8860B 60%, #9A7209 100%);
  border-radius: 22px; padding: 2rem 2rem; color: #fff;
  box-shadow: 0 10px 30px rgba(184,134,11,.30); margin-bottom: 1.4rem;
  border-top: 4px solid #E9C767;
}}
.hero h1 {{ color: #fff !important; font-size: 1.8rem; margin: 0; }}
.hero p {{ color: #FFF6DC !important; margin: .4rem 0 0; }}
.card {{
  background: #fff; border: 1px solid {LINE}; border-radius: 18px;
  padding: 1.2rem 1.3rem; box-shadow: 0 2px 10px rgba(17,24,39,.06);
  margin-bottom: 1.1rem;
}}
.card h3, .card h4 {{ color: {INK} !important; margin-top: 0; }}
.card h3 .ico {{ color: {GOLD_DARK}; margin-right: .4rem; }}
.stButton > button {{
  background: {GOLD}; color: #fff; border-radius: 999px;
  border: 1px solid {GOLD}; font-weight: 700; padding: .45rem 1.8rem;
}}
.stButton > button:hover {{ background: {GOLD_DARK}; border-color: {GOLD_DARK}; color: #fff; }}
.stButton > button:disabled {{ background: #E5E7EB; border-color: #E5E7EB; color: #9CA3AF; }}
.stDownloadButton > button {{
  background: #fff; color: {GOLD_DARK}; border-radius: 999px;
  border: 1.5px solid {GOLD}; font-weight: 700;
}}
.badge {{
  display: inline-block; background: #FBEFCB; color: {GOLD_DARK};
  border-radius: 999px; padding: .1rem .7rem; font-size: .8rem; font-weight: 700;
}}
.codebox {{
  border: 1px solid {LINE}; border-radius: 12px; background: #FAFAF9;
  padding: .8rem .95rem; margin-top: .5rem;
}}
.codebox .lbl {{ color: {MUTED}; font-size: .78rem; margin-bottom: .3rem; }}
.codebox code {{
  font-family: ui-monospace, Consolas, monospace; font-size: .85rem;
  color: {INK}; word-spacing: .15rem; line-height: 1.7;
}}
html, body, [class*="st-"] {{ color: {INK}; }}
label, .stMarkdown p, .stCaption {{ color: {INK} !important; }}
div[data-testid="stMetricValue"] {{ color: {INK} !important; }}
button[data-baseweb="tab"] {{ color: {INK} !important; font-weight: 600; }}
thead th {{
  background: #FBF3D9 !important; color: {GOLD_DARK} !important; font-weight: 700 !important;
}}
tbody td {{ color: {INK} !important; }}
.stAlert {{ border-radius: 12px; }}
input[type="text"], textarea {{
  background: #fff !important; border: 1px solid #D1D5DB !important;
  border-radius: 12px !important; color: {INK} !important;
}}
input[type="text"]::placeholder, textarea::placeholder {{ color: #9CA3AF !important; }}
div[data-baseweb="select"] > div {{
  background: #fff !important; border: 1px solid #D1D5DB !important;
  border-radius: 12px !important; color: {INK} !important;
}}
div[data-testid="stTextInput"] label p, div[data-testid="stTextArea"] label p,
div[data-testid="stSelectbox"] label p {{
  color: {INK} !important; font-weight: 600 !important;
}}
</style>
"""


@st.cache_resource
def init_db():
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "db"))
    if not DB_PATH.exists():
        import seed
        seed.seed(str(DB_PATH), str(OUT_DIR))
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
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


def log_request(con, master_id, profile, req, curated):
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


def kept_partitions(curated, master):
    """Partisi yang lolos aturan SKIP (isi wajib saja dibuang bila multi-partisi)."""
    mset = {normalize_code(x) for x in get_mandatory_list(master)}
    multi = len(curated["grouped"]) > 1
    return [p for p in sorted(curated["grouped"])
            if [v for v in curated["grouped"][p] if normalize_code(v) not in mset] or not multi]


def download_stem(master):
    """Nama file unduh standar, ex 'SUSENAS 2023 KP' (tanpa karakter ilegal)."""
    stem = f"{master.get('survey_id', 'kurasi')} {master.get('period', '')}".strip()
    return re.sub(r'[\\/:*?"<>|]+', "-", stem).strip() or "kurasi"


st.set_page_config(page_title="BPS Curator — Lab Digital FEB Undip", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(
    "<div class='hero'><h1>BPS Curator</h1>"
    "<p>Kurasi variabel master BPS menjadi do-file Stata — Lab Digital FEB Undip</p></div>",
    unsafe_allow_html=True)

con = init_db()
catalog = load_catalog()
menu = st.radio("Navigasi", ["Katalog", "Kurasi"], horizontal=True, label_visibility="collapsed")

# ---------------- KATALOG ----------------
if menu == "Katalog":
    st.markdown("<div class='card'><h3><span class='ico'>●</span> Katalog master</h3>", unsafe_allow_html=True)
    q = st.text_input("Cari survei / periode / variabel / label",
                      "", help="Label ikut dicari, bukan cuma kode variabel")
    rows = [{"Survei": c["survey"], "Periode": c["period"], "Jumlah Variabel": c["n_vars"],
             "Jumlah Partisi": c["n_partitions"], "Wajib": c["mandatory"]} for c in catalog]
    if q:
        qf, ql = normalize_code(q), q.lower()
        hit = set()
        var_hits = []
        if qf:
            for r in con.execute(
                    "SELECT m.survey_id, m.period, v.code, v.label FROM variables v "
                    "JOIN masters m ON m.drive_id = v.master_id "
                    "WHERE v.fold LIKE '%' || ? || '%' OR LOWER(v.label) LIKE '%' || ? || '%'"
                    " ORDER BY m.survey_id, m.period, v.code LIMIT 200",
                    (qf, ql)):
                hit.add((r["survey_id"], r["period"]))
                var_hits.append({"Variabel": r["code"], "Label": r["label"],
                                 "Survei": r["survey_id"], "Periode": r["period"]})
        rows = [r for r in rows
                if q.lower() in (r["Survei"] + " " + r["Periode"]).lower()
                or (r["Survei"], r["Periode"]) in hit]
        st.caption(f"<span class='badge'>{len(rows)} master, {len(var_hits)} variabel cocok untuk '{q}'</span>",
                   unsafe_allow_html=True)
        if var_hits:
            st.write("**Variabel cocok (nama + label):**")
            st.dataframe(var_hits, use_container_width=True, hide_index=True)
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- KURASI ----------------
else:
    labels = [f"{c['survey']} — {c['period']}" for c in catalog]
    pick = st.selectbox("Pilih Survei Master", labels)
    entry = catalog[labels.index(pick)]
    m = load_master_vars(entry["file"])
    avail_entry = load_availability().get((m.get("survey_id", ""), m.get("period", "")), {})
    avail_map = avail_entry.get("partitions") if avail_entry else None
    avail_badge = (f" <span class='badge'>Data tersedia: {len(avail_map)} dari "
                   f"{len(m['partitions'])} partisi</span>" if avail_map else "")
    st.markdown(f"<div class='card'><h4 style='margin-top:0;'>Informasi Dataset</h4>"
                f"<span class='badge'>Total Variabel: {m['n_variables']}</span> "
                f"<span class='badge'>Total Partisi: {len(m['partitions'])}</span>{avail_badge}</div>",
                unsafe_allow_html=True)

    req_text = st.text_area("Tempel Daftar Variabel (pisahkan dengan spasi, koma, atau baris baru)",
                            height=130,
                            help="Tak perlu centang — tempel daftar lalu tekan Proses")
    req = [t for t in re.split(r"[\s,;]+", req_text) if t]
    if req:
        st.caption(f"<span class='badge'>{len(req)} variabel ditempel</span>", unsafe_allow_html=True)
    if st.button("Proses Kurasi", disabled=not req):
        c = curate(req, m, availability=avail_map)
        do, txt = generate_do(c, m), generate_readme(c, m)
        mid = con.execute("SELECT drive_id FROM masters WHERE survey_id = ? AND period = ?",
                          (m["survey_id"], m["period"])).fetchone()
        log_request(con, mid["drive_id"] if mid else "", None, req, c)
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Ditemukan", len(c["found"]))
        s2.metric("Hilang", len(c["missing"]))
        s3.metric("Wajib ditambah", len(c["mandatory_added"]))
        s4.metric("Tak tersedia di data", len(c.get("unavailable", [])))
        if c["missing"]:
            st.warning(f"Tidak ditemukan: {', '.join(c['missing'])}")
        req_norm = {normalize_code(r) for r in req}
        unav_req = [u for u in c.get("unavailable", []) if normalize_code(u) in req_norm]
        if unav_req:
            st.warning(f"Tidak tersedia di file data: {', '.join(unav_req)}")
        if c.get("unavailable_partitions"):
            st.warning(f"Partisi tanpa file data: {', '.join(c['unavailable_partitions'])}")
        unav_set = set(c.get("unavailable", []))
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### Pemetaan Variabel Valid")
        st.dataframe([{"Kode": v["code"], "Label": v["label"]}
                      for v in sorted(c["found"], key=lambda x: x["code"])
                      if v["code"] not in unav_set],
                     use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("#### Detail Partisi")
        for p in kept_partitions(c, m):
            st.markdown(
                f"<div class='card'><div style='font-weight:700;margin-bottom:.3rem;'>Partisi: {p}</div>"
                f"<div class='codebox'><div class='lbl'>Kode Variabel:</div>"
                f"<code>{' '.join(c['grouped'][p])}</code></div></div>", unsafe_allow_html=True)
        st.markdown("#### Preview Output")
        t1, t2 = st.tabs(["Kode Stata (.do)", "README (.txt)"])
        with t1:
            st.code(do, language="stata")
        with t2:
            st.text(txt)
        st.markdown("#### Unduh Hasil")
        stem = download_stem(m)
        d1, d2 = st.columns(2)
        with d1:
            st.download_button("Unduh Kode Stata (.do)", do, file_name=f"{stem}.do")
        with d2:
            st.download_button("Unduh Metadata (README.txt)", txt, file_name=f"{stem} README.txt")
