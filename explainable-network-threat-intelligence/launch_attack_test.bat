@echo off
title ThreatIntel - Live Attack Simulator
color 0C
echo ============================================================
echo   Transmitting Real Live TCP SYN PortScan Attack Packets
echo ============================================================
echo.
cd /d "%~dp0"
backend\venv\Scripts\python src/launch_live_attack.py
pause

