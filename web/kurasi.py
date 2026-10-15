"""Halaman Kurasi: tempel daftar variabel -> metrik, partisi, preview, unduh."""
import re

import streamlit as st

from bps_curator.curator import curate, generate_do, generate_readme
from bps_curator.normalize import normalize_code
from bps_curator.surveys import survey_name, period_name
from data import get_master_drive_id, load_availability, load_documents, load_master_vars, log_request
from helpers import download_stem, kept_partitions


def render_kurasi(catalog):
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
    doc = (load_documents() or {}).get((m.get("survey_id", ""), m.get("period", "")), {})
    doc_badge = (f" <a class='doclink' href='{doc['kuesioner_url']}' target='_blank'>Kuesioner</a>"
                 if doc.get("kuesioner_url") else "")
    st.markdown(f"<div class='card'><h4 style='margin-top:0;'>Informasi Dataset</h4>"
                f"<span class='badge'>Total Variabel: {m['n_variables']}</span> "
                f"<span class='badge'>Total Partisi: {len(m['partitions'])}</span>{avail_badge}{doc_badge}</div>",
                unsafe_allow_html=True)

    # req_text disimpan di session_state supaya pindah tab tidak mengosongkan
    # kotak tempel (kalau kosong, hasil kurasi ikut hilang karena signature beda).
    if "req_input" not in st.session_state:
        st.session_state["req_input"] = st.session_state.get("req_saved", "")
    st.text_area("Tempel Daftar Variabel (pisahkan dengan spasi, koma, atau baris baru)",
                 height=130, key="req_input")
    st.caption("Tak perlu centang — tempel daftar lalu tekan Proses.")
    req_text = st.session_state["req_input"]
    st.session_state["req_saved"] = req_text
    req = [t for t in re.split(r"[\s,;]+", req_text) if t]
    if req:
        st.caption(f"<span class='badge'>{len(req)} variabel ditempel</span>", unsafe_allow_html=True)
    h_awal = st.session_state.get("hasil")

    def _clear_kurasi():
        st.session_state["req_input"] = ""
        st.session_state["req_saved"] = ""
        st.session_state.pop("hasil", None)

    b1, b2 = st.columns(2)
    with b1:
        proses = st.button("Proses Kurasi", disabled=not req, use_container_width=True)
    with b2:
        st.button("Bersihkan", disabled=not (req_text or h_awal),
                  use_container_width=True, on_click=_clear_kurasi)
    if proses:
        c = curate(req, m, availability=avail_map)
        do, txt = generate_do(c, m), generate_readme(c, m)
        mid = get_master_drive_id(m["survey_id"], m["period"])
        log_request(mid, None, req, c)
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
        req_norm = {normalize_code(r) for r in req}
        unav_req = [u for u in c.get("unavailable", []) if normalize_code(u) in req_norm]
        if c["missing"] or unav_req:
            parts = list(c["missing"]) + [f"{u} (tidak dilanggan FEB Undip)" for u in unav_req]
            st.warning(f"Tidak ditemukan: {', '.join(parts)}")
        unav_set = set(c.get("unavailable", []))
        found_rows = [{"Kode": v["code"], "Label": v["label"]}
                      for v in sorted(c["found"], key=lambda x: x["code"])
                      if v["code"] not in unav_set]
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### Pemetaan Variabel Valid")
        st.table(found_rows)
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
