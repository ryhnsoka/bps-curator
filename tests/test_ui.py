"""Uji alur UI headless via AppTest: katalog search label + kurasi + preview + unduh."""
from streamlit.testing.v1 import AppTest


def test_ui_flow():
    at = AppTest.from_file("web/app.py", default_timeout=120)
    at.run()
    assert not at.exception, at.exception
    assert any("BPS Curator" in m.value for m in at.markdown), [m.value[:40] for m in at.markdown]
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
    """Baris tabel hasil Kurasi (kolom Kode/Label)."""
    for df in at.dataframe:
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


def test_ui_katalog_pilih_lewat_daftar():
    """Pilih variabel Katalog lewat daftar (fallback ketuk baris) -> badge + unduh."""
    at = AppTest.from_file("web/app.py", default_timeout=120)
    at.run()
    at.text_input[0].set_value("B10_1001").run()
    assert not at.exception, at.exception
    assert len(at.multiselect) == 1, "daftar pilih tampil saat ada hasil"
    opt = next(o for o in at.multiselect[0].options if o.startswith("B10_1001 "))
    at.multiselect[0].set_value([opt]).run()
    assert not at.exception, at.exception
    assert any("1 variabel dipilih" in str(c.value) for c in at.caption), \
        [str(c.value) for c in at.caption]
    print("UI OK: katalog pilih-lewat-daftar -> unduh TXT")


if __name__ == "__main__":
    test_ui_flow()
    test_ui_state_survives_tab_switch()
    test_ui_katalog_pilih_lewat_daftar()