---
description: "重启开发服务: 停止并重新启动前后端服务"
argument-hint: "[backend|frontend|all]"
---

# 重启开发服务

停止现有进程并重新启动前端和后端开发服务器。

## 参数

用户输入: `$ARGUMENTS`

支持的参数:
- `backend` / `be`: 仅重启后端 (FastAPI on port 8000)
- `frontend` / `fe`: 仅重启前端 (Next.js on port 3000)
- `all` / 空: 重启前后端 (默认)

## 工作流程

### Step 1: 停止现有进程

#### Windows 平台

```bash
# 停止后端 (端口 8000)
taskkill /F /IM python.exe /FI "WINDOWTITLE eq uvicorn*" 2>nul
netstat -ano | findstr :8000 | for /f "tokens=5" %a in ('more') do taskkill /F /PID %a 2>nul

# 停止前端 (端口 3000)
taskkill /F /IM node.exe /FI "WINDOWTITLE eq next*" 2>nul
netstat -ano | findstr :3000 | for /f "tokens=5" %a in ('more') do taskkill /F /PID %a 2>nul
```

#### macOS/Linux 平台

```bash
# 停止后端
lsof -ti:8000 | xargs kill -9 2>/dev/null

# 停止前端
lsof -ti:3000 | xargs kill -9 2>/dev/null
```

### Step 2: 启动服务 (后台运行)

#### 后端启动

工作目录: `D:\project\AI_ad_spend02\backend`

```bash
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

#### 前端启动

工作目录: `D:\project\AI_ad_spend02\frontend`

```bash
npm run dev
```

### Step 3: 健康检查

等待服务启动后验证:

```bash
# 后端健康检查
curl http://localhost:8000/api/v1/health

# 前端检查
curl http://localhost:3000
```

## 示例

```bash
# 重启所有服务
/restart

# 仅重启后端
/restart backend

# 仅重启前端
/restart frontend
```

## 端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端 (FastAPI) | 8000 | API 服务 |
| 前端 (Next.js) | 3000 | Web 应用 |

## 注意事项

- 服务以后台模式启动，日志输出到任务文件
- 使用 `/tasks` 查看运行中的后台任务
- 前端通过 Next.js rewrites 代理 API 请求到后端
- 确保 `.env` 文件配置正确
