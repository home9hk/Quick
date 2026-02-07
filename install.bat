@echo off
chcp 65001 >nul
title 速成輸入法 - 安裝程式

echo ══════════════════════════════════════════════
echo   速成輸入法 Quick Input Method - 安裝程式
echo ══════════════════════════════════════════════
echo.

:: 檢查 Python 是否已安裝
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] 未偵測到 Python，請先安裝 Python 3.8 或以上版本。
    echo 下載地址: https://www.python.org/downloads/
    echo.
    echo 安裝 Python 時請勾選 "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/4] Python 已偵測到：
python --version
echo.

:: 檢查 tkinter 是否可用
echo [2/4] 檢查 tkinter...
python -c "import tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] tkinter 未安裝。
    echo 請重新安裝 Python 並勾選 "tcl/tk and IDLE" 選項。
    pause
    exit /b 1
)
echo       tkinter 可用
echo.

:: 建立桌面捷徑
echo [3/4] 建立桌面捷徑...
set SCRIPT_DIR=%~dp0
set SHORTCUT_PATH=%USERPROFILE%\Desktop\速成輸入法.bat

(
    echo @echo off
    echo chcp 65001 ^>nul
    echo cd /d "%SCRIPT_DIR%"
    echo start /min pythonw -m quick_input
) > "%SHORTCUT_PATH%"

echo       捷徑已建立: %SHORTCUT_PATH%
echo.

:: 建立開始功能表捷徑
echo [4/4] 建立開始功能表項目...
set START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs
if not exist "%START_MENU%\速成輸入法" mkdir "%START_MENU%\速成輸入法"

(
    echo @echo off
    echo chcp 65001 ^>nul
    echo cd /d "%SCRIPT_DIR%"
    echo start /min pythonw -m quick_input
) > "%START_MENU%\速成輸入法\速成輸入法.bat"

echo       開始功能表項目已建立
echo.

echo ══════════════════════════════════════════════
echo   安裝完成！
echo ══════════════════════════════════════════════
echo.
echo   啟動方式：
echo     1. 雙擊桌面上的「速成輸入法」捷徑
echo     2. 或在命令列執行: python -m quick_input
echo     3. 或雙擊 run.bat
echo.
echo   使用方式：
echo     Ctrl+Space  切換中/英文模式
echo     a-y         輸入速成碼
echo     1-9         選擇候選字
echo     Space       選擇第一個候選字
echo.
echo   選字視窗可以用滑鼠在邊界位置拖曳來放大和縮小
echo.
pause
