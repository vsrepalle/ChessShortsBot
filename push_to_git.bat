@echo off
title Push ChessShortsBot to GitHub

echo ===================================================
echo        ChessShortsBot Git Push Utility
echo ===================================================
echo.

REM Change to the folder where this BAT file exists
cd /d "%~dp0"

REM Check if Git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo Git is not installed or not available in PATH.
    pause
    exit /b 1
)

REM Initialize repository if needed
if not exist ".git" (
    echo Initializing Git repository...
    git init
)

REM Configure remote
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo Adding remote origin...
    git remote add origin https://github.com/vsrepalle/ChessShortsBot.git
) else (
    echo Updating remote origin...
    git remote set-url origin https://github.com/vsrepalle/ChessShortsBot.git
)

echo.
echo Adding files...
git add .

echo.
set /p msg=Enter Commit Message: 
if "%msg%"=="" set msg=Project Update

echo.
echo Committing...
git commit -m "%msg%"

echo.
echo Detecting default branch...

git branch --show-current > branch.tmp
set /p BRANCH=<branch.tmp
del branch.tmp

if "%BRANCH%"=="" (
    set BRANCH=main
    git branch -M main
)

echo.
echo Pushing to GitHub...
git push -u origin %BRANCH%

echo.
echo ===================================================
echo Done!
echo ===================================================
pause