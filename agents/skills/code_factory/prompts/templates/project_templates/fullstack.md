# 全栈项目模板

## 技术栈概览

| 层 | 技术 | 版本 |
|---|------|------|
| 后端 | FastAPI + SQLAlchemy 2.x + Pydantic v2 | latest |
| 前端 | Next.js 16 + TanStack Query v5 + shadcn/ui | latest |
| 认证 | Supabase Auth | latest |
| 数据库 | PostgreSQL (via Supabase) | 15+ |

## 开发流程

### 新功能开发顺序

```
1. 数据库设计 (Schema)
   ↓
2. 后端开发
   Model → Schema → Service → Router → Tests
   ↓
3. 前端开发
   Types → API → Hooks → Components → Page → Tests
   ↓
4. 集成测试
```

## 后端开发

### 1. 数据模型
```python
# backend/models/{model}.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum

# SoT: STATE_MACHINE.md#{model}
class {Model}Status(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"

class {Model}(Base):
    __tablename__ = "{models}"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    status = Column(Enum({Model}Status), default={Model}Status.DRAFT)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # 外键关联
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="{models}")
```

### 2. Pydantic Schema
```python
# backend/schemas/{model}.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from .{model}_status import {Model}Status

class {Model}Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=100)

class {Model}Create({Model}Base):
    pass

class {Model}Response({Model}Base):
    id: int
    status: {Model}Status
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
```

### 3. Service 层
```python
# backend/services/{model}_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from models.{model} import {Model}
from schemas.{model} import {Model}Create
from core.error_codes import BusinessError, BusinessErrorCodes

class {Model}Service:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self, 
        data: {Model}Create, 
        user_id: int
    ) -> {Model}:
        """创建 {model}"""
        instance = {Model}(
            **data.model_dump(),
            user_id=user_id,
        )
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance
    
    async def get_by_id(self, id: int) -> Optional[{Model}]:
        """获取单个 {model}"""
        result = await self.db.execute(
            select({Model}).where({Model}.id == id)
        )
        return result.scalar_one_or_none()
    
    async def list_by_user(
        self, 
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[{Model}]:
        """获取用户的 {model} 列表"""
        result = await self.db.execute(
            select({Model})
            .where({Model}.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
```

### 4. Router 层
```python
# backend/routers/{model}_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.database import get_db
from core.response import success_response
from core.auth import get_current_user
from models.user import User
from schemas.{model} import {Model}Create, {Model}Response
from services.{model}_service import {Model}Service

router = APIRouter(prefix="/{models}", tags=["{Model}"])

@router.get("/", response_model=dict)
async def list_{models}(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的 {model} 列表"""
    service = {Model}Service(db)
    items = await service.list_by_user(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return success_response(data=items)

@router.post("/", response_model=dict)
async def create_{model}(
    data: {Model}Create,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建 {model}"""
    service = {Model}Service(db)
    item = await service.create(data, user_id=current_user.id)
    return success_response(data=item, message="创建成功")
```

## 前端开发

### 1. 类型定义
```typescript
// frontend/src/features/{model}/types.ts
export interface {Model} {
  id: number;
  name: string;
  status: {Model}Status;
  user_id: number;
  created_at: string;
  updated_at: string | null;
}

export type {Model}Status = 'draft' | 'pending' | 'approved';

export interface {Model}CreateInput {
  name: string;
}
```

### 2. API 层
```typescript
// frontend/src/features/{model}/api.ts
import { apiGet, apiPost } from '@/lib/api';
import type { {Model}, {Model}CreateInput } from './types';

export const {model}Api = {
  list: () => apiGet<{Model}[]>('/api/v1/{models}'),
  create: (data: {Model}CreateInput) => apiPost<{Model}>('/api/v1/{models}', data),
};
```

### 3. Hooks
```typescript
// frontend/src/features/{model}/hooks.ts
'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { {model}Api } from './api';

export function use{Model}s() {
  return useQuery({
    queryKey: ['{models}'],
    queryFn: {model}Api.list,
  });
}

export function useCreate{Model}() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: {model}Api.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['{models}'] });
    },
  });
}
```

### 4. 页面
```tsx
// frontend/src/app/(dashboard)/{models}/page.tsx
'use client';

import { use{Model}s } from '@/features/{model}/hooks';
import { Button } from '@/components/ui/button';

export default function {Model}sPage() {
  const { data, isLoading } = use{Model}s();
  
  if (isLoading) return <div>加载中...</div>;
  
  return (
    <div>
      <h1>{Model}列表</h1>
      <ul>
        {data?.map(item => (
          <li key={item.id}>{item.name}</li>
        ))}
      </ul>
    </div>
  );
}
```

## API 规范

### 请求格式
```http
POST /api/v1/{models}
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "示例"
}
```

### 响应格式
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "示例",
    "status": "draft",
    "created_at": "2024-12-30T10:00:00Z"
  },
  "message": "创建成功",
  "error": null
}
```

### 错误响应
```json
{
  "success": false,
  "data": null,
  "message": "验证失败",
  "error": {
    "code": "VAL-001",
    "message": "name 字段不能为空"
  }
}
```

## 检查清单

### 后端
- [ ] Model 有 SoT 状态标注
- [ ] Schema 使用 Pydantic v2
- [ ] Service 有错误处理
- [ ] Router 有权限验证
- [ ] 响应使用 success_response

### 前端
- [ ] Types 与后端一致
- [ ] API 使用 apiFetch
- [ ] Hooks 使用 TanStack Query v5
- [ ] 组件使用 shadcn/ui
- [ ] 页面有 'use client' 指令


