# Prompt untuk Gemini Pro — UI BPS Curator (UI SAJA, backend tetap)

> Salin seluruh teks di bawah garis ke Gemini Pro.

---

Kamu adalah front-end developer Streamlit. Tugasmu **HANYA membuat ulang UI** (satu file `web/app.py` + opsional `web/../.streamlit/config.toml`).
**DILARANG** mengubah logika parsing/kurasi — backend Python yang sudah ada dipakai apa adanya.

## Konteks backend (JANGAN diubah, tinggal import)

Paket `src/bps_curator/` (tambahkan `src` ke `sys.path` di baris paling atas, SEBELUM import lain):

```python
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from bps_curator.curator import curate, generate_do, generate_readme, get_mandatory_list
from bps_curator.normalize import normalize_code
```

Fungsi yang tersedia (sudah dites, JANGAN tulis ulang):
- `curate(requested: list[str], master: dict, add_mandatory=True, profile=None) -> {found, missing, mandatory_added, grouped}`
  - Input tidak sensitif kapital/spasi/strip. Output kode standar master.
- `generate_do(curated, master) -> str` (isi file `.do`, hanya perintah `keep`)
- `generate_readme(curated, master) -> str` (teks datar `.txt`: wajib vs request + label)
- `normalize_code(s) -> str`

Data siap pakai (baca langsung, JANGAN fetch ulang):
- `output/catalog.json`: list 34 master → `{survey, period, n_vars, n_partitions, partitions, mandatory, file}`
  - `mandatory` = angka (jumlah variabel wajib, gabungan profil) atau 0.
- `output/master_*.json`: `{survey_id, period, n_variables, partitions[], mandatory, variables[]}`
  - `mandatory` = `[]` | `[kode...]` | `{profil: [kode...]}` (contoh profil: `RT/IND/Mig` di Susenas)
  - tiap variable = `{code, label, type, partitions[]}`
- SQLite `bps.db` (buat jika belum ada via `db/seed.py`): tabel `masters, partitions, variables(fold,label), mandatory, requests, request_items`.
  - Cari lintas master: `SELECT m.survey_id, m.period, v.code, v.label FROM variables v JOIN masters m ON m.drive_id=v.master_id WHERE v.fold LIKE '%Q%' OR LOWER(v.label) LIKE '%q%'`

Aturan bisnis (SUDAH dienkode di backend, UI tinggal menampilkan):
- Variabel wajib: selalu union SEMUA profil (tidak ada selector profil).
- Partisi yang isinya hanya variabel wajib di-SKIP (multi-partisi).
- Setiap proses WAJIB dicatat ke `requests` + `request_items`.

## Yang harus kamu bangun (UI saja)

1. **Navigasi atas horizontal**: `Katalog | Kurasi` (radio horizontal, bukan sidebar).
2. **Katalog**: tabel 34 master + search box. Search mencocokkan survei/periode/kode/label lintas SEMUA master; hasil WAJIB menampilkan tabel variabel cocok: `Variabel | Label | Survei | Periode` (maks 200 baris). Kolom Wajib = angka saja.
3. **Kurasi**: pilih master (dropdown) → kartu info (badge jumlah variabel + partisi, TANPA daftar nama variabel wajib) → textarea tempel daftar variabel (spasi/koma/baris baru) → tombol Proses.
4. **Hasil**: metrik Ditemukan/Hilang/Wajib-ditambah → warning jika ada missing → tabel pemetaan `Kode | Label` SAJA (TANPA kolom partisi/jenis) → kartu per partisi berisi codebox `Kode Variabel: ...` → tab Preview `.do` + `README` → tombol **Unduh .do** + **Unduh README (.txt)**. Preview WAJIB tampil SEBELUM tombol unduh bisa dipakai.
5. **Tema**: terang (`base="light"`), latar abu `#F4F5F7`, kartu putih rounded 18px + shadow lembut, aksen emas `#B8860B`/`#8F6A08`, tombol pill, input putih border `#D1D5DB` rounded 12px + label tebal, header tabel tint emas.

## Batasan teknis (WAJIB dipatuhi)

- Dependensi HANYA: `streamlit==1.39.0`, `openpyxl` (JANGAN tambah library lain).
- Kompatibel Streamlit 1.39: TIDAK ada `st.download_button` di `AppTest` versi ini — itu tidak masalah, tapi pastikan download_button dipakai normal di app.
- JANGAN pakai emoji. JANGAN sidebar untuk navigasi.
- File utama HARUS `web/app.py`, config tema di `.streamlit/config.toml` (root project).
- Kode harus lolos pola uji ini (akan saya jalankan): buka Katalog → search `umur` → tabel memuat baris `K10 | K10 UMUR`; buka Kurasi → pilih SAKERNAS 2024 Agustus → tempel `K10 k3 TIDAKADA` → Proses → tab preview berisi `keep` + `K10`, warning `TIDAKADA`, tanpa exception.

## Deliverable

1. Kode lengkap `web/app.py` (satu file, siap timpa).
2. Isi `.streamlit/config.toml` bila berubah.
3. Cara jalan lokal: `pip install -r requirements.txt && streamlit run web/app.py`.
4. Daftar asumsi + hal yang KAMU ubah dari spesifikasi (jika ada).
