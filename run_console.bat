@echo off
chcp 65001 >nul
title 速成輸入法
cd /d "%~dp0"
python -m quick_input
pause
