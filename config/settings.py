"""Lee .env, define rutas y la lista de SPOTS (= carpetas = categorías = tags de PT4)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


SPOTS = [
    "3BetPots", "BlindWar", "DudaSize", "ErrorGrave",
    "ManosTopValue", "OOP", "Review", "vsRECRE",
]

# --- Rutas ---
HAND_REVIEW_DIR = Path(_env("HAND_REVIEW_DIR", "G:/Mi unidad/Hand_Review"))
TESSERACT_CMD = _env("TESSERACT_CMD", "C:/Program Files/Tesseract-OCR/tesseract.exe")
KNOWLEDGE_DIR = BASE_DIR / "knowledge_base"
LOG_DIR = BASE_DIR / "logs"
STATE_DB = BASE_DIR / "state.db"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}

# --- PostgreSQL de PT4 ---
PT4_DB = {
    "host": _env("PT4_DB_HOST", "localhost"),
    "port": int(_env("PT4_DB_PORT", "5432")),
    "dbname": _env("PT4_DB_NAME"),
    "user": _env("PT4_DB_USER", "postgres"),
    "password": _env("PT4_DB_PASSWORD"),
}
PT4_HAND_ENUM_TYPE = _env("PT4_HAND_ENUM_TYPE", "H")

# --- Ollama ---
OLLAMA_URL = _env("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = _env("OLLAMA_MODEL", "qwen2.5:7b")
# Capas en GPU: vacío = lo decide Ollama; 0 = solo CPU (driver NVIDIA antiguo -> error CUDA PTX)
OLLAMA_NUM_GPU = int(_env("OLLAMA_NUM_GPU")) if _env("OLLAMA_NUM_GPU") else None

# --- Subida ---
API_UPLOAD_URL = _env("API_UPLOAD_URL")
API_TOKEN = _env("API_TOKEN")

# --- Valores de la mano en la web ---
HERO_ALIAS = _env("HERO_ALIAS")                      # nick en la web (users_hand_review)
DEFAULT_TIPO_RIVAL = _env("DEFAULT_TIPO_RIVAL", "Desconocido (Default)")
MODALIDAD = "NoLimitHoldem"
VARIEDAD = "CASH_GAME"

# Spot (carpeta) -> id de la tabla categorias de la web
SPOT_CATEGORIAS = {
    "ErrorGrave": 1,
    "ManosTopValue": 2,
    "3BetPots": 5,
    "vsRECRE": 6,
    "DudaSize": 8,
    "BlindWar": 10,
    "OOP": 11,
    "Review": 12,
}
