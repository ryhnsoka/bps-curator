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
    assert any("Klik baris untuk melihat definisi" in str(c.value) for c in at.caption), \
        "petunjuk klik tampil"
    assert any("variabel punya" in str(c.value) for c in at.caption), "cakupan dilaporkan"
    # ketuk baris R51A -> definisi prakerja tampil (AppTest tak punya select(),
    # jadi state selection disimulasikan lewat session_state)
    row = next(i for i, r in enumerate(df_has_kode(at, "K10"))
               if r["Kode"] == "R51A")
    at.session_state["hasiltabel"] = {"selection": {"rows": [row]}}
    at.run()
    assert not at.exception, at.exception
    box = [m.value for m in at.markdown if is_defbox(m.value)]
    assert box, "kotak definisi tampil setelah baris diklik"
    assert "R51A" in box[0] and "Kartu Prakerja" in box[0], box[0][:200]
    print("UI OK: katalog-search, kurasi-tempel, preview, definisi-klik, 2 unduhan")


def is_defbox(v):
    """True untuk markdown kotak definisi (bukan blok CSS di atas)."""
    return "class='defbox'" in str(v)


def df_has_kode(at, kode):
    """Baris tabel hasil (kolom Kode/Label) dari frame pertama yang punya kolom tsb."""
    for df in at.dataframe:
        v = df.value
        if "Kode" in list(v.columns):
            return v.to_dict("records")
    raise AssertionError("tabel hasil tidak ditemukan")


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
    assert any("Klik baris" in c for c in caps), caps
    rows = df_has_kode(at, "B10_1001")
    at.session_state["hasiltabel"] = {"selection": {"rows": [0]}}
    at.run()
    assert not at.exception, at.exception
    box = [m.value for m in at.markdown if is_defbox(m.value)]
    assert box and "B10_1001" in box[0], box[:1]
    assert "usaha" in box[0].lower(), box[0][:200]
    # baris tanpa definisi (B10_1002 tidak terpeta) tidak menghasilkan kotak
    assert len([m for m in at.markdown if is_defbox(m.value)]) == 1
    print("UI OK: definisi IMK (kode underscore) + ambang cakupan")


if __name__ == "__main__":
    test_ui_flow()
    test_ui_definitions_underscore_master()
