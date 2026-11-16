"""Obtiene el nº de mano: 1º del nombre del archivo, 2º por OCR del título del replayer.

Devuelve siempre el formato con el que PT4 guarda cash_hand_summary.hand_no:
  - PokerStars / Yatahay: los dígitos tal cual (262289151822, 2836922363)
  - Winamax: "23193082-973-1794694246" -> "23193082" + "000973" = "23193082000973"
"""
import re
from pathlib import Path

from PIL import Image, ImageOps

from config import settings

# Winamax: <mesa>-<nº>-<timestamp>  (el timestamp es opcional)
_WINAMAX = re.compile(r"(?<!\d)(\d{6,10})-(\d{1,6})(?:-\d+)?(?!\d)")
_DIGITS = re.compile(r"(?<!\d)(\d{9,15})(?!\d)")
# Título del replayer: "... Hand #262289151822" (OCR puede meter espacios)
_TITLE = re.compile(r"Hand\s*[#:]?\s*#?\s*([0-9OoIl|\-\s]{9,40})", re.IGNORECASE)
_OCR_FIX = str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1", "|": "1"})


class HandNumberNotFound(Exception):
    pass


def normalize(raw: str) -> str | None:
    """Convierte un nº de mano en bruto al formato hand_no de PT4."""
    raw = raw.strip()
    m = _WINAMAX.search(raw)
    if m:
        return m.group(1) + m.group(2).zfill(6)
    m = _DIGITS.search(raw)
    return m.group(1) if m else None


def from_filename(path: Path) -> str | None:
    return normalize(path.stem)


def _ocr_text(img: Image.Image, psm: int = 6) -> str:
    import pytesseract

    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    gray = ImageOps.grayscale(img.convert("RGB"))
    # Ampliar ayuda mucho con el texto pequeño de la barra de título
    big = gray.resize((gray.width * 2, gray.height * 2), Image.LANCZOS)
    return pytesseract.image_to_string(big, config=f"--psm {psm}")


def _regions(img: Image.Image):
    """Zonas donde buscar el título "Playback for <sala> Hand #...":
    1º franjas finas arriba, enteras y por trozos de ancho (si hay varias ventanas
       lado a lado con fondos distintos, Tesseract se lía con la franja entera);
    2º toda la imagen como texto disperso;
    3º barrido por bandas (por si el replayer no está arriba del todo)."""
    w, h = img.size
    xs = [(0, w), (0, w // 2), (w // 2, w), (0, w * 2 // 3), (w // 3, w)]
    for strip in (30, 45):
        for x0, x1 in xs:
            yield img.crop((x0, 0, x1, min(strip, h))), 7
    yield img, 11
    for y in range(30, h, 25):
        for x0, x1 in xs[1:3]:
            yield img.crop((x0, y, x1, min(y + 35, h))), 7


def from_ocr(path: Path) -> str | None:
    with Image.open(path) as img:
        img.load()
    for region, psm in _regions(img):
        text = _ocr_text(region, psm)
        for m in _TITLE.finditer(text):
            candidate = m.group(1).translate(_OCR_FIX)
            candidate = re.sub(r"\s+", "", candidate)
            hand_no = normalize(candidate)
            if hand_no:
                return hand_no
    return None


def get_hand_number(path: Path) -> tuple[str, str]:
    """Devuelve (hand_no, origen) donde origen es 'nombre' u 'ocr'."""
    hand_no = from_filename(path)
    if hand_no:
        return hand_no, "nombre"
    hand_no = from_ocr(path)
    if hand_no:
        return hand_no, "ocr"
    raise HandNumberNotFound(
        f"No se encontró el nº de mano en '{path.name}'. "
        "Renombra el archivo con el nº de mano o incluye el título del replayer en la captura."
    )
