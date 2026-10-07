"""Uji alur UI headless via AppTest: katalog search label + kurasi + preview + unduh."""
from streamlit.testing.v1 import AppTest


def test_ui_flow():
    at = AppTest.from_file("web/app.py", default_timeout=120)
    at.run()
    assert not at.exception, at.exception
    assert any("BPS Curator" in m.value for m in at.markdown), [m.value[:40] for m in at.markdown]
    # Katalog: cari label 'umur' -> tabel variabel wajib tampil nama + label
    at.radio[0].set_value("Katalog").run()
    at.text_input[0].set_value("umur").run()
    frames = [df.value for df in at.dataframe]
    assert any(((fr["Variabel"] == "K10") & (fr["Label"] == "K10 UMUR")).any()
               for fr in frames if "Variabel" in list(fr.columns)), "tabel variabel cocok"
    # Kurasi: pilih SAK2024, cari, centang, proses
    at.radio[0].set_value("Kurasi").run()
    idx = next(i for i, o in enumerate(at.selectbox[0].options) if "2024 Agustus" in o and "SAKERNAS" in o)
    at.selectbox[0].set_value(at.selectbox[0].options[idx]).run()
    at.text_input[0].set_value("umur").run()
    codes = at.multiselect[0].options
    assert any(o.startswith("K10 ") for o in codes), codes[:5]
    at.multiselect[0].set_value(["K10"]).run()
    at.button[0].click().run()
    assert not at.exception, at.exception
    do_text = at.tabs[0].code[0].value
    assert "keep " in do_text and "K10" in do_text, do_text[:200]
    assert any("Variabel request user" in m.value for m in at.markdown)
    print("UI OK: katalog-search, kurasi, preview, 2 unduhan")


if __name__ == "__main__":
    test_ui_flow()
