"""Extrae del historial: sala, modalidad, stake (NL25), hero y su posición.

Soporta los formatos de PokerStars, Winamax y Yatahay tal y como los guarda PT4.
"""
import re
from dataclasses import dataclass

_BLINDS = re.compile(r"[$€£]?\s*(\d+(?:\.\d+)?)\s*[$€£]?\s*/\s*[$€£]?\s*(\d+(?:\.\d+)?)")
_SEAT = re.compile(r"^Seat (\d+): (.+?) \((.*)\)\s*$")
_BUTTON = re.compile(r"Seat #(\d+) is the button")
_HERO = re.compile(r"^Dealt to (.+?) \[")
_SB = re.compile(r"^(.+?):? posts (?:the )?small blind")
_BB = re.compile(r"^(.+?):? posts (?:the )?big blind")

_WAITING = re.compile(r"^(.+?):? (?:waits for big blind|is sitting out|sits out)")
_BY_DIST ={1: "CO", 2: "HJ", 3: "MP", 4: "UTG+2", 5: "UTG+1"}


_MAX = re.compile(r"(\d+)-max", re.IGNORECASE)
_ANTE = re.compile(r"posts (?:the )?ante", re.IGNORECASE)


@dataclass
class HandInfo:
    sala: str
    modalidad: str
    nivel_stake: str
    hero: str | None
    posicion: str | None
    jugadores: int
    max_jugadores: int = 6
    ante: bool = False

    @property
    def subtipo(self) -> str:
        """Subtipo tal y como existe en la tabla subtipos de la web (CASH_GAME)."""
        if self.modalidad == "Zoom":
            return "ZOOM"
        mesa = "9max" if self.max_jugadores >= 7 else "6Max"
        return f"{mesa} - {'CON' if self.ante else 'SIN'} ANTE"


def parse_max_jugadores(history: str) -> int:
    head = "\n".join(history.splitlines()[:2])
    m = _MAX.search(head)
    if m:
        return int(m.group(1))
    return 9 if "9-max" in head or "full ring" in head.lower() else 6


def parse_sala(first_line: str) -> str:
    if first_line.startswith("PokerStars"):
        return "PokerStars"
    if first_line.startswith("Winamax"):
        return "Winamax"
    if first_line.startswith("Hand #"):
        return "Yatahay"
    return "Desconocida"


def parse_modalidad(history: str) -> str:
    head = "\n".join(history.splitlines()[:2]).lower()
    if "zoom" in head or "fast" in head or "go fast" in head:
        return "Zoom"
    return "Normal"


def parse_stake(history: str) -> str:
    m = _BLINDS.search(history.splitlines()[0])
    if not m:
        return ""
    bb = float(m.group(2))
    return f"NL{round(bb * 100)}"


def _seats(lines: list[str]) -> list[tuple[int, str]]:
    """Asientos que reciben cartas (sin los sentados fuera o esperando a la BB)."""
    seats, out = [], set()
    in_seats = True
    for line in lines[1:]:
        if line.startswith("Dealt to") or line.startswith(("*** HOLE", "*** PRE-FLOP")):
            break
        if line.startswith("***"):
            in_seats = False
            continue
        m = _SEAT.match(line) if in_seats else None
        if m:
            stack = re.search(r"\d+(?:\.\d+)?", m.group(3))
            empty = stack is not None and float(stack.group()) == 0
            if "sitting out" not in line.lower() and not empty:
                seats.append((int(m.group(1)), m.group(2)))
            continue
        w = _WAITING.match(line)
        if w:
            out.add(w.group(1))
    seats = [s for s in seats if s[1] not in out]

    # Winamax no marca a quien está sentado sin jugar: solo cuenta quien paga
    # ciega o actúa antes del flop
    preflop = []
    for line in lines[1:]:
        if line.startswith(("*** FLOP", "*** SUMMARY")):
            break
        if not line.startswith("Seat ") and not _WAITING.match(line):
            preflop.append(line)
    acted = [s for s in seats if any(l.startswith((s[1] + " ", s[1] + ":")) for l in preflop)]
    return acted if len(acted) >= 2 else seats


def _by_distance(dist: int, first_after_bb: bool) -> str:
    """Nombre por distancia al botón (igual que PT4): 1=CO, 2=HJ, 3=MP...
    El primero en hablar tras la BB se llama UTG si está a 3 o más del botón."""
    if dist == 0:
        return "BTN"
    if dist >= 3 and first_after_bb:
        return "UTG"
    return _BY_DIST.get(dist, "MP")


def _positions(lines: list[str], history: str) -> dict[str, str]:
    """{jugador: posición} tomando como referencia el botón y quien paga la BB."""
    seats = _seats(lines)
    if len(seats) < 2:
        return {}
    bm = _BUTTON.search(history)
    btn = int(bm.group(1)) if bm else seats[-1][0]

    # Orden de reparto: empieza en el asiento siguiente al botón, el botón (o el
    # último antes de él si su asiento está vacío) queda al final
    after = [s for s in seats if s[0] > btn] + [s for s in seats if s[0] <= btn]
    ordered = [name for _, name in after]
    n = len(ordered)
    bb = next((m.group(1) for l in lines if (m := _BB.match(l))), None)
    if n == 2:  # heads-up: manda quien paga la BB (Yatahay a veces marca mal el botón)
        if bb in ordered:
            other = ordered[1 - ordered.index(bb)]
            return {other: "SB", bb: "BB"}
        return {ordered[-1]: "SB", ordered[0]: "BB"}

    bb_i = ordered.index(bb) if bb in ordered and ordered.index(bb) < n - 1 else min(1, n - 2)

    pos = {}
    for i, name in enumerate(ordered):
        if i < bb_i:
            pos[name] = "SB"
        elif i == bb_i:
            pos[name] = "BB"
        else:
            pos[name] = _by_distance(n - 1 - i, i == bb_i + 1)
    return pos


def positions(history: str) -> dict[str, str]:
    """{jugador: posición} de todos los jugadores de la mano."""
    return _positions(history.splitlines(), history)


def parse_position(history: str, hero: str | None = None) -> str | None:
    hero = hero or parse_hero(history)
    return _positions(history.splitlines(), history).get(hero) if hero else None


def parse_hero(history: str) -> str | None:
    for line in history.splitlines():
        m = _HERO.match(line)
        if m:
            return m.group(1)
    return None


def parse(history: str) -> HandInfo:
    hero = parse_hero(history)
    first = history.splitlines()[0] if history else ""
    return HandInfo(
        sala=parse_sala(first),
        modalidad=parse_modalidad(history),
        nivel_stake=parse_stake(history),
        hero=hero,
        posicion=parse_position(history, hero),
        jugadores=len(_seats(history.splitlines())),
        max_jugadores=parse_max_jugadores(history),
        ante=bool(_ANTE.search(history)),
    )
