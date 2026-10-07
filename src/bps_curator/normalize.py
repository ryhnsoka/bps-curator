"""Normalisasi kode variabel: huruf+angka saja, abaikan kapital/spasi/strip/titik/underscore."""
import re


def normalize_code(s):
    return re.sub(r"[^A-Z0-9]", "", str(s or "").strip().upper())
