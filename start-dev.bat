@echo off
echo ====================================
echo AI广告代投系统 - 开发环境启动脚本
echo ====================================

echo [1/4] 清理环境变量冲突...
set ALLOWED_ORIGINS=
set DATABASE_URL=
set JWT_SECRET=
set SUPABASE_URL=

echo [2/4] 启动后端服务...
cd /d "%~dp0backend"
start "FastAPI Backend" cmd /k "unset ALLOWED_ORIGINS && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo [3/4] 等待后端启动...
timeout /t 5 /nobreak > nul

echo [4/4] 启动前端服务...
cd /d "%~dp0frontend"
start "Next.js Frontend" cmd /k "npm run dev"

echo.
echo ====================================
echo ✅ 系统启动完成！
echo 📡 后端API: http://localhost:8000
echo 🌐 前端界面: http://localhost:3000
echo 📚 API文档: http://localhost:8000/docs
echo ====================================
pause