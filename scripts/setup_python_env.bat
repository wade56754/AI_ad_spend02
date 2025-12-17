@echo off
REM AI 广告代投系统 - Python 环境配置脚本
REM 运行方式: scripts\setup_python_env.bat

echo ============================================
echo   AI 广告代投系统 - Python 环境配置
echo ============================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 未安装或不在 PATH 中
    echo.
    echo 请安装 Python 3.11+:
    echo   1. 访问 https://www.python.org/downloads/
    echo   2. 下载 Python 3.11 或更高版本
    echo   3. 安装时勾选 "Add Python to PATH"
    echo   4. 重新运行此脚本
    echo.
    pause
    exit /b 1
)

echo [OK] Python 已安装:
python --version
echo.

REM 检查 pip
pip --version >nul 2>&1
if errorlevel 1 (
    REM 尝试使用 python -m pip
    python -m pip --version >nul 2>&1
    if errorlevel 1 (
        echo [错误] pip 未安装
        echo 请运行: python -m ensurepip
        pause
        exit /b 1
    ) else (
        echo [OK] pip 可通过 python -m pip 访问
    )
)

REM 创建虚拟环境
echo [1/4] 创建虚拟环境...
if exist .venv (
    echo      虚拟环境已存在，跳过创建
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo      虚拟环境创建成功: .venv
)
echo.

REM 激活虚拟环境
echo [2/4] 激活虚拟环境...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 激活虚拟环境失败
    pause
    exit /b 1
)
echo      激活成功
echo.

REM 升级 pip
echo [3/4] 升级 pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo [警告] pip 升级失败，继续...
)
echo.

REM 安装依赖
echo [4/4] 安装项目依赖...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [警告] 部分依赖安装失败，继续安装其他依赖...
)

REM 安装代码工厂依赖
echo.
echo [额外] 安装代码工厂依赖...
if exist agents\requirements.txt (
    python -m pip install -r agents\requirements.txt
    if errorlevel 1 (
        echo [警告] 代码工厂依赖安装失败
    )
) else (
    echo [警告] agents\requirements.txt 不存在，跳过代码工厂依赖安装
)
echo.

echo ============================================
echo   环境配置完成!
echo ============================================
echo.
echo 激活虚拟环境:
echo   .venv\Scripts\activate
echo.
echo 运行代码工厂测试:
echo   python agents\skills\test_code_factory.py
echo.
pause
