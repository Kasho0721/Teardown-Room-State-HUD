@echo off
setlocal enabledelayedexpansion
cd /d %~dp0\..

set "ROOT=%cd%"
set "PY=%ROOT%\.venv312\Scripts\python.exe"
set "DIST_DIR=%ROOT%\run_bridge.dist"
set "DIST_OLD=%ROOT%\run_bridge.dist.old"
set "BUILD_DIR=%ROOT%\run_bridge.build"
set "EXE_PATH=%DIST_DIR%\run_bridge.exe"
set "ZIP_PATH=%ROOT%\dist\run_bridge-dist.zip"
set "README_DST=%DIST_DIR%\README.txt"

echo [1/8] Checking Python 3.12 environment...
if not exist "%PY%" (
  echo ERROR: venv not found: %PY%
  echo Please create it first: /c/Users/18621/AppData/Local/Programs/Python/Python312/python.exe -m venv .venv312
  exit /b 1
)

"%PY%" --version || exit /b 1
"%PY%" -m nuitka --version || exit /b 1

echo.
echo [2/8] Stopping old running release process if needed...
taskkill /F /IM run_bridge.exe >nul 2>nul

echo.
echo [3/8] Cleaning old build artifacts...
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%ZIP_PATH%" del /f /q "%ZIP_PATH%"
if exist "%DIST_OLD%" rmdir /s /q "%DIST_OLD%"

echo.
echo [4/8] Preparing release directory...
if exist "%DIST_DIR%" (
  move "%DIST_DIR%" "%DIST_OLD%" >nul
  if errorlevel 1 (
    echo ERROR: Failed to move old dist directory. It is probably still locked by another process.
    exit /b 1
  )
)
if not exist "%ROOT%\dist" mkdir "%ROOT%\dist"

echo.
echo [5/8] Building standalone with Nuitka + Zig...
"%PY%" -m nuitka ^
  --mode=standalone ^
  --disable-ccache ^
  --assume-yes-for-downloads ^
  --zig ^
  --remove-output ^
  --include-package=agent ^
  --include-data-files=web\webui.html=webui.html ^
  --include-data-files=web\ui.html=ui.html ^
  --include-data-files=bridge_config.json=bridge_config.json ^
  run_bridge.py
if errorlevel 1 (
  echo.
  echo ERROR: Nuitka build failed.
  exit /b 1
)

echo.
echo [6/8] Verifying release files...
if not exist "%EXE_PATH%" (
  echo ERROR: Missing executable: %EXE_PATH%
  exit /b 1
)
if not exist "%DIST_DIR%\webui.html" (
  echo ERROR: Missing webui.html in release directory.
  exit /b 1
)
if not exist "%DIST_DIR%\ui.html" (
  echo ERROR: Missing ui.html in release directory.
  exit /b 1
)
if not exist "%DIST_DIR%\bridge_config.json" (
  echo ERROR: Missing bridge_config.json in release directory.
  exit /b 1
)

echo.
echo [7/8] Copying release notes...
if exist "%ROOT%\README.txt" copy /y "%ROOT%\README.txt" "%README_DST%" >nul

echo.
echo [8/8] Creating zip package...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path '%DIST_DIR%\*' -DestinationPath '%ZIP_PATH%' -Force"
if errorlevel 1 (
  echo ERROR: Failed to create zip package.
  exit /b 1
)

echo.
echo Release complete.
echo EXE : %EXE_PATH%
echo ZIP : %ZIP_PATH%
echo DIR : %DIST_DIR%
if exist "%DIST_OLD%" echo OLD : %DIST_OLD%
exit /b 0
