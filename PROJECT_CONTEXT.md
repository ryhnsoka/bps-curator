# BPS Curator — Project Context (Lengkap)

**Tanggal**: 2026-10-07  
**Owner**: Royhan, Mahasiswa Digital Business, FEB Undip  
**Agent**: Black Swan  
**Branch aktif**: `feature/web-ui` (dari `develop` → `main`)

---

## 🎯 Tujuan Project
Alat bantu asisten Lab Digital FEB Undip untuk **mengkurasi variabel BPS** → menghasilkan file `.do` Stata (`keep` per partisi) + `README.txt` dengan pemetaan `Kode | Label | Partisi`. Mengotomatisasi proses manual: buka folder → cari master → cek partisi → tambah variabel wajib → tulis `.do` manual.

---

## 📂 Struktur Project

```
bps-curator/
├── src/bps_curator/           # Paket inti (5 file)
│   ├── __init__.py
│   ├── normalize.py           # normalisasi kode (huruf+angka saja)
│   ├── parser.py              # Parser universal master BPS
│   ├── curator.py             # Kurasi + generate .do + generate README.txt
│   └── cli.py                 # CLI: parse & curate
├── db/
│   ├── schema.sql             # SQLite: surveys→masters→partitions→variables + mandatory + requests
│   └── seed.py                # Seed dari output/master_*.json → SQLite
├── data/
│   ├── masters.csv            # 34 master: drive_id, survey, period, local_file
│   └── *.xlsx (di-ignore)     # ±20 MB file master lokal
├── output/
│   ├── catalog.json           # Ringkasan 34 master (wajib = union profil)
│   └── master_*.json          # 34 file parsed (variabel, partisi, wajib)
├── web/
│   ├── app.py                 # Streamlit UI (tema emas-putih, kartu putih)
│   └── .streamlit/config.toml # base="light", primaryColor=#B8860B
├── examples/
│   ├── request_27vars.txt     # Contoh request SAK 2024
│   ├── kurasi_27.do / _README.txt
│   └── kurasi_27_README.txt
├── db/bps.db                  # SQLite (di-ignore, build via seed.py)
├── tests/
│   ├── test_core.py           # Tes normalisasi, kurasi, README txt
│   ├── test_ui.py             # AppTest alur Katalog→Kurasi
│   └── screen.py              # Screening 34 master (0 temuan)
├── requirements.txt           # openpyxl, streamlit==1.39.0
├── requirements-dev.txt       # pytest
└── README.md                  # Dokumentasi paket
```

---

## ✅ Fitur Yang Sudah Jadi

### 1. Parser Universal (`parser.py`)
- Auto-deteksi sheet kamus (header `Variabel` + `Partisi` di kanannya)
- Baca sheet `.` (wajib) → format: 1 baris, multi-profil (RT/IND/Mig), atau baris tunggal
- Fallback: scan sel kuning (`FFFFFF00` dkk) di sheet kamus → irisan ke kode kamus
- Output JSON standar: `survey_id, period, n_variables, partitions[], mandatory, variables[]`

### 2. Kurasi & Generator (`curator.py`)
- Normalisasi input: kapital/spasi/strip/titik/underscore diabaikan → cocok ke kode master
- Wajib otomatis (union semua profil untuk Susenas/IMK)
- Grouping per partisi; **skip partisi isi wajib saja** (multi-partisi)
- Output `.do` hanya `keep` per partisi; `README.txt` format datar (bukan MD)

### 3. Database (`db/`)
- SQLite siap pakai, skema siap migrasi ke Postgres
- Tabel: `surveys, masters, partitions, variables, var_partitions, mandatory, requests, request_items`
- Seed idempoten dari `output/master_*.json` → `bps.db` (34 master, 7076 variabel)

