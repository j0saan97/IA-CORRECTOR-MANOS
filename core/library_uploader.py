"""POST multipart a api_upload.php con la imagen y los campos de la mano."""
import json
import mimetypes
from dataclasses import dataclass

import requests

from config import settings


class UploadError(Exception):
    pass


@dataclass
class UploadResult:
    status: str          # 'success' o 'duplicate'
    id: int | None
    message: str


def build_fields(r) -> dict:
    """Campos que se envían a api_upload.php (r = pipeline.Result)."""
    return {
        "hand_id": r.hand_no,
        "modalidad": settings.MODALIDAD,
        "variedad": settings.VARIEDAD,
        "subtipo": r.info.subtipo,
        "nivel": r.info.nivel_stake,
        "rival": settings.DEFAULT_TIPO_RIVAL,
        "posicion": r.info.posicion or "all",
        # narracionMano no se envía: es la descripción que el usuario escribe a mano
        # en drag-and_dropV4.html ("Describe la mano..."). Desde aquí queda NULL.
        "duda": r.hand.nota,
        "categorias": json.dumps([settings.SPOT_CATEGORIAS[r.spot]]),
        "jugador_alias": settings.HERO_ALIAS,
        # analisis_ia no se envía: se guarda en local (<SPOT>/<hand_id>.txt) y el usuario
        # lo pega a mano si le sirve. En la BD queda NULL.
    }


def upload(r) -> UploadResult:
    if not settings.API_UPLOAD_URL or not settings.API_TOKEN:
        raise UploadError("Falta API_UPLOAD_URL o API_TOKEN en el .env")

    mime = mimetypes.guess_type(r.path.name)[0] or "image/png"
    with open(r.path, "rb") as img:
        resp = requests.post(
            settings.API_UPLOAD_URL,
            headers={"X-Api-Token": settings.API_TOKEN},
            data=build_fields(r),
            files={"foto_mano": (r.path.name, img, mime)},
            timeout=60,
        )

    try:
        body = resp.json()
    except ValueError:
        raise UploadError(f"HTTP {resp.status_code}: respuesta no JSON: {resp.text[:200]}")

    if resp.status_code in (200, 201) and body.get("status") == "success":
        return UploadResult("success", body.get("id"), body.get("message", ""))
    if resp.status_code == 409:
        return UploadResult("duplicate", body.get("id"), body.get("message", ""))
    raise UploadError(f"HTTP {resp.status_code}: {body.get('message', body)}")


def check() -> str:
    """Comprueba que el endpoint existe y que el token es válido (sin subir nada).
    Con token válido y sin imagen, api_upload.php responde 400 'Falta la imagen'."""
    resp = requests.post(
        settings.API_UPLOAD_URL,
        headers={"X-Api-Token": settings.API_TOKEN},
        data={"hand_id": "000000", "categorias": "[]"},
        timeout=20,
    )
    try:
        msg = resp.json().get("message", "")
    except ValueError:
        msg = resp.text[:100]
    if resp.status_code == 400 and "imagen" in msg.lower():
        return f"{settings.API_UPLOAD_URL} responde y el token es válido"
    raise UploadError(f"HTTP {resp.status_code}: {msg}")
