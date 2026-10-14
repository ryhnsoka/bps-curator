"""Website BPS Master — Lab Digital FEB Undip. Entrypoint tipis: bootstrap + routing."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "web"))

import streamlit as st

from data import ensure_db, load_catalog
from katalog import render_katalog
from kurasi import render_kurasi
from theme import CSS, HERO_HTML

st.set_page_config(page_title="Website BPS Master — Lab Digital FEB Undip", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(HERO_HTML, unsafe_allow_html=True)

ensure_db()
catalog = load_catalog()
menu = st.radio("Navigasi", ["Katalog", "Kurasi"], horizontal=True, label_visibility="collapsed")

if menu == "Katalog":
    render_katalog(catalog)
else:
    render_kurasi(catalog)
