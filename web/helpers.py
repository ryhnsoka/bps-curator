"""Helper presentasi murni (tanpa Streamlit): dipakai halaman Katalog & Kurasi."""
import re

from bps_curator.curator import get_mandatory_list
from bps_curator.normalize import normalize_code


def kept_partitions(curated, master):
    """Partisi yang lolos aturan SKIP (isi wajib saja dibuang bila multi-partisi)."""
    mset = {normalize_code(x) for x in get_mandatory_list(master)}
    multi = len(curated["grouped"]) > 1
    return [p for p in sorted(curated["grouped"])
            if [v for v in curated["grouped"][p] if normalize_code(v) not in mset] or not multi]


def download_stem(master):
    """Nama file unduh standar, ex 'SUSENAS 2023 KP' (tanpa karakter ilegal)."""
    stem = f"{master.get('survey_id', 'kurasi')} {master.get('period', '')}".strip()
    return re.sub(r'[\\/:*?"<>|]+', "-", stem).strip() or "kurasi"


def group_selection(tapped):
    """Kelompokkan pilihan Katalog per (Survei, Periode) — jaga urutan temu pertama.

    tapped: [{"Variabel", "Survei", "Periode"}] -> (groups, order).
    """
    groups, order = {}, []
    for v in tapped:
        key = (v["Survei"], v["Periode"])
        if key not in groups:
            groups[key] = []
            order.append(key)
        if v["Variabel"] not in groups[key]:
            groups[key].append(v["Variabel"])
    return groups, order


def selection_key(v):
    """Kunci stabil satu baris pilihan: (kode, survei, periode)."""
    return (v["Variabel"], v["Survei"], v["Periode"])


def merge_saved_selection(tapped_now, var_hits, saved):
    """Simpanan otoritatif: widget menang untuk baris yang terlihat; kode
    simpanan di luar hasil saat ini dipertahankan (selamat dari ganti query)."""
    vis = {selection_key(v) for v in var_hits}
    keep = [x for x in (saved or []) if tuple(x) not in vis]
    return [[v["Variabel"], v["Survei"], v["Periode"]] for v in tapped_now] + keep


def restore_selection(var_hits, saved):
    """Kembalikan pilihan tersimpan ke baris hasil saat ini (setelah pindah tab)."""
    want = {tuple(x) for x in (saved or [])}
    return [v for v in var_hits if selection_key(v) in want]
