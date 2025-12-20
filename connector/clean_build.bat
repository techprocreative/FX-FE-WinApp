@echo off
REM ============================================
REM NexusTrade Clean Build
REM Remove old build artifacts and rebuild
REM ============================================

cd /d "%~dp0"

echo ============================================
echo       NexusTrade Clean Build
echo ============================================
echo.

echo [1/4] Removing build and dist folders...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo       Done.

echo [2/4] Removing ALL __pycache__ folders recursively...
for /d /r %%d in (__pycache__) do @if exist "%%d" (
    echo       Removing: %%d
    rmdir /s /q "%%d"
)
echo       Done.

echo [3/4] Removing all .pyc files...
del /s /q *.pyc 2>nul
echo       Done.

echo [4/4] Removing PyInstaller temp files...
if exist "*.spec.bak" del /q *.spec.bak 2>nul
echo       Done.

echo.
echo ============================================
echo    Clean complete! Starting fresh build...
echo ============================================
echo.

call build.bat
