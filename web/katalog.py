"""Halaman Katalog: cari master/variabel, ketuk baris, salin kode per master."""
import streamlit as st

from bps_curator.normalize import normalize_code
from bps_curator.surveys import survey_name, period_name
from data import load_documents, load_master_vars, search_variables
from helpers import group_selection, merge_saved_selection, restore_selection


def render_katalog(catalog):
    st.markdown("<div class='card'><h3><span class='ico'>●</span> Katalog master</h3>", unsafe_allow_html=True)
    docs = load_documents()
    doc_by_display = {}
    for c in catalog:
        d = (docs or {}).get((c["survey"], c["period"]), {})
        if d.get("kuesioner_url"):
            doc_by_display[(survey_name(c["survey"]), period_name(c["period"]))] = d["kuesioner_url"]
    # Mirror q_saved: Streamlit membuang state widget yang tak-dirender saat
    # pindah tab — hasil cari + pilihan kembali utuh saat tab dibuka lagi.
    if "q_input" not in st.session_state:
        st.session_state["q_input"] = st.session_state.get("q_saved", "")
    st.text_input("Cari survei / periode / variabel / label", key="q_input")
    q = st.session_state["q_input"]
    st.session_state["q_saved"] = q
    rows_all = [{"Survei": survey_name(c["survey"]), "Periode": period_name(c["period"]), "Jumlah Variabel": c["n_vars"],
                 "Jumlah Partisi": c["n_partitions"], "Wajib": c["mandatory"]} for c in catalog]
    rows = rows_all
    if q:
        qf, ql = normalize_code(q), q.lower()
        hit = set()
        var_hits = []
        if qf:
            for r in search_variables(qf, ql):
                hit.add((survey_name(r["survey_id"]), period_name(r["period"])))
                var_hits.append({"Variabel": r["code"], "Label": r["label"],
                                 "Survei": survey_name(r["survey_id"]), "Periode": period_name(r["period"])})
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
        st.caption(f"<span class='badge'>{len(rows)} master, {len(var_hits)} variabel cocok untuk '{q}'</span>",
                   unsafe_allow_html=True)
        seen_docs = {}
        for v in var_hits:
            k = (v["Survei"], v["Periode"])
            if k not in seen_docs and k in doc_by_display:
                seen_docs[k] = doc_by_display[k]
        if seen_docs:
            links = " ".join(
                f"<a class='doclink' href='{u}' target='_blank'>{sv} {pr}</a>"
                for (sv, pr), u in seen_docs.items())
            st.markdown(f"Kuesioner terkait: {links}", unsafe_allow_html=True)
        if var_hits:
            st.write("**Variabel cocok (nama + label) — pilih lalu salin:**")
            st.caption("Klik kotak di ujung kiri baris untuk memilih "
                       "(klik isi sel hanya menyorot teks untuk disalin).")
            # Flag SEBELUM dataframe dirender: False = baru kembali dari tab
            # lain (state varhits dibuang Streamlit) -> pulihkan dari simpanan.
            had_sel = "varhits" in st.session_state
            st.dataframe(var_hits, use_container_width=True, hide_index=True,
                         column_config={"Label": st.column_config.TextColumn(width="large")},
                         selection_mode="multi-row", on_select="rerun", key="varhits")
            _vs = st.session_state.get("varhits")
            _sel = getattr(_vs, "selection", None) if _vs is not None else None
            _rows = getattr(_sel, "rows", []) if _sel is not None else []
            row_idx = {i for i in (_rows or []) if 0 <= i < len(var_hits)}
            if had_sel:
                tapped = [var_hits[i] for i in sorted(row_idx)]
                st.session_state["picked_saved"] = merge_saved_selection(
                    tapped, var_hits, st.session_state.get("picked_saved"))
            else:
                tapped = restore_selection(
                    var_hits, st.session_state.get("picked_saved"))
            if tapped:
                st.caption(f"<span class='badge'>{len(tapped)} variabel dipilih</span>",
                           unsafe_allow_html=True)
                groups, order = group_selection(tapped)
                for sv, pr in order:
                    extra = (f" <a class='doclink' href='{seen_docs[(sv, pr)]}' target='_blank'>Kuesioner</a>"
                             if (sv, pr) in seen_docs else "")
                    st.markdown(f"**{sv} {pr}:**{extra}", unsafe_allow_html=True)
                    st.code(" ".join(groups[(sv, pr)]), language="text")

                def _clear_katalog():
                    st.session_state.pop("varhits", None)
                    st.session_state["picked_saved"] = []

                if st.button("Bersihkan pilihan", on_click=_clear_katalog):
                    pass
    st.table(rows)
    st.markdown("</div>", unsafe_allow_html=True)
