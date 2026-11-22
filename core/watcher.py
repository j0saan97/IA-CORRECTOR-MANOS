"""Vigila Hand_Review/<SPOT>/, espera a que el archivo termine de sincronizar y procesa pendientes al arrancar."""
import logging
import queue
import threading
import time
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

from config import settings
from core import pipeline, state

log = logging.getLogger("watcher")

POLL_SECONDS = 5        # cada cuánto mira las carpetas (PollingObserver: fiable en Google Drive)
STABLE_SECONDS = 3      # el archivo no debe cambiar durante este tiempo para darlo por terminado
STABLE_TIMEOUT = 300    # si en 5 min no se estabiliza, se omite (se reintenta al reiniciar)


def _say(msg: str, level: int = logging.INFO) -> None:
    print(f"{time.strftime('%H:%M:%S')}  {msg}", flush=True)
    log.log(level, msg)


def is_capture(path: Path) -> bool:
    """Imagen directamente dentro de Hand_Review/<SPOT>/."""
    return (
        path.suffix.lower() in settings.IMAGE_EXTENSIONS
        and path.parent.name in settings.SPOTS
        and path.parent.parent.resolve() == settings.HAND_REVIEW_DIR.resolve()
    )


def wait_until_stable(path: Path) -> bool:
    """Espera a que el archivo deje de cambiar y se pueda abrir (captura o sync de Drive terminados)."""
    deadline = time.monotonic() + STABLE_TIMEOUT
    last = None
    stable_since = time.monotonic()
    while time.monotonic() < deadline:
        try:
            st = path.stat()
            sig = (st.st_size, st.st_mtime)
        except FileNotFoundError:
            return False                      # lo borraron o renombraron
        if sig != last:
            last, stable_since = sig, time.monotonic()
        elif sig[0] > 0 and time.monotonic() - stable_since >= STABLE_SECONDS:
            try:
                with open(path, "rb"):
                    return True
            except OSError:
                pass                          # aún bloqueado por otro programa
        time.sleep(1)
    return False


def pending() -> list[Path]:
    """Capturas de todas las carpetas de spot que aún no se han subido bien."""
    out = []
    for spot in settings.SPOTS:
        d = settings.HAND_REVIEW_DIR / spot
        if d.is_dir():
            out += [p for p in sorted(d.iterdir())
                    if p.is_file() and is_capture(p) and not state.is_processed(p)]
    return out


class _Handler(FileSystemEventHandler):
    def __init__(self, on_capture: Callable[[Path], None]):
        self.on_capture = on_capture

    def _push(self, p: str) -> None:
        path = Path(p)
        if is_capture(path):
            self.on_capture(path)

    def on_created(self, event):
        if not event.is_directory:
            self._push(event.src_path)

    def on_moved(self, event):           # herramientas que guardan a temporal y renombran
        if not event.is_directory:
            self._push(event.dest_path)


def _handle(path: Path, dry_run: bool) -> None:
    if not dry_run and state.is_processed(path):
        return
    if not wait_until_stable(path):
        _say(f"{path.name}: no terminó de escribirse o desapareció; se omite.", logging.WARNING)
        return
    _say(f"Procesando {path.parent.name}/{path.name} ...")
    try:
        pipeline.process(path, dry_run=dry_run)
    except Exception as e:
        _say(f"[ERROR] {path.parent.name}/{path.name}: {e}", logging.ERROR)


def run(dry_run: bool = False) -> int:
    root = settings.HAND_REVIEW_DIR
    if not root.is_dir():
        print(f"[ERROR] No existe la carpeta {root} (HAND_REVIEW_DIR en .env).")
        return 1

    q: "queue.Queue[Path]" = queue.Queue()
    queued: set[Path] = set()
    lock = threading.Lock()

    def enqueue(p: Path) -> None:
        """Encola una captura una sola vez aunque lleguen varios eventos seguidos."""
        with lock:
            if p in queued:
                return
            queued.add(p)
        q.put(p)

    modo = " (DRY-RUN: no se sube nada)" if dry_run else ""
    _say(f"Vigilando {root}{modo}. Ctrl+C para parar.")

    for p in pending():
        enqueue(p)
    if q.qsize():
        _say(f"{q.qsize()} captura(s) pendiente(s) al arrancar.")

    observer = PollingObserver(timeout=POLL_SECONDS)
    observer.schedule(_Handler(enqueue), str(root), recursive=True)
    observer.start()
    try:
        while True:
            try:
                path = q.get(timeout=1)
            except queue.Empty:
                continue
            try:
                _handle(path, dry_run)
            finally:
                with lock:
                    queued.discard(path)
    except KeyboardInterrupt:
        _say("Parado por el usuario.")
    finally:
        observer.stop()
        observer.join()
    return 0
