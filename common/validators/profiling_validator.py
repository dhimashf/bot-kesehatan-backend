import re
from fastapi import HTTPException

def is_valid_email(email: str) -> bool:
    """
    Validates an email address.
    """
    # Regular expression for validating an Email
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    # pass the regular expression
    # and the string into the fullmatch() method
    if(re.fullmatch(regex, email)):
        return True
    else:
        return False

def validate_biodata(biodata: dict):
    """
    Validates user biodata.
    Raises HTTPException if validation fails.
    """
    # Email validation
    email = biodata.get("email")
    if not email or not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Format email tidak valid.")

    # Gender-specific validation: status kehamilan hanya divalidasi untuk perempuan
    jenis_kelamin = biodata.get("jenis_kelamin")
    status_kehamilan = biodata.get("status_kehamilan")
    
    if jenis_kelamin == "Perempuan":
        # Validasi status kehamilan hanya untuk perempuan
        if status_kehamilan is None or status_kehamilan == "":
            raise HTTPException(status_code=400, detail="Status kehamilan harus diisi untuk perempuan.")
    elif jenis_kelamin == "Laki-laki":
        # Untuk laki-laki, status kehamilan tidak relevan, set ke default "Tidak"
        biodata["status_kehamilan"] = "Tidak"

    # Phone number validation (simple regex for Indonesian numbers)
    no_wa = biodata.get("no_wa")
    # Pola regex yang lebih fleksibel untuk nomor Indonesia (08, 628, +628)
    # dengan total 10-15 digit.
    if not no_wa or not re.match(r"^(08|\+628|628)\d{8,15}$", no_wa.replace("-", "").replace(" ", "")):
        raise HTTPException(status_code=400, detail="Format nomor WhatsApp tidak valid. Contoh: 081234567890 atau +6281234567890.")

    # Age validation
    usia = biodata.get("usia")
    if not isinstance(usia, int) or not (18 <= usia <= 65):
        raise HTTPException(status_code=400, detail="Usia harus antara 18 dan 65 tahun.")
