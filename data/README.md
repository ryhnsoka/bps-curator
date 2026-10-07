# data/

File `*.xlsx` master TIDAK di-push (lihat `.gitignore`, total ±20MB).
Sumber kanonis: folder Drive `Kode Variabel BPS`.

Alur ambil master:
1. Lihat `masters.csv` (drive_id per survei-periode).
2. Unduh via akses Drive yang sudah terhubung, simpan sesuai `local_file`.
3. Parse: `python -m bps_curator.cli parse data/<file> --survey SAKERNAS --period "2024 Agustus" -o output/<nama>.json`
4. Seed ulang DB: `python db/seed.py --db bps.db --json-dir output`
