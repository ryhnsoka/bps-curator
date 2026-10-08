# Prompt untuk Gemini Pro — UI BPS Curator (UI SAJA, backend tetap)

> Salin seluruh teks di bawah garis ke Gemini Pro.

---

Kamu adalah front-end developer Streamlit. Tugasmu **HANYA membuat ulang UI** (satu file `web/app.py` + opsional `.streamlit/config.toml`).
**DILARANG** mengubah logika parsing/kurasi — backend Python yang sudah ada dipakai apa adanya.

## Konteks backend (JANGAN diubah, tinggal import)

Paket `src/bps_curator/` (tambahkan `src` ke `sys.path` di baris paling atas, SEBELUM import lain).
Fungsi: `curate(requested, master, profile=None)`, `generate_do`, `generate_readme`, `get_mandatory_list`, `normalize_code`.
Data: `output/catalog.json` (34 master), `output/master_*.json` (variables, partitions, mandatory), SQLite `bps.db`.

Aturan bisnis (SUDAH dienkode, UI tinggal menampilkan): wajib = union SEMUA profil; partisi isi-wajib di-SKIP; tiap proses WAJIB dicatat ke `requests` + `request_items`.

## Yang harus kamu bangun (UI saja)

1. Navigasi atas horizontal Katalog | Kurasi (radio horizontal, bukan sidebar).
2. Katalog: tabel 34 master + search survei/periode/kode/label; hasil WAJIB tabel `Variabel | Label | Survei | Periode` (maks 200).
3. Kurasi: dropdown master → kartu info (badge jumlah, TANPA daftar nama wajib) → textarea tempel daftar → tombol Proses.
4. Hasil: metrik Ditemukan/Hilang/Wajib-ditambah → tabel `Kode | Label` SAJA → kartu per partisi berisi codebox → tab Preview `.do` + `README` → Unduh .do + README (.txt). Preview WAJIB sebelum unduh.
5. Tema terang, latar abu #F4F5F7, kartu putih rounded 18px, aksen emas #B8860B/#8F6A08, tombol pill, input putih border #D1D5DB rounded 12px + label tebal.

## Batasan teknis (WAJIB)

- Dependensi HANYA: `streamlit==1.39.0`, `openpyxl`. JANGAN pakai emoji. JANGAN sidebar untuk navigasi.
- File utama HARUS `web/app.py`, config tema di `.streamlit/config.toml` (root project).
