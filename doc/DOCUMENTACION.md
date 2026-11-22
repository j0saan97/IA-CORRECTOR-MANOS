# Documentación técnica

## Uso

```
python main.py --check                     # comprueba conexiones (PT4, Tesseract, Ollama, token)
python main.py --file RUTA.png --dry-run   # procesa una captura sin subir
python main.py --file RUTA.png             # procesa y sube
python main.py                             # modo vigilancia: sube solo lo que guardes
python main.py --dry-run                   # vigilancia sin subir (para probar)
python -m pytest                           # tests
```

### Modo vigilancia (watcher)

- **Solo funciona mientras `python main.py` está abierto.** Si lo cierras, las capturas
  nuevas se quedan pendientes y se suben la próxima vez que arranque.
- Mira `Hand_Review/<SPOT>/` cada 5 s. Solo imágenes (`.png .jpg .jpeg .bmp .webp`)
  directamente dentro de una carpeta de spot: ignora `.txt`, subcarpetas y carpetas
  que no son spots (p. ej. `Hand_Review/_archivo/`, donde se guardan las capturas viejas).
- Espera a que el archivo deje de cambiar 3 s antes de procesarlo (captura o sync de Drive).
- Al arrancar procesa todo lo que no esté subido. Las capturas con error se reintentan
  en cada arranque (es normal ver el mismo error en el log hasta arreglarlas o apartarlas).
- Una mano ya subida no se repite: `state.db` por archivo y 409 del servidor por `hand_id`.
- Todo queda en `logs/pipeline.log`.

### Arranque automático con Windows

Tarea programada **IA-Corrector-Manos**: al iniciar sesión (con 1 min de retraso para que
arranquen PT4/PostgreSQL y la red) lanza `pythonw.exe main.py`, **sin ventana**. Si se cae,
Windows lo reintenta 3 veces (cada 1 min). Al no haber ventana, para ver qué hace se mira
`logs/pipeline.log`.

```
powershell -ExecutionPolicy Bypass -File scripts\arranque_windows.ps1           # instalar
powershell -ExecutionPolicy Bypass -File scripts\arranque_windows.ps1 -Quitar   # quitar
Get-ScheduledTask -TaskName IA-Corrector-Manos                                  # estado
Stop-ScheduledTask  -TaskName IA-Corrector-Manos                                # parar ahora
Start-ScheduledTask -TaskName IA-Corrector-Manos                                # arrancar ahora
```

Si quieres usar `python main.py` en una consola (para ver la salida), para antes la tarea.
Si los dos corren a la vez no se duplican manos (el servidor responde 409), pero el log sale doble.

Si una captura falla porque PT4 aún no ha importado la mano o PostgreSQL no estaba
arrancado, se reintenta en el siguiente arranque (o con `Stop`/`Start-ScheduledTask`).

### Cómo preparar una captura

1. Etiqueta la mano en PT4 con el tag del spot y escribe la duda en la nota de mano.
   **Cierra la ventana de notas**: PT4 solo guarda la nota al cerrarla.
2. Abre la mano en el replayer y haz la captura incluyendo el título de la ventana,
   o nombra el archivo con el nº de mano (`262289151822.png`).
3. Guárdala en `Hand_Review/<SPOT>/`.

### Spot: carpeta, tag y nota de PT4

| Dato | ¿Obligatorio? | Para qué se usa |
|------|---------------|-----------------|
| **Carpeta** `Hand_Review/<SPOT>/` | **Sí** | Es lo ÚNICO que decide el spot y la categoría de la web. |
| **Tag de PT4** (mismo nombre que la carpeta) | No, pero recomendado | Solo se compara con la carpeta: si no coincide, sale el aviso `(!) la mano no tiene el tag '<SPOT>' en PT4`. No se envía a la web. |
| **Nota de mano de PT4** | **Sí** (en la práctica) | Es la `duda` que aparece en la web y lo que leerá la IA (Fase 4). Sin nota la mano se sube con la duda vacía. |

Por qué conviene poner el tag aunque no sea obligatorio:

- **Filtros en PT4:** permite sacar todas las manos de un spot en PT4 y ver sus stats sin depender de las capturas.
- **Control de errores:** si la captura acaba en la carpeta equivocada, el aviso lo detecta. Sin tag no hay con qué comparar.
- **Futuro:** si algún día se procesan manos directamente desde PT4 (sin captura), el tag será lo único que indique el spot.

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

## Entornos web (repo poker_library)

| Entorno | Rama | Subir manos (drag & drop) | Buscar manos |
|---------|------|---------------------------|--------------|
| **DEV** (pruebas) | `dev` | https://dev.poker-library.com/drag-and_dropV4.html | https://dev.poker-library.com/BUSCADORV2.html |
| **PRODUCCIÓN** | `main` | por confirmar | por confirmar (buscar.poker-library.com) |

- Endpoint del script en DEV: `https://dev.poker-library.com/api_upload.php` (`API_UPLOAD_URL` en `.env`).
- Ahora mismo el watcher sube a **DEV**: las manos subidas aparecen en el buscador de DEV.
- Deploy: cada push a `dev` o `main` del repo poker_library se sube por FTP con GitHub Actions
  (`dev` → carpeta `poker-library-dev/`, `main` → `poker-library/`). Tarda 1-2 min.
- Repo local: `C:\Users\Administrador\Desktop\poker_library` (lista de URLs también en su `urls-dev.txt`).
- **No hay entorno localhost:** el PC no tiene PHP ni MySQL y la base de datos solo existe
  en BanaHosting. Para probar cambios de la web se hace push a `dev` y se mira en DEV.

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
