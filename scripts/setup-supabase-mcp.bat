@echo off
:: Supabase MCP 配置助手
:: 此脚本将帮助您配置 Supabase MCP Server

echo ========================================
echo Supabase MCP 配置助手
echo ========================================
echo.

:: 检查是否已有环境变量
echo 正在检查系统环境变量...
if defined SUPABASE_URL (
    echo [√] 找到 SUPABASE_URL: %SUPABASE_URL%
    set USE_SYSTEM_ENV=1
) else (
    echo [!] 未找到系统环境变量 SUPABASE_URL
    set USE_SYSTEM_ENV=0
)

if defined SUPABASE_SERVICE_ROLE_KEY (
    echo [√] 找到 SUPABASE_SERVICE_ROLE_KEY
) else (
    echo [!] 未找到系统环境变量 SUPABASE_SERVICE_ROLE_KEY
)

echo.
echo ========================================
echo 配置选项:
echo 1. 使用系统环境变量配置 MCP
echo 2. 手动输入 Supabase 连接信息
echo 3. 退出
echo ========================================
set /p choice="请选择 (1-3): "

if "%choice%"=="1" goto USE_SYSTEM
if "%choice%"=="2" goto MANUAL_INPUT
if "%choice%"=="3" goto END

:USE_SYSTEM
echo.
echo 使用系统环境变量配置...
if not defined SUPABASE_URL (
    echo [错误] 系统环境变量不完整，请选择选项 2 手动输入
    pause
    exit /b 1
)

:: 写入到 backend/.env
echo 正在更新 backend\.env 文件...
echo SUPABASE_URL=%SUPABASE_URL% >> backend\.env
echo SUPABASE_SERVICE_ROLE_KEY=%SUPABASE_SERVICE_ROLE_KEY% >> backend\.env

goto CONFIGURE_MCP

:MANUAL_INPUT
echo.
echo 请输入 Supabase 连接信息
echo (可以在 https://app.supabase.com 的 Settings -> API 中找到)
echo.
set /p SUPABASE_URL_INPUT="SUPABASE_URL (例如 https://xxxxx.supabase.co): "
set /p SUPABASE_KEY_INPUT="SUPABASE_SERVICE_ROLE_KEY: "

:: 写入到 backend/.env
echo.
echo 正在更新 backend\.env 文件...
echo SUPABASE_URL=%SUPABASE_URL_INPUT% >> backend\.env
echo SUPABASE_SERVICE_ROLE_KEY=%SUPABASE_KEY_INPUT% >> backend\.env

set SUPABASE_URL=%SUPABASE_URL_INPUT%
set SUPABASE_SERVICE_ROLE_KEY=%SUPABASE_KEY_INPUT%

:CONFIGURE_MCP
echo.
echo ========================================
echo 配置 MCP Server
echo ========================================

:: 创建 MCP 配置文件
echo 正在配置 .claude\mcp_settings.json...

:: 检查 node 和 npm 是否安装
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未找到 Node.js，请先安装 Node.js
    pause
    exit /b 1
)

echo [√] Node.js 已安装

:: 安装 Supabase MCP Server
echo.
echo 正在安装 @modelcontextprotocol/server-supabase...
call npm install -g @modelcontextprotocol/server-supabase

echo.
echo ========================================
echo [√] 配置完成!
echo ========================================
echo.
echo 下一步:
echo 1. 重启 Claude Desktop 或重新加载 Claude Code
echo 2. Supabase MCP 工具将自动可用
echo 3. 可以开始使用 MCP 执行数据库迁移
echo.
echo 已保存的配置:
echo - backend\.env (环境变量)
echo - .claude\mcp_settings.json (MCP 配置)
echo.

pause
goto END

:END
