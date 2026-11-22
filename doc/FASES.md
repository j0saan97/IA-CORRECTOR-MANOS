# Fases de implantación

| Fase | Estado |
|------|--------|
| 0 — Preparación | Completada |
| 1 — Lectura local sin subir | Completada |
| 2 — Servidor | Completada (en dev) |
| 3 — Subida real de una mano | Completada |
| 4 — Apuntes + IA | **Pendiente** |
| 5 — Automático | **En curso**: watcher y arranque con Windows hechos; falta pasar a producción |

## Fase 0 — Preparación

- [x] Instalar Python 3.11+ (3.14.2), Tesseract OCR (5.5.3) y Ollama.
- [x] `ollama pull qwen2.5:7b`
- [x] Copiar `.env.example` → `.env` y rellenar.
- [x] `pip install -r requirements.txt`
- [x] Verificar los puntos de [INVESTIGACION.md](INVESTIGACION.md#verificaciones-en-el-equipo).

Comprobado 16/11/2026.

## Fase 1 — Lectura local sin subir (validar datos)

- [x] `python main.py --check` → todo en `[OK]`.
  Carpetas de momento en local: `C:/Users/Administrador/Desktop/Hand_Review/<SPOT>/`.
  Para pasar a Drive basta cambiar `HAND_REVIEW_DIR` en `.env` a `G:/Mi unidad/Hand_Review`.
- [x] Guardar una captura en `Hand_Review/<SPOT>/`.
  Captura real de Winamax en ErrorGrave: nº de mano leído por OCR del título
  `Playback for Winamax Hand #23194209000298` (con dos ventanas lado a lado).
- [x] `python main.py --file RUTA.png --dry-run` (por nombre de archivo y por OCR del título).
- [x] Revisar en consola con una captura real: hand_id, stake, posición, duda e historial
  correctos (Winamax NL20, SB, duda "BET FOLD RIVER", 16/11/2026).

Código hecho: `config/settings.py`, `core/ocr.py`, `note_parser.py`, `hh_parser.py`,
`pt4_connector.py`, `state.py`, `pipeline.py`, `main.py` y tests (12 en verde).

## Fase 2 — Servidor

- [x] Migración en phpMyAdmin (categorías 10, 11 y 12 creadas). SQL en
  [DOCUMENTACION.md](DOCUMENTACION.md#migración-mysql).
- [x] `api_upload.php` en el repo poker_library (misma carpeta que `upload.php`).
  Rama dev de poker_library: `api_upload.php` + NL20 + categorías 10-12 en
  `BUSCADORV2.html` y `drag-and_dropV4.html` + `config_api.php` excluido de git y FTP.
  Push a dev y a main (commit `efe3919`).
- [x] `config_api.php` subido por cPanel (16/11/2026). En dev `--check` da "token válido".
  - [ ] Confirmar que también está en la carpeta de producción antes de cambiar
    `API_UPLOAD_URL` a la web real.
- [x] Token generado y puesto igual en `server/config_api.php` (local, ignorado por git) y en `.env`.
  `API_UPLOAD_URL` apunta de momento a `dev.poker-library.com`.

## Fase 3 — Subida real de una mano

Código hecho: `core/library_uploader.py` (POST + check del token en `--check`),
subtipo desde el historial (ZOOM / 6Max / 9max, CON/SIN ANTE), categoría por spot.

- [x] `python main.py --file RUTA` (sin `--dry-run`): mano Winamax 23194209000298
  (55 en SB, NL20, ErrorGrave) → id 42 en dev.
- [x] Comprobar en `BUSCADORV2.html`: campos, imagen, duda y categoría correctos.
- [x] Repetir la misma → "ya estaba en la biblioteca (id 42)" (409).
- [x] `narracionMano` ya no se envía (ver [INVESTIGACION.md](INVESTIGACION.md#narracionmano)).
- [ ] Limpiar la mano de prueba en phpMyAdmin (dev), subida antes del cambio:
  `UPDATE manos_review SET narracionMano = NULL WHERE id = 42;`

## Fase 4 — Apuntes + IA

- [ ] Exportar apuntes de Drive a `knowledge_base/<SPOT>.md`
  (ahora los 9 `.md` solo tienen el título).
- [ ] Escribir `core/ai_analyzer.py` (ahora vacío) y engancharlo en `pipeline.py`
  (paso 8) → guarda `Hand_Review/<SPOT>/<hand_id>.txt` (no va en el POST).
- [ ] Probar varias manos con `--dry-run` y ajustar el prompt.
- ~~Mostrar `analisis_ia` en el modal del buscador~~ → descartado (22/11/2026): el
  análisis lo valida el usuario y lo pega a mano.

## Fase 5 — Automático

- [x] `core/watcher.py` y `python main.py` (modo vigilancia): detecta capturas nuevas
  (sondeo cada 5 s), espera a que terminen de escribirse, procesa pendientes al arrancar,
  no repite (`state.db`) y registra errores en log. Tests en `tests/test_watcher.py`.
  Probado 22/11/2026: captura nueva detectada en 3 s (dry-run) y mano PokerStars
  262442102849 (AQ, UTG, NL25, ErrorGrave) subida sola → id 43 en dev.
- [x] Arranque con Windows: tarea `IA-Corrector-Manos` (`scripts/arranque_windows.ps1`),
  `pythonw.exe` sin ventana al iniciar sesión. Instalada y en marcha 22/11/2026.
- [ ] Pasar a producción: confirmar `config_api.php` en la carpeta real y cambiar
  `API_UPLOAD_URL` en `.env` a la web real.
- [ ] Opcional: `HAND_REVIEW_DIR` → `G:/Mi unidad/Hand_Review` (Google Drive).
