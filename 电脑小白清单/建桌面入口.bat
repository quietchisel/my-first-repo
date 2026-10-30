@echo off
title Build desktop shortcuts
setlocal
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0?????.ps1"
pause
