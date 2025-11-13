# Claude + Bolt.new 协调开发指南

## 🎯 概述

本指南详细说明如何在AI广告代投系统开发中，实现Claude（后端）与Bolt.new（前端）的高效协调开发模式。

## 🔄 开发工作流程

### 1. 分工策略

#### Claude负责（后端）
- ✅ FastAPI应用开发
- ✅ 数据库设计和迁移
- ✅ API接口实现
- ✅ 业务逻辑开发
- ✅ 认证授权系统
- ✅ 数据验证和错误处理
- ✅ WebSocket实时服务
- ✅ 单元测试和集成测试

#### Bolt.new负责（前端）
- ✅ Next.js应用开发
- ✅ UI组件实现
- ✅ 页面路由和布局
- ✅ 状态管理（React Query）
- ✅ 用户交互逻辑
- ✅ 数据可视化
- ✅ 响应式设计
- ✅ E2E测试

### 2. 协调流程图

```mermaid
sequenceDiagram
    participant PM as 项目管理
    participant Claude as Claude(后端)
    participant Bolt as Bolt.new(前端)
    participant API as API文档

    PM->>Claude: 后端需求说明
    PM->>Bolt: 前端需求说明

    Claude->>API: 生成OpenAPI规范
    API->>Bolt: 同步API文档

    Bolt->>Claude: 确认接口设计
    Claude->>Bolt: 确认设计OK

    par 并行开发
        Claude->>Claude: 实现后端API
    and
        Bolt->>Bolt: 实现前端界面
    end

    Bolt->>Claude: 测试API调用
    Claude->>Bolt: 修复问题

    PM->>PM: 集成测试
    PM->>PM: 部署上线
```

## 🛠️ 环境配置

### 1. 共享开发环境

#### 后端环境配置（Claude）
```python
# .env.backend
DATABASE_URL=postgresql://user:pass@localhost:5432/ai_ad_spend
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS配置
ALLOWED_ORIGINS=["http://localhost:3000", "https://your-bolt-app.vercel.app"]

# 开发模式
DEBUG=True
RELOAD=True
```

#### 前端环境配置（Bolt.new）
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_APP_NAME=AI广告代投系统
NEXT_PUBLIC_VERSION=2.1.0
```

### 2. Docker开发环境

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/ai_ad_spend
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=ai_ad_spend
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

## 📋 接口协调机制

### 1. API优先设计原则

#### 步骤1：Claude定义API规范
```python
# backend/schemas/project.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ProjectCreate(BaseModel):
    name: str
    client_id: int
    description: Optional[str] = None
    budget: float
    start_date: datetime
    end_date: datetime
    priority: str = "medium"

class ProjectResponse(BaseModel):
    id: int
    name: str
    client_name: str
    budget: float
    current_spend: float
    status: str
    progress: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

#### 步骤2：Claude生成OpenAPI文档
```python
# backend/main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="AI广告代投系统 API",
    version="2.1.0",
    description="Claude生成的后端API接口"
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="AI广告代投系统 API",
        version="2.1.0",
        description="供Bolt.new前端调用的RESTful API",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

#### 步骤3：Bolt.new同步类型定义
```typescript
// frontend/types/api.ts - Bolt.new根据OpenAPI生成
export interface Project {
  id: number;
  name: string;
  client_name: string;
  budget: number;
  current_spend: number;
  status: 'planning' | 'active' | 'paused' | 'completed' | 'archived';
  progress: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  client_id: number;
  description?: string;
  budget: number;
  start_date: string;
  end_date: string;
  priority?: 'low' | 'medium' | 'high';
}

export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message: string;
  code: string;
  request_id: string;
  timestamp: string;
}
```

### 2. 实时数据同步

#### Claude实现WebSocket服务
```python
# backend/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from typing import Dict

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps(message))

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_text(json.dumps(message))

manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # 处理前端订阅请求
            if message['type'] == 'subscribe_project':
                project_id = message['project_id']
                # 订阅项目更新
                await handle_project_subscription(user_id, project_id)

            elif message['type'] == 'subscribe_metrics':
                # 订阅实时指标
                await handle_metrics_subscription(user_id)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
