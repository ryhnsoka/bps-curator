# BPS Curator — Session Bootstrap (dibaca otomatis tiap sesi di folder ini)

- Proyek: kurasi variabel master BPS → do-file Stata + README.txt (Lab Digital FEB Undip).
- WAJIB pertama kali: baca `PROJECT_CONTEXT.md` di folder ini sampai tuntas sebelum bertindak.
- Branch kerja: `feature/web-ui`. Jangan commit ke `main`/`develop` langsung.
- Aturan sebelum commit: uji lokal dulu (`pytest tests/ -q` harus hijau).
- Server lokal: `streamlit run web/app.py --server.port 8501`. Jika port bentrok, matikan proses basi dulu.
- Jangan tampilkan nama variabel wajib di UI (hanya jumlahnya). README tetap format `.txt`.
