@echo off
chcp 65001 >nul
title 速成輸入法 - 打包為 EXE

echo ══════════════════════════════════════════════
echo   速成輸入法 - 打包為獨立執行檔 (.exe)
echo ══════════════════════════════════════════════
echo.

:: 檢查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] 未偵測到 Python
    pause
    exit /b 1
)

:: 安裝 PyInstaller
echo [1/3] 安裝 PyInstaller...
pip install pyinstaller >nul 2>&1
echo       完成
echo.

:: 打包
echo [2/3] 正在打包...
cd /d "%~dp0"
pyinstaller --noconfirm --onefile --windowed ^
    --name "QuickInput" ^
    --add-data "quick_input/quick_dict.py;quick_input" ^
    --hidden-import "quick_input" ^
    --hidden-import "quick_input.main" ^
    --hidden-import "quick_input.engine" ^
    --hidden-import "quick_input.candidate_window" ^
    --hidden-import "quick_input.keyboard_hook" ^
    --hidden-import "quick_input.config" ^
    --hidden-import "quick_input.quick_dict" ^
    run_exe.py

if %errorlevel% neq 0 (
    echo [錯誤] 打包失敗
    pause
    exit /b 1
)

echo.
echo [3/3] 打包完成！
echo.
echo   執行檔位置: dist\QuickInput.exe
echo   可將 QuickInput.exe 複製到任意位置使用
echo.
pause
