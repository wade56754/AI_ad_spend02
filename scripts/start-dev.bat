@echo off
title AI广告代投系统开发环境

echo 🚀 启动AI广告代投系统开发环境...

REM 检查Python环境
echo 📋 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装，请先安装Python 3.11+
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do echo ✅ %%i

REM 检查Node.js环境
echo 📋 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js未安装，请先安装Node.js 18+
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do echo ✅ Node.js版本: %%i
for /f "tokens=*" %%i in ('npm --version') do echo ✅ npm版本: %%i

REM 设置端口
set BACKEND_PORT=8001
set FRONTEND_PORT=3002

REM 检查并停止现有服务
echo 📋 检查端口占用情况...
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find "python.exe" >nul
if not errorlevel 1 (
    echo ⚠️  发现Python进程，尝试停止...
    taskkill /F /IM python.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
)

tasklist /FI "IMAGENAME eq node.exe" 2>nul | find "node.exe" >nul
if not errorlevel 1 (
    echo ⚠️  发现Node.js进程，尝试停止...
    taskkill /F /IM node.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
)

REM 创建日志目录
if not exist logs mkdir logs

REM 启动后端服务
echo 🔧 启动后端服务...
cd backend

REM 检查虚拟环境
if not exist venv (
    echo 📦 创建Python虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境并安装依赖
call venv\Scripts\activate

echo 📦 检查Python依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo 📦 安装Python依赖...
    pip install fastapi uvicorn python-multipart
)

echo 🚀 启动FastAPI后端服务 (端口: %BACKEND_PORT%)...
start /B python simple_backend.py

REM 等待后端启动
echo ⏳ 等待后端服务启动...
timeout /t 3 /nobreak >nul

REM 测试后端健康检查
curl -s http://localhost:%BACKEND_PORT%/health >nul 2>&1
if errorlevel 1 (
    echo ❌ 后端服务启动失败，请检查错误信息
    pause
    exit /b 1
)

echo ✅ 后端服务启动成功

REM 返回项目根目录
cd ..

REM 启动前端服务
echo 🎨 启动前端服务...
cd frontend

REM 检查依赖
if not exist node_modules (
    echo 📦 安装前端依赖...
    npm install
)

REM 检查环境变量文件
if not exist .env.local (
    echo 📝 创建前端环境变量文件...
    (
        echo NEXT_PUBLIC_API_URL=http://localhost:%BACKEND_PORT%
        echo NEXT_PUBLIC_WS_URL=ws://localhost:%BACKEND_PORT%/ws
        echo NEXT_PUBLIC_APP_NAME=AI广告代投系统
        echo NEXT_PUBLIC_VERSION=2.1.0
        echo NODE_ENV=development
    ) > .env.local
)

echo 🚀 启动Next.js前端服务 (端口: %FRONTEND_PORT%)...
start /B npx next dev --port %FRONTEND_PORT%

REM 等待前端启动
echo ⏳ 等待前端服务启动...
timeout /t 5 /nobreak >nul

REM 返回项目根目录
cd ..

echo.
echo 🎉 开发环境启动成功！
echo.
echo 📊 服务地址：
echo    后端API: http://localhost:%BACKEND_PORT%
echo    前端应用: http://localhost:%FRONTEND_PORT%
echo    API文档: http://localhost:%BACKEND_PORT%/docs
echo.
echo 📝 日志文件：
echo    后端日志: logs\backend.log
echo    前端日志: logs\frontend.log
echo.
echo 🛑 停止服务：
echo    scripts\stop-dev.bat
echo.
echo 🧪 测试连接：
echo    curl http://localhost:%BACKEND_PORT%/health
echo.

echo 按任意键停止所有服务...
pause >nul

echo 🛑 正在停止服务...

REM 停止所有Python和Node.js进程
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1

echo ✅ 所有服务已停止
timeout /t 2 /nobreak >nul