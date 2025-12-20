@echo off
REM ============================================
REM NexusTrade Windows Connector - Build Script
REM Easy deployment for Windows VPS
REM
REM This script:
REM - Sets up Python virtual environment
REM - Installs all dependencies
REM - Cleans old build cache (NEW!)
REM - Builds NexusTrade.exe with PyInstaller
REM
REM IMPORTANT: Always run this for clean builds
REM to ensure UI changes are included!
REM ============================================

setlocal enabledelayedexpansion

echo.
echo  _   _                     _____              _      
echo ^| ^| ^| ^|                   ^|_   _^|            ^| ^|     
echo ^| ^|_^| ^| _____  ___   _ ___  ^| ^| _ __ __ _  __^| ^| ___ 
echo ^|  _  ^|/ _ \ \/ / ^| ^| / __^| ^| ^|^| '__/ _` ^|/ _` ^|/ _ \
echo ^| ^| ^| ^|  __/^>  ^<^| ^|_^| \__ \ ^| ^|^| ^| ^| (_^| ^| (_^| ^|  __/
echo \_^| ^|_/\___/_/\_\\__,_^|___/ \_/^|_^|  \__,_^|\__,_^|\___^|
echo.
echo ============================================
echo          Windows Connector Build
echo ============================================
echo.

REM Set paths
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

REM Check Python
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.12+ from python.org
    goto :error
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo       Python %PYVER% found

REM Check/Create venv
echo [2/6] Setting up virtual environment...
if not exist "venv" (
    echo       Creating new venv...
    python -m venv venv
    if errorlevel 1 goto :error
)
call venv\Scripts\activate.bat
echo       Virtual environment activated

REM Install dependencies
echo [3/6] Installing dependencies (this may take a while)...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    goto :error
)
echo       Dependencies installed

REM Install PyInstaller
echo [4/6] Installing PyInstaller...
python -m pip install pyinstaller
if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller
    goto :error
)
echo       PyInstaller ready

REM Clean build artifacts and cache
echo [4.5/6] Cleaning old build artifacts and cache...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul
echo       Build cache cleaned

REM Create assets folder
if not exist "assets" mkdir assets

REM Build EXE
echo [5/6] Building EXE (this may take a few minutes)...
echo.
pyinstaller nexustrade.spec --clean --noconfirm
if errorlevel 1 (
    echo [ERROR] Build failed!
    goto :error
)

REM Verify build
echo [6/6] Verifying build...
if exist "dist\NexusTrade.exe" (
    for %%A in ("dist\NexusTrade.exe") do set "FILESIZE=%%~zA"
    set /a "FILESIZE_MB=!FILESIZE!/1048576"
    echo.
    echo ============================================
    echo           BUILD SUCCESS!
    echo ============================================
    echo.
    echo   Output:   dist\NexusTrade.exe
    echo   Size:     !FILESIZE_MB! MB
    echo.
    echo   To run:   dist\NexusTrade.exe
    echo.
    echo ============================================
    goto :end
) else (
    echo [ERROR] EXE not found after build
    goto :error
)

:error
echo.
echo ============================================
echo           BUILD FAILED!
echo ============================================
echo Check the output above for errors.
echo.
pause
exit /b 1

:end
echo Build completed successfully!
pause
exit /b 0
