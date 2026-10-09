"""BPS Curator — Lab Digital FEB Undip. Tone emas-putih situs utama lab."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import html
import json
import re
import sqlite3

import streamlit as st

from bps_curator.curator import curate, generate_do, generate_readme, get_mandatory_list, generate_basket_txt
from bps_curator.normalize import normalize_code
from bps_curator.surveys import survey_name, period_name
from bps_curator.definitions import (load_definitions, definitions_for,
                                     has_definition)

OUT_DIR = ROOT / "output"
DB_PATH = ROOT / "bps.db"
MAX_DEF_BOXES = 50

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
.defbox {{
  border: 1px solid #E8D9A8; border-left: 5px solid {GOLD};
  border-radius: 12px; background: #FEFDF8;
  padding: .8rem 1rem; margin-top: .6rem;
}}
.defbox .defhdr {{ font-weight: 700; color: {INK}; font-size: .95rem; }}
.defbox .defhdr .code {{
  font-family: ui-monospace, Consolas, monospace; color: {GOLD_DARK};
}}
.defbox .defsrc {{ color: {MUTED}; font-size: .78rem; margin: .25rem 0 .5rem; }}
.defbox .deftext {{
  color: {INK}; font-size: .85rem; line-height: 1.7;
  white-space: pre-wrap;
  border-top: 1px dashed {LINE}; padding-top: .5rem;
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
    rows_all = [{"Survei": survey_name(c["survey"]), "Periode": period_name(c["period"]), "Jumlah Variabel": c["n_vars"],
                 "Jumlah Partisi": c["n_partitions"], "Wajib": c["mandatory"]} for c in catalog]
    rows = rows_all
    if q:
        qf, ql = normalize_code(q), q.lower()
        hit = set()
        var_hits, var_keys = [], []
        if qf:
            for r in con.execute(
                    "SELECT m.survey_id, m.period, v.code, v.label FROM variables v "
                    "JOIN masters m ON m.drive_id = v.master_id "
                    "WHERE v.fold LIKE '%' || ? || '%' OR LOWER(v.label) LIKE '%' || ? || '%'"
                    " ORDER BY m.survey_id, m.period, v.code LIMIT 200",
                    (qf, ql)):
                hit.add((survey_name(r["survey_id"]), period_name(r["period"])))
                var_hits.append({"Variabel": r["code"], "Label": r["label"],
                                 "Survei": survey_name(r["survey_id"]), "Periode": period_name(r["period"])})
                var_keys.append((r["survey_id"], r["period"], r["code"]))
        rows = [r for r, c in zip(rows_all, catalog)
                if ql in f"{r['Survei']} {r['Periode']} {c['survey']} {c['period']}".lower()
                or (r["Survei"], r["Periode"]) in hit]
        for c in catalog:
            if ql in f"{survey_name(c['survey'])} {period_name(c['period'])} {c['survey']} {c['period']}".lower():
                seen = {(v["Variabel"], v["Survei"], v["Periode"]) for v in var_hits}
                m_all = load_master_vars(c["file"])
                for v in m_all["variables"]:
                    key = (v["code"], survey_name(c["survey"]), period_name(c["period"]))
                    if key not in seen and len(var_hits) < 500:
                        seen.add(key)
                        var_hits.append({"Variabel": v["code"], "Label": v["label"],
                                         "Survei": key[1], "Periode": key[2]})
                        var_keys.append((c["survey"], c["period"], v["code"]))
        st.caption(f"<span class='badge'>{len(rows)} master, {len(var_hits)} variabel cocok untuk '{q}'</span>",
                   unsafe_allow_html=True)
        if var_hits:
            defs_all = load_definitions(OUT_DIR / "definitions")
            st.write("**Variabel cocok (nama + label) — pilih lalu unduh:**")
            st.caption("Klik kotak di ujung kiri baris untuk memilih "
                       "(klik isi sel hanya menyorot teks untuk disalin). "
                       "Atau pilih lewat daftar — hasilnya sama.")
            st.dataframe(var_hits, use_container_width=True, hide_index=True,
                         column_config={"Label": st.column_config.TextColumn(width="large")},
                         selection_mode="multi-row", on_select="rerun", key="varhits")
            _vs = st.session_state.get("varhits")
            _sel = getattr(_vs, "selection", None) if _vs is not None else None
            _rows = getattr(_sel, "rows", []) if _sel is not None else []
            row_idx = {i for i in (_rows or []) if 0 <= i < len(var_hits)}
            _opts, _seen, _opt_idx = [], set(), {}
            for i, v in enumerate(var_hits):
                o = f"{v['Variabel']} — {v['Label']} | {v['Survei']} {v['Periode']}"
                if o in _seen:
                    o = f"{o} #{v['Variabel']}"
                _seen.add(o)
                _opts.append(o)
                _opt_idx[o] = i
            picked = st.multiselect("Atau pilih lewat daftar (bisa ketik kode/label)",
                                    _opts, key="varpick")
            pick_idx = {_opt_idx[o] for o in picked if o in _opt_idx}
            tapped = [var_hits[i] for i in sorted(row_idx | pick_idx)]
            if tapped:
                st.caption(f"<span class='badge'>{len(tapped)} variabel dipilih</span>",
                           unsafe_allow_html=True)
                txt = generate_basket_txt(
                    [{"code": v["Variabel"], "survey": v["Survei"], "period": v["Periode"]}
                     for v in tapped])
                st.download_button("Unduh TXT", txt, file_name="pilihan.txt")
            marked = [i for i, k in enumerate(var_keys)
                      if has_definition(defs_all, k[0], k[1], k[2])]
            if marked:
                shown = marked[:MAX_DEF_BOXES]
                st.markdown("#### Definisi variabel yang cocok")
                st.caption(f"Menampilkan {len(shown)} definisi "
                           f"(dari {len(var_hits)} variabel cocok).")
                for i in shown:
                    v = var_hits[i]
                    dd = definitions_for(defs_all, *var_keys[i][:2]).get(var_keys[i][2], {})
                    st.markdown(
                        f"<div class='defbox'><div class='defhdr'>"
                        f"<span class='code'>{html.escape(v['Variabel'])}</span> — "
                        f"{html.escape(v['Label'])}</div>"
                        f"<div class='defsrc'>Sumber: {html.escape(dd.get('source', ''))} "
                        f"· {html.escape(v['Survei'])} {html.escape(v['Periode'])}</div>"
                        f"<div class='deftext'>{html.escape(dd.get('text', ''))}</div></div>",
                        unsafe_allow_html=True)
                if len(marked) > MAX_DEF_BOXES:
                    st.caption(f"{len(marked) - MAX_DEF_BOXES} definisi lain tidak "
                               f"ditampilkan — persempit pencarian.")
    st.dataframe(rows, hide_index=True,
                 column_config={"Survei": st.column_config.TextColumn(width="large"),
                                "Periode": st.column_config.TextColumn(width="large"),
                                "Jumlah Variabel": st.column_config.NumberColumn(width="small"),
                                "Jumlah Partisi": st.column_config.NumberColumn(width="small"),
                                "Wajib": st.column_config.NumberColumn(width="small")})
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- KURASI ----------------
else:
    labels = [f"{survey_name(c['survey'])} — {period_name(c['period'])}" for c in catalog]
    # Streamlit membuang state widget yang tidak dirender di run tersebut. Simpan
    # mirror-nya di *_saved supaya pindah tab ke Katalog tidak mengosongkan
    # pilihan master maupun daftar variabel.
    if "pick_input" not in st.session_state:
        st.session_state["pick_input"] = st.session_state.get("pick_saved", labels[0])
    pick = st.selectbox("Pilih Survei Master", labels, key="pick_input")
    st.session_state["pick_saved"] = pick
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

    # req_text disimpan di session_state supaya pindah tab tidak mengosongkan
    # kotak tempel (kalau kosong, hasil kurasi ikut hilang karena signature beda).
    if "req_input" not in st.session_state:
        st.session_state["req_input"] = st.session_state.get("req_saved", "")
    st.text_area("Tempel Daftar Variabel (pisahkan dengan spasi, koma, atau baris baru)",
                 height=130, key="req_input",
                 help="Tak perlu centang — tempel daftar lalu tekan Proses")
    req_text = st.session_state["req_input"]
    st.session_state["req_saved"] = req_text
    req = [t for t in re.split(r"[\s,;]+", req_text) if t]
    if req:
        st.caption(f"<span class='badge'>{len(req)} variabel ditempel</span>", unsafe_allow_html=True)
    if st.button("Proses Kurasi", disabled=not req):
        c = curate(req, m, availability=avail_map)
        do, txt = generate_do(c, m), generate_readme(c, m)
        mid = con.execute("SELECT drive_id FROM masters WHERE survey_id = ? AND period = ?",
                          (m["survey_id"], m["period"])).fetchone()
        log_request(con, mid["drive_id"] if mid else "", None, req, c)
        st.session_state.hasil = {"sig": (entry["file"], req_text),
                                  "req": list(req), "c": c, "do": do, "txt": txt}
    h = st.session_state.get("hasil")
    # Streamlit menghapus state widget yang tak dirender di run itu, jadi pindah
    # tab ke Katalog mengosongkan req_input. Hasil disimpan terpisah supaya tetap
    # tampil begitu user kembali ke tab Kurasi.
    if h:
        c, do, txt, req = h["c"], h["do"], h["txt"], h["req"]
        if h.get("sig", (None, None))[1] != req_text:
            st.caption("Hasil di bawah dari permintaan sebelumnya — tekan "
                       "Proses Kurasi untuk memperbarui.")
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
        unav_set = set(c.get("unavailable", []))
        found_rows = [{"Kode": v["code"], "Label": v["label"]}
                      for v in sorted(c["found"], key=lambda x: x["code"])
                      if v["code"] not in unav_set]
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### Pemetaan Variabel Valid")
        st.dataframe(found_rows, use_container_width=True, hide_index=True)
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
