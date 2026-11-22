"""Convierte el historial de PokerStars en un resumen claro en español para la IA.

Un modelo pequeño (7B) lee mal el historial en bruto (inglés, euros, nombres). Aquí se
calcula todo lo objetivo — posiciones, cartas, acciones por calle en BB, bote y all-ins —
para que la IA solo tenga que razonar. v1: formato PokerStars.
"""
import re

from core import hh_parser

_AMT = r"[€$£]?([\d,]+(?:\.\d+)?)"
_BLINDS = re.compile(r"\(" + _AMT + r"/" + _AMT)
_SEAT = re.compile(r"^Seat \d+: (.+?) \(" + _AMT + r" in chips")
_DEALT = re.compile(r"^Dealt to (.+?) \[(.+?)\]")
_STREET = re.compile(r"^\*\*\* (FLOP|TURN|RIVER) \*\*\* (.*)")
_POST = re.compile(r"^(.+?): posts (?:small blind|big blind|small & big blinds|the ante) " + _AMT)
_FOLD = re.compile(r"^(.+?): folds")
_CHECK = re.compile(r"^(.+?): checks")
_CALL = re.compile(r"^(.+?): calls " + _AMT)
_BET = re.compile(r"^(.+?): bets " + _AMT)
_RAISE = re.compile(r"^(.+?): raises " + _AMT + r" to " + _AMT)
_UNCALLED = re.compile(r"^Uncalled bet \(" + _AMT + r"\) returned to (.+)")
_SHOWS = re.compile(r"^(.+?): shows \[(.+?)\](?: \((.+)\))?")
_COLLECTED = re.compile(r"^(.+?) collected " + _AMT)

_SUITS = {"h": "♥", "d": "♦", "c": "♣", "s": "♠"}


def _num(s: str) -> float:
    return float(s.replace(",", ""))


def cards(s: str) -> str:
    """'Qh Ah' -> 'Q♥ A♥'"""
    return " ".join(c[:-1].replace("T", "10") + _SUITS.get(c[-1], c[-1]) for c in s.split())


def summarize(history: str, hero: str | None = None, with_result: bool = True) -> str:
    """Resumen por calles en BB. Devuelve '' si el formato no se reconoce.
    with_result=False omite el showdown (para que la IA no juzgue por el resultado)."""
    lines = [l.strip() for l in history.splitlines() if l.strip()]
    if not lines:
        return ""
    m = _BLINDS.search(lines[0])
    if not m:
        return ""
    bb = _num(m.group(2))
    hero = hero or hh_parser.parse_hero(history)
    pos = hh_parser.positions(history)

    def bbs(x: float) -> str:
        return f"{x / bb:.1f}".rstrip("0").rstrip(".") + " BB"

    def who(name: str) -> str:
        p = pos.get(name, "?")
        return f"HERO ({p})" if name == hero else p

    stacks = {}
    for l in lines:
        sm = _SEAT.match(l)
        if sm and sm.group(1) in pos:
            stacks[sm.group(1)] = _num(sm.group(2))

    out = [f"Ciegas {m.group(1)}/{m.group(2)} (cantidades en BB). Jugadores: {len(pos)}.",
           "Stacks iniciales: " + ", ".join(
               f"{who(n)} {bbs(s)}" for n, s in sorted(stacks.items(), key=lambda x: x[0] != hero))]

    pot = 0.0                        # bote de calles anteriores
    street: dict[str, float] = {}    # lo puesto por cada jugador en la calle actual
    remaining = dict(stacks)
    calle = "PREFLOP"
    showdown: list[str] = []

    def put(name: str, total_in_street: float) -> bool:
        """Actualiza lo puesto en la calle; devuelve True si el jugador queda all-in."""
        prev = street.get(name, 0.0)
        street[name] = total_in_street
        if name in remaining:
            remaining[name] -= total_in_street - prev
            return remaining[name] <= 1e-9
        return False

    for l in lines:
        if l.startswith("*** SUMMARY"):
            break
        if (d := _DEALT.match(l)) and d.group(1) == hero:
            out += [f"Cartas de HERO: {cards(d.group(2))}", "", "PREFLOP:"]
        elif s := _STREET.match(l):
            pot += sum(street.values())
            street = {}
            calle = s.group(1)
            board = " ".join(cards(b) for b in re.findall(r"\[(.+?)\]", s.group(2)))
            out += ["", f"{calle} [{board}] — bote {bbs(pot)}:"]
        elif p := _POST.match(l):
            put(p.group(1), street.get(p.group(1), 0.0) + _num(p.group(2)))
        elif a := _FOLD.match(l):
            out.append(f"  {who(a.group(1))} se retira")
        elif a := _CHECK.match(l):
            out.append(f"  {who(a.group(1))} pasa")
        elif a := _CALL.match(l):
            n = a.group(1)
            allin = put(n, street.get(n, 0.0) + _num(a.group(2)))
            out.append(f"  {who(n)} paga {bbs(_num(a.group(2)))}" + (" y va ALL-IN" if allin else ""))
        elif a := _BET.match(l):
            n = a.group(1)
            bote = pot + sum(street.values())
            allin = put(n, _num(a.group(2)))
            out.append(f"  {who(n)} apuesta {bbs(_num(a.group(2)))} en un bote de {bbs(bote)}"
                       + (" y va ALL-IN" if allin else ""))
        elif a := _RAISE.match(l):
            n = a.group(1)
            allin = put(n, _num(a.group(3)))
            verbo = "sube a" if calle == "PREFLOP" else "resube a"
            out.append(f"  {who(n)} {verbo} {bbs(_num(a.group(3)))}" + (" y va ALL-IN" if allin else ""))
        elif a := _UNCALLED.match(l):
            n = a.group(2)
            street[n] = street.get(n, 0.0) - _num(a.group(1))
            out.append(f"  (a {who(n)} se le devuelven {bbs(_num(a.group(1)))} que nadie pagó)")
        elif a := _SHOWS.match(l):
            jugada = f" ({a.group(3)})" if a.group(3) else ""
            showdown.append(f"  {who(a.group(1))} enseña {cards(a.group(2))}{jugada}")
        elif a := _COLLECTED.match(l):
            showdown.append(f"  {who(a.group(1))} gana {bbs(_num(a.group(2)))}")

    if showdown and with_result:
        out += ["", "RESULTADO (solo referencia: juzga la decisión con la info que tenía HERO, no el resultado):"]
        out += showdown
    return "\n".join(out)
