"""Nama survei lengkap sesuai master (tampilan), ID singkat tetap untuk data."""

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


def survey_name(survey_id):
    return SURVEY_NAMES.get(survey_id or "", survey_id or "")


# Periode modul Susenas yang disingkat di master -> bentuk lengkap untuk tampilan.
# Kunci = string periode persis seperti di master/DB (hanya muncul di Susenas).
PERIOD_NAMES = {
    "2023 KP": "2023 Konsumsi dan Pengeluaran",
    "2024 Modul": "2024 Modul Konsumsi dan Pengeluaran",
    "2023 KOR": "2023 Kor (Inti)",
    "2024 KOR": "2024 Kor (Inti)",
    "2024 MSBP": "2024 Modul Sosial Budaya dan Pendidikan",
}


def period_name(period):
    return PERIOD_NAMES.get(period or "", period or "")
