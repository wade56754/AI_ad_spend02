# Claude + Bolt.new 协调开发操作手册

## 🎯 快速开始

### 第一步：环境准备

#### 1.1 检查现有环境
```bash
# 检查项目结构
ls -la

# 应该看到以下目录结构
# AI_ad_spend02/
# ├── backend/          # Claude后端开发目录
# ├── frontend/         # Bolt.new前端开发目录
# ├── docs/             # 文档目录
# ├── docker-compose.dev.yml
# └── .env.example
```

#### 1.2 启动开发环境
```bash
# 启动Docker开发环境（包含数据库和Redis）
docker-compose -f docker-compose.dev.yml up -d

# 检查服务状态
docker-compose -f docker-compose.dev.yml ps

# 应该看到以下服务运行中：
# backend    - FastAPI后端服务
# db         - PostgreSQL数据库
# redis      - Redis缓存服务
```

#### 1.3 启动Claude后端开发
```bash
# 进入后端目录
cd backend

# 激活Python虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖（如果还没有）
pip install -r requirements.txt

# 启动后端开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 后端API将在 http://localhost:8000 启动
# API文档在 http://localhost:8000/docs
```

#### 1.4 准备Bolt.new前端开发
```bash
# 新开一个终端窗口

# 进入前端目录
cd frontend

# 安装依赖（如果还没有）
npm install

# 复制环境变量配置
cp .env.example .env.local

# 编辑环境变量
nano .env.local
```

#### 1.5 配置前端环境变量
```bash
# 在 .env.local 中添加以下配置：
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_APP_NAME=AI广告代投系统
NEXT_PUBLIC_VERSION=2.1.0

# 启动前端开发服务器
npm run dev

# 前端应用将在 http://localhost:3000 启动
```

### 第二步：验证环境连通性

#### 2.1 测试后端API
```bash
# 测试健康检查
curl http://localhost:8000/health

# 应该返回：{"status": "healthy", "timestamp": "..."}

# 测试API文档访问
curl http://localhost:8000/openapi.json

# 应该返回完整的OpenAPI规范JSON
```

#### 2.2 测试前端连接
```bash
# 在浏览器中访问 http://localhost:3000
# 应该能看到AI广告代投系统的登录页面

# 打开浏览器开发者工具（F12）
# 在Console中测试API连接：
fetch('http://localhost:8000/health')
  .then(response => response.json())
  .then(data => console.log('API连接成功:', data))
  .catch(error => console.error('API连接失败:', error))
```

## 🔄 实际开发流程演示

### 场景1：开发新模块 - 用户管理功能

#### 步骤1：Claude创建后端API

```bash
# 在Claude中输入以下提示：
"""
请为AI广告代投系统创建用户管理模块的后端API，包括：

1. 用户列表查询 - GET /api/v1/users
2. 用户详情获取 - GET /api/v1/users/{user_id}
3. 用户创建 - POST /api/v1/users
4. 用户更新 - PUT /api/v1/users/{user_id}
5. 用户删除 - DELETE /api/v1/users/{user_id}

要求：
- 使用统一的响应格式
- 包含完整的错误处理
- 添加必要的权限验证
- 编写API文档注释
- 创建对应的单元测试
"""
```

#### Claude会自动生成以下文件：

```python
# backend/api/v1/users.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.core.auth import require_role
import uuid

router = APIRouter()

@router.get("/", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户列表"""
    require_role(current_user, ["admin", "manager"])

    query = db.query(User).filter(User.is_active == True)

    if search:
        query = query.filter(
            User.username.contains(search) |
            User.email.contains(search) |
            User.full_name.contains(search)
        )

    if role:
        query = query.filter(User.role == role)

    if status:
        query = query.filter(User.status == status)

    total = query.count()
    users = query.offset((page - 1) * size).limit(size).all()

    return UserListResponse(
        success=True,
        data={
            "items": users,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": (total + size - 1) // size
        },
        message="获取用户列表成功",
        request_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow().isoformat()
    )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户详情"""
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    require_role(current_user, ["admin", "manager"], or_self=user_id)

    return UserResponse(
        success=True,
        data=user,
        message="获取用户详情成功",
        request_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow().isoformat()
    )

# ... 其他API端点
```

```python
# backend/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: str
    phone: Optional[str] = None
    department: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    phone: Optional[str]
    department: Optional[str]
    status: str
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    success: bool
    data: dict
    message: str
    request_id: str
    timestamp: str
```

