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
