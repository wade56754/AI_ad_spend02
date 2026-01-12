# Python 技能 - 核心指令

> **技术栈**: FastAPI + SQLAlchemy 2.x + Pydantic v2

## 必须遵守的规范

### Pydantic v2 语法

```python
# SoT: .cursorrules#F-008
from pydantic import BaseModel, ConfigDict

class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    
    # ✅ 使用 model_dump() 
    def to_dict(self):
        return self.model_dump()

# ❌ 禁止使用 Pydantic v1 语法
# class Config:
#     orm_mode = True  # ❌
```

### SQLAlchemy 2.x 查询

```python
# SoT: .cursorrules#F-008
from sqlalchemy import select

# ✅ 正确: 使用 select()
result = session.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()

# ❌ 错误: 使用旧语法
# user = session.query(User).filter_by(id=user_id).first()
```

### API 响应格式 (Envelope)

```python
# SoT: AGENTS.md#API响应格式
from backend.core.response import success_response, error_response

# ✅ 成功响应
return success_response(data={"id": 1}, message="创建成功")

# ✅ 业务错误
from backend.core.error_codes import BusinessError, BusinessErrorCodes
raise BusinessError(code=BusinessErrorCodes.INVALID_STATE_TRANSITION)

# ❌ 禁止直接返回数据
# return {"id": 1, "name": "..."}

# ❌ 禁止自定义错误码
# raise HTTPException(status_code=400, detail="Invalid state")
```

### 类型提示

```python
# 所有函数必须有类型提示
async def get_user(user_id: UUID, db: Session) -> Optional[User]:
    ...

# 使用 Optional 而非 | None (兼容性)
from typing import Optional, List, Dict
```

## 反模式检查表

| 反模式 | 正确做法 |
|--------|---------|
| `class Config: orm_mode = True` | `model_config = ConfigDict(from_attributes=True)` |
| `session.query(User)` | `session.execute(select(User))` |
| `.dict()` | `.model_dump()` |
| `raise HTTPException(400)` | `raise BusinessError(code=...)` |
