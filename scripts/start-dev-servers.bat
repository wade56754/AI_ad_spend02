@echo off
REM 启动前后端开发服务器
REM 用途: 快速启动完整的开发环境

echo ========================================
echo 启动开发服务器
echo ========================================
echo.

REM 检查是否在正确的目录
if not exist "backend\main.py" (
    echo 错误: 请在项目根目录运行此脚本
    pause
    exit /b 1
)

echo [1/2] 启动后端服务 (端口 8000)...
start "Backend Server" cmd /k "cd backend && python -m uvicorn backend.main:app --reload --port 8000"

echo [2/2] 等待2秒后启动前端服务...
timeout /t 2 /nobreak >nul

echo [2/2] 启动前端服务 (端口 3000)...
start "Frontend Server" cmd /k "cd frontend && pnpm run dev"

echo.
echo ========================================
echo ✅ 开发服务器启动完成
echo ========================================
echo.
echo 前端: http://localhost:3000
echo 后端: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
echo 按任意键打开浏览器...
pause >nul

start http://localhost:3000

echo.
echo 提示: 关闭此窗口不会停止服务器
echo 如需停止服务器,请手动关闭对应的命令行窗口
echo.
