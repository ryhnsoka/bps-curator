"""Seed SQLite dari output/master_*.json hasil parser. Idempoten per drive_id."""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from bps_curator.normalize import normalize_code

SURVEY_NAMES = {
    "SAKERNAS": "Survei Angkatan Kerja Nasional",
    "SUSENAS": "Survei Sosial Ekonomi Nasional",
    "STPIM": "Survei Tahunan Perusahaan Industri Manufaktur",
    "KOMUTER": "Survei Komuter",
    "IMK": "Survei Industri Mikro dan Kecil",
    "PODES": "Pendataan Potensi Desa",
    "ECOM": "Survei E-Commerce",
    "SPAK": "Survei Perilaku Anti Korupsi",
}

# drive_id per file JSON lokal (sumber kanonis folder Kode Variabel BPS)
DRIVE_IDS = {
    "master_sak2024.json": "1-l10YyvD66AjaCArnYLru0_w2rjJzYtI_kpvHXf1WfA",
    "master_sak2023.json": "1-2orWBPOT0_38qmWOluzOBnIO1vwqVWX",
    "master_sak2022.json": "15fewZUbiRNgRVRZOxDJY_9KjN4f6hXwwkw37h5jgmW0",
    "master_sak2021.json": "1ac5Y6dyJytBwrN2RSJujtik0kelIkHDZ41BLMocb2cs",
    "master_susenas2023kp.json": "1wxWQ_NE4reZcfQacNZAjDpejAEoVfFhA",
    "master_susenas2024modul.json": "19YipO7D8BBPgWUHr57MIYaS6avAaisSPsJwhHY3q3ys",
    "master_susenas2024kor.json": "1azOFGpdAONSN2kBf-354yohpRKskDiRRIqmFI5WNzFM",
    "master_susenas2024msbp.json": "1RE3O0jp1Cn_FY4scpjnphq1Vaj__LER8CXUB0C38WH0",
    "master_susenas2023kor.json": "1yiRAImQs6sADaxCX3CIlP50korfUQ0Ho",
    "master_stpim2019.json": "1frMszO26WXDNBu21866XsFM4u27c_zh-",
    "master_stpim2018.json": "104Lby7FrsiBtSSDEVXDs4x7_RRDHaw3p",
    "master_stpim2017.json": "1jgoAOT-avqAd8PkZfR00m_Ko3xMSZpdi",
    "master_spak2024.json": "1twrH4E2SKe85sypFiZAsgk4-0p2lkV3OOW6FllvQAxo",
    "master_komuter_banjarbakula2023.json": "1MkAitjg2Naqaz8tUZ0jg1PY6PmNeq-H6S0LubsVSm-8",
    "master_komuter_mamminasata2023.json": "1LETI-QyOwzSVLsOxCQT7YL1r5khOOXC3l63N-4wk9x8",
    "master_komuter_patungraya2023.json": "1WNUGZEMCDhECCscP0S-bxFjQKYqTWgWZnLieWAIHcko",
    "master_komuter_sarbagita2023.json": "1eFDl_0YGmkb57Bq8jEsFKhqjruanatLcPgnfpRQvj3Y",
    "master_komuter_jabo2023.json": "1I3heeBN4ZIVzp8u8ulj_j2l0ohbLi5HhfOpy0bEOaZU",
    "master_komuter_jabo2014.json": "1UxmAAuEKOg0FpRJapRuHWLw5OLYQ-Xsxk_qW9-nsHfs",
    "master_komuter_jabo2019.json": "1pwgpurlOjvyBR2lttOoceooLMV0QWnus41FRISBAUhU",
    "master_imk2019.json": "1D19TMiefB0Wa9zSJFDv0FMV8xQVAKOcjciNkrqK86gI",
    "master_imk2022.json": "1RCjucnOODAypYq_jCHK2TM0E_Pn5fFAxWWWAtAHgm2g",
    "master_imk2023.json": "1j5-g_q2hpwlufs3V9ogrOhK0I9OEY2SlO1I47EjZ0Uk",
    "master_podeskab2021.json": "14o_6HMDYIGjrk5gWZCZaZk3A1PgxgOzx",
    "master_podeskec2021.json": "1mxnP_I7iD2EuX0XH7p5z64hOei5Y23SW",
    "master_podesdesa2021.json": "14sa0HyhcqQxOOQnv8jvewkyJaAGR6YKe",
    "master_podesdesa2024.json": "1shuv4YYJELu4xJ-seee-OZXUCtEmf8hpm_csqUVWopw",
    "master_podeskec2024.json": "1BA4Poj2-xK59mR42bIa2bMdM0EoMLe96lvXUtPGbOGc",
    "master_podesinfra2024.json": "1y2ukfM5pnXdf7WdgCKJFdlo34apJIbjTvyYCf1sCDsc",
    "master_podesterdepan2024.json": "1otYeKGejji-fv12pX4TaXROfbP1sN8AkqjBUrnEn0HQ",
    "master_podesp2kt2024.json": "12RzTyu24zIikha23aPXOZhYDhnnR0mvXsAzWGwEnbPM",
    "master_podesterluar2024.json": "1P8d06UBobur7z90DaYtA51SXbzTJzZNDFaTaRZuPShs",
    "master_ecom2024.json": "16w1IIwI80JjxP4YhNIeUr9IvWH-o30D-RVG-eScVNBA",
    "master_ecom2023.json": "1s08fdZxw1tJcf2idSx87GESURK9KpLHpVrj1Re4pGW0",
}


