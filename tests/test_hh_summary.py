from core import hh_summary

HH = """PokerStars Zoom Hand #262442102849:  Hold'em No Limit (€0.10/€0.25) - 2026/10/19 1:00:47 CET [2026/10/18 19:00:47 ET]
Table 'Atria' 6-max Seat #1 is the button
Seat 1: Riswi (€31.81 in chips)
Seat 2: TotoFigo13 (€28.90 in chips)
Seat 3: anonio9 (€25.23 in chips)
Seat 4: y0saN (€26.02 in chips)
Seat 5: magiamonty (€32.43 in chips)
Seat 6: Manyuel (€8.65 in chips)
TotoFigo13: posts small blind €0.10
anonio9: posts big blind €0.25
*** HOLE CARDS ***
Dealt to y0saN [Qh Ah]
y0saN: raises €0.30 to €0.55
magiamonty: folds
Manyuel: calls €0.55
Riswi: folds
TotoFigo13: calls €0.45
anonio9: folds
*** FLOP *** [Ad Qd 2d]
TotoFigo13: checks
y0saN: checks
Manyuel: bets €1.80
TotoFigo13: folds
y0saN: raises €8.70 to €10.50
Manyuel: calls €6.30 and is all-in
Uncalled bet (€2.40) returned to y0saN
*** TURN *** [Ad Qd 2d] [8c]
*** RIVER *** [Ad Qd 2d 8c] [5d]
*** SHOW DOWN ***
y0saN: shows [Qh Ah] (two pair, Aces and Queens)
Manyuel: shows [2c 2h] (three of a kind, Deuces)
Manyuel collected €17.20 from pot
*** SUMMARY ***
Total pot €18.10 | Rake €0.90
"""


def test_cards():
    assert hh_summary.cards("Qh Ah Td") == "Q♥ A♥ 10♦"


def test_summary_streets_and_allin():
    s = hh_summary.summarize(HH)
    assert "Cartas de HERO: Q♥ A♥" in s
    assert "HERO (UTG) sube a 2.2 BB" in s
    assert "FLOP [A♦ Q♦ 2♦] — bote 7.6 BB:" in s
    assert "CO apuesta 7.2 BB en un bote de 7.6 BB" in s
    assert "HERO (UTG) resube a 42 BB" in s
    assert "CO paga 25.2 BB y va ALL-IN" in s
    assert "TURN [A♦ Q♦ 2♦ 8♣] — bote 72.4 BB:" in s
    assert "CO enseña 2♣ 2♥" in s


def test_summary_without_result():
    s = hh_summary.summarize(HH, with_result=False)
    assert "2♣ 2♥" not in s and "RESULTADO" not in s


def test_unknown_format():
    assert hh_summary.summarize("texto que no es un historial") == ""
