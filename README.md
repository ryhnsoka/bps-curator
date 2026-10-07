# BPS Curator — kurasi variabel BPS → do-file Stata

Asisten Lab Digital FEB Undip: pilih survei/periode + daftar variabel → dapat
`keep` per partisi (.do) + variabel wajib otomatis + variabel hilang dilaporkan.

## Struktur

```
bps-curator/
  src/bps_curator/   paket inti: normalize | parser | curator | cli
  db/                schema.sql + seed.py (SQLite, siap naik ke Postgres)
  data/              masters.csv + xlsx lokal (xlsx DIABAIKAN git, ±20MB)
  output/            master_*.json hasil parse (commit) + catalog.json
  examples/          contoh request + .do
  tests/             tes inti
```

## Mulai

```
pip install -r requirements.txt
$env:PYTHONPATH = 'src'   # Powershell; bash: export PYTHONPATH=src
python -m bps_curator.cli parse data/Master_SAK2024_Agustus.xlsx --survey SAKERNAS --period "2024 Agustus" -o output/master_sak2024.json
python -m bps_curator.cli curate --master output/master_sak2024.json --req examples/request_27vars.txt -o kurasi.do
python db/seed.py --db bps.db --json-dir output   # bangun database
```

Aturan: partisi berisi wajib saja di-SKIP (multi-partisi); output hanya `keep`;
input dinormalisasi (kapital/spasi/strip diabaikan), output kode standar master.

## Web UI (Streamlit, tone emas-putih labdigital)

```
pip install -r requirements.txt
streamlit run web/app.py
```

Menu **Katalog**: cari survei/periode/variabel/label lintas 34 master.
Menu **Kurasi**: pilih master → cari + centang variabel (kode+label+partisi) →
pilih profil wajib bila ada → **preview `.do` dan README dulu** → unduh.
Tiap proses tercatat di `requests`/`request_items` (audit).

## Branch (GitHub)

- `main` — stabil, rilis
- `develop` — integrasi
- `feature/<nama>` — fitur, ex `feature/web-ui`, `feature/susenas-profil`
- `data/<survei-periode>` — update master, ex `data/sak2024-revisi`

Alur: `feature/*` → PR ke `develop` → uji → PR ke `main` → tag `vX.Y.Z`.
File `*.xlsx` dan `*.db` tidak di-push; DB dibangun ulang via `db/seed.py`.
