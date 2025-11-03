@echo off
chcp 65001 > nul
echo Starting MQTT Scanner API Service...
cd /d "E:\Kerja 2\mqttpunyafile\mqttpunyafile\mqtt-scanner"
set PYTHONIOENCODING=utf-8
python app.py