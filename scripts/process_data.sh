#!/bin/bash
set -e
echo "DEBUG: Script inicializa con argumento: $@" >> /app/reports/process_data_debug.log
if [ $# -ne 1 ]; then
    echo "ERROR: Se requiere solo un argumento " >> /app/reports/process_data_debug.log
    exit 1
fi
FILE="$1"
echo "DEBUG: Procesando: $FILE" >> /app/reports/process_data_debug.log
if [ ! -f "$FILE" ]; then
    echo "ERROR:  $FILE no existe" >> /app/reports/process_data_debug.log
    exit 1
fi
echo "$(date -u +'%Y-%m-%d %H:%M:%S') - Procesando: $FILE" >> /app/reports/processed_files.log
cat "$FILE" >> /app/reports/processed_files.log
echo "DEBUG: Proceso exitoso" >> /app/reports/process_data_debug.log