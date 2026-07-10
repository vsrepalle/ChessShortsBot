@echo off
echo ==========================================
echo Creating ChessShortsBot Stage 1 Structure
echo ==========================================

:: Root folders
mkdir assets 2>nul
mkdir config 2>nul
mkdir logs 2>nul
mkdir temp 2>nul
mkdir output 2>nul

:: Inputs
mkdir inputs 2>nul
mkdir inputs\pending 2>nul
mkdir inputs\pending\brochures 2>nul
mkdir inputs\pending\pgn 2>nul
mkdir inputs\archive 2>nul
mkdir inputs\archive\brochures 2>nul
mkdir inputs\archive\pgn 2>nul

:: Output
mkdir output\videos 2>nul
mkdir output\thumbnails 2>nul
mkdir output\metadata 2>nul

:: Assets
mkdir assets\audio 2>nul
mkdir assets\fonts 2>nul
mkdir assets\backgrounds 2>nul
mkdir assets\logos 2>nul

:: Source
mkdir src 2>nul

mkdir src\core 2>nul
mkdir src\processors 2>nul
mkdir src\renderers 2>nul
mkdir src\watchers 2>nul
mkdir src\ocr 2>nul
mkdir src\utils 2>nul

:: Python packages
type nul > src\__init__.py
type nul > src\core\__init__.py
type nul > src\processors\__init__.py
type nul > src\renderers\__init__.py
type nul > src\watchers\__init__.py
type nul > src\ocr\__init__.py
type nul > src\utils\__init__.py

echo.
echo Stage 1 folder structure created.
pause