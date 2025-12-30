# FastAPI 项目模板

## 技术栈

| 组件 | 版本 | 说明 |
|------|------|------|
| FastAPI | 0.104+ | Web 框架 |
| SQLAlchemy | 2.x | ORM |
| Pydantic | v2 | 数据验证 |
| Alembic | 1.13+ | 数据库迁移 |
| PostgreSQL | 15+ | 数据库 |

## 项目结构

```
backend/
├── main.py                 # 应用入口
├── core/
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接
│   ├── response.py        # 响应封装
│   └── error_codes.py     # 错误码定义
├── models/
│   └── {model}.py         # SQLAlchemy 模型
├── schemas/
│   └── {schema}.py        # Pydantic Schema
├── services/
│   └── {service}.py       # 业务逻辑
├── routers/
│   └── {router}.py        # API 路由
└── tests/
    └── test_{module}.py   # 测试文件
```

## 代码规范

### 模型定义
```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class {Model}(Base):
    __tablename__ = "{table_name}"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # 关联关系
    # parent = relationship("Parent", back_populates="{children}")
```

### Schema 定义
```python
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

class {Model}Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=100)

class {Model}Create({Model}Base):
    pass

class {Model}Update({Model}Base):
    name: Optional[str] = None

class {Model}Response({Model}Base):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
```

### Service 定义
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

class {Model}Service:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, id: int) -> Optional[{Model}]:
        result = await self.db.execute(
            select({Model}).where({Model}.id == id)
        )
        return result.scalar_one_or_none()
    
    async def list(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[{Model}]:
        result = await self.db.execute(
            select({Model}).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def create(self, data: {Model}Create) -> {Model}:
        instance = {Model}(**data.model_dump())
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance
```

### Router 定义
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.database import get_db
from core.response import success_response
from core.error_codes import BusinessError, BusinessErrorCodes

router = APIRouter(prefix="/{models}", tags=["{Model}"])

@router.get("/", response_model=dict)
async def list_{models}(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """获取列表"""
    service = {Model}Service(db)
    items = await service.list(skip=skip, limit=limit)
    return success_response(data=items)

@router.get("/{id}", response_model=dict)
async def get_{model}(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取详情"""
    service = {Model}Service(db)
    item = await service.get_by_id(id)
    if not item:
        raise BusinessError(code=BusinessErrorCodes.NOT_FOUND)
    return success_response(data=item)

@router.post("/", response_model=dict)
async def create_{model}(
    data: {Model}Create,
    db: AsyncSession = Depends(get_db),
):
    """创建"""
    service = {Model}Service(db)
    item = await service.create(data)
    return success_response(data=item, message="创建成功")
```

## 响应格式

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功",
  "error": null
}
```

## 错误处理

```python
from core.error_codes import BusinessError, BusinessErrorCodes

# 业务错误
raise BusinessError(
    code=BusinessErrorCodes.INVALID_STATE_TRANSITION,
    message="状态转换非法"
)

# 响应格式
{
  "success": false,
  "data": null,
  "message": "状态转换非法",
  "error": {
    "code": "BIZ-STATE-001",
    "message": "状态转换非法"
  }
}
```

