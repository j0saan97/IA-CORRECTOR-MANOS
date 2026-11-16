"""Punto de entrada: modo vigilancia, --check, --file y --dry-run."""
import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path

import requests

from config import settings

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def setup_logging() -> None:
    settings.LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(settings.LOG_DIR / "pipeline.log", encoding="utf-8")],
    )


def run_checks() -> bool:
    ok = True

    def line(status: str, name: str, msg: str) -> None:
        print(f"[{status}] {name:<12} {msg}")

    # .env
    if (settings.BASE_DIR / ".env").exists():
        line("OK", ".env", "encontrado")
    else:
        line("XX", ".env", "no existe: copia .env.example a .env"); ok = False

    # Carpetas de spots
    d = settings.HAND_REVIEW_DIR
    if d.is_dir():
        missing = [s for s in settings.SPOTS if not (d / s).is_dir()]
        if missing:
            line("!!", "Carpetas", f"{d} existe, faltan: {', '.join(missing)}")
        else:
            line("OK", "Carpetas", f"{d} con los {len(settings.SPOTS)} spots")
    else:
        line("XX", "Carpetas", f"no existe {d}"); ok = False

    # Tesseract
    exe = settings.TESSERACT_CMD
    if Path(exe).exists() or shutil.which(exe):
        v = subprocess.run([exe, "--version"], capture_output=True, text=True).stdout.splitlines()
        line("OK", "Tesseract", v[0] if v else exe)
    else:
        line("XX", "Tesseract", f"no encontrado en {exe}"); ok = False

    # PT4
    try:
        from core import pt4_connector
        line("OK", "PT4", pt4_connector.check())
    except Exception as e:
        line("XX", "PT4", str(e).strip().splitlines()[0]); ok = False

    # Ollama
    try:
        tags = requests.get(f"{settings.OLLAMA_URL}/api/tags", timeout=5).json()
        models = [m["name"] for m in tags.get("models", [])]
        if settings.OLLAMA_MODEL in models:
            line("OK", "Ollama", f"modelo {settings.OLLAMA_MODEL} disponible")
        else:
            line("XX", "Ollama", f"falta el modelo {settings.OLLAMA_MODEL} (ollama pull)"); ok = False
    except Exception:
        line("XX", "Ollama", f"no responde en {settings.OLLAMA_URL} (¿está abierto?)"); ok = False

    # API
    if not settings.API_TOKEN or not settings.API_UPLOAD_URL:
        line("XX", "API", "falta API_UPLOAD_URL o API_TOKEN en .env"); ok = False
    else:
        try:
            from core import library_uploader
            line("OK", "API", library_uploader.check())
        except Exception as e:
            line("XX", "API", str(e)); ok = False
    if not settings.HERO_ALIAS:
        line("!!", "Alias", "HERO_ALIAS vacío en .env: la mano se subirá sin jugador")

    print("\nTodo listo." if ok else "\nHay puntos en [XX] que corregir.")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Poker Coach IA local")
    parser.add_argument("--check", action="store_true", help="Comprueba PT4, Ollama, Tesseract y carpetas")
    parser.add_argument("--file", help="Procesa una sola captura")
    parser.add_argument("--dry-run", action="store_true", help="No sube nada a la web")
    args = parser.parse_args()
    setup_logging()

    if args.check:
        return 0 if run_checks() else 1

    if args.file:
        from core import pipeline
        try:
            pipeline.process(Path(args.file), dry_run=args.dry_run)
        except Exception as e:
            print(f"[ERROR] {e}")
            return 1
        return 0

    print("El modo vigilancia llega en la Fase 5. Usa --check o --file RUTA --dry-run.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
