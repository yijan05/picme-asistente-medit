#!/usr/bin/env bash
# Descarga el modelo de MediaPipe Face Landmarker (468 puntos 3D).
# Se ejecuta UNA sola vez en cada máquina donde se vaya a correr PicMe.
#
# El archivo no viaja en el repositorio porque es un binario de varios MB
# distribuido por Google (no por MediaPipe vía pip); descargarlo aparte
# es el flujo oficial recomendado por la propia documentación de
# MediaPipe Tasks.
set -euo pipefail

MODEL_URL="https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
DEST_DIR="$(dirname "$0")/models"
DEST_FILE="$DEST_DIR/face_landmarker.task"

mkdir -p "$DEST_DIR"

if [ -f "$DEST_FILE" ]; then
    echo "El modelo ya existe en $DEST_FILE — no se vuelve a descargar."
    echo "(Si quieres forzar la descarga de nuevo, borra ese archivo y vuelve a correr este script.)"
    exit 0
fi

echo "Descargando modelo de MediaPipe FaceLandmarker..."
if command -v curl >/dev/null 2>&1; then
    curl -L --fail -o "$DEST_FILE" "$MODEL_URL"
elif command -v wget >/dev/null 2>&1; then
    wget -O "$DEST_FILE" "$MODEL_URL"
else
    echo "No se encontró curl ni wget. Descarga manualmente desde:"
    echo "  $MODEL_URL"
    echo "y guárdalo en: $DEST_FILE"
    exit 1
fi

echo "Listo: modelo guardado en $DEST_FILE"
