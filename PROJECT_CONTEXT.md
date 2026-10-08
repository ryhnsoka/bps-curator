# BPS Curator — Project Context (Lengkap)

**Owner**: Royhan, Mahasiswa Digital Business, FEB Undip
**Branch aktif**: `feature/web-ui` (dari `develop` → `main`)

---

## Tujuan Project

Alat bantu asisten Lab Digital FEB Undip untuk **mengkurasi variabel BPS** → file `.do` Stata (`keep` per partisi) + `README.txt` pemetaan `Kode | Label | Partisi`.

---

## Struktur Project

```
bps-curator/
├── src/bps_curator/           # Paket inti (normalize, parser, curator, cli)
├── db/                          # schema.sql + seed.py (SQLite → siap Postgres)
├── data/                        # masters.csv + xlsx lokal (xlsx DIABAIKAN git)
├── output/                      # catalog.json + master_*.json (34 master)
├── web/                         # app.py Streamlit + .streamlit/config.toml
├── examples/                    # contoh request + .do
├── tests/                       # test_core, test_ui (AppTest), screen
├── requirements.txt             # openpyxl, streamlit==1.39.0
└── README.md
```

---

## Fitur

- Parser universal master BPS (auto-deteksi sheet kamus, sheet `.`, fallback sel kuning)
- Normalisasi input, wajib otomatis (union profil), skip partisi isi-wajib, output hanya `keep`
- README.txt datar: semua wajib + request + missing
- Web UI Streamlit tone emas-putih: Katalog (search kode/label) + Kurasi (tempel daftar, preview, unduh)
- Logging request ke DB untuk audit
- 34 master unik (7076 variabel), screening 0 temuan, tes 7/7 hijau

---

## Cara Jalankan (Lokal)

```bash
pip install -r requirements.txt
streamlit run web/app.py --server.port 8501
# Buka http://localhost:8501
```

DB: `python db/seed.py --db bps.db --json-dir output`. Tes: `PYTHONPATH=src pytest tests/ -q`.

---

## Catatan

- `*.xlsx` & `bps.db` di-ignore; bangun ulang via `db/seed.py`.
- `streamlit==1.39.0` (1.65 gagal ekstrak di Windows path panjang).
