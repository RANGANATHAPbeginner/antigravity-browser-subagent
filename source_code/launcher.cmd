@echo off
setlocal enabledelayedexpansion

:: Real Google Chrome binary (High-DPI, crisp consumer branding, zero "TEST" watermark)
set "CHROME_BIN=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME_BIN%" (
    set "CHROME_BIN=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
)

:: Isolated pristine sandbox profile (Completely separate from personal Chrome User Data)
set "PROFILE=C:\Users\super\.gemini\browser-agent-profile"
if not exist "%PROFILE%" (
    mkdir "%PROFILE%" >nul 2>&1
)

set "URL_FILE=%PROFILE%\target_url.txt"
set "TARGET_URL=chrome://newtab"

if not "%~1"=="" (
    set "TARGET_URL=%~1"
) else if exist "%URL_FILE%" (
    set /p TARGET_URL=<"%URL_FILE%"
    del "%URL_FILE%" >nul 2>&1
)

:: Launch with isolation flags (No artificial bubble suppression - clean natural Chrome behavior)
start "" "%CHROME_BIN%" --remote-debugging-port=9222 --start-maximized --no-first-run --no-default-browser-check --disable-sync --disable-background-mode --user-data-dir="%PROFILE%" "!TARGET_URL!"
