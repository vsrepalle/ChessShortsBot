@echo off
echo ========================================
echo    ChessShorts Bot - Watcher Launcher
echo ========================================

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting Watcher...
python watch.py

pause
