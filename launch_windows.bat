@echo off
setlocal
cd /d "%~dp0"
title Interview Assist - Local Server

echo.
echo ====================================================
echo    INTERVIEW ASSIST  ^|  Windows Launcher
echo ====================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Setting up Python virtual environment...
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )
    if errorlevel 1 (
        echo ERROR: Python 3.10 or later must be installed.
        echo Install Python from https://www.python.org/downloads/
        echo Tick "Add Python to PATH" when installing.
        pause
        exit /b 1
    )
)

if not exist ".env" (
    echo [2/3] Creating local .env configuration...
    copy /y ".env.example" ".env" >nul
)

REM On first launch, ask for a NEW key without echoing typed characters.
REM The key is stored only on this computer, not in any distributed file.
".venv\Scripts\python.exe" setup_api_key.py
if errorlevel 1 (
    echo API key setup was not completed. You can rerun the launcher.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -c "import fastapi, uvicorn, httpx, dotenv, docx, pypdf, multipart" >nul 2>nul
if errorlevel 1 (
    echo [3/3] Installing Python packages (first run only)...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Package installation failed. Check internet access.
        pause
        exit /b 1
    )
)

echo.
echo -----------------------------------------------
echo Open this link in Chrome or Edge:
echo.
echo     http://127.0.0.1:8765
echo.
echo Keep THIS window open while using the bot.
echo Press CTRL+C to stop the server.
echo -----------------------------------------------
echo.
".venv\Scripts\python.exe" -m uvicorn server.main:app --host 127.0.0.1 --port 8765
if errorlevel 1 (
    echo.
    echo The server stopped with an error. A second running copy
    echo or another program using port 8765 may be responsible.
    pause
)
endlocal
