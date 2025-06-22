#!/bin/bash
set -e
echo "DEBUG: Script started with args: $@" >> /app/reports/process_data_debug.log
if [ $# -ne 1 ]; then
    echo "ERROR: Exactly one file argument required" >> /app/reports/process_data_debug.log
    exit 1
fi
FILE="$1"
echo "DEBUG: Processing file: $FILE" >> /app/reports/process_data_debug.log
if [ ! -f "$FILE" ]; then
    echo "ERROR: File $FILE does not exist" >> /app/reports/process_data_debug.log
    exit 1
fi
echo "$(date -u +'%Y-%m-%d %H:%M:%S') - Processing file: $FILE" >> /app/reports/processed_files.log
cat "$FILE" >> /app/reports/processed_files.log
echo "DEBUG: File processed successfully" >> /app/reports/process_data_debug.log