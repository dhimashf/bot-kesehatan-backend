from enum import Enum, auto

# --- State Management with Enums ---
# This makes the code more readable and less error-prone than using range().
class State(Enum):
    # Onboarding Flow
    ASK_ACCOUNT = auto()
    AWAIT_LOGIN_EMAIL = auto()
    REGISTER_EMAIL = auto()
    # Biodata Flow
    BIODATA_EMAIL = auto()
    BIODATA_INISIAL = auto()
    BIODATA_NOWA = auto()
    BIODATA_USIA = auto()
    BIODATA_JK = auto()
    BIODATA_PENDIDIKAN = auto()
    BIODATA_LAMA_BEKERJA = auto()
    BIODATA_STATUS_PEGAWAI = auto()
    BIODATA_JABATAN = auto()
    BIODATA_JABATAN_LAIN = auto()
    BIODATA_UNIT = auto()
    BIODATA_PERKAWINAN = auto()
    BIODATA_KEHAMILAN = auto()
    BIODATA_JUMLAH_ANAK = auto()
    # Questionnaire Flow
    WHO5 = auto()
    GAD7 = auto()
    MBI = auto()
    NAQR = auto()
    NAQR_Q81_TEXT = auto() # New state for NAQR Q81 text input
    NAQR_Q82_TEXT = auto() # New state for NAQR Q82 text input
    NAQR_PERUNDUNGAN = auto() # State untuk sub-handler perundungan
    K10 = auto()