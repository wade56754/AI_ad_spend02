# 代码生成提示词 (Generate Prompt)

## 目标

基于澄清后的需求，生成符合项目规范的代码。

## 生成原则

### 1. 搜索优先
- 先搜索项目中是否有类似实现
- 基于已有代码模式进行适配
- 标注所有参考来源

### 2. SoT 合规
- 状态值必须来自 STATE_MACHINE.md
- 角色值必须来自 AUTH_SPEC.md
- 错误码必须来自 ERROR_CODES_SOT.md
- 字段定义必须符合 DATA_SCHEMA.md

### 3. 分层架构
后端生成顺序:
```
Schema → Service → Router
```

前端生成顺序:
```
Types → API → Hooks → Components → Page
```

## 代码来源标注

**必须使用统一格式**:
```python
# SoT: {DOC}#{SECTION}
```

示例:
```python
# SoT: STATE_MACHINE.md#daily_report
class ReportStatus(str, Enum):
    RAW_SUBMITTED = "raw_submitted"
    TREND_PENDING = "trend_pending"
    ...

# SoT: ERROR_CODES_SOT.md#RPT-001
raise BusinessError(code="RPT-001", message="日报日期不能是未来")

# SoT: API_SOT.md#POST /daily-reports
@router.post("/daily-reports")
async def create_daily_report(...):
    ...
```

## 后端代码模板

### Schema (Pydantic v2)
```python
# SoT: DATA_SCHEMA.md#{table_name}
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal

class {Name}Base(BaseModel):
    """基础模型"""
    model_config = ConfigDict(from_attributes=True)
    
    field1: str = Field(..., description="{描述}")
    field2: Optional[int] = Field(None, description="{描述}")

class {Name}Create({Name}Base):
    """创建模型"""
    pass

class {Name}Response({Name}Base):
    """响应模型"""
    id: int
    created_at: datetime
```

### Service
```python
# SoT: BUSINESS_RULES.md#{rule_id}
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class {Name}Service:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, data: {Name}Create) -> {Name}:
        """创建 {name}"""
        # 业务规则验证
        # SoT: BUSINESS_RULES.md#BR-XXX
        ...
        
        instance = {Name}(**data.model_dump())
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance
```

### Router
```python
# SoT: API_SOT.md#{endpoint}
from fastapi import APIRouter, Depends, HTTPException
from core.response import success_response
from core.error_codes import BusinessError, BusinessErrorCodes

router = APIRouter(prefix="/{name}s", tags=["{name}"])

@router.post("/", response_model=dict)
async def create_{name}(
    data: {Name}Create,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建 {name}"""
    service = {Name}Service(db)
    result = await service.create(data)
    return success_response(data=result)
```

## 前端代码模板

### Types
```typescript
// SoT: DATA_SCHEMA.md#{table_name}
export interface {Name} {
  id: number;
  field1: string;
  field2?: number;
  created_at: string;
}

export interface {Name}CreateInput {
  field1: string;
  field2?: number;
}
```

### API
```typescript
// SoT: API_SOT.md#{endpoint}
import { apiGet, apiPost } from '@/lib/api';

export const {name}Api = {
  list: (params?: {Name}ListParams) => 
    apiGet<{Name}[]>('/api/v1/{name}s', { params }),
  
  create: (data: {Name}CreateInput) =>
    apiPost<{Name}>('/api/v1/{name}s', data),
};
```

### Hooks
```typescript
// TanStack Query v5
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function use{Name}s(params?: {Name}ListParams) {
  return useQuery({
    queryKey: ['{name}s', params],
    queryFn: () => {name}Api.list(params),
  });
}

export function useCreate{Name}() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: {name}Api.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['{name}s'] });
    },
  });
}
```

## 验证清单

生成代码后必须验证:

- [ ] 所有状态值来自 STATE_MACHINE.md
- [ ] 所有角色值来自 AUTH_SPEC.md  
- [ ] 所有错误码来自 ERROR_CODES_SOT.md
- [ ] 代码有 SoT 来源标注
- [ ] 使用 Pydantic v2 语法
- [ ] 使用 SQLAlchemy 2.x 语法
- [ ] 前端使用 shadcn/ui 组件


