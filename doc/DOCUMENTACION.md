# Documentación técnica

## Uso

```
python main.py --check                     # comprueba conexiones (PT4, Tesseract, Ollama, token)
python main.py --file RUTA.png --dry-run   # procesa una captura sin subir
python main.py --file RUTA.png             # procesa y sube
python main.py                             # modo vigilancia (Fase 5)
python -m pytest                           # tests
```

### Cómo preparar una captura

1. Etiqueta la mano en PT4 con el tag del spot y escribe la duda en la nota de mano.
   **Cierra la ventana de notas**: PT4 solo guarda la nota al cerrarla.
2. Abre la mano en el replayer y haz la captura incluyendo el título de la ventana,
   o nombra el archivo con el nº de mano (`262289151822.png`).
3. Guárdala en `Hand_Review/<SPOT>/`.

## Configuración (`.env`)

Copiar [../.env.example](../.env.example) como `.env`. Nunca subir `.env` a GitHub.

| Variable | Uso |
|----------|-----|
| `HAND_REVIEW_DIR` | Carpeta raíz con una subcarpeta por spot |
| `TESSERACT_CMD` | Ruta a `tesseract.exe` |
| `PT4_DB_HOST`, `PT4_DB_PORT`, `PT4_DB_NAME`, `PT4_DB_USER`, `PT4_DB_PASSWORD` | PostgreSQL de PT4 |
| `PT4_HAND_ENUM_TYPE` | `enum_type` de notas/tags de mano (`H`) |
| `OLLAMA_URL`, `OLLAMA_MODEL` | Servidor y modelo de Ollama |
| `API_UPLOAD_URL` | Endpoint `api_upload.php` (ahora dev) |
| `API_TOKEN` | Token, igual que en `config_api.php` del servidor |
| `HERO_ALIAS` | Nick con el que apareces en la web (`users_hand_review`) |
| `DEFAULT_TIPO_RIVAL` | `Desconocido (Default)`, `Fish`, `Reg Agresivo`, `Nit`, `Whale / Ballena`, `Loco-Maniatico`, `Pagón` |

## Mapeo de datos (PT4 / local → MySQL `manos_review`)

| Origen | Columna MySQL |
|--------|---------------|
| nº de mano (OCR / nombre de archivo) | `hand_id` (NUEVA, UNIQUE) |
| carpeta del archivo (= spot) | `mano_categorias` (por id, ver tabla abajo) |
| fijo `NoLimitHoldem` (ENUM) | `modalidad` |
| fijo `CASH_GAME` | `variedad_id` (se busca por nombre) |
| historial: Zoom/Fast → `ZOOM`; si no `6Max - SIN ANTE` / `9max - SIN ANTE` (CON ANTE si hay ante) | `subtipo_id` (se busca por nombre) |
| historial → `parse_stake` (NL20, NL25) | `nivel_stake` |
| historial → `parse_position` | `posicion` (SB BB UTG MP HJ CO BTN, igual que la web) |
| `.env` `DEFAULT_TIPO_RIVAL` | `tipo_rival` |
| `.env` `HERO_ALIAS` | `jugador_alias` |
| nota de mano PT4 | `duda` |
| no se envía (es el "Describe la mano" de drag&drop) | `narracionMano` (queda NULL) |
| historial completo | solo local: parseo + prompt de la IA |
| respuesta de Ollama | no se envía: se guarda en `Hand_Review/<SPOT>/<hand_id>.txt`. La columna `analisis_ia` existe pero queda NULL |
| imagen | `ruta_imagen` (solo el nombre; la web antepone `uploads/`) |
| manual en el buscador | `correccion` |
| `'pendiente'` | `estado_revision` |
| automático | `fecha_registro` |

### Spot (carpeta) → categoría web (id)

En la BD las categorías ya se llaman como los spots (confirmado 16/11/2026).

| Spot | id |
|------|----|
| ErrorGrave | 1 |
| ManosTopValue | 2 |
| 3BetPots | 5 |
| vsRECRE | 6 |
| DudaSize | 8 |
| BlindWar | 10 (nueva) |
| OOP | 11 (nueva) |
| Review | 12 (nueva) |

## Servidor

- `api_upload.php` vive en el repo **poker_library**, junto a `upload.php`, y reutiliza `db_connect.php`.
- `config_api.php` (con el token) se sube a mano por cPanel; está excluido de git y del FTP.
  Plantilla: [../server/config_api.example.php](../server/config_api.example.php).
- Respuesta 409 = la mano ya existe (`hand_id` duplicado).

### Migración MySQL

Ya aplicada en dev (el archivo se eliminó del repo; se deja aquí como referencia):

```sql
ALTER TABLE manos_review
    ADD COLUMN hand_id VARCHAR(32) NULL,
    ADD COLUMN analisis_ia TEXT NULL,
    ADD UNIQUE KEY uq_manos_review_hand_id (hand_id);

INSERT IGNORE INTO categorias (id, nombre) VALUES
    (10, 'BlindWar'), (11, 'OOP'), (12, 'Review');
```
