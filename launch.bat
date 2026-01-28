@echo off
cd /d "%~dp0"

echo ========================================
echo    Voice Transcriber - Starting...
echo ========================================
echo.

REM Check if packages need installing
pip show customtkinter >nul 2>&1
if %errorlevel% neq 0 (
    echo First run detected - installing packages...
    echo This may take a few minutes...
    echo.
    pip install -r requirements.txt
    echo.
    echo Packages installed!
    echo.
)

echo Launching Voice Transcriber...
echo (First transcription downloads the AI model - be patient!)
echo.
python recorder.py

if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo ERROR: Something went wrong.
    echo Make sure Python is installed.
    echo ========================================
)
pause
