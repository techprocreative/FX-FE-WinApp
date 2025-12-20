@echo off
REM ============================================
REM NexusTrade Windows Connector - Complete Build
REM Guaranteed build without TensorFlow hook conflicts
REM ============================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================
echo     NexusTrade Complete Build Script
echo ============================================
echo.

REM Step 1: Activate venv
echo [1/7] Activating virtual environment...
if not exist "venv" (
    echo [ERROR] Virtual environment not found!
    echo Run: python -m venv venv
    goto :error
)
call venv\Scripts\activate.bat
echo       Done.

REM Step 2: Remove TensorFlow completely
echo [2/7] Removing TensorFlow/Keras packages...
pip uninstall tensorflow tensorflow-intel tensorflow-cpu tensorflow-gpu keras -y 2>nul
echo       Done.

REM Step 3: Disable TensorFlow hook in pyinstaller-hooks-contrib
echo [3/7] Disabling problematic TensorFlow PyInstaller hook...
set "HOOKS_DIR=venv\Lib\site-packages\_pyinstaller_hooks_contrib\pre_safe_import_module"
if exist "%HOOKS_DIR%\hook-tensorflow.py" (
    REM Backup original hook
    if not exist "%HOOKS_DIR%\hook-tensorflow.py.bak" (
        copy "%HOOKS_DIR%\hook-tensorflow.py" "%HOOKS_DIR%\hook-tensorflow.py.bak" >nul
    )
    REM Replace with empty hook
    (
        echo # Disabled TensorFlow hook - tensorflow is excluded from build
        echo def pre_safe_import_module^(api^):
        echo     pass
    ) > "%HOOKS_DIR%\hook-tensorflow.py"
    echo       TensorFlow hook disabled.
) else (
    echo       TensorFlow hook not found (OK).
)
echo       Done.

REM Step 4: Clean build artifacts
echo [4/7] Cleaning build artifacts...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul
echo       Done.

REM Step 5: Ensure hooks directory exists
echo [5/7] Setting up custom hooks...
if not exist "hooks" mkdir hooks
if not exist "hooks\pre_safe_import_module" mkdir hooks\pre_safe_import_module

REM Create empty tensorflow hook in our custom hooks
(
    echo # Empty TensorFlow hook - tensorflow excluded from build
    echo def pre_safe_import_module^(api^):
    echo     pass
) > "hooks\pre_safe_import_module\hook-tensorflow.py"
echo       Done.

REM Step 6: Build
echo [6/7] Building executable...
echo.
pyinstaller nexustrade.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build failed!
    goto :error
)

REM Step 7: Verify
echo [7/7] Verifying build...
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
    echo   To run:   double-click dist\NexusTrade.exe
    echo.
    echo ============================================
    goto :end
) else (
    echo [ERROR] EXE not found after build!
    goto :error
)

:error
echo.
echo ============================================
echo           BUILD FAILED
echo ============================================
echo Check the output above for errors.
echo.
pause
exit /b 1

:end
echo.
pause
exit /b 0
