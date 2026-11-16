"""Tests de OCR-regex, notas XML e historial (con historiales inventados)."""
from pathlib import Path

from core import hh_parser
from core.note_parser import note_to_text
from core.ocr import from_filename, normalize

STARS = """PokerStars Hand #262709582290:  Hold'em No Limit (€0.10/€0.25 EUR) - 2026/11/14 15:00:56 CET
Table 'Mesa I' 6-max Seat #6 is the button
Seat 1: p1 (€18.86 in chips)
Seat 2: p2 (€10.14 in chips)
Seat 3: p3 (€11.05 in chips)
Seat 4: p4 (€8.95 in chips)
Seat 5: p5 (€9.00 in chips)
Seat 6: hero1 (€9.06 in chips)
p1: posts small blind €0.10
p2: posts big blind €0.25
*** HOLE CARDS ***
Dealt to hero1 [4s 9s]
p3: folds
p4: folds
p5: folds
hero1: folds
p1: folds
"""

WINAMAX = """Winamax Poker - CashGame - HandId: #23193082-973-1794694246 - Holdem no limit (0.05€/0.10€) - 2026/11/14 22:10:46 UTC
Table: 'Mesa 08' 5-max (real money) Seat #3 is the button
Seat 1: p1 (10€)
Seat 2: p2 (61.85€)
Seat 3: p3 (13.28€)
Seat 4: hero2 (14.30€)
Seat 5: p5 (22.95€)
*** ANTE/BLINDS ***
hero2 posts small blind 0.05€
p5 posts big blind 0.10€
Dealt to hero2 [Ah Ad]
*** PRE-FLOP ***
p1 folds
p2 folds
p3 folds
hero2 raises 0.20€ to 0.30€
p5 folds
"""

YATAHAY = """Hand #2836922363 - Holdem (No Limit) - $0.05/$0.10 - 2026/10/01 19:15:32 UTC
Mesa 6-max Seat #4 is the button
Seat 1: p1 ($13.53)
Seat 2: p2 ($2.27)
Seat 3: p3 ($11.74)
Seat 4: hero3 ($10.58)
Seat 5: p5 ($19.03)
Seat 6: p6 ($10.10)
p5 posts the small blind $0.05
p6 posts the big blind $0.10
*** HOLE CARDS ***
Dealt to hero3 [2h Jd]
p1 folds
p2 folds
p3 folds
hero3 folds
p5 folds
"""

NOTE = """<?xml version="1.0" encoding="UTF-8"?>
<richtext version="1.0.0.0" xmlns="http://www.wxwidgets.org">
  <paragraphlayout>
    <paragraph><text>CHECK TURN TENE AQ</text></paragraph>
    <paragraph><text>y el river?</text></paragraph>
    <paragraph><text></text></paragraph>
  </paragraphlayout>
</richtext>"""


# --- nº de mano ---
def test_filename_stars():
    assert from_filename(Path("262289151822.png")) == "262289151822"


def test_filename_with_text():
    assert from_filename(Path("OOP 262289151822 duda.png")) == "262289151822"


def test_winamax_normalize():
    assert normalize("23193082-973-1794694246") == "23193082000973"
    assert normalize("23193082-973") == "23193082000973"


def test_filename_without_number():
    assert from_filename(Path("Captura de pantalla 2026.png")) is None


# --- nota ---
def test_note_xml():
    assert note_to_text(NOTE) == "CHECK TURN TENE AQ\ny el river?"


def test_note_plain_and_empty():
    assert note_to_text("hola") == "hola"
    assert note_to_text(None) == ""


# --- historial ---
def test_stars():
    i = hh_parser.parse(STARS)
    assert (i.sala, i.nivel_stake, i.hero, i.posicion, i.jugadores) == (
        "PokerStars", "NL25", "hero1", "BTN", 6)


def test_winamax():
    i = hh_parser.parse(WINAMAX)
    assert (i.sala, i.nivel_stake, i.hero, i.posicion) == ("Winamax", "NL10", "hero2", "SB")


def test_yatahay():
    i = hh_parser.parse(YATAHAY)
    assert (i.sala, i.nivel_stake, i.hero, i.posicion) == ("Yatahay", "NL10", "hero3", "BTN")


def test_positions_6max():
    # SB=p1, BB=p2, UTG=p3, HJ=p4, CO=p5, BTN=hero1
    pos = {n: hh_parser.parse_position(STARS, n) for n in ["p1", "p2", "p3", "p4", "p5"]}
    assert pos == {"p1": "SB", "p2": "BB", "p3": "UTG", "p4": "HJ", "p5": "CO"}


def test_winamax_ignora_sentados_sin_jugar():
    # p1 y p2 están sentados pero no reciben cartas (no actúan)
    hh = WINAMAX.replace("p1 folds\n", "").replace("p2 folds\n", "")
    i = hh_parser.parse(hh)
    assert i.jugadores == 3 and i.posicion == "SB"
    assert hh_parser.parse_position(hh, "p3") == "BTN"


def test_heads_up_manda_la_bb():
    hh = """Hand #1 - Holdem (No Limit) - $0.10/$0.25 - 2026/09/26 18:34:48 UTC
Mesa 6-max Seat #3 is the button
Seat 1: p1 ($25.00)
Seat 3: p3 ($25.84)
Seat 4: hero ($55.55)
hero posts the small blind $0.10
p1 sits out
p3 posts the big blind $0.25
*** HOLE CARDS ***
Dealt to hero [3d Tc]
hero folds
"""
    assert hh_parser.parse_position(hh) == "SB"
