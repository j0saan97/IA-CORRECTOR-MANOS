"""Busca la mano en PT4 (PostgreSQL) por hand_no: historial, nota y tags. Solo lectura."""
from dataclasses import dataclass, field
from datetime import datetime, timezone

import psycopg2

from config import settings
from core.note_parser import note_to_text


class HandNotInPT4(Exception):
    pass


@dataclass
class PT4Hand:
    id_hand: int
    hand_no: str
    sala: str
    fecha: datetime
    history: str
    nota: str
    tags: list[str] = field(default_factory=list)


def connect():
    conn = psycopg2.connect(**settings.PT4_DB, connect_timeout=5)
    conn.set_session(readonly=True, autocommit=True)
    return conn


def get_hand(hand_no: str) -> PT4Hand:
    enum = settings.PT4_HAND_ENUM_TYPE
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT s.id_hand, s.date_played, ls.site_name
                 FROM cash_hand_summary s
                 JOIN lookup_sites ls ON ls.id_site = s.id_site
                WHERE s.hand_no = %s""",
            (hand_no,),
        )
        row = cur.fetchone()
        if not row:
            raise HandNotInPT4(
                f"La mano {hand_no} no está en la base de PT4 '{settings.PT4_DB['dbname']}'."
            )
        id_hand, fecha, sala = row
        # PT4 guarda date_played en UTC: pasarlo a la hora local del PC
        fecha = fecha.replace(tzinfo=timezone.utc).astimezone().replace(tzinfo=None)

        cur.execute("SELECT history FROM cash_hand_histories WHERE id_hand = %s", (id_hand,))
        hh = cur.fetchone()
        history = hh[0] if hh else ""

        cur.execute(
            """SELECT note FROM notes
                WHERE id_x = %s AND enum_type = %s AND NOT flg_tournament
                ORDER BY date_note""",
            (id_hand, enum),
        )
        nota = "\n".join(t for t in (note_to_text(r[0]) for r in cur.fetchall()) if t)

        cur.execute(
            """SELECT lt.tag FROM tags t
                 JOIN lookup_tags lt ON lt.id_tag = t.id_tag
                WHERE t.id_x = %s AND t.enum_type = %s AND NOT t.flg_tournament
                ORDER BY lt.tag""",
            (id_hand, enum),
        )
        tags = [r[0] for r in cur.fetchall()]

    return PT4Hand(id_hand, hand_no, sala, fecha, history, nota, tags)


def check() -> str:
    """Comprueba conexión y tablas. Devuelve un resumen o lanza excepción."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*), max(date_played) FROM cash_hand_summary")
        n, last = cur.fetchone()
        cur.execute("SELECT 1 FROM cash_hand_histories LIMIT 1")
        cur.execute("SELECT count(*) FROM notes WHERE enum_type = %s", (settings.PT4_HAND_ENUM_TYPE,))
        notas = cur.fetchone()[0]
    return f"{settings.PT4_DB['dbname']}: {n} manos, última {last:%d/%m/%Y}, {notas} notas de mano"