#### 步骤2：测试后端API

```bash
# 测试用户列表API
curl -X GET "http://localhost:8000/api/v1/users?page=1&size=20" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 测试创建用户API
curl -X POST "http://localhost:8000/api/v1/users" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "测试用户",
    "role": "media_buyer",
    "password": "securepassword123"
  }'
```

#### 步骤3：在Bolt.new中创建前端界面

现在在Bolt.new中输入以下提示：

"""
请基于以下API规范创建用户管理的前端界面：

API端点：
- GET /api/v1/users - 获取用户列表
- GET /api/v1/users/{id} - 获取用户详情
- POST /api/v1/users - 创建用户
- PUT /api/v1/users/{id} - 更新用户
- DELETE /api/v1/users/{id} - 删除用户

要求：
1. 创建用户管理主页面 /app/users/page.tsx
2. 创建用户表单组件 /components/users/user-form.tsx
3. 创建用户列表组件 /components/users/user-list.tsx
4. 使用shadcn/ui组件库
5. 包含搜索、筛选、分页功能
6. 支持创建、编辑、删除操作
7. 使用React Query进行数据管理
8. 添加TypeScript类型定义
"""

#### Bolt.new会自动生成前端组件：

```typescript
// frontend/app/users/page.tsx
'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { User, PaginatedApiResponse } from '@/types/api';
import { UserList } from '@/components/users/user-list';
import { UserForm } from '@/components/users/user-form';
import { Button } from '@/components/ui/button';
import { Plus, Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

export default function UsersPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  const { data: usersData, isLoading, refetch } = useQuery<PaginatedApiResponse<User>>({
    queryKey: ['users', searchTerm],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: '1',
        size: '20',
        ...(searchTerm && { search: searchTerm })
      });
      return await apiClient.get(`/api/v1/users?${params}`);
    },
  });

  const handleUserCreated = () => {
    refetch();
    setIsCreateDialogOpen(false);
  };

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">用户管理</h1>

        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              新建用户
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>创建新用户</DialogTitle>
            </DialogHeader>
            <UserForm onSuccess={handleUserCreated} />
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            placeholder="搜索用户..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      <UserList
        users={usersData?.data?.items || []}
        isLoading={isLoading}
        onUserUpdate={refetch}
      />
    </div>
  );
}
```

```typescript
// frontend/types/api.ts
export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'manager' | 'media_buyer' | 'account_manager' | 'finance';
  phone?: string;
  department?: string;
  status: 'active' | 'inactive' | 'suspended';
  last_login?: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedApiResponse<T> {
  success: boolean;
  data: {
    items: T[];
    total: number;
    page: number;
    size: number;
    total_pages: number;
  };
  message: string;
  request_id: string;
  timestamp: string;
}
```

#### 步骤4：测试前后端集成

```bash
# 确保后端和前端都在运行

# 在浏览器中访问 http://localhost:3000/users
# 应该能看到用户管理界面

# 测试创建用户：
# 1. 点击"新建用户"按钮
# 2. 填写用户信息
# 3. 提交表单
# 4. 检查用户是否出现在列表中

# 在浏览器开发者工具的Network标签中检查API调用：
# - 应该看到对 /api/v1/users 的请求
# - 检查请求和响应的数据格式
```

### 场景2：实时数据同步演示

#### 步骤1：Claude创建WebSocket服务

```bash
# 在Claude中输入：
"""
请为AI广告代投系统创建WebSocket实时数据推送服务，包括：

1. 项目状态变更实时推送
2. 充值申请状态变更通知
3. 系统告警实时推送
4. 用户在线状态管理

要求：
- 创建WebSocket连接管理器
- 实现消息广播和定向推送
- 添加用户认证和权限验证
- 包含连接状态监控
"""
```

#### Claude生成WebSocket服务：

