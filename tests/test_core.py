"""Tes inti: normalisasi, kurasi, skip partisi, fallback wajib-semua."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from bps_curator.normalize import normalize_code
from bps_curator.curator import curate, generate_do, generate_readme
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
    assert "Variabel wajib (7)" in txt and "KLASIFIKAS" in txt
    assert "K1" in txt and "Tidak ditemukan (0)" in txt


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
    assert "Tidak tersedia di data (2)" in txt and "Variabel wajib (1)" in txt
