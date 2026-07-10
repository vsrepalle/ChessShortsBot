@echo off
echo ========================================
echo    ChessShorts Creator - Build EXE
echo ========================================

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing PyInstaller...
pip install pyinstaller

echo Building executable...
pyinstaller --onefile --windowed --name ChessShortsCreator ^
    --add-data "assets;assets" ^
    --hidden-import=streamlit ^
    --hidden-import=chess ^
    app.py

echo.
echo Build Complete!
echo Executable: dist\ChessShortsCreator.exe
pause
