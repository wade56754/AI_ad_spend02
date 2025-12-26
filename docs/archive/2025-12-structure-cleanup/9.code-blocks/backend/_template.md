# [代码块名称] - [中文名]

> **复用级别**: :red_circle: 核心 / :yellow_circle: 模块 / :green_circle: 专用
> **源码位置**: `backend/xxx/xxx.py`
> **最后更新**: YYYY-MM-DD

---

## 1. 概述

一句话描述这个代码块解决什么问题。

**使用场景**:
- 场景 1
- 场景 2

---

## 2. 接口契约

### 2.1 函数签名

```python
def function_name(
    param1: str,
    param2: int = 0,
    *,
    db: Session,
    current_user: User
) -> ReturnType:
    """
    函数说明

    Args:
        param1: 参数1说明
        param2: 参数2说明
        db: 数据库会话
        current_user: 当前用户

    Returns:
        返回值说明

    Raises:
        BusinessError: 业务错误
        ValidationError: 参数校验错误
    """
```

### 2.2 输入参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `param1` | `str` | :white_check_mark: | - | 描述 |
| `param2` | `int` | :x: | `0` | 描述 |
| `db` | `Session` | :white_check_mark: | - | 数据库会话 |
| `current_user` | `User` | :white_check_mark: | - | 当前用户 |

### 2.3 返回值

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 是否成功 |
| `data` | `dict` | 返回数据 |
| `message` | `str` | 消息 |

### 2.4 Pydantic Schema

```python
class InputSchema(BaseModel):
    """输入模型"""
    model_config = ConfigDict(from_attributes=True)

    field1: str
    field2: int = 0

class OutputSchema(BaseModel):
    """输出模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
```

---

## 3. 依赖

### 3.1 模块依赖

| 模块 | 用途 |
|------|------|
| `core.response` | 标准响应封装 |
| `core.error_codes` | 错误码定义 |

### 3.2 服务依赖

| 服务 | 用途 |
|------|------|
| `AuditService` | 审计日志 |
| `PermissionService` | 权限检查 |

### 3.3 代码块依赖

| 代码块 | 用途 |
|--------|------|
| `pagination` | 分页处理 |
| `audit-log` | 日志记录 |

---

## 4. 错误码

| 错误码 | 触发条件 | HTTP 状态 |
|--------|---------|----------|
| `VAL-001` | 参数校验失败 | 400 |
| `AUTH-002` | 权限不足 | 403 |
| `BIZ-003` | 业务规则违反 | 422 |
| `SYS-001` | 系统错误 | 500 |

---

## 5. 使用示例

### 5.1 基础用法

```python
from backend.services.xxx_service import function_name

# 在 Router 中使用
@router.post("/endpoint")
async def endpoint(
    request: InputSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = function_name(
        param1=request.field1,
        param2=request.field2,
        db=db,
        current_user=current_user
    )
    return success_response(data=result)
```

### 5.2 在 Service 中组合

```python
from backend.services.xxx_service import function_name
from backend.services.audit_service import AuditService

class MyService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def business_logic(self, user: User, data: dict):
        # 使用代码块
        result = function_name(
            param1=data["field1"],
            db=self.db,
            current_user=user
        )

        # 记录审计日志
        self.audit.log(
            entity_type="xxx",
            entity_id=result["id"],
            action="create",
            user_id=user.id
        )

        return result
```

---

## 6. 组合规则

### 6.1 推荐组合

| 组合代码块 | 组合方式 | 效果 |
|-----------|---------|------|
| `audit-log` | 后置调用 | 记录操作日志 |
| `permission-filter` | 前置调用 | 权限校验 |

### 6.2 互斥组合

| 互斥代码块 | 原因 |
|-----------|------|
| `xxx` | 功能重复 |

---

## 7. 数据库操作

### 7.1 读取操作

```python
# 查询示例
query = select(Model).where(Model.field == value)
result = db.execute(query).scalars().all()
```

### 7.2 写入操作

```python
# 创建示例
model = Model(**data)
db.add(model)
db.commit()
db.refresh(model)
```

---

## 8. 测试

### 8.1 测试文件位置

```
backend/tests/xxx/test_function_name.py
```

### 8.2 测试用例清单

- [ ] 正常流程测试
- [ ] 参数校验测试
- [ ] 权限校验测试
- [ ] 边界条件测试
- [ ] 错误处理测试

### 8.3 测试示例

```python
import pytest
from backend.services.xxx_service import function_name

def test_function_name_success(db_session, test_user):
    """测试正常流程"""
    result = function_name(
        param1="test",
        db=db_session,
        current_user=test_user
    )
    assert result["success"] is True

def test_function_name_validation_error(db_session, test_user):
    """测试参数校验"""
    with pytest.raises(ValidationError):
        function_name(
            param1="",  # 空字符串应该失败
            db=db_session,
            current_user=test_user
        )
```

---

## 9. 源码位置

| 类型 | 路径 |
|------|------|
| 实现 | `backend/services/xxx_service.py` |
| Schema | `backend/schemas/xxx.py` |
| 测试 | `backend/tests/services/test_xxx.py` |

---

## 10. 性能考虑

| 场景 | 建议 |
|------|------|
| 大数据量查询 | 使用分页 |
| 频繁调用 | 考虑缓存 |
| 批量操作 | 使用批量 API |

---

## 11. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | YYYY-MM-DD | 初始版本 |

---

## 12. 相关文档

- [API 定义](../../sot/API_SOT.md)
- [数据模型](../../sot/DATA_SCHEMA.md)
- [错误码](../../sot/ERROR_CODES_SOT.md)
