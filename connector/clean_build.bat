@echo off
REM ============================================
REM NexusTrade Clean Build
REM Remove old build artifacts and rebuild
REM ============================================

cd /d "%~dp0"

echo Cleaning old build files...

if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "__pycache__" rmdir /s /q __pycache__

echo Clean complete. Starting fresh build...
echo.

call build.bat
