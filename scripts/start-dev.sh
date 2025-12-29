#!/bin/bash

echo "===================================="
echo "AI广告代投系统 - 开发环境启动脚本"
echo "===================================="

echo "[1/4] 清理环境变量冲突..."
unset ALLOWED_ORIGINS
unset DATABASE_URL
unset JWT_SECRET
unset SUPABASE_URL

echo "[2/4] 启动后端服务..."
cd backend
unset ALLOWED_ORIGINS && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo "[3/4] 等待后端启动..."
sleep 5

echo "[4/4] 启动前端服务..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "===================================="
echo "✅ 系统启动完成！"
echo "📡 后端API: http://localhost:8000"
echo "🌐 前端界面: http://localhost:3000"
echo "📚 API文档: http://localhost:8000/docs"
echo ""
echo "停止服务请运行: kill $BACKEND_PID $FRONTEND_PID"
echo "===================================="

# 等待用户输入来停止脚本
read -p "按回车键停止服务..."
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
echo "服务已停止"