@echo off
cd /d "%~dp0"

REM Activate the virtualenv if present
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"

REM Load .env if present
if exist ".env" (
    for /f "usebackq tokens=1,2 delims==" %%A in (".env") do (
        set "%%A=%%B"
    )
)

if "%HOST%"=="" set HOST=127.0.0.1
if "%PORT%"=="" set PORT=8000

REM IMPORTANT: use server.py, not raw uvicorn, so Windows + Playwright works.
python server.py
