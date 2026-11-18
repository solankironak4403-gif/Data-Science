@echo off
title ThreatIntel - FastAPI Backend Server
color 0A
echo ============================================================
echo   Starting Explainable Threat Intelligence System Backend
echo   URL: http://127.0.0.1:8000
echo   Docs: http://127.0.0.1:8000/docs
echo ============================================================
echo.
cd /d "%~dp0backend"
venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
pause

