@echo off
title Universal Multi-Agent LangGraph Platform
echo ====================================================================
echo Starting Universal Multi-Agent Platform (Ports 8550, 8050, 8080)...
echo ====================================================================

set PYTHON_EXE=C:\Users\panka\.gemini\antigravity\scratch\ocr_multiagent_system\venv_ocr\Scripts\python.exe

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Virtual environment Python not found at: %PYTHON_EXE%
    pause
    exit /b 1
)

cd /d "%~dp0"
"%PYTHON_EXE%" run_platform.py %*
pause