```python
# backend/websocket/manager.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # 存储活跃连接：{user_id: {connection_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # 存储连接元数据：{connection_id: {user_id, connected_at, last_ping}}
        self.connection_metadata: Dict[str, dict] = {}
        # 存储用户订阅：{user_id: {subscriptions}}
        self.user_subscriptions: Dict[str, Set[str]] = {}
        self.connection_counter = 0

    async def connect(self, websocket: WebSocket, user_id: str):
        """接受WebSocket连接"""
        await websocket.accept()

        connection_id = f"conn_{self.connection_counter}"
        self.connection_counter += 1

        # 存储连接
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}

        self.active_connections[user_id][connection_id] = websocket

        # 存储连接元数据
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }

        logger.info(f"用户 {user_id} 建立WebSocket连接 {connection_id}")

        # 发送连接成功消息
        await self.send_personal_message({
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        }, user_id)

        return connection_id

    def disconnect(self, connection_id: str, user_id: str):
        """断开WebSocket连接"""
        if user_id in self.active_connections:
            if connection_id in self.active_connections[user_id]:
                del self.active_connections[user_id][connection_id]

            # 如果用户没有其他连接，清理用户数据
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                if user_id in self.user_subscriptions:
                    del self.user_subscriptions[user_id]

        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]

        logger.info(f"用户 {user_id} 断开WebSocket连接 {connection_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        """发送个人消息"""
        if user_id in self.active_connections:
            disconnected_connections = []

            for connection_id, websocket in self.active_connections[user_id].items():
                try:
                    await websocket.send_text(json.dumps(message, ensure_ascii=False))
                except Exception as e:
                    logger.error(f"发送消息失败: {e}")
                    disconnected_connections.append(connection_id)

            # 清理断开的连接
            for connection_id in disconnected_connections:
                self.disconnect(connection_id, user_id)

    async def broadcast_to_role(self, message: dict, role: str):
        """向特定角色用户广播消息"""
        from app.models.user import User
        from app.api.deps import get_db

        # 这里需要数据库查询，实际使用时需要优化
        db = next(get_db())
        try:
            users = db.query(User).filter(User.role == role, User.is_active == True).all()
            for user in users:
                await self.send_personal_message(message, str(user.id))
        finally:
            db.close()

    async def subscribe_project(self, user_id: str, project_id: str):
        """订阅项目更新"""
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        self.user_subscriptions[user_id].add(f"project_{project_id}")

    async def unsubscribe_project(self, user_id: str, project_id: str):
        """取消订阅项目更新"""
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(f"project_{project_id}")

# 全局连接管理器实例
manager = ConnectionManager()
```

```python
# backend/api/v1/websocket.py
from fastapi import WebSocket, Depends, HTTPException
from app.api.deps import get_current_user_ws
from app.websocket.manager import manager
from app.models.user import User
import json

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket连接端点"""
    # 验证用户身份（这里简化处理，实际应该通过JWT验证）
    try:
        # current_user = await get_current_user_ws(user_id)
        connection_id = await manager.connect(websocket, user_id)

        try:
            while True:
                # 接收客户端消息
                data = await websocket.receive_text()
                message = json.loads(data)

                message_type = message.get("type")

                if message_type == "subscribe_project":
                    project_id = message.get("project_id")
                    if project_id:
                        await manager.subscribe_project(user_id, project_id)
                        await manager.send_personal_message({
                            "type": "subscription_confirmed",
                            "subscription": f"project_{project_id}",
                            "timestamp": datetime.utcnow().isoformat()
                        }, user_id)

                elif message_type == "unsubscribe_project":
                    project_id = message.get("project_id")
                    if project_id:
                        await manager.unsubscribe_project(user_id, project_id)

                elif message_type == "ping":
                    # 心跳包
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, user_id)

        except WebSocketDisconnect:
            manager.disconnect(connection_id, user_id)

    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
        await websocket.close()
```

#### 步骤2：Bolt.new创建WebSocket客户端

在Bolt.new中输入：

"""
请创建WebSocket客户端组件，实现以下功能：
1. WebSocket连接管理
2. 实时消息接收和处理
3. 自动重连机制
4. 消息订阅和取消订阅
5. 连接状态显示
"""

Bolt.new生成客户端组件：

