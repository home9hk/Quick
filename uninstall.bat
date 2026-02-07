@echo off
chcp 65001 >nul
title 速成輸入法 - 解除安裝

echo ══════════════════════════════════════════════
echo   速成輸入法 - 解除安裝
echo ══════════════════════════════════════════════
echo.

set SHORTCUT_PATH=%USERPROFILE%\Desktop\速成輸入法.bat
set START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\速成輸入法

if exist "%SHORTCUT_PATH%" (
    del "%SHORTCUT_PATH%"
    echo   已移除桌面捷徑
)

if exist "%START_MENU%" (
    rmdir /s /q "%START_MENU%"
    echo   已移除開始功能表項目
)

echo.
echo   解除安裝完成。
echo   程式檔案保留在目前資料夾中，可手動刪除。
echo.
pause
