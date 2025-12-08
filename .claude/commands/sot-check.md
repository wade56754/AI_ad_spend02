---
description: "SoT 合规检查: 验证代码是否符合真相源规范"
argument-hint: "[file_or_dir]"
---

# SoT 合规检查器

检查代码是否符合 SoT (Source of Truth) 规范。

## 检查范围

用户输入: `$ARGUMENTS`

- 如果指定文件/目录，检查该范围
- 如果为空，检查 `backend/` 目录

## SoT 裁判链

按优先级检查:
```
1. STATE_MACHINE.md v2.6  - 状态枚举、转换规则
2. DATA_SCHEMA.md v5.2    - 数据模型、字段类型
3. BUSINESS_RULES.md v3.1 - 业务规则编号
4. API_SOT.md v9.0        - API 端点、请求响应
5. ERROR_CODES_SOT.md v2.1 - 错误码格式
6. LEDGER_SOT.md v1.1     - 账本操作规则
```

## 检查项

### 1. 状态枚举检查
- ❌ 禁止: 代码中自定义状态枚举
- ✅ 正确: 引用 STATE_MACHINE.md 定义的状态

```python
# ❌ 错误
class ReportStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"

# ✅ 正确 - 使用 8 状态机
# raw_submitted → trend_pending → trend_ok/trend_flagged
# → trend_resolved → final_pending → final_confirmed → final_locked
```

### 2. 错误码检查
- ❌ 禁止: 自定义错误码格式
- ✅ 正确: 使用 ERROR_CODES_SOT.md 中的错误码

```python
# ❌ 错误
raise HTTPException(status_code=400, detail="Invalid input")

# ✅ 正确
raise HTTPException(status_code=400, detail={"code": "VAL-001", "message": "..."})
```

### 3. 账本操作检查
- ❌ 禁止: 直接修改 balance 字段
- ✅ 正确: 通过 ledger_entries 表记录

### 4. 模型字段检查
- 验证字段类型与 DATA_SCHEMA.md 一致
- 验证主键类型 (BIGSERIAL vs UUID)
- 验证时间戳类型 (TIMESTAMPTZ)

## 输出格式

```
## SoT 合规检查报告

### 检查范围
- 目录: backend/routers/
- 文件数: N

### 发现问题

#### P0 (阻断级)
| 文件 | 行号 | 问题 | SoT 引用 |
|------|------|------|----------|
| xxx.py | 42 | 自定义状态枚举 | STATE_MACHINE.md §8 |

#### P1 (警告级)
| 文件 | 行号 | 问题 | SoT 引用 |
|------|------|------|----------|
| yyy.py | 88 | 错误码格式不规范 | ERROR_CODES_SOT.md |

### 统计
- P0: N 个
- P1: M 个
- 合规率: X%

### 建议修复
1. xxx.py:42 - 删除自定义枚举，使用 backend/models/enums.py
2. yyy.py:88 - 改用标准错误码格式
```
