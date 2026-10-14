"""Uji alur UI headless via AppTest: katalog search label + kurasi + preview + unduh."""
from streamlit.testing.v1 import AppTest


def test_ui_flow():
    at = AppTest.from_file("web/app.py", default_timeout=120)
    at.run()
    assert not at.exception, at.exception
    assert any("Website BPS Master" in m.value for m in at.markdown), [m.value[:40] for m in at.markdown]
    # navigasi di atas (bukan sidebar)
    assert at.radio[0].value == "Katalog"
    # Katalog: cari label 'umur' -> tabel variabel wajib tampil nama + label
    at.radio[0].set_value("Katalog").run()
    at.text_input[0].set_value("umur").run()
    frames = [df.value for df in at.dataframe]
    assert any(((fr["Variabel"] == "K10") & (fr["Label"] == "K10 UMUR")).any()
               for fr in frames if "Variabel" in list(fr.columns)), "tabel variabel cocok"
    # cari nama survei -> semua variabel master cocok tampil
    at.text_input[0].set_value("komuter banjarbakula").run()
    frames = [df.value for df in at.dataframe]
    assert any(((fr["Variabel"] == "B6R617") & (fr["Survei"] == "Survei Komuter")).any()
               for fr in frames if "Variabel" in list(fr.columns)), "semua variabel master"
    # Tanpa tombol keranjang (ketuk baris diuji di browser); unduh langsung dari ketukan
    at.run()
    assert not at.exception, at.exception
    assert not any("keranjang" in b.label.lower() for b in at.button), "tanpa tombol keranjang"
    # Kurasi: pilih SAK2024, tempel daftar, proses
    at.radio[0].set_value("Kurasi").run()
    idx = next(i for i, o in enumerate(at.selectbox[0].options)
               if "2024 Agustus" in o and "Survei Angkatan Kerja Nasional" in o)
    at.selectbox[0].set_value(at.selectbox[0].options[idx]).run()
    at.text_area[0].set_value("R51A K10 k3 TIDAKADA").run()
    at.button[0].click().run()
    assert not at.exception, at.exception
    assert any("TIDAKADA" in str(w.value) for w in at.warning), "missing dilaporkan"
    do_text = at.tabs[0].code[0].value
    assert "keep " in do_text and "K10" in do_text, do_text[:200]
    assert any("Pemetaan Variabel Valid" in m.value for m in at.markdown)
    print("UI OK: katalog-search, kurasi-tempel, preview, 2 unduhan")


def _hasil_rows(at):
    """Baris tabel hasil Kurasi (kolom Kode/Label, static st.table)."""
    for df in at.table:
        v = df.value
        if "Kode" in list(v.columns):
            return v.to_dict("records")
    raise AssertionError("tabel hasil tidak ditemukan")


def test_ui_state_survives_tab_switch():
    """Pindah tab tidak boleh menghapus pilihan master, daftar variabel, atau hasil."""
    at = AppTest.from_file("web/app.py", default_timeout=120)
    at.run()
    at.radio[0].set_value("Kurasi").run()
    idx = next(i for i, o in enumerate(at.selectbox[0].options)
               if "Mikro dan Kecil" in o and o.endswith("2019"))
    chosen = at.selectbox[0].options[idx]
    at.selectbox[0].set_value(chosen).run()
    at.text_area[0].set_value("B10_1001 B10_1002").run()
    at.button[0].click().run()
    assert not at.exception, at.exception
    assert any("Pemetaan Variabel Valid" in m.value for m in at.markdown)

    at.radio[0].set_value("Katalog").run()
    at.radio[0].set_value("Kurasi").run()
    assert not at.exception, at.exception
    assert at.text_area[0].value == "B10_1001 B10_1002", \
        f"daftar variabel hilang: {at.text_area[0].value!r}"
    assert at.selectbox[0].value == chosen, \
        f"master reset: {at.selectbox[0].value!r}"
    assert any("Pemetaan Variabel Valid" in m.value for m in at.markdown), \
        "hasil kurasi hilang setelah pindah tab"
    codes = [r["Kode"] for r in _hasil_rows(at)]
    assert "B10_1001" in codes, "hasil hilang setelah pindah tab"
    print("UI OK: pindah tab tidak menghapus state kurasi")


def test_ui_katalog_tanpa_daftar():
    """Dropdown pilih-lewat-daftar sudah dihapus -> hanya ketuk baris + unduh."""
    at = AppTest.from_file("web/app.py", default_timeout=120)
    at.run()
    at.text_input[0].set_value("B10_1001").run()
    assert not at.exception, at.exception
    assert len(at.multiselect) == 0, "dropdown pilih-lewat-daftar harus hilang"
    frames = [df.value for df in at.dataframe]
    assert any("Variabel" in list(fr.columns) for fr in frames), "tabel variabel cocok tetap ada"
    print("UI OK: dropdown dihapus, tabel ketuk-baris tetap ada")


def test_ui_katalog_persists_across_tabs():
    """Query + hasil cari Katalog tidak hilang saat pindah ke Kurasi dan kembali."""
    at = AppTest.from_file("web/app.py", default_timeout=120)
    at.run()
    at.text_input[0].set_value("umur").run()
    assert not at.exception, at.exception
    assert at.text_input[0].value == "umur"
    assert any("Variabel" in list(fr.columns) for fr in (df.value for df in at.dataframe)), \
        "tabel variabel cocok harus tampil"
    at.radio[0].set_value("Kurasi").run()
    at.radio[0].set_value("Katalog").run()
    assert not at.exception, at.exception
    assert at.text_input[0].value == "umur", "query katalog hilang setelah pindah tab"
    assert any("Variabel" in list(fr.columns) for fr in (df.value for df in at.dataframe)), \
        "hasil cari katalog hilang setelah pindah tab"
    print("UI OK: katalog persisten lintas tab")


def test_ui_kurasi_marks_unsubscribed():
    """Variabel kamus tanpa data (Blok 42) -> missing berlabel tak dilanggan."""
    at = AppTest.from_file("web/app.py", default_timeout=120)
    at.run()
    at.radio[0].set_value("Kurasi").run()
    idx = next(i for i, o in enumerate(at.selectbox[0].options)
               if o.endswith("2024 Modul Konsumsi dan Pengeluaran") and "Sosial Ekonomi" in o)
    at.selectbox[0].set_value(at.selectbox[0].options[idx]).run()
    at.text_area[0].set_value("B42K3 R101").run()
    at.button[0].click().run()
    assert not at.exception, at.exception
    assert any("tidak dilanggan FEB Undip" in str(w.value) and "B42K3" in str(w.value)
               for w in at.warning), [str(w.value) for w in at.warning]
    print("UI OK: tak dilanggan berlabel di missing")


if __name__ == "__main__":
    test_ui_flow()
    test_ui_state_survives_tab_switch()
    test_ui_katalog_tanpa_daftar()
    test_ui_katalog_persists_across_tabs()
    test_ui_kurasi_marks_unsubscribed()