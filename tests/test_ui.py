"""Uji alur UI headless via AppTest: katalog search label + kurasi + preview + unduh."""
from streamlit.testing.v1 import AppTest


def _expander_map(at):
    """{kode variabel: (label expander, [isi markdown])} dari tab Definisi."""
    out = {}
    for e in at.expander:
        kode = str(e.label).split(" ")[0]
        out[kode] = (str(e.label), [str(m.value) for m in e.markdown]
                     + [str(c.value) for c in e.caption])
    return out


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
    # Kurasi: pilih SAK2024, cari, centang, proses
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
    assert any("Definisi Variabel" in m.value for m in at.markdown), "seksi definisi"
    assert any("variabel punya" in str(c.value) for c in at.caption), "cakupan dilaporkan"
    # definisi prakerja ada di expander R51A (bukan selectbox tersembunyi)
    ex = _expander_map(at)
    assert "R51A" in ex, sorted(ex)[:10]
    isi = " ".join(ex["R51A"][1])
    assert "Kartu Prakerja" in isi, isi[:200]
    print("UI OK: katalog-search, kurasi-tempel, preview, definisi, 2 unduhan")


def test_ui_definitions_underscore_master():
    """IMK pakai kode ber-underscore (B10_1001): definisi harus tetap ketemu."""
    at = AppTest.from_file("web/app.py", default_timeout=120)
    at.run()
    at.radio[0].set_value("Kurasi").run()
    idx = next(i for i, o in enumerate(at.selectbox[0].options)
               if "Mikro dan Kecil" in o and o.endswith("2019"))
    at.selectbox[0].set_value(at.selectbox[0].options[idx]).run()
    at.text_area[0].set_value("B10_1001 B10_1002").run()
    at.button[0].click().run()
    assert not at.exception, at.exception
    caps = [str(c.value) for c in at.caption]
    assert any("149 dari 199" in c for c in caps), caps
    assert any("Ketuk nama variabel" in c for c in caps), caps
    ex = _expander_map(at)
    assert "B10_1001" in ex, sorted(ex)[:10]
    isi = " ".join(ex["B10_1001"][1])
    assert "usaha" in isi.lower(), isi[:200]
    assert any("VIMK19_KBLI.pdf" in s for s in ex["B10_1001"][1]), "sumber disebut"
    # B10_1002 tidak punya peta -> tidak boleh ada expander-nya
    assert "B10_1002" not in ex, sorted(ex)
    print("UI OK: definisi IMK (kode underscore) + ambang cakupan")


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
    assert "B10_1001" in _expander_map(at), "definisi hilang setelah pindah tab"
    print("UI OK: pindah tab tidak menghapus state kurasi")


if __name__ == "__main__":
    test_ui_flow()
    test_ui_definitions_underscore_master()
    test_ui_state_survives_tab_switch()