#!/bin/bash
# ============================================================
# Download Olist Brazilian E-Commerce Dataset from Kaggle
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data/olist"

echo "============================================"
echo "Descargando dataset Olist desde Kaggle..."
echo "============================================"

mkdir -p "$DATA_DIR"

cd "$DATA_DIR"

kaggle datasets download -d olistbr/brazilian-ecommerce

unzip -o brazilian-ecommerce.zip -d .

rm brazilian-ecommerce.zip

echo ""
echo "============================================"
echo "Dataset descargado exitosamente!"
echo "============================================"
echo ""
echo "Archivos disponibles:"
ls -la "$DATA_DIR"/*.csv 2>/dev/null || ls -la "$DATA_DIR"/