```typescript
// frontend/hooks/useWebSocket.ts
import { useEffect, useRef, useState, useCallback } from 'react';
import { useUserStore } from '@/stores/user';

interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp: string;
  connection_id?: string;
}

interface WebSocketHookReturn {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  sendMessage: (message: any) => void;
  subscribeProject: (projectId: string) => void;
  unsubscribeProject: (projectId: string) => void;
  connectionError: string | null;
}

export function useWebSocket(): WebSocketHookReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const pingInterval = useRef<NodeJS.Timeout | null>(null);

  const { user } = useUserStore();
  const userId = user?.id?.toString();

  const connect = useCallback(() => {
    if (!userId || ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/ws/${userId}`;
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log('WebSocket连接已建立');
        setIsConnected(true);
        setConnectionError(null);

        // 启动心跳包
        pingInterval.current = setInterval(() => {
          if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
      };

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);

          // 处理不同类型的消息
          switch (message.type) {
            case 'connection_established':
              console.log('WebSocket连接确认:', message.connection_id);
              break;

            case 'project_updated':
              // 项目更新通知
              // 这里可以触发全局状态更新
              break;

            case 'topup_status_changed':
              // 充值状态变更通知
              break;

            case 'system_alert':
              // 系统告警
              break;

            case 'pong':
              // 心跳响应
              break;
          }
        } catch (error) {
          console.error('解析WebSocket消息失败:', error);
        }
      };

      ws.current.onclose = () => {
        console.log('WebSocket连接已关闭');
        setIsConnected(false);

        // 清理心跳包
        if (pingInterval.current) {
          clearInterval(pingInterval.current);
          pingInterval.current = null;
        }

        // 自动重连（延迟5秒）
        reconnectTimeout.current = setTimeout(() => {
          console.log('尝试重新连接WebSocket...');
          connect();
        }, 5000);
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket连接错误:', error);
        setConnectionError('WebSocket连接失败');
      };

    } catch (error) {
      console.error('创建WebSocket连接失败:', error);
      setConnectionError('无法建立WebSocket连接');
    }
  }, [userId]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }

    if (pingInterval.current) {
      clearInterval(pingInterval.current);
      pingInterval.current = null;
    }

    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }

    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket未连接，无法发送消息');
    }
  }, []);

  const subscribeProject = useCallback((projectId: string) => {
    sendMessage({
      type: 'subscribe_project',
      project_id: projectId
    });
  }, [sendMessage]);

  const unsubscribeProject = useCallback((projectId: string) => {
    sendMessage({
      type: 'unsubscribe_project',
      project_id: projectId
    });
  }, [sendMessage]);

  useEffect(() => {
    if (userId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [userId, connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    subscribeProject,
    unsubscribeProject,
    connectionError
  };
};
```

#### 步骤3：集成实时通知组件

在Bolt.new中创建：

```typescript
// frontend/components/notifications/real-time-notifications.tsx
'use client';

import React, { useEffect, useState } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';
import { Bell, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

export function RealTimeNotifications() {
  const { isConnected, lastMessage, connectionError } = useWebSocket();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (lastMessage) {
      switch (lastMessage.type) {
        case 'project_updated':
          toast.success('项目状态已更新', {
            description: `项目 ${lastMessage.data.project_name} 状态变更为 ${lastMessage.data.new_status}`,
            icon: <CheckCircle className="w-4 h-4" />,
          });
          setUnreadCount(prev => prev + 1);
          break;

        case 'topup_status_changed':
          if (lastMessage.data.new_status === 'approved') {
            toast.success('充值申请已批准', {
              description: `¥${lastMessage.data.amount} 充值申请已批准`,
              icon: <CheckCircle className="w-4 h-4" />,
            });
          } else if (lastMessage.data.new_status === 'rejected') {
            toast.error('充值申请被拒绝', {
              description: lastMessage.data.reason || '申请被拒绝',
              icon: <XCircle className="w-4 h-4" />,
            });
          }
          setUnreadCount(prev => prev + 1);
          break;

        case 'system_alert':
          toast.warning('系统告警', {
            description: lastMessage.data.message,
            icon: <AlertTriangle className="w-4 h-4" />,
          });
          setUnreadCount(prev => prev + 1);
          break;
      }
    }
  }, [lastMessage]);

  return (
    <div className="relative">
      <Bell className="w-5 h-5" />

      {/* 连接状态指示器 */}
      <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full ${
        isConnected ? 'bg-green-500' : 'bg-red-500'
      }`} />

      {/* 未读消息计数 */}
      {unreadCount > 0 && (
        <Badge
          variant="destructive"
          className="absolute -top-2 -right-2 w-5 h-5 flex items-center justify-center p-0 text-xs"
        >
          {unreadCount > 99 ? '99+' : unreadCount}
        </Badge>
      )}

      {/* 连接错误提示 */}
      {connectionError && (
        <div className="absolute top-6 right-0 w-48 p-2 bg-red-100 border border-red-300 rounded-md text-xs">
          <div className="flex items-center gap-1 text-red-700">
            <AlertTriangle className="w-3 h-3" />
            {connectionError}
          </div>
        </div>
      )}
    </div>
  );
}
```

#### 步骤4：测试实时同步

```bash
# 1. 确保后端和前端都在运行

# 2. 在浏览器中打开两个标签页：
# - http://localhost:3000/projects (项目页面)
# - http://localhost:3000/finance (财务页面)

# 3. 在一个标签页中修改项目状态或提交充值申请

# 4. 观察另一个标签页是否收到实时通知

# 5. 在浏览器开发者工具的Console中观察：
# - WebSocket连接状态
# - 消息收发情况
# - 自动重连机制
```

## 🛠️ 高级操作技巧

### 1. API文档自动同步

```bash
# 在Claude后端添加自动生成TypeScript类型的脚本

# 创建 backend/scripts/generate-types.js
const fs = require('fs');
const fetch = require('node-fetch');

async function generateTypes() {
  try {
    const response = await fetch('http://localhost:8000/openapi.json');
    const openapi = await response.json();

    // 生成TypeScript类型定义
    let types = `// 自动生成的API类型定义
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message: string;
  code: string;
  request_id: string;
  timestamp: string;
}
`;

    // 遍历API端点生成类型
    Object.entries(openapi.components.schemas).forEach(([name, schema]) => {
      types += generateTypeDefinition(name, schema);
    });

    fs.writeFileSync('../frontend/types/api-generated.ts', types);
    console.log('TypeScript类型定义已更新');
  } catch (error) {
    console.error('生成类型定义失败:', error);
  }
}

function generateTypeDefinition(name, schema) {
  // 这里实现具体的类型生成逻辑
  return `export interface ${name} {
  // 自动生成的类型定义
}\n`;
}

// 每次API变更后运行
generateTypes();
```

### 2. 自动化测试脚本

```bash
# 创建 scripts/test-integration.sh
#!/bin/bash

echo "🧪 开始集成测试..."

# 测试后端API健康检查
echo "1. 测试后端API健康检查..."
curl -f http://localhost:8000/health || exit 1

# 测试前端连接
echo "2. 测试前端API连接..."
curl -f http://localhost:3000 || exit 1

# 测试API认证
echo "3. 测试API认证..."
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | \
  jq -r '.data.access_token')

if [ "$TOKEN" != "null" ]; then
  echo "✅ API认证测试通过"
else
  echo "❌ API认证测试失败"
  exit 1
fi

# 测试数据创建
echo "4. 测试数据创建..."
curl -f -X POST "http://localhost:8000/api/v1/projects" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"测试项目","client_id":1,"budget":50000}' || exit 1

echo "✅ 所有集成测试通过！"
```

### 3. 开发环境快速重启脚本

```bash
# 创建 scripts/restart-dev.sh
#!/bin/bash

echo "🔄 重启开发环境..."

# 停止现有服务
docker-compose -f docker-compose.dev.yml down

# 清理容器和卷
docker system prune -f

# 重新构建并启动
docker-compose -f docker-compose.dev.yml build --no-cache
docker-compose -f docker-compose.dev.yml up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
docker-compose -f docker-compose.dev.yml ps

# 运行数据库迁移
echo "运行数据库迁移..."
cd backend && alembic upgrade head && cd ..

echo "✅ 开发环境重启完成！"
echo "后端API: http://localhost:8000"
echo "前端应用: http://localhost:3000"
echo "API文档: http://localhost:8000/docs"
```

## 🚨 常见问题解决

### 1. CORS跨域问题

```python
# backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://your-bolt-app.vercel.app"  # Bolt.new部署地址
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. WebSocket连接失败

```bash
# 检查防火墙设置
sudo ufw allow 8000

# 检查WebSocket路由
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: test" \
     -H "Sec-WebSocket-Version: 13" \
     http://localhost:8000/ws/1
```

### 3. 热重载不工作

```bash
# 确保文件监听正常
# 在后端目录运行：
find . -name "*.py" | entr -r uvicorn app.main:app --reload

# 在前端目录运行：
npm run dev -- --turbopack
```

这个操作手册提供了具体的、可执行的步骤，让你能够立即开始Claude与Bolt.new的协调开发！