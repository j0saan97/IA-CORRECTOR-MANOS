"""Orquesta los pasos para UNA captura."""
import logging
from dataclasses import dataclass
from pathlib import Path

from config import settings
from core import hh_parser, ocr, pt4_connector, state

log = logging.getLogger("pipeline")


@dataclass
class Result:
    path: Path
    spot: str
    hand_no: str
    origen_hand_no: str
    hand: pt4_connector.PT4Hand
    info: hh_parser.HandInfo


def spot_from_path(path: Path) -> str:
    spot = path.parent.name
    if spot not in settings.SPOTS:
        raise ValueError(
            f"La carpeta '{spot}' no es un spot válido. Spots: {', '.join(settings.SPOTS)}"
        )
    return spot


def collect(path: Path) -> Result:
    """Pasos 5-7: nº de mano, datos de PT4 y parseo del historial."""
    spot = spot_from_path(path)
    hand_no, origen = ocr.get_hand_number(path)
    hand = pt4_connector.get_hand(hand_no)
    info = hh_parser.parse(hand.history)
    return Result(path, spot, hand_no, origen, hand, info)


def print_result(r: Result) -> None:
    i, h = r.info, r.hand
    warn = ""
    if r.spot not in h.tags:
        warn = f"   (!) la mano no tiene el tag '{r.spot}' en PT4"
    print(f"""
==================== {r.path.name} ====================
 Spot / categoría : {r.spot}{warn}
 Tags PT4         : {', '.join(h.tags) or '-'}
 hand_id          : {r.hand_no}   (sacado por {r.origen_hand_no})
 Sala             : {h.sala}
 Fecha            : {h.fecha:%d/%m/%Y %H:%M}
 Modalidad        : {i.modalidad}
 Stake            : {i.nivel_stake}
 Hero             : {i.hero}
 Posición         : {i.posicion}   ({i.jugadores} jugadores)
 Duda (nota PT4)  : {h.nota or '(sin nota)'}
------------------------------ historial ------------------------------
{h.history.strip()}
=======================================================================""")


def process(path: Path, dry_run: bool = False) -> Result | None:
    path = Path(path)
    try:
        r = collect(path)
    except Exception as e:
        log.error("%s -> %s", path, e)
        if not dry_run:
            state.mark(path, None, "error", str(e))
        raise

    log.info("%s -> mano %s (%s, %s, %s)", path.name, r.hand_no, r.info.nivel_stake,
             r.info.posicion, r.spot)
    if dry_run:
        print_result(r)
        return r

    # Pasos 8-10 (IA + subida): Fases 3 y 4
    raise NotImplementedError("La subida real llega en la Fase 3. Usa --dry-run por ahora.")
