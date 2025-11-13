#!/bin/bash

# AI广告代投系统开发环境启动脚本
# 用于快速启动前后端开发环境

echo "🚀 启动AI广告代投系统开发环境..."

# 检查Python环境
echo "📋 检查Python环境..."
if ! command -v python &> /dev/null; then
    echo "❌ Python未安装，请先安装Python 3.11+"
    exit 1
fi

echo "✅ Python版本: $(python --version)"

# 检查Node.js环境
echo "📋 检查Node.js环境..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js未安装，请先安装Node.js 18+"
    exit 1
fi

echo "✅ Node.js版本: $(node --version)"
echo "✅ npm版本: $(npm --version)"

# 检查端口占用情况
echo "📋 检查端口占用情况..."

BACKEND_PORT=8001
FRONTEND_PORT=3002

if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口 $BACKEND_PORT 已被占用，尝试停止现有服务..."
    pkill -f "python.*simple_backend.py" || true
    sleep 2
fi

if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口 $FRONTEND_PORT 已被占用，尝试停止现有服务..."
    pkill -f "next.*dev" || true
    sleep 2
fi

# 启动后端服务
echo "🔧 启动后端服务..."
cd backend

# 检查依赖
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python -m venv venv
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate 2>/dev/null || venv\\Scripts\\activate 2>/dev/null

if [ ! -f "venv/_pyversion" ] || [ "$(cat venv/_pyversion)" != "$(python --version)" ]; then
    echo "📦 安装Python依赖..."
    pip install -q fastapi uvicorn python-multipart
    python --version > venv/_pyversion
fi

# 启动后端
echo "🚀 启动FastAPI后端服务 (端口: $BACKEND_PORT)..."
nohup python simple_backend.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "后端PID: $BACKEND_PID"

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 3

# 测试后端健康检查
if curl -s http://localhost:$BACKEND_PORT/health > /dev/null; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败，请检查日志: logs/backend.log"
    exit 1
fi

# 返回项目根目录
cd ..

# 启动前端服务
echo "🎨 启动前端服务..."
cd frontend

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 检查环境变量文件
if [ ! -f ".env.local" ]; then
    echo "📝 创建前端环境变量文件..."
    cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:$BACKEND_PORT
NEXT_PUBLIC_WS_URL=ws://localhost:$BACKEND_PORT/ws
NEXT_PUBLIC_APP_NAME=AI广告代投系统
NEXT_PUBLIC_VERSION=2.1.0
NODE_ENV=development
EOF
fi

# 启动前端
echo "🚀 启动Next.js前端服务 (端口: $FRONTEND_PORT)..."
nohup npx next dev --port $FRONTEND_PORT > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端PID: $FRONTEND_PID"

# 等待前端启动
echo "⏳ 等待前端服务启动..."
sleep 5

# 返回项目根目录
cd ..

# 创建日志目录
mkdir -p logs

# 保存进程ID
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo ""
echo "🎉 开发环境启动成功！"
echo ""
echo "📊 服务地址："
echo "   后端API: http://localhost:$BACKEND_PORT"
echo "   前端应用: http://localhost:$FRONTEND_PORT"
echo "   API文档: http://localhost:$BACKEND_PORT/docs"
echo ""
echo "📝 日志文件："
echo "   后端日志: logs/backend.log"
echo "   前端日志: logs/frontend.log"
echo ""
echo "🛑 停止服务："
echo "   ./scripts/stop-dev.sh"
echo ""
echo "🧪 测试连接："
echo "   curl http://localhost:$BACKEND_PORT/health"
echo ""

# 等待用户输入
echo "按 Ctrl+C 停止所有服务..."
trap 'echo "🛑 正在停止服务..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit' INT
wait