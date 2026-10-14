"""Tes inti: normalisasi, kurasi, skip partisi, fallback wajib-semua."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from bps_curator.normalize import normalize_code
from bps_curator.curator import curate, generate_do, generate_readme
from bps_curator.definitions import load_definitions, definitions_for
import json

SAK = json.loads(Path("output/master_sak2024.json").read_text(encoding="utf-8"))


def test_normalize():
    assert normalize_code("UrutAn") == "URUTAN"
    assert normalize_code("R16-2") == normalize_code("R16_2")
    assert normalize_code(" r 10b ") == "R10B"


def test_case_insensitive_output_master():
    c = curate("urutan weight k3".split(), SAK, add_mandatory=False)
    assert [v["code"] for v in c["found"]] == ["URUTAN", "WEIGHT", "K3"]
    assert c["missing"] == []


def test_skip_partition_only_mandatory():
    c = curate("K1 K10".split(), SAK)
    do = generate_do(c, SAK)
    assert "SKIP sak202408_part2" in do and "keep " in do


def test_missing_reported():
    c = curate(["K1", "TIDAKADA"], SAK)
    assert c["missing"] == ["TIDAKADA"]


def test_labels_from_kamus_block():
    by_code = {v["code"]: v for v in SAK["variables"]}
    assert by_code["K10"]["label"] == "K10 UMUR"
    assert by_code["URUTAN"]["label"] == "IDENTITAS UNIK"


def test_readme_maps_mandatory_vs_request():
    c = curate("K1 K10".split(), SAK)
    txt = generate_readme(c, SAK)
    assert "Variabel wajib (7 unik" in txt and "KLASIFIKAS" in txt
    assert "K1" in txt and "Tidak ditemukan (0)" in txt


def test_full_survey_names():
    from bps_curator.surveys import survey_name, period_name
    assert survey_name("SAKERNAS") == "Survei Angkatan Kerja Nasional"
    assert survey_name("PODES") == "Pendataan Potensi Desa"
    assert survey_name("ECOM") == "Survei E-Commerce"
    assert survey_name("XX") == "XX"
    assert period_name("2024 MSBP") == "2024 Modul Sosial Budaya dan Pendidikan"
    assert period_name("2024 Agustus") == "2024 Agustus"
    c = curate("K1 K10".split(), SAK)
    assert "Survei Angkatan Kerja Nasional 2024 Agustus" in generate_do(c, SAK)
    assert "Survei Angkatan Kerja Nasional 2024 Agustus" in generate_readme(c, SAK)


def _mini_master():
    return {
        "survey_id": "UJI", "period": "2024 Modul", "mandatory": ["W1", "W2"],
        "variables": [
            {"code": "W1", "label": "WAJIB SATU", "type": "", "partitions": ["p1"]},
            {"code": "W2", "label": "WAJIB DUA", "type": "", "partitions": ["pX"]},
            {"code": "A1", "label": "A SATU", "type": "", "partitions": ["p1"]},
            {"code": "A2", "label": "A DUA", "type": "", "partitions": ["pX"]},
        ],
    }


def test_availability_filters_keep():
    c = curate(["A1", "A2", "W2"], _mini_master(), availability={"p1": ["W1", "A1"]})
    assert c["missing"] == []
    assert c["mandatory_added"] == ["W1"]
    assert c["grouped"] == {"p1": ["A1", "W1"]}
    assert sorted(c["unavailable"]) == ["A2", "W2"]
    assert c["unavailable_partitions"] == ["pX"]
    do = generate_do(c, _mini_master())
    assert "tidak tersedia di data" in do and "pX" in do and "keep A1 W1" in do
    txt = generate_readme(c, _mini_master())
    assert "Tidak tersedia di data (2)" in txt and "Variabel wajib (1 unik" in txt


def test_definitions_loader(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps({
        "survey_id": "SAKERNAS", "period": "2024 Agustus", "source": "prakerja.pdf",
        "map_question_to_codes": {"51J": ["R51J1", "R51J2"]},
        "definitions": {"51A": "Apakah tahu prakerja?", "51J": "Untuk apa insentif?"}}), encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps({
        "survey_id": "SAKERNAS", "period": "2024 Agustus", "source": "kuesioner.pdf",
        "mapped": {"K10": {"soal": "10", "teks": "Umur responden", "skor": 0.9}}}), encoding="utf-8")
    defs = definitions_for(load_definitions(tmp_path), "SAKERNAS", "2024 Agustus")
    assert defs["R51A"]["kind"] == "definisi" and "prakerja" in defs["R51A"]["text"]
    assert defs["R51J1"]["text"].startswith("Untuk apa insentif")
    assert defs["K10"]["kind"] == "soal"
    assert definitions_for(load_definitions(tmp_path), "XX", "2000") == {}


def test_definitions_underscore_alias_and_mark(tmp_path):
    from bps_curator.definitions import has_definition
    (tmp_path / "c.json").write_text(json.dumps({
        "survey_id": "IMK", "period": "2019", "source": "kues.pdf",
        "mapped": {"B10_1001": {"soal": "910", "teks": "Apakah ada usaha"}}}), encoding="utf-8")
    defs = load_definitions(tmp_path)
    # kode master ber-underscore harus tetap ketemu (kode polos jadi alias)
    bucket = definitions_for(defs, "IMK", "2019")
    assert bucket["B10_1001"]["text"] == "Apakah ada usaha"
    assert bucket["B10_1001"]["source"] == "kues.pdf"
    assert has_definition(defs, "IMK", "2019", "B10_1001") is True
    assert has_definition(defs, "IMK", "2019", "B10_1002") is False
    assert has_definition(defs, "IMK", "1999", "B10_1001") is False


def test_basket_txt_side_by_side():
    from bps_curator import generate_basket_txt
    sel = [
        {"code": "AB", "survey": "Susenas", "period": ""},
        {"code": "BC", "survey": "Susenas", "period": ""},
        {"code": "CD", "survey": "Susenas", "period": ""},
        {"code": "BAA", "survey": "Sakernas", "period": ""},
        {"code": "BAC", "survey": "Sakernas", "period": ""},
        {"code": "BAB", "survey": "Sakernas", "period": ""},
    ]
    txt = generate_basket_txt(sel)
    assert txt == "Susenas:\nAB BC CD\nSakernas:\nBAA BAC BAB\n"
    assert generate_basket_txt([]) == ""


def test_readme_marks_unsubscribed():
    c = curate(["A1", "A2", "W2"], _mini_master(), availability={"p1": ["W1", "A1"]})
    txt = generate_readme(c, _mini_master())
    assert "Tidak ditemukan (2)" in txt
    assert "A2 (tidak dilanggan FEB Undip)" in txt
    assert "Tidak tersedia di data (2)" in txt


def test_selection_merge_and_restore():
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "web"))
    from helpers import merge_saved_selection, restore_selection
    hits = [
        {"Variabel": "K10", "Survei": "S", "Periode": "P"},
        {"Variabel": "R51A", "Survei": "S", "Periode": "P"},
    ]
    # otoritatif: uncheck tidak bangkit lagi, kode luar-hasil dipertahankan
    saved = merge_saved_selection([hits[0]], hits, [["XX", "S", "P"]])
    assert saved == [["K10", "S", "P"], ["XX", "S", "P"]]
    # restore setelah pindah tab: hanya yang cocok hasil saat ini
    assert restore_selection(hits, saved) == hits[:1] + []
    assert restore_selection(hits, []) == []
