# Arquitectura — Poker Coach IA local → poker-library.com

v1 — 15/11/2026

## Objetivo

Guardar una captura de PT4 en la carpeta del spot y que, sin hacer nada más,
la mano aparezca en buscar.poker-library.com con:

- la imagen
- tu duda (nota de mano de PT4)
- la categoría (= carpeta / tag). La carpeta local y la categoría del drag&drop
  tienen que llamarse igual.

Además, en local (NO se sube a la web):

- un pre-análisis de IA local en formato `.txt`, basado en TUS apuntes del spot,
  que se guarda en la carpeta del spot con el ID de la mano (`<SPOT>/<hand_id>.txt`).
  Lo valido yo: si me gusta el análisis, lo pego a mano en el buscador de manos.

Salas: de momento solo se valida **PokerStars**. El código ya soporta Winamax y
Yatahay, que se validarán en versiones posteriores.

## 1. Stack y tecnologías

### Local (PC con Windows)

| Pieza | Tecnología |
|-------|------------|
| Lenguaje | Python 3.11+ |
| Vigilancia de carpetas | watchdog (PollingObserver, fiable en Google Drive G:) |
| OCR | Tesseract OCR + pytesseract + Pillow |
| Base de datos PT4 | PostgreSQL (la de PokerTracker 4) vía psycopg2 |
| IA | Ollama + modelo de texto `qwen2.5:7b` (sin visión: el historial de PT4 ya es exacto, la visión solo añade errores) |
| Estado local | SQLite (`state.db`) → capturas ya procesadas |
| Configuración | `.env` + python-dotenv |
| Subida | requests (POST multipart con token) |

### Servidor (BanaHosting, sin Node)

| Pieza | Tecnología |
|-------|------------|
| Backend | PHP 8 + mysqli (`getDB()` de `db_connect.php`) |
| Base de datos | MySQL (`nofxdyfx_texas_holdem_cash_table`) |
| Endpoint | `api_upload.php` (protegido con token `X-Api-Token`) |
| Frontend existente | `drag-and_dropV4.html` (subida manual), `BUSCADORV2.html` |
| Deploy | GitHub Actions por FTP (`main` → web real, `dev` → pruebas) |

### Herramientas

VSCode, DBeaver (PT4/PostgreSQL), phpMyAdmin (MySQL BanaHosting), GitHub.

## 2. Estructura del proyecto

```
IA-CORRECTOR-MANOS/
├── .env.example              Plantilla de configuración (copiar como .env)
├── .gitignore                Excluye .env, state.db, logs, config_api.php
├── requirements.txt          Dependencias Python (pip install -r)
├── README.md                 Instalación y uso rápido
├── main.py                   Entrada: watcher / --check / --file / --dry-run
│
├── doc/                      Esta documentación
│
├── config/
│   └── settings.py           Lee .env, rutas, lista de SPOTS
│
├── core/
│   ├── watcher.py            Vigila Hand_Review/<SPOT>/, espera a que el archivo
│   │                         termine de sincronizar, procesa pendientes al arrancar
│   ├── ocr.py                Saca el nº de mano: 1º del nombre del archivo,
│   │                         2º por OCR del título "PokerStars Hand #XXXX"
│   ├── pt4_connector.py      Busca la mano en PT4 por hand_no: historial, nota, tags
│   ├── note_parser.py        Convierte la nota XML (richtext) de PT4 a texto
│   ├── hh_parser.py          Del historial: modalidad, stake (NL25), posición hero
│   ├── ai_analyzer.py        Prompt + apuntes del spot → Ollama → <SPOT>/<hand_id>.txt
│   ├── library_uploader.py   POST a api_upload.php (409 = ya subida)
│   ├── state.py              SQLite con lo ya procesado (no repite)
│   └── pipeline.py           Orquesta los pasos para UNA captura
│
├── knowledge_base/           Tus apuntes, 1 archivo por spot (mismo nombre)
│   ├── global_rules.md
│   ├── 3BetPots.md  BlindWar.md  DudaSize.md  ErrorGrave.md
│   └── ManosTopValue.md  OOP.md  Review.md  vsRECRE.md
│
├── server/
│   └── config_api.example.php  Plantilla del token (config_api.php va solo al servidor)
│   (api_upload.php vive en el repo poker_library, junto a upload.php)
│
├── tests/
│   └── test_parsers.py       Tests de OCR-regex, notas XML e historial
│
└── logs/
    └── pipeline.log          Registro de cada mano procesada / errores
```

## 3. Flujo (pipeline)

1. Juegas, etiquetas la mano en PT4 y escribes la DUDA en la nota de mano.
2. Abres la mano en el replayer de PT4 y haces una captura que INCLUYA el título
   de la ventana (`Playback for PokerStars Hand #262289151822`).
   Truco infalible: nombrar el archivo con el nº de mano (`262289151822.png`).
3. Guardas la captura en `Hand_Review/<SPOT>/`.
4. `watcher.py` detecta el archivo y espera a que termine de escribirse.
5. `ocr.py` obtiene el nº de mano (nombre del archivo > OCR).
6. `pt4_connector.py` consulta PostgreSQL:
   - `cash_hand_summary.hand_no` → `id_hand`, fecha
   - `cash_hand_histories` → historial en texto
   - `notes` (`id_x = id_hand`) → tu duda (XML → texto)
   - `tags` + `lookup_tags` → tags de PT4
7. `hh_parser.py` calcula modalidad, stake y posición.
8. `ai_analyzer.py` envía a Ollama: `global_rules.md` + `<SPOT>.md` + historial + duda.
   Devuelve: resumen, decisión clave, veredicto, explicación, alternativa y
   regla de apuntes aplicada. Sin EV ni números inventados.
   Se guarda en `Hand_Review/<SPOT>/<hand_id>.txt`, junto a la captura. **No se sube.**
9. `library_uploader.py` hace POST a `api_upload.php` con la imagen y los campos
   (sin el análisis de IA).
10. `api_upload.php` valida el token, rechaza duplicados (`hand_id`), guarda la
    imagen en `uploads/`, inserta en `manos_review` y enlaza la categoría.
11. La mano aparece en `BUSCADORV2.html`. Revisas el `.txt`; si el análisis te
    sirve, lo pegas en el buscador. La CORRECCIÓN la escribes tú a mano.

## 4. Seguridad

- `api_upload.php` solo acepta peticiones con `X-Api-Token` correcto (`hash_equals`).
- El token vive en `.env` (local) y `config_api.php` (servidor). Ninguno va a GitHub.
- Validación de imagen (extensión + `getimagesize` + máx. 15 MB) y consultas
  preparadas (mysqli, igual que el resto de la web).
- Variedad, subtipo y categorías deben existir; `api_upload.php` NO los crea.
- Transacción: si falla el INSERT se borra la imagen subida.