```

#### Bolt.new实现WebSocket客户端
```typescript
// frontend/hooks/useWebSocket.ts - Bolt.new实现
import { useEffect, useRef, useState } from 'react';

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export function useWebSocket(userId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/ws/${userId}`;

    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket连接已建立');
    };

    ws.current.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      setLastMessage(message);
    };

    ws.current.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket连接已关闭');
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [userId]);

  const sendMessage = (message: any) => {
    if (ws.current && isConnected) {
      ws.current.send(JSON.stringify(message));
    }
  };

  const subscribeProject = (projectId: string) => {
    sendMessage({
      type: 'subscribe_project',
      project_id: projectId
    });
  };

  return { isConnected, lastMessage, sendMessage, subscribeProject };
}
```

## 🔄 开发协调实践

### 1. 项目管理模块协调示例

#### 第一天：接口设计（Claude主导）
```python
# Claude先创建后端API
@router.get("/projects", response_model=PaginatedResponse[ProjectResponse])
async def get_projects(
    page: int = 1,
    size: int = 20,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目列表API"""
    query = db.query(Project).filter(Project.is_active == True)

    if status:
        query = query.filter(Project.status == status)
    if priority:
        query = query.filter(Project.priority == priority)
    if search:
        query = query.filter(Project.name.contains(search))

    total = query.count()
    projects = query.offset((page - 1) * size).limit(size).all()

    return PaginatedResponse(
        success=True,
        data=projects,
        message="获取项目列表成功",
        total=total,
        page=page,
        size=size,
        total_pages=(total + size - 1) // size
    )
```

#### 第二天：前端界面开发（Bolt.new主导）
```typescript
// Bolt.new根据API创建前端组件
// frontend/app/projects/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Project, PaginatedApiResponse } from '@/types/api';

export default function ProjectsPage() {
  const [view, setView] = useState<'list' | 'kanban'>('list');
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    search: ''
  });

  const { data: projectsData, isLoading, error } = useQuery<PaginatedApiResponse<Project>>({
    queryKey: ['projects', filters],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: '1',
        size: '20',
        ...(filters.status && { status: filters.status }),
        ...(filters.priority && { priority: filters.priority }),
        ...(filters.search && { search: filters.search })
      });

      return await apiClient.get(`/api/v1/projects?${params}`);
    }
  });

  if (isLoading) return <div>加载中...</div>;
  if (error) return <div>加载失败: {error.message}</div>;

  return (
    <div className="container mx-auto p-6">
      {/* 项目管理界面由Bolt.new实现 */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">项目管理</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setView('list')}
            className={`px-4 py-2 rounded ${view === 'list' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            列表视图
          </button>
          <button
            onClick={() => setView('kanban')}
            className={`px-4 py-2 rounded ${view === 'kanban' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            看板视图
          </button>
        </div>
      </div>

      {view === 'list' ? (
        <ProjectListView projects={projectsData?.data?.items || []} />
      ) : (
        <ProjectKanbanView projects={projectsData?.data?.items || []} />
      )}
    </div>
  );
}
```

#### 第三天：集成联调（Claude + Bolt.new协作）
```bash
# Claude检查后端API
curl -X GET "http://localhost:8000/api/v1/projects?page=1&size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Bolt.new测试前端调用
# 在浏览器控制台验证API调用是否正常
```

### 2. 实时数据协调示例

#### Claude实现后端实时推送
```python
# backend/services/real_time_service.py
import asyncio
from datetime import datetime
from websocket import manager

class RealTimeService:
    def __init__(self):
        self.active_subscriptions = {}

    async def subscribe_project_updates(self, user_id: str, project_id: int):
        """订阅项目更新"""
        if user_id not in self.active_subscriptions:
            self.active_subscriptions[user_id] = set()

        self.active_subscriptions[user_id].add(project_id)

        # 发送订阅确认
        await manager.send_personal_message({
            "type": "subscription_confirmed",
            "project_id": project_id,
            "timestamp": datetime.utcnow().isoformat()
        }, user_id)

    async def notify_project_update(self, project_id: int, update_data: dict):
        """通知项目更新"""
        for user_id, subscriptions in self.active_subscriptions.items():
            if project_id in subscriptions:
                await manager.send_personal_message({
                    "type": "project_updated",
                    "project_id": project_id,
                    "data": update_data,
                    "timestamp": datetime.utcnow().isoformat()
                }, user_id)

real_time_service = RealTimeService()
```

#### Bolt.new实现前端实时更新
```typescript
// frontend/components/projects/project-real-time-updates.tsx
'use client';

import { useEffect, useState } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { Project } from '@/types/api';

interface ProjectRealTimeUpdatesProps {
  project: Project;
  onProjectUpdate: (updatedProject: Project) => void;
}

export function ProjectRealTimeUpdates({ project, onProjectUpdate }: ProjectRealTimeUpdatesProps) {
  const { lastMessage, subscribeProject } = useWebSocket('current-user-id');
  const [lastUpdateTime, setLastUpdateTime] = useState<string | null>(null);

  useEffect(() => {
    // 订阅项目更新
    subscribeProject(project.id.toString());
  }, [project.id]);

  useEffect(() => {
    if (lastMessage) {
      switch (lastMessage.type) {
        case 'project_updated':
          if (lastMessage.data.project_id === project.id) {
            onProjectUpdate(lastMessage.data.project);
            setLastUpdateTime(new Date().toLocaleTimeString());
          }
          break;

        case 'budget_alert':
          if (lastMessage.data.project_id === project.id) {
            // 显示预算警告
            showBudgetAlert(lastMessage.data.message);
          }
          break;
      }
    }
  }, [lastMessage]);

  return (
    <div className="fixed bottom-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg">
      {lastUpdateTime && (
        <div className="text-sm">
          项目已更新 - {lastUpdateTime}
        </div>
      )}
    </div>
  );
}
```

## 🧪 测试协调策略

### 1. API测试（Claude负责）
```python
# backend/tests/test_projects_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_projects():
    """测试获取项目列表API"""
    response = client.get(
        "/api/v1/projects",
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "items" in data["data"]

def test_create_project():
    """测试创建项目API"""
    project_data = {
        "name": "测试项目",
        "client_id": 1,
        "budget": 50000,
        "start_date": "2025-01-01T00:00:00Z",
        "end_date": "2025-03-31T00:00:00Z",
        "priority": "high"
    }

    response = client.post(
        "/api/v1/projects",
        json=project_data,
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "测试项目"
```

### 2. 前端测试（Bolt.new负责）
```typescript
// frontend/__tests__/projects.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ProjectsPage from '../app/projects/page';

const mockProjectsData = {
  success: true,
  data: {
    items: [
      {
        id: 1,
        name: "测试项目",
        client_name: "测试客户",
        budget: 50000,
        current_spend: 25000,
        status: "active",
        progress: 50
      }
    ]
  }
};

// Mock API调用
jest.mock('@/lib/api-client', () => ({
  apiClient: {
    get: jest.fn().mockResolvedValue(mockProjectsData),
    post: jest.fn().mockResolvedValue({ success: true })
  }
}));

test('项目列表页面正常渲染', async () => {
  const queryClient = new QueryClient();

  render(
    <QueryClientProvider client={queryClient}>
      <ProjectsPage />
    </QueryClientProvider>
  );

  // 等待数据加载
  await waitFor(() => {
    expect(screen.getByText('项目管理')).toBeInTheDocument();
  });

  await waitFor(() => {
    expect(screen.getByText('测试项目')).toBeInTheDocument();
  });
});
```

### 3. 集成测试（Claude + Bolt.new协作）
```typescript
// frontend/__tests__/integration/projects.integration.test.ts
import { test, expect } from '@playwright/test';

test('项目创建流程完整测试', async ({ page }) => {
  // 访问项目页面
  await page.goto('/projects');

  // 点击新建项目按钮
  await page.click('[data-testid="create-project-btn"]');

  // 填写项目信息
  await page.fill('[data-testid="project-name"]', 'E2E测试项目');
  await page.fill('[data-testid="project-budget"]', '100000');
  await page.selectOption('[data-testid="project-priority"]', 'high');

  // 提交表单
  await page.click('[data-testid="submit-btn"]');

  // 验证项目创建成功
  await expect(page.locator('text=项目创建成功')).toBeVisible();
  await expect(page.locator('text=E2E测试项目')).toBeVisible();
});
```

## 🚀 部署协调

### 1. 开发环境部署
```yaml
# docker-compose.dev.yml - Claude创建
version: '3.8'
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/ai_ad_spend
      - REDIS_URL=redis://redis:6379
      - DEBUG=True
    depends_on:
      - db
      - redis

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
```

### 2. 生产环境部署
```bash
# Claude构建后端Docker镜像
docker build -t ai-ad-spend-backend ./backend

# Bolt.new构建前端应用
cd frontend
npm run build
docker build -t ai-ad-spend-frontend .

# 部署到生产环境
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 协调效率指标

### 1. 开发效率指标
- **接口同步时间**: < 30分钟
- **前后端联调时间**: < 2小时/模块
- **Bug修复响应时间**: < 1小时
- **功能交付周期**: 2-3天/模块

### 2. 质量保证指标
- **API测试覆盖率**: > 90%
- **前端组件测试覆盖率**: > 80%
- **E2E测试覆盖率**: > 70%
- **代码审查通过率**: 100%

### 3. 协作沟通指标
- **日常同步会议**: 15分钟/天
- **技术评审会议**: 30分钟/周
- **功能演示会议**: 1小时/两周
- **回顾改进会议**: 1小时/月

## 🎯 最佳实践总结

### 1. Claude后端开发最佳实践
- ✅ 始终先写API文档，再写实现
- ✅ 使用统一的响应格式
- ✅ 实现完善的错误处理
- ✅ 添加详细的API注释
- ✅ 编写全面的单元测试
- ✅ 考虑性能和安全优化

### 2. Bolt.new前端开发最佳实践
- ✅ 根据API文档生成TypeScript类型
- ✅ 使用React Query进行数据管理
- ✅ 实现优雅的加载和错误状态
- ✅ 保持UI组件的可复用性
- ✅ 响应式设计和用户体验
- ✅ 编写组件和集成测试

### 3. 协调沟通最佳实践
- ✅ 每日15分钟站会同步进度
- ✅ API变更及时通知前端
- ✅ 需求变更及时通知后端
- ✅ 使用共享文档跟踪进度
- ✅ 定期进行代码审查
- ✅ 保持积极的沟通态度

通过这套协调开发指南，Claude和Bolt.new可以实现高效的并行开发，大大提升AI广告代投系统的开发效率和交付质量。