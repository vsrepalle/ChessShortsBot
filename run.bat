@echo off
echo ========================================
echo    ChessShorts Creator - Launcher
echo ========================================

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting ChessShorts Creator...
streamlit run app.py

pause
