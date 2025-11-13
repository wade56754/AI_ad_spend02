@echo off
title 停止AI广告代投系统开发环境

echo 🛑 停止AI广告代投系统开发环境...

echo 🧹 清理Python进程...
taskkill /F /IM python.exe >nul 2>&1

echo 🧹 清理Node.js进程...
taskkill /F /IM node.exe >nul 2>&1

echo.
echo ✅ 所有服务已停止
echo.

timeout /t 2 /nobreak >nul