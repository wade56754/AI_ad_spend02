@echo off
:: Playwright MCP 配置助手
:: 此脚本将帮助您配置 Playwright MCP Server

echo ========================================
echo Playwright MCP 配置助手
echo ========================================
echo.

:: 检查 node 和 npm 是否安装
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未找到 Node.js，请先安装 Node.js
    pause
    exit /b 1
)

echo [√] Node.js 已安装

:: 安装 Playwright 浏览器驱动
echo.
echo 正在安装 Playwright 浏览器驱动...
call npx -y playwright install

if %ERRORLEVEL% NEQ 0 (
    echo [错误] Playwright 浏览器驱动安装失败
    pause
    exit /b 1
)

echo [√] Playwright 浏览器驱动安装完成

:: 更新 MCP 配置
echo.
echo 正在更新 MCP 配置...
call python update_mcp_config.py

if %ERRORLEVEL% NEQ 0 (
    echo [错误] MCP 配置更新失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo [√] 配置完成!
echo ========================================
echo.
echo 下一步:
echo 1. 重启 Claude Desktop 或重新加载 Claude Code
echo 2. Playwright MCP 工具将自动可用
echo 3. 可以开始使用 MCP 执行浏览器自动化任务
echo.
echo 已更新的配置:
echo - .mcp.json (项目配置)
echo - %USERPROFILE%\.mcp.json (用户配置)
echo.

pause


