"""Tema Zamrud Akademik: krem + hijau tua, judul serif (pilihan T5)."""

GREEN, GREEN_DARK, GREEN_DEEP, INK, MUTED, LINE, PANEL, PAPER, CREAM = (
    "#059669", "#047857", "#065F46", "#1C2B23", "#6B7A6E", "#D9D2BE", "#F6F4EE",
    "#FFFDF8", "#FEFCE8",
)

CSS = f"""
<style>
.block-container {{ max-width: 1100px; padding-top: 1.2rem; }}
[data-testid="stAppViewContainer"] {{ background: {PANEL}; }}

/* ---------- HERO ---------- */
.hero {{
  background: linear-gradient(135deg, {GREEN_DARK} 0%, {GREEN} 55%, #10B981 100%);
  border-radius: 20px; padding: 1.8rem 2rem; color: #fff;
  box-shadow: 0 10px 26px rgba(6,95,70,.28); margin-bottom: 1.4rem;
  border: 1px solid rgba(255,255,255,.25);
  position: relative; overflow: hidden;
}}
.hero .watermark {{
  position: absolute; right: 26px; top: 2px; font-size: 5.5rem;
  opacity: .15; line-height: 1; pointer-events: none;
  font-family: Georgia, 'Times New Roman', serif;
}}
.hero .crest {{
  display: inline-block; font-size: .68rem; letter-spacing: .22em;
  background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.35);
  border-radius: 999px; padding: .15rem .9rem; margin-bottom: .6rem;
}}
.hero h1 {{ color: #fff !important; font-size: 1.8rem; margin: 0;
  font-family: Georgia, 'Times New Roman', serif; }}
.hero p {{ color: #D1FAE5 !important; margin: .4rem 0 0; font-style: italic; }}

/* ---------- NAVIGASI (radio ganti halaman -> pil seperti template) ---------- */
div[data-testid="stRadio"] div[role="radiogroup"] {{ gap: 10px; }}
div[data-testid="stRadio"] label {{
  background: #E7E2D3 !important; color: #4B5A50 !important;
  border-radius: 12px !important; padding: 9px 28px !important;
  font-weight: 700 !important; border: none !important; margin: 0 !important;
}}
div[data-testid="stRadio"] label > div:first-child {{ display: none; }}
div[data-testid="stRadio"] label:has(input:checked) {{
  background: {GREEN_DEEP} !important; color: #fff !important;
  box-shadow: 0 4px 12px rgba(6,95,70,.3);
}}

/* ---------- KARTU ---------- */
.card {{
  background: {PAPER}; border: 1px solid {LINE}; border-radius: 14px;
  padding: 1.2rem 1.3rem; box-shadow: 0 2px 8px rgba(60,50,20,.06);
  margin-bottom: 1.1rem;
}}
.card h3, .card h4 {{ color: {GREEN_DEEP} !important; margin-top: 0;
  font-family: Georgia, 'Times New Roman', serif; }}
.card h3 .ico {{ color: {GREEN} ; margin-right: .4rem; }}
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
  font-family: Georgia, 'Times New Roman', serif; color: {GREEN_DEEP} !important;
}}

/* ---------- TOMBOL ---------- */
.stButton > button {{
  background: {GREEN_DEEP}; color: #fff; border-radius: 10px;
  border: 1px solid {GREEN_DEEP}; font-weight: 700; padding: .45rem 1.8rem;
}}
.stButton > button:hover {{ background: {GREEN_DARK}; border-color: {GREEN_DARK}; color: #fff; }}
.stButton > button:disabled {{ background: #E5E7EB; border-color: #E5E7EB; color: #9CA3AF; }}
.stDownloadButton > button {{
  background: #fff; color: {GREEN_DEEP}; border-radius: 10px;
  border: 1.5px solid {GREEN_DEEP}; font-weight: 700;
}}
.stDownloadButton > button:hover {{ background: {GREEN_DEEP}; color: #fff; }}
div[data-testid="column"]:nth-of-type(1) .stDownloadButton > button {{
  background: {GREEN_DEEP}; color: #fff;
}}

/* ---------- TAB PREVIEW (.do / README) ---------- */
div[data-testid="stTabs"] button[data-baseweb="tab"] {{
  color: {INK} !important; font-weight: 600;
}}
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {{
  color: {GREEN_DEEP} !important; font-weight: 800 !important;
}}

/* ---------- METRIK (mimbar angka ala template) ---------- */
div[data-testid="stMetric"] {{
  background: #fff; border: 1px solid {LINE}; border-top: 3px solid {GREEN};
  border-radius: 10px; padding: .6rem .4rem;
}}
div[data-testid="stMetricValue"] {{ color: {GREEN_DEEP} !important; }}
div[data-testid="stMetricLabel"] {{ color: {MUTED} !important; }}

/* ---------- BLOK KODE SALIN (gelap seperti template) ---------- */
div[data-testid="stCodeBlock"] pre {{
  background: {INK} !important; border: 1px solid {GREEN_DEEP} !important;
  border-radius: 10px !important;
}}
div[data-testid="stCodeBlock"] code, div[data-testid="stCodeBlock"] code span {{
  color: #A7F3D0 !important;
}}
div[data-testid="stCodeBlock"] button {{
  color: #A7F3D0 !important;
}}

/* ---------- LAINNYA ---------- */
.badge {{
  display: inline-block; background: #D1FAE5; color: {GREEN_DEEP};
  border-radius: 999px; padding: .1rem .7rem; font-size: .8rem; font-weight: 700;
}}
.codebox {{
  border: 1px solid {GREEN_DEEP}; border-radius: 10px; background: {INK};
  padding: .8rem .95rem; margin-top: .5rem;
}}
.codebox .lbl {{ color: #A7F3D0; font-size: .78rem; margin-bottom: .3rem; }}
.codebox code {{
  font-family: ui-monospace, Consolas, monospace; font-size: .85rem;
  color: #A7F3D0 !important; background: transparent !important;
  padding: 0 !important; border: none !important;
  word-spacing: .15rem; line-height: 1.7;
  white-space: normal; word-break: break-word;
}}
html, body, [class*="st-"] {{ color: {INK}; }}
label, .stMarkdown p, .stCaption {{ color: {INK} !important; }}
thead th {{
  background: {GREEN_DEEP} !important; color: {CREAM} !important; font-weight: 700 !important;
}}
thead th:first-child {{
  border-radius: 8px 0 0 0 !important;
}}
thead th:last-child {{
  border-radius: 0 8px 0 0 !important;
}}
tbody tr:nth-child(even) td {{ background: #F9F7EF !important; }}
tbody td {{ color: {INK} !important; }}
.stAlert {{ border-radius: 12px; }}
input[type="text"], textarea {{
  background: #fff !important; border: 1px solid #C9C2A8 !important;
  border-radius: 10px !important; color: {INK} !important;
}}
input[type="text"]::placeholder, textarea::placeholder {{ color: #9CA3AF !important; }}
input[type="text"]:focus, textarea:focus {{
  outline: 2px solid {GREEN} !important; border-color: {GREEN} !important;
}}
div[data-baseweb="select"] > div {{
  background: #fff !important; border: 1px solid #C9C2A8 !important;
  border-radius: 10px !important; color: {INK} !important;
}}
div[data-testid="stTextInput"] label p, div[data-testid="stTextArea"] label p,
div[data-testid="stSelectbox"] label p {{
  color: {INK} !important; font-weight: 600 !important;
}}

/* ---------- TAMPILAN DEPLOYMENT: sembunyikan chrome Streamlit ---------- */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
div[data-testid="stToolbar"] {{visibility: hidden;}}
div[data-testid="stDecoration"] {{visibility: hidden;}}
div[data-testid="stStatusWidget"] {{visibility: hidden;}}
[data-testid="stHeaderActionElements"] {{display: none !important;}}
a.header-anchor {{display: none !important;}}
div[data-testid="stElementToolbar"] {{display: none !important;}}

/* ---------- OVERRIDE AKHIR: hero & pil nav harus menang atas aturan umum ---------- */
.hero h1 {{
  color: #fff !important; -webkit-text-fill-color: #fff !important;
  text-shadow: 0 1px 10px rgba(0,0,0,.30);
}}
.hero p {{
  color: #D1FAE5 !important; -webkit-text-fill-color: #D1FAE5 !important;
  font-size: 1.02rem; text-shadow: 0 1px 8px rgba(0,0,0,.25);
}}
.hero .crest {{ color: #fff !important; -webkit-text-fill-color: #fff !important; }}
div[data-testid="stRadio"] p {{ color: inherit !important; }}
div[data-testid="stRadio"] label:has(input:checked),
div[data-testid="stRadio"] label:has(input:checked) p {{
  color: #fff !important; -webkit-text-fill-color: #fff !important;
}}
</style>
"""

HERO_HTML = (
    "<div class='hero'><span class='watermark'>❧</span>"
    "<span class='crest'>LAB DIGITAL · FEB UNDIP</span>"
    "<h1>Website BPS Master</h1>"
    "<p>Alat Bantu Cari dan Kurasi Variabel BPS yang dilanggan FEB Undip.</p></div>"
)
