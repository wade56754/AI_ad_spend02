@echo off
setlocal EnableDelayedExpansion

REM ============================================================================
REM ai-ad-agents MCP Server 启动脚本
REM
REM 功能: 一键启动 AI_ad_spend02 项目的 ai-ad-agents MCP Server
REM 用法: 双击此脚本，或在命令行中执行
REM
REM 参考文档: docs/dev/LOCAL_ENV_BASELINE_AI_AD_SPEND02_v1.0.md
REM ============================================================================

REM ----- 1. 计算项目根目录 -----
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%\.."
set "PROJECT_ROOT=%CD%"
echo [INFO] 项目根目录: %PROJECT_ROOT%

REM ----- 2. 检查虚拟环境是否存在 -----
if not exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" (
    echo [ERROR] 未找到 Python 虚拟环境: %PROJECT_ROOT%\.venv\
    echo [ERROR] 请先创建虚拟环境: python -m venv .venv
    echo [ERROR] 然后安装依赖: pip install -r requirements.txt
    popd
    endlocal
    pause
    exit /b 1
)
echo [INFO] 虚拟环境已找到: %PROJECT_ROOT%\.venv\

REM ----- 3. 检查 agent_platform 模块是否可导入 -----
"%PROJECT_ROOT%\.venv\Scripts\python.exe" -c "import agent_platform.mcp.server" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] 无法导入 agent_platform.mcp.server 模块
    echo [ERROR] 请检查依赖是否已安装: pip install -r requirements.txt
    popd
    endlocal
    pause
    exit /b 1
)
echo [INFO] agent_platform 模块检查通过

REM ----- 4. 设置 MCP 模式环境变量 -----
set "AGENT_PLATFORM_MODE=mcp"
echo [INFO] 环境变量 AGENT_PLATFORM_MODE=%AGENT_PLATFORM_MODE%

REM ----- 5. 启动 MCP Server -----
echo [INFO] 正在启动 ai-ad-agents MCP Server...
echo [INFO] 日志将输出到 stderr（不干扰 MCP 协议）
echo ============================================================================
"%PROJECT_ROOT%\.venv\Scripts\python.exe" -m agent_platform.mcp.server

REM ----- 6. 退出处理 -----
set "EXIT_CODE=%ERRORLEVEL%"
echo ============================================================================
if %EXIT_CODE% equ 0 (
    echo [INFO] MCP Server 正常退出
) else (
    echo [WARN] MCP Server 退出码: %EXIT_CODE%
)

popd
endlocal
pause
