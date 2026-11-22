# Investigación, problemas y decisiones

Registro de lo que se ha comprobado, los problemas encontrados y por qué se decidió cada cosa.
Añadir aquí cada nuevo problema con fecha, síntoma, causa y solución.

## Verificaciones en el equipo

- [x] Tabla del historial en PT4: `cash_hand_histories (id_hand, history)`. Existe.
- [x] Valor de `enum_type` para notas y tags de mano: `'H'`.
- [x] Los 8 spots coinciden con los tags de mano de PT4 (`lookup_tags`).
- [x] `ruta_imagen`: `upload.php` guarda solo el nombre del archivo (la web pone `uploads/`).
- [x] Variedad `CASH_GAME` y subtipos por nombre (`6Max - SIN ANTE`, `ZOOM`...).
  Sacado de `datos_maestros.sql` y `drag-and_dropV4.html` del repo poker_library.
- [x] Formato de `posicion`: SB, BB, UTG, MP, HJ, CO, BTN (coincide con `hh_parser`).
- [x] La web usa mysqli, no PDO. `api_upload.php` reutiliza `db_connect.php`.
- [ ] Gráfica: `qwen2.5:7b` necesita ~6 GB de VRAM (con CPU funciona, pero lento).

## Salas en PT4

PT4 tiene 3 salas y el código de `hh_parser.py` soporta las tres. **v1: solo se valida
PokerStars.** Winamax y Yatahay se validarán en versiones posteriores (no se bloquean en el código).

| Sala | Nick |
|------|------|
| PokerStars | y0saN |
| Winamax | y0saan23 |
| Yatahay | AutoY0saaN |

- **Winamax:** el nº `#23193082-973-...` se guarda en PT4 como `hand_no` `23193082000973`.
- **Posición:** validada contra la de PT4 en las 56.115 manos del hero: 0 errores.
- **Fechas:** PT4 guarda `date_played` en UTC; se convierte a hora local.

## Decisiones

| Fecha | Decisión | Motivo |
|-------|----------|--------|
| 15/11/2026 | IA de texto (`qwen2.5:7b`), sin modelo de visión | El historial de PT4 ya es exacto; leer la imagen solo añade errores |
| 15/11/2026 | Nº de mano: primero el nombre del archivo, luego OCR | El nombre es infalible; el OCR depende de que se vea el título |
| 15/11/2026 | watchdog con `PollingObserver` | Los eventos nativos no son fiables en la unidad de Google Drive |
| 16/11/2026 | Nuevas categorías 10 BlindWar, 11 OOP, 12 Review y nivel NL20 en la web | Faltaban spots y stake de Winamax |
| 16/11/2026 | Carpetas en local (`Desktop/Hand_Review`) | Sincronización de Google Drive en pausa |
| 16/11/2026 | Eliminados `server/api_upload.php` y `server/migration.sql` de este repo | El endpoint vive en poker_library; la migración ya está aplicada |
| 22/11/2026 | El análisis de IA se guarda en `<SPOT>/<hand_id>.txt` y NO se sube a la web | El usuario valida el análisis y lo pega a mano en el buscador si le sirve |
| 22/11/2026 | El spot se decide por la carpeta; el tag de PT4 solo genera un aviso si no coincide | La carpeta siempre existe (hace falta para guardar la captura); el tag puede olvidarse. Ver [DOCUMENTACION.md](DOCUMENTACION.md#spot-carpeta-tag-y-nota-de-pt4) |
| 22/11/2026 | v1 solo valida PokerStars; Winamax y Yatahay quedan en el código sin bloquear | Acotar las pruebas; las otras salas llegan en versiones posteriores |

## Problemas encontrados

### narracionMano
- **Síntoma:** el historial completo de PT4 aparecía como "descripción" en el buscador.
- **Causa:** se enviaba el historial en `narracionMano`, que en realidad es el texto
  "Describe la mano..." que el usuario escribe en `drag-and_dropV4.html`.
- **Solución (16/11/2026):** ya no se envía; queda NULL y el buscador no muestra la línea.
  Pendiente limpiar la mano de prueba id 42 en dev (ver [FASES.md](FASES.md#fase-3--subida-real-de-una-mano)).

### La duda sale vacía
- **Causa:** PT4 solo guarda la nota de mano al CERRAR la ventana de notas.
- **Solución:** cerrar la ventana de notas antes de guardar la captura.

### Nota y tag puestos en otra mano (22/11/2026)
- **Síntoma:** la captura salía "sin nota" y sin tag aunque se habían puesto en PT4.
- **Causa:** se pusieron en la mano 262442102849, pero la captura era de la 262416268488.
  El script busca nota y tag **por nº de mano**. Además, la ventana de notas de la captura
  se quedó abierta y esa nota nunca se guardó.
- **Solución:** la nota y el tag tienen que estar en la MISMA mano que sale en el título
  del replayer, y hay que cerrar la ventana de notas. Comprobar con `--dry-run`.

### Ollama: error CUDA con la GTX 1050 Ti (22/11/2026)
- **Síntoma:** `500` de Ollama: `CUDA error: the provided PTX was compiled with an unsupported toolchain`.
- **Causa:** driver NVIDIA 560.94 demasiado antiguo para Ollama 0.40.17.
- **Solución temporal:** `OLLAMA_NUM_GPU=0` en `.env` (solo CPU): ~80-95 s por mano.
- **Solución real:** actualizar el driver NVIDIA y quitar `OLLAMA_NUM_GPU`. Aun así la GPU
  tiene 4 GB y `qwen2.5:7b` pide ~6 GB: irá repartido GPU/CPU.

### Calidad del análisis con qwen2.5:7b (22/11/2026)
Prueba con la mano 262442102849 (A♥Q♥ UTG, check-raise all-in en flop A♦Q♦2♦ contra 22):
1. **Historial en bruto:** se inventó "ases y reyes" y un all-in en el river.
2. **Con resumen calculado (`hh_summary`):** cartas y acciones bien, pero situó la decisión
   en el turn y juzgó por el resultado ("Error" porque el rival tenía trío).
3. **Sin showdown + reglas más estrictas:** volvió a inventar cartas (Q♠A♠) y acciones.

Conclusión: un 7B en CPU no razona bien manos de póker aunque reciba los datos exactos.
El resumen exacto de la mano (sin IA) sí es fiable y se guarda siempre en el `.txt`.
Opciones pendientes de decidir: apuntes completos + modelo local mayor (lento en este PC),
o IA en la nube (mucho mejor razonamiento, coste por mano, la mano sale del PC).
Estas capturas se movieron a `Hand_Review/_archivo/` el 22/11/2026.
- `PokerTracker4_1ueqqVFO2g.png`: sin nº de mano legible → renombrar con el nº.
- `buenraise-allin.flop.png`: la mano 262215195727 no está en la BD de PT4 actual.
- `mejor-fold.png`: falta el tag ManosTopValue en PT4 (solo tiene Review).

### Login de revisor en el buscador no deja comentar (abierto)
- Código y endpoints (`auth.php` / `comentario.php`) correctos y sin cambios.
- **Por revisar:** que el usuario exista en `users_hand_review` con `user_type = 'top_reg'` en la BD de dev.
