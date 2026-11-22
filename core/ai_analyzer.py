"""Pre-análisis de la mano con IA local (Ollama) usando los apuntes del spot.

Resultado: Hand_Review/<SPOT>/<hand_id>.txt junto a la captura. NO se sube a la web:
el usuario lo revisa y, si le sirve, lo pega a mano en el buscador.
"""
import json
import logging
import time
from datetime import datetime
from pathlib import Path

import requests

from config import settings
from core import hh_summary

log = logging.getLogger("ai_analyzer")

OLLAMA_TIMEOUT = 900    # GTX 1050 Ti 4 GB: qwen2.5:7b va en parte por CPU y puede tardar minutos

CAMPOS = [
    ("resumen", "RESUMEN"),
    ("decision_clave", "DECISIÓN CLAVE"),
    ("veredicto", "VEREDICTO"),
    ("explicacion", "EXPLICACIÓN"),
    ("alternativa", "ALTERNATIVA"),
    ("regla_aplicada", "REGLA DE TUS APUNTES APLICADA"),
]

SYSTEM = """Eres un coach de póker NL Hold'em cash (micro-stakes) que revisa manos de su alumno.
Reglas estrictas:
- Responde SIEMPRE en español.
- Analiza SOLO lo que pone la mano. No inventes cartas, stacks, acciones ni lecturas del rival.
  Las cartas de HERO, el board, las acciones y los all-in que se dan son EXACTOS: cópialos tal cual.
- La decisión clave es una acción de HERO (no del rival). Indica la calle exacta (PREFLOP/FLOP/TURN/RIVER)
  tal como aparece en la mano.
- No conoces las cartas del rival ni el resultado: juzga la decisión con la información que tenía HERO.
- Si la duda pregunta por una calle concreta, la "decision_clave" es esa acción de esa calle.
- NO des EV, equities, porcentajes ni frecuencias numéricas inventadas.
- Prioriza los APUNTES DEL ALUMNO sobre la teoría general. Si los apuntes no cubren el caso,
  dilo en "regla_aplicada" ("Los apuntes no cubren este caso") y razona con teoría estándar.
- Responde a la DUDA del alumno de forma directa.
- Devuelve SOLO un objeto JSON con estas claves (texto breve en cada una):
  "resumen": la mano en 1-2 frases (posición, cartas, línea),
  "decision_clave": la calle y acción que decide la mano,
  "veredicto": "Correcta", "Dudosa" o "Error",
  "explicacion": por qué, en 3-6 frases,
  "alternativa": qué línea es mejor (o "Ninguna" si fue correcta),
  "regla_aplicada": qué regla de los apuntes aplica (cítala) o que no la hay."""


def _read_kb(name: str) -> str:
    """Contenido útil de knowledge_base/<name>.md ('' si solo tiene el título)."""
    p = settings.KNOWLEDGE_DIR / f"{name}.md"
    if not p.exists():
        return ""
    lines = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    if len(lines) <= 1 and (not lines or lines[0].lstrip().startswith("#")):
        return ""
    return "\n".join(lines)


def build_prompt(r) -> str:
    """r = pipeline.Result."""
    i, h = r.info, r.hand
    reglas = _read_kb("global_rules") or "(sin apuntes generales todavía)"
    spot = _read_kb(r.spot) or f"(sin apuntes del spot {r.spot} todavía)"
    return f"""## APUNTES GENERALES DEL ALUMNO
{reglas}

## APUNTES DEL SPOT: {r.spot}
{spot}

## DATOS DE LA MANO
Sala: {h.sala} | {i.modalidad} | {i.nivel_stake} | {i.jugadores} jugadores
Hero: {i.hero} en {i.posicion}

## DUDA DEL ALUMNO
{h.nota or "(no escribió duda: revisa la mano entera y señala la decisión más importante)"}

## LA MANO (resumen exacto calculado del historial; HERO es el alumno)
{hh_summary.summarize(h.history, i.hero, with_result=False) or h.history.strip()}
"""


def _options() -> dict:
    opts = {"temperature": 0.2, "num_ctx": 8192}
    if settings.OLLAMA_NUM_GPU is not None:
        opts["num_gpu"] = settings.OLLAMA_NUM_GPU
    return opts


def ask_ollama(prompt: str) -> dict:
    resp = requests.post(
        f"{settings.OLLAMA_URL}/api/chat",
        json={
            "model": settings.OLLAMA_MODEL,
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": prompt}],
            "format": "json",
            "stream": False,
            "options": _options(),
        },
        timeout=OLLAMA_TIMEOUT,
    )
    resp.raise_for_status()
    content = resp.json()["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"explicacion": content}      # el modelo no devolvió JSON: se guarda tal cual


def render(r, data: dict, segundos: float) -> str:
    i, h = r.info, r.hand
    out = [
        f"PRE-ANÁLISIS IA — mano {r.hand_no} ({r.spot})",
        f"{h.sala} {i.modalidad} {i.nivel_stake} | Hero {i.posicion} | {h.fecha:%d/%m/%Y %H:%M}",
        f"Duda: {h.nota or '(sin duda)'}",
        "=" * 70,
    ]
    resumen = hh_summary.summarize(h.history, i.hero)
    if resumen:
        out += ["", "LA MANO (calculado del historial, exacto):", resumen, "", "=" * 70]
    out += ["", "ANÁLISIS IA (revisar: puede equivocarse):"]
    for key, titulo in CAMPOS:
        val = data.get(key)
        if val:
            out += ["", f"{titulo}:", str(val).strip()]
    out += ["", "=" * 70,
            f"Generado {datetime.now():%d/%m/%Y %H:%M} con {settings.OLLAMA_MODEL} en {segundos:.0f} s. "
            "Revisar antes de usar: la IA puede equivocarse."]
    return "\n".join(out) + "\n"


def txt_path(r) -> Path:
    return r.path.parent / f"{r.hand_no}.txt"


def analyze(r, overwrite: bool = False) -> Path | None:
    """Genera y guarda <SPOT>/<hand_id>.txt. Devuelve la ruta, o None si ya existía."""
    dest = txt_path(r)
    if dest.exists() and not overwrite:
        return None
    t0 = time.monotonic()
    data = ask_ollama(build_prompt(r))
    dest.write_text(render(r, data, time.monotonic() - t0), encoding="utf-8")
    log.info("%s -> análisis IA guardado en %s", r.path.name, dest)
    return dest
