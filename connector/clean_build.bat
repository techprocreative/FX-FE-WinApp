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

echo [1/5] Activating virtual environment...
call venv\Scripts\activate.bat
echo       Done.

echo [2/5] Removing TensorFlow (prevents PyInstaller hook conflict)...
pip uninstall tensorflow keras tensorflow-intel -y 2>nul
echo       Done.

echo [3/5] Removing build and dist folders...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo       Done.

echo [4/5] Removing ALL __pycache__ folders recursively...
for /d /r %%d in (__pycache__) do @if exist "%%d" (
    rmdir /s /q "%%d"
)
del /s /q *.pyc 2>nul
echo       Done.

echo [5/5] Removing PyInstaller temp files...
if exist "*.spec.bak" del /q *.spec.bak 2>nul
echo       Done.

echo.
echo ============================================
echo    Clean complete! Starting fresh build...
echo ============================================
echo.

call build.bat
