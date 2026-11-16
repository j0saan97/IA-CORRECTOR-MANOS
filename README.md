# IA Corrector de Manos (Poker Coach IA local)

Guarda una captura de PT4 en `Hand_Review/<SPOT>/` y la mano aparece en
buscar.poker-library.com con imagen, historial, duda, categoría y pre-análisis de IA local.

Ver [ARQUITECTURA.txt](ARQUITECTURA.txt) para el diseño completo.

## Instalación rápida
1. Python 3.11+, Tesseract OCR y Ollama (`ollama pull qwen2.5:7b`).
2. `pip install -r requirements.txt`
3. Copiar `.env.example` a `.env` y rellenar.

## Uso
```
python main.py --check                     # comprueba conexiones
python main.py --file RUTA.png --dry-run   # procesa una captura sin subir
python main.py --file RUTA.png             # procesa y sube
python main.py                             # modo vigilancia
```
