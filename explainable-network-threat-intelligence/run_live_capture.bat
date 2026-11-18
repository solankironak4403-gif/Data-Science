@echo off
title ThreatIntel - Automated Live Traffic Capture
color 0E
echo ============================================================
echo   Starting Automated Live Traffic Capture & Detection Engine
echo ============================================================
echo.
cd /d "%~dp0"
backend\venv\Scripts\python src/capture.py
pause

