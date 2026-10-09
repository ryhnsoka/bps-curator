-- BPS Curator, SQLite (kolom standar, siap naik ke Postgres).
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS surveys (
    id          TEXT PRIMARY KEY,   -- ex SAKERNAS
    name        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS masters (
    drive_id    TEXT PRIMARY KEY,   -- Google Drive file ID
    survey_id   TEXT NOT NULL REFERENCES surveys(id),
    period      TEXT NOT NULL,      -- ex '2024 Agustus'
    source_file TEXT NOT NULL,
    kamus_sheet TEXT NOT NULL,
    n_variables INTEGER NOT NULL,
    drive_modified TEXT
);
CREATE INDEX IF NOT EXISTS idx_masters_survey ON masters(survey_id);

CREATE TABLE IF NOT EXISTS partitions (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    master_id TEXT NOT NULL REFERENCES masters(drive_id) ON DELETE CASCADE,
    name      TEXT NOT NULL,
    UNIQUE(master_id, name)
);

CREATE TABLE IF NOT EXISTS variables (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    master_id TEXT NOT NULL REFERENCES masters(drive_id) ON DELETE CASCADE,
    code      TEXT NOT NULL,        -- kode standar master (asli)
    fold      TEXT NOT NULL,        -- normalisasi A-Z0-9 untuk pencarian
    label     TEXT NOT NULL DEFAULT '',
    vtype     TEXT NOT NULL DEFAULT '',
    UNIQUE(master_id, fold)
);
CREATE INDEX IF NOT EXISTS idx_variables_master ON variables(master_id);
CREATE INDEX IF NOT EXISTS idx_variables_fold ON variables(fold);

CREATE TABLE IF NOT EXISTS var_partitions (
    variable_id  INTEGER NOT NULL REFERENCES variables(id) ON DELETE CASCADE,
    partition_id INTEGER NOT NULL REFERENCES partitions(id) ON DELETE CASCADE,
    PRIMARY KEY (variable_id, partition_id)
);

-- profile '' = wajib umum ; 'RT'/'IND'/'Mig' = profil Susenas
CREATE TABLE IF NOT EXISTS mandatory (
    master_id TEXT NOT NULL REFERENCES masters(drive_id) ON DELETE CASCADE,
    profile   TEXT NOT NULL DEFAULT '',
    code      TEXT NOT NULL,
    PRIMARY KEY (master_id, profile, code)
);

CREATE TABLE IF NOT EXISTS requests (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    master_id TEXT NOT NULL REFERENCES masters(drive_id),
    profile   TEXT NOT NULL DEFAULT '',
    note      TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS request_items (
    request_id INTEGER NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    code_raw  TEXT NOT NULL,        -- input user apa adanya
    code_norm TEXT NOT NULL,        -- hasil normalisasi
    status    TEXT NOT NULL,        -- 'found' | 'missing'
    PRIMARY KEY (request_id, code_raw)
);

-- Variabel yang benar-benar tersedia di file data (subset kamus).
-- Partisi kamus yang tidak tercantum di sini = tidak ada datanya.
CREATE TABLE IF NOT EXISTS data_availability (
    master_id TEXT NOT NULL REFERENCES masters(drive_id) ON DELETE CASCADE,
    partition TEXT NOT NULL,        -- nama partisi kamus
    code      TEXT NOT NULL,        -- kode standar master
    PRIMARY KEY (master_id, partition, code)
);
CREATE INDEX IF NOT EXISTS idx_avail_master ON data_availability(master_id);