def seed(db_path, json_dir):
    json_dir = Path(json_dir)
    con = sqlite3.connect(db_path)
    con.executescript(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))
    n_m, n_v = 0, 0
    for jf in sorted(json_dir.glob("master_*.json")):
        if jf.name not in DRIVE_IDS:
            print("lewati (tanpa drive_id):", jf.name)
            continue
        m = json.loads(jf.read_text(encoding="utf-8"))
        drive_id = DRIVE_IDS[jf.name]
        con.execute("INSERT OR IGNORE INTO surveys(id, name) VALUES (?, ?)",
                    (m["survey_id"], SURVEY_NAMES.get(m["survey_id"], m["survey_id"])))
        con.execute("DELETE FROM requests WHERE master_id = ?", (drive_id,))  # kaskade ke request_items
        con.execute("DELETE FROM data_availability WHERE master_id = ?", (drive_id,))
        con.execute("DELETE FROM masters WHERE drive_id = ?", (drive_id,))
        for tbl in ("var_partitions", "mandatory"):
            pass
        con.execute("DELETE FROM var_partitions WHERE variable_id IN "
                    "(SELECT id FROM variables WHERE master_id = ?)", (drive_id,))
        con.execute("DELETE FROM mandatory WHERE master_id = ?", (drive_id,))
        con.execute("DELETE FROM variables WHERE master_id = ?", (drive_id,))
        con.execute("DELETE FROM partitions WHERE master_id = ?", (drive_id,))
        con.execute("INSERT INTO masters(drive_id, survey_id, period, source_file, kamus_sheet, n_variables)"
                    " VALUES (?, ?, ?, ?, ?, ?)",
                    (drive_id, m["survey_id"], m["period"], m["source_file"], m["kamus_sheet"], m["n_variables"]))
        part_ids = {}
        for p in m["partitions"]:
            part_ids[p] = con.execute("INSERT INTO partitions(master_id, name) VALUES (?, ?)",
                                      (drive_id, p)).lastrowid
        for v in m["variables"]:
            vid = con.execute("INSERT INTO variables(master_id, code, fold, label, vtype) VALUES (?, ?, ?, ?, ?)",
                              (drive_id, v["code"], normalize_code(v["code"]), v["label"], v["type"])).lastrowid
            for p in v["partitions"]:
                if p in part_ids:
                    con.execute("INSERT OR IGNORE INTO var_partitions(variable_id, partition_id) VALUES (?, ?)",
                                (vid, part_ids[p]))
            n_v += 1
        mand = m.get("mandatory", [])
        profiles = mand.items() if isinstance(mand, dict) else [("", mand)]
        for prof, codes in profiles:
            for c in codes:
                con.execute("INSERT OR IGNORE INTO mandatory(master_id, profile, code) VALUES (?, ?, ?)",
                            (drive_id, prof, c))
        n_m += 1
    avail_path = json_dir / "availability.json"
    n_a = 0
    if avail_path.exists():
        avail = json.loads(avail_path.read_text(encoding="utf-8"))
        for entry in avail.get("masters", []):
            row = con.execute("SELECT drive_id FROM masters WHERE survey_id = ? AND period = ?",
                              (entry.get("survey_id", ""), entry.get("period", ""))).fetchone()
            if not row:
                print("avail dilewati (master tak dikenal):",
                      entry.get("survey_id"), entry.get("period"))
                continue
            mid = row[0]
            con.execute("DELETE FROM data_availability WHERE master_id = ?", (mid,))
            for part, codes in entry.get("partitions", {}).items():
                for c in codes:
                    con.execute("INSERT OR IGNORE INTO data_availability(master_id, partition, code)"
                                " VALUES (?, ?, ?)", (mid, part, c))
                    n_a += 1
    con.commit()
    nv = con.execute("SELECT COUNT(*) FROM variables").fetchone()[0]
    print(f"masters={n_m} variables={nv} avail={n_a} -> {db_path}")
    con.close()


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="bps.db")
    p.add_argument("--json-dir", default="output")
    a = p.parse_args()
    seed(a.db, a.json_dir)
