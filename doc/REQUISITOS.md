# Requisitos

## Requisitos funcionales

| ID | Requisito | Estado |
|----|-----------|--------|
| RF-01 | Detectar capturas nuevas en `Hand_Review/<SPOT>/` sin intervención del usuario | Hecho (`python main.py`; arranque con Windows pendiente) |
| RF-02 | Obtener el nº de mano del nombre del archivo o, si no, por OCR del título del replayer | Hecho |
| RF-03 | Soportar PokerStars (v1). Winamax y Yatahay ya están en el código, pero se validarán en versiones posteriores | Hecho (PokerStars por validar con mano real) |
| RF-04 | Leer de PT4 el historial, la nota de mano (duda) y los tags | Hecho |
| RF-05 | Calcular modalidad, stake, subtipo (ZOOM / 6Max / 9max, CON/SIN ANTE) y posición del hero | Hecho |
| RF-06 | La categoría de la web es la carpeta del spot | Hecho |
| RF-07 | Generar un pre-análisis con IA local usando los apuntes del spot, sin EV ni números inventados, y guardarlo en `<SPOT>/<hand_id>.txt` (no se sube; lo valida el usuario) | Pendiente (Fase 4) |
| RF-08 | Subir la mano a poker-library.com (imagen + campos) con token | Hecho |
| RF-09 | No subir dos veces la misma mano (estado local + `hand_id` UNIQUE / 409) | Hecho |
| RF-10 | ~~Mostrar `analisis_ia` en el modal del buscador~~ | Descartado: el análisis lo pega el usuario a mano |
| RF-11 | Modo `--dry-run` que procesa sin subir y `--check` que valida conexiones | Hecho |
| RF-12 | Registrar cada mano procesada y los errores en `logs/pipeline.log` | Hecho |

## Requisitos no funcionales

- **Privacidad:** el análisis de IA se hace en local (Ollama); no se envían manos a servicios externos de IA.
- **Seguridad:** token fuera de git (`.env` y `config_api.php`); ver [ARQUITECTURA.md](ARQUITECTURA.md#4-seguridad).
- **Fiabilidad:** el watcher debe esperar a que el archivo termine de sincronizar (Google Drive) y procesar pendientes al arrancar.
- **Compatibilidad web:** los valores enviados deben coincidir con los de la web (posiciones, stakes, subtipos, categorías por id).

## Requisitos de software

| Software | Versión instalada | Notas |
|----------|-------------------|-------|
| Python | 3.14.2 | Mínimo 3.11 |
| Tesseract OCR | 5.5.3 | Instalador UB-Mannheim |
| Ollama | — | Modelo `qwen2.5:7b` |
| PokerTracker 4 | — | PostgreSQL local |

Dependencias Python en [../requirements.txt](../requirements.txt) (se queda en la raíz porque
`pip install -r requirements.txt` lo busca ahí):
`watchdog`, `pytesseract`, `Pillow`, `psycopg2-binary`, `requests`, `python-dotenv`, `pytest`.

## Requisitos de hardware

- `qwen2.5:7b` necesita ~6 GB de VRAM. Con CPU funciona, pero lento. **Pendiente de verificar en tu equipo.**