### 4. Web UI (`web/app.py`) — **Streamlit 1.39.0**, tema emas-putih
- **Katalog**: 34 master, search kode/label → tabel variabel cocok (Kode + Label + Survei + Periode)
- **Kurasi**: pilih master → tempel daftar variabel (spasi/koma/baru) → **tanpa selector profil** (union otomatis) → **tanpa centang** → Proses
- Output: metrik (Ditemukan/Hilang/Wajib+) → tabel **Kode + Label** (tanah partisi) → **Dataset per partisi** (codebox per partisi) → Preview `.do` + `README.txt` → **Unduh .do + README.txt**
- Logging request ke DB untuk audit

### 5. Katalog & Data
- 34 master unik dari folder Drive `Kode Variabel BPS (1Y6IRN23...)`
- SAKERNAS 4, SUSENAS 5, STPIM 3, KOMUTER 7, IMK 3, PODES 9, E-COM 2, SPAK 1
- Catalog `output/catalog.json`: wajib = union profil (angka saja)
- Peta Indonesia dilewati (tidak ada master)
- Overlay `output/availability.json` → tabel `data_availability`: variabel yang benar-benar ada di file data per partisi (ex SUSENAS 2024 Modul: Blok 42 tanpa data, Blok 41/43 agregat). `.do`/README otomatis hanya keep yang tersedia + seksi "Tidak tersedia di data".

---

## 🖥️ Cara Jalankan (Lokal)

```bash
# 1. Install
pip install -r requirements.txt

# 2. (Optional) Parse ulang master xlsx → JSON
$env:PYTHONPATH='src'
python -m bps_curator.cli parse data/Master_SAK2024_Agustus.xlsx --survey SAKERNAS --period "2024 Agustus" -o output/master_sak2024.json

# 3. Seed database
python db/seed.py --db bps.db --json-dir output

# 4. Jalankan Web UI
streamlit run web/app.py --server.port 8501
# Buka http://localhost:8501
```

> **Catatan**: `streamlit==1.39.0` (1.65 gagal ekstrak di Windows). `requirements.txt` sudah dipin.

---

## 🌿 Git Branching
```
main (e7697ec) ── develop (0e6689e) ── feature/web-ui (0fe00e8 ← HEAD)
```
- `main`: rilis stabil
- `develop`: integrasi
- `feature/web-ui`: UI development
- Push: `git push -u origin main develop feature/web-ui`

---

## ✅ Status Terkini (Commit `0fe00e8`)

| Fitur | Status |
|-------|--------|
| Parser universal | ✅ 34 master parsed, 0 screening issue |
| Kurasi + .do + README.txt | ✅ |
| IMK tanpa selector profil (union otomatis) | ✅ |
| Badge nama variabel wajib dihapus | ✅ |
| Kolom partisi dihapus dari tabel hasil | ✅ |
| README format `.txt` datar | ✅ |
| Katalog: wajib = angka union, search tampil nama+label | ✅ |
| Input border jelas, label tebal | ✅ |
| Tema putih + kartu putih + emas | ✅ |
| Navigasi atas horizontal | ✅ |
| 7/7 tes lolos (core + UI) | ✅ |

---

## 🔜 Next Steps (Kalau Lanjut)

1. **Deploy**: Push ke GitHub → Vercel (frontend) + Neon Postgres (migrasi schema) + seed via GitHub Action
2. **Multi-user**: Tambah auth (Google OAuth) + role asisten/admin + audit log per user
3. **Versioning master**: Snapshot tiap revisi master + diff
4. **Export batch**: Banyak request sekaligus → zip .do + README
5. **Validasi cross-master**: Cek konsistensi kode variabel lintas survei

---

## 📌 Catatan Penting
- File `.xlsx` & `bps.db` **di-ignore** (lihat `.gitignore`). Bangun ulang via `db/seed.py`.
- Streamlit dipin `1.39.0` (1.65 gagal ekstrak di Windows path panjang).
- Tes: `$env:PYTHONPATH='src'; python -m pytest tests/ -q` (7/7 lolos).
- Server: `streamlit run web/app.py --server.port 8501` → `http://localhost:8501`.

---

**Simpan file ini sebagai `PROJECT_CONTEXT.md` di root project untuk sesi depan.**