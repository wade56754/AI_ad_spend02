# 📋 P2 阶段详细规划文档

**版本**：v1.0
**日期**：2025-11-20
**状态**：规划阶段（待批准后分批执行）

---

## 📌 总览

P2 阶段主要聚焦于三大方向的规范化工作：
1. **数据库层规范化**：清洗历史角色数据、调整字段约束
2. **错误码统一**：对齐 ERROR_CODES.md 规范
3. **响应格式统一**：统一接口响应结构，添加 request_id 等字段

---

## 1️⃣ 数据库层规范化

### 1.1 当前状态分析

**发现的问题**：
1. `users` 表的 `role` 字段可能存在历史旧角色值（user, manager, operator, viewer）
2. `users` 表没有 CHECK 约束来限制 role 字段只能是 5 个合法角色
3. 数据库中可能残留 `hashed_password` 字段（虽然 model 和 schema 已清理）

**涉及的表**：
- `public.users` - 用户表
- `public.audit_logs` - 审计日志表（可能需要清洗旧角色记录）

---

### 1.2 数据库迁移 SQL 脚本

#### **脚本 1：清洗历史角色数据**

```sql
-- ============================================================
-- P2 数据库迁移脚本 #1：清洗历史角色数据
-- ============================================================
-- 用途：将 users 表中的旧角色值映射到新的合法角色
-- 风险：中等 - 会修改现有用户的角色数据
-- 建议：执行前先备份 users 表
-- ============================================================

BEGIN;

-- 创建临时表记录变更
CREATE TEMP TABLE role_migration_log (
    user_id UUID,
    old_role TEXT,
    new_role TEXT,
    migrated_at TIMESTAMP DEFAULT NOW()
);

-- 映射规则：
-- user → media_buyer（默认最低权限角色）
-- manager → account_manager
-- operator → data_operator
-- viewer → media_buyer（视为最低权限）
-- 其他未知角色 → media_buyer

-- 更新 user → media_buyer
INSERT INTO role_migration_log (user_id, old_role, new_role)
SELECT id, role, 'media_buyer'
FROM users
WHERE role = 'user';

UPDATE users
SET role = 'media_buyer', updated_at = NOW()
WHERE role = 'user';

-- 更新 manager → account_manager
INSERT INTO role_migration_log (user_id, old_role, new_role)
SELECT id, role, 'account_manager'
FROM users
WHERE role = 'manager';

UPDATE users
SET role = 'account_manager', updated_at = NOW()
WHERE role = 'manager';

-- 更新 operator → data_operator
INSERT INTO role_migration_log (user_id, old_role, new_role)
SELECT id, role, 'data_operator'
FROM users
WHERE role = 'operator';

UPDATE users
SET role = 'data_operator', updated_at = NOW()
WHERE role = 'operator';

-- 更新 viewer → media_buyer
INSERT INTO role_migration_log (user_id, old_role, new_role)
SELECT id, role, 'media_buyer'
FROM users
WHERE role = 'viewer';

UPDATE users
SET role = 'media_buyer', updated_at = NOW()
WHERE role = 'viewer';

-- 更新其他未知角色 → media_buyer（容错处理）
INSERT INTO role_migration_log (user_id, old_role, new_role)
SELECT id, role, 'media_buyer'
FROM users
WHERE role NOT IN ('admin', 'finance', 'account_manager', 'data_operator', 'media_buyer');

UPDATE users
SET role = 'media_buyer', updated_at = NOW()
WHERE role NOT IN ('admin', 'finance', 'account_manager', 'data_operator', 'media_buyer');

-- 输出变更日志
SELECT
    old_role,
    new_role,
    COUNT(*) as user_count
FROM role_migration_log
GROUP BY old_role, new_role
ORDER BY old_role;

-- 如果一切正常，提交事务
-- COMMIT;

-- 如果需要回滚，执行：
-- ROLLBACK;
```

**执行前检查**：
```sql
-- 检查当前 users 表中的角色分布
SELECT role, COUNT(*) as count
FROM users
GROUP BY role
ORDER BY count DESC;
```

**预期输出**：
```
| old_role  | new_role         | user_count |
|-----------|------------------|------------|
| user      | media_buyer      | X          |
| manager   | account_manager  | Y          |
| operator  | data_operator    | Z          |
| viewer    | media_buyer      | W          |
```

---

#### **脚本 2：添加角色约束**

```sql
-- ============================================================
-- P2 数据库迁移脚本 #2：添加角色 CHECK 约束
-- ============================================================
-- 用途：强制 role 字段只能是 5 个合法角色之一
-- 风险：低 - 仅添加约束，不修改数据
-- 前提：必须先执行脚本 #1 清洗历史数据
-- ============================================================

BEGIN;

-- 添加 CHECK 约束
ALTER TABLE users
ADD CONSTRAINT check_role_enum
CHECK (role IN ('admin', 'finance', 'account_manager', 'data_operator', 'media_buyer'));

-- 验证约束已生效
SELECT
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'users'::regclass
  AND contype = 'c';

COMMIT;
```

**回滚脚本**（如需撤销约束）：
```sql
ALTER TABLE users DROP CONSTRAINT IF EXISTS check_role_enum;
```

---

#### **脚本 3：删除 hashed_password 字段（可选）**

```sql
-- ============================================================
-- P2 数据库迁移脚本 #3：删除 hashed_password 字段
-- ============================================================
-- 用途：从 users 表删除 hashed_password 字段（如果存在）
-- 风险：高 - 不可逆操作，删除后无法恢复
-- 前提：确认已完全迁移到 Supabase Auth
-- 建议：先在测试环境验证，生产环境执行前备份
-- ============================================================

-- ⚠️ 警告：此操作不可逆！请先确认备份！

BEGIN;

-- 检查字段是否存在
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'users'
  AND column_name = 'hashed_password';

-- 如果存在，则删除
ALTER TABLE users DROP COLUMN IF EXISTS hashed_password;

COMMIT;
```

**执行前确认**：
```sql
-- 确认所有用户都已迁移到 Supabase Auth
SELECT COUNT(*) as users_without_supabase_link
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM auth.users au WHERE au.id = u.id
);

-- 应该返回 0，否则不要执行删除操作
```

---

### 1.3 Alembic 迁移文件（推荐方式）

创建文件：`backend/alembic/versions/YYYYMMDD_HHMM_p2_role_cleanup.py`

```python
"""P2: 清洗历史角色数据并添加约束

Revision ID: p2_role_cleanup
Revises: <previous_revision>
Create Date: 2025-11-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'p2_role_cleanup'
down_revision = '<previous_revision>'  # 替换为实际的上一个版本号
branch_labels = None
depends_on = None


def upgrade():
    """升级：清洗角色数据并添加约束"""

    # 1. 创建临时日志表
    op.execute("""
        CREATE TEMP TABLE role_migration_log (
            user_id UUID,
            old_role TEXT,
            new_role TEXT,
            migrated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # 2. 映射旧角色到新角色
    role_mappings = [
        ('user', 'media_buyer'),
        ('manager', 'account_manager'),
        ('operator', 'data_operator'),
        ('viewer', 'media_buyer'),
    ]

    for old_role, new_role in role_mappings:
        # 记录日志
        op.execute(f"""
            INSERT INTO role_migration_log (user_id, old_role, new_role)
            SELECT id, role, '{new_role}'
            FROM users
            WHERE role = '{old_role}'
        """)

        # 更新角色
        op.execute(f"""
            UPDATE users
            SET role = '{new_role}', updated_at = NOW()
            WHERE role = '{old_role}'
        """)

    # 3. 处理其他未知角色（容错）
    op.execute("""
        UPDATE users
        SET role = 'media_buyer', updated_at = NOW()
        WHERE role NOT IN ('admin', 'finance', 'account_manager', 'data_operator', 'media_buyer')
    """)

    # 4. 添加 CHECK 约束
    op.create_check_constraint(
        'check_role_enum',
        'users',
        "role IN ('admin', 'finance', 'account_manager', 'data_operator', 'media_buyer')"
    )

    # 5. 输出变更统计（写入日志）
    print("=== Role Migration Summary ===")
    result = op.get_bind().execute("""
        SELECT old_role, new_role, COUNT(*) as user_count
        FROM role_migration_log
        GROUP BY old_role, new_role
        ORDER BY old_role
    """)
    for row in result:
        print(f"{row.old_role} → {row.new_role}: {row.user_count} users")


def downgrade():
    """降级：移除约束（不恢复旧角色数据）"""

    # 移除 CHECK 约束
    op.drop_constraint('check_role_enum', 'users', type_='check')

    # 注意：不恢复旧角色数据，因为映射是有损的
    print("警告：角色数据不会回滚到旧值")
```

**执行命令**：
```bash
# 生成迁移文件
alembic revision --autogenerate -m "P2: 清洗历史角色数据并添加约束"

# 执行迁移
alembic upgrade head

# 如需回滚
alembic downgrade -1
```

---

### 1.4 影响范围与风险评估

| 变更项 | 影响范围 | 风险等级 | 缓解措施 |
|--------|----------|----------|----------|
| 清洗角色数据 | 所有 users 表记录 | 🟡 中 | 1. 先在测试环境验证<br>2. 执行前备份数据库<br>3. 使用事务确保原子性 |
| 添加 CHECK 约束 | 新增/更新用户操作 | 🟢 低 | 1. 确保应用层代码已更新<br>2. 约束可以随时移除 |
| 删除 hashed_password | users 表结构 | 🔴 高 | 1. 仅在确认 100% 迁移到 Supabase Auth 后执行<br>2. 不可逆操作，谨慎执行 |

**影响的应用层文件**：
- 无（P1 阶段已完成应用层修改）

---

## 2️⃣ 错误码统一方案

### 2.1 当前状态分析

**ERROR_CODES.md 规范要求**：
```json
{
    "success": false,
    "message": "具体错误信息",
    "code": "AUTH_401",  // ✅ 使用错误码标识符
    "request_id": "uuid-string",  // ✅ 必须包含
    "timestamp": "2025-11-20T10:00:00Z"
}
```

**当前实现问题**：
1. `dependencies.py` 中的 HTTPException 使用了 `code` 字段，但是数字而非字符串标识符（如 `"code": "AUTH_400"`）
2. `app/utils/response.py` 中的响应函数使用 `code` 作为 HTTP 状态码（数字），而非错误码标识符
3. 缺少 `request_id` 字段
4. `app/api/v1/auth.py` 使用旧的响应格式

---

### 2.2 错误码映射表

| HTTP 状态码 | 错误码标识符 | 错误信息 | 使用场景 |
|-------------|-------------|----------|----------|
| 400 | `AUTH_400` | 未提供认证令牌 | 请求头缺少 Authorization |
| 401 | `AUTH_401` | 无效的认证令牌 | Token 验证失败 |
| 401 | `AUTH_402` | 令牌已过期 | Token 过期 |
| 403 | `AUTH_002` | 账户已被禁用 | is_active = False |
| 403 | `AUTH_500` | 权限不足 | 角色权限不足 |
| 404 | `AUTH_004` | 用户不存在或已被禁用 | 用户查询失败 |
| 500 | `SYS_001` | 系统内部错误 | 未捕获的异常 |

---

### 2.3 需要修改的文件清单

| 文件路径 | 当前问题 | 修改内容 |
|----------|----------|----------|
| `app/utils/response.py` | 响应格式缺少 `request_id` 和错误码标识符 | 1. 添加 `request_id` 生成逻辑<br>2. `code` 字段改为错误码标识符<br>3. 新增 `http_status` 字段存储 HTTP 状态码 |
| `app/dependencies.py` | HTTPException detail 格式不符合规范 | 1. 添加 `request_id`<br>2. `code` 改为字符串标识符（如 `"AUTH_400"`） |
| `app/api/v1/auth.py` | 使用旧的 `create_api_response` 格式 | 1. 统一使用新的响应格式<br>2. 添加错误码标识符 |
| `app/routers/auth.py` | 返回格式简单（可能需要完善） | 确保符合新规范 |
| `app/routers/me.py` | 同上 | 同上 |
| `app/routers/admin_roles.py` | 返回裸字典格式 | 改用统一响应函数 |

---

### 2.4 修改方案

#### **方案 A：渐进式升级（推荐）**

**阶段 1**：保持向后兼容，添加新字段
- 在 `response.py` 中添加 `request_id` 生成
- 新增 `error_code` 字段，保留 `code` 作为 HTTP 状态码
- 响应格式：
  ```json
  {
      "success": false,
      "message": "错误信息",
      "code": 401,  // HTTP 状态码（兼容旧版）
      "error_code": "AUTH_401",  // 新增：错误码标识符
      "request_id": "uuid",  // 新增
      "timestamp": "2025-11-20T10:00:00Z"
  }
  ```

**阶段 2**（待前端适配后）：移除 `code` 字段，`error_code` 改名为 `code`
- 最终格式：
  ```json
  {
      "success": false,
      "message": "错误信息",
      "code": "AUTH_401",  // 错误码标识符
      "request_id": "uuid",
      "timestamp": "2025-11-20T10:00:00Z"
  }
  ```

---

#### **方案 B：一步到位（风险较高）**

直接按照 ERROR_CODES.md 规范修改所有响应格式，可能导致前端调用失败。

**不推荐理由**：
- 需要前端同步修改
- 可能影响线上服务
- 缺少过渡期

---

### 2.5 代码修改示例（方案 A - 阶段 1）

#### **修改 `app/utils/response.py`**

```python
import uuid
from datetime import datetime
from typing import Any, Optional, Dict

def generate_request_id() -> str:
    """生成唯一请求 ID"""
    return str(uuid.uuid4())

def error_response(
    message: str = "操作失败",
    code: int = 400,  # HTTP 状态码（兼容旧版）
    error_code: Optional[str] = None,  # ✅ 新增：错误码标识符
    data: Any = None,
    timestamp: str = None,
    request_id: str = None  # ✅ 新增
) -> Dict[str, Any]:
    """错误响应格式（符合 ERROR_CODES.md 规范）"""

    response = {
        "success": False,
        "message": message,
        "code": code,  # 兼容旧版
        "data": data,
        "timestamp": timestamp or datetime.now().isoformat(),
        "request_id": request_id or generate_request_id()  # ✅ 新增
    }

    # ✅ 新增：错误码标识符
    if error_code:
        response["error_code"] = error_code

    logger.error(f"API响应错误: {message} [request_id={response['request_id']}]")
    return response
```

#### **修改 `app/dependencies.py`**

```python
async def get_current_user(...) -> CurrentUser:
    if not credentials:
        request_id = str(uuid.uuid4())
        logger.warning(f"未提供认证令牌 [request_id={request_id}]")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "未提供认证令牌",
                "code": 401,  # HTTP 状态码（兼容）
                "error_code": "AUTH_400",  # ✅ 新增：错误码标识符
                "request_id": request_id  # ✅ 新增
            }
        )
```

---

### 2.6 影响范围与风险评估

| 变更项 | 影响文件数 | API 数量 | 风险等级 | 缓解措施 |
|--------|-----------|----------|----------|----------|
| 添加 `request_id` 和 `error_code` | 6 个 | ~15 个 | 🟢 低 | 向后兼容，不破坏现有调用 |
| 统一错误码标识符 | 6 个 | ~15 个 | 🟡 中 | 需要文档说明新字段 |
| 移除旧 `code` 字段 | 6 个 | ~15 个 | 🔴 高 | 需要前端同步修改，建议延后执行 |

**影响的 API 端点**：
- `POST /auth/login`
- `POST /auth/register`
- `GET /auth/me`
- `GET /me`
- `POST /admin/users/{user_id}/roles/{role_id}`
- 所有受保护的 API（使用 `get_current_user` 依赖）

---

## 3️⃣ 响应格式统一方案

### 3.1 当前状态分析

**发现的不一致**：

1. `app/routers/admin_roles.py` 返回裸字典：
   ```python
   return {"data": data, "error": None, "meta": {"count": len(data)}}
   ```

2. `app/api/v1/auth.py` 使用 `create_api_response`（格式正确但缺少 request_id）

3. `app/routers/auth.py` 和 `app/routers/me.py` 返回裸字典（P1 阶段已修复字段名，但格式仍需完善）

---

### 3.2 标准响应格式

**成功响应**：
```json
{
    "success": true,
    "message": "操作成功",
    "data": {...},
    "request_id": "uuid",
    "timestamp": "2025-11-20T10:00:00Z"
}
```

**错误响应**：
```json
{
    "success": false,
    "message": "错误信息",
    "code": "AUTH_401",  // 错误码标识符
    "request_id": "uuid",
    "timestamp": "2025-11-20T10:00:00Z",
    "data": null  // 可选，错误详情
}
```

**分页响应**：
```json
{
    "success": true,
    "message": "查询成功",
    "data": {
        "items": [...],
        "total": 100,
        "page": 1,
        "size": 20,
        "pages": 5
    },
    "request_id": "uuid",
    "timestamp": "2025-11-20T10:00:00Z"
}
```

---

### 3.3 需要修改的文件

| 文件 | 当前问题 | 修改方案 |
|------|----------|----------|
| `app/routers/admin_roles.py` | 返回裸字典 `{"data": ..., "error": ...}` | 改用 `success_response()` 或 `error_response()` |
| `app/routers/auth.py` | 返回裸字典 | 同上 |
| `app/routers/me.py` | 返回裸字典 | 同上 |

---

### 3.4 修改示例

#### **修改前（`app/routers/admin_roles.py`）**：
```python
@router.get("/roles", response_model=dict)
def list_roles(...):
    roles = db.query(Role).all()
    data = [{"id": r.id, "name": r.name, "description": r.description} for r in roles]
    return {"data": data, "error": None, "meta": {"count": len(data)}}
```

#### **修改后**：
```python
from app.utils.response import success_response

@router.get("/roles", response_model=dict)
def list_roles(...):
    roles = db.query(Role).all()
    data = [{"id": r.id, "name": r.name, "description": r.description} for r in roles]

    return success_response(
        data={
            "items": data,
            "total": len(data)
        },
        message="查询角色列表成功"
    )
```

---

### 3.5 影响范围

| Router 文件 | 端点数量 | 修改工作量 | 风险 |
|------------|----------|-----------|------|
| `admin_roles.py` | 4 个 | 小 | 低 |
| `auth.py` | 1 个 | 小 | 低 |
| `me.py` | 1 个 | 小 | 低 |
| **合计** | **6 个** | | |

---

## 4️⃣ 综合实施计划

### 4.1 推荐执行顺序

| 阶段 | 任务 | 优先级 | 风险 | 预估工作量 |
|------|------|--------|------|-----------|
| **P2.1** | 数据库角色数据清洗 | 🔴 高 | 🟡 中 | 2-4 小时 |
| **P2.2** | 添加角色 CHECK 约束 | 🔴 高 | 🟢 低 | 1 小时 |
| **P2.3** | 响应格式添加 request_id | 🟡 中 | 🟢 低 | 2-3 小时 |
| **P2.4** | 统一 Router 响应格式 | 🟡 中 | 🟢 低 | 2-3 小时 |
| **P2.5** | 错误码标识符统一 | 🟢 低 | 🟡 中 | 3-4 小时 |
| **P2.6** | 删除 hashed_password 字段 | ⚪ 可选 | 🔴 高 | 1 小时 |

---

### 4.2 分批执行建议

#### **第一批（数据库层）**：
- ✅ 执行数据库角色清洗（脚本 #1）
- ✅ 添加 CHECK 约束（脚本 #2）
- ⏸️ 暂不删除 hashed_password 字段

**理由**：先解决数据层规范化，确保应用层代码有正确的数据基础。

---

#### **第二批（响应格式 - 向后兼容）**：
- ✅ 在 `response.py` 中添加 `request_id` 生成
- ✅ 添加 `error_code` 字段（保留旧 `code` 字段）
- ✅ 统一 `admin_roles.py`, `auth.py`, `me.py` 的响应格式

**理由**：向后兼容，不破坏现有前端调用。

---

#### **第三批（错误码统一 - 需前端配合）**：
- 前端适配新的 `error_code` 字段
- 后端移除旧 `code` 字段，`error_code` 改名为 `code`

**理由**：需要前端同步修改，建议协调后执行。

---

### 4.3 回滚策略

| 阶段 | 回滚方法 |
|------|----------|
| 数据库角色清洗 | 使用备份恢复 `users` 表（无法精确回滚，因为映射有损） |
| CHECK 约束 | `ALTER TABLE users DROP CONSTRAINT check_role_enum;` |
| 响应格式修改 | Git revert 对应 commit |
| 删除字段 | **不可回滚** - 只能从备份恢复 |

---

## 5️⃣ 风险汇总与缓解措施

### 5.1 高风险项

| 风险项 | 影响 | 缓解措施 |
|--------|------|----------|
| 数据库角色清洗错误 | 用户角色被错误修改 | 1. 执行前完整备份<br>2. 先在测试环境验证<br>3. 使用事务确保原子性 |
| 删除 hashed_password | 数据永久丢失 | 1. 确认 100% 迁移到 Supabase Auth<br>2. 延后执行<br>3. 多次确认 |
| 错误码变更破坏前端 | API 调用失败 | 1. 采用渐进式方案<br>2. 向后兼容<br>3. 与前端团队协调 |

---

### 5.2 中风险项

| 风险项 | 影响 | 缓解措施 |
|--------|------|----------|
| 响应格式统一 | 部分前端需要适配 | 1. 提前通知<br>2. 提供迁移文档<br>3. 保留过渡期 |
| CHECK 约束阻止写入 | 测试数据无法插入 | 1. 更新测试数据生成器<br>2. 使用合法角色值 |

---

## 6️⃣ 测试计划

### 6.1 数据库迁移测试

```sql
-- 测试 1：验证角色清洗
SELECT role, COUNT(*) FROM users GROUP BY role;
-- 应该只返回 5 个合法角色

-- 测试 2：验证 CHECK 约束
INSERT INTO users (id, email, name, role)
VALUES (uuid_generate_v4(), 'test@example.com', 'Test', 'invalid_role');
-- 应该抛出 CHECK 约束错误

-- 测试 3：验证合法角色可以插入
INSERT INTO users (id, email, name, role)
VALUES (uuid_generate_v4(), 'test2@example.com', 'Test2', 'media_buyer');
-- 应该成功
```

---

### 6.2 API 测试清单

| 测试项 | 测试用例 | 预期结果 |
|--------|----------|----------|
| 响应包含 request_id | 调用任意 API | 响应包含 `request_id` 字段 |
| 错误响应包含 error_code | 触发 401 错误 | 响应包含 `"error_code": "AUTH_401"` |
| 统一响应格式 | 调用 `GET /admin/roles` | 返回 `{success, message, data, request_id, timestamp}` |
| 角色权限检查 | 非 admin 访问 `/admin` 端点 | 返回 403 + `"error_code": "AUTH_500"` |

---

## 7️⃣ 文档更新清单

完成 P2 阶段后，需要更新以下文档：

1. **API 文档**：更新响应格式示例，添加 `request_id` 和 `error_code` 说明
2. **错误码文档**：补充所有错误码的使用场景
3. **数据库 Schema 文档**：更新 `users` 表的 CHECK 约束说明
4. **迁移指南**：前端如何适配新的响应格式

---

## 8️⃣ 总结

### P2 阶段工作量预估

| 类别 | 任务数 | 预估时间 | 风险等级 |
|------|--------|----------|----------|
| 数据库迁移 | 3 个脚本 | 4-6 小时 | 🟡 中 |
| 错误码统一 | 6 个文件 | 6-8 小时 | 🟡 中 |
| 响应格式统一 | 3 个文件 | 4-5 小时 | 🟢 低 |
| 测试验证 | 全面测试 | 4-6 小时 | - |
| **合计** | - | **18-25 小时** | - |

---

### 推荐执行策略

1. **优先执行数据库层清洗**（P2.1 + P2.2）
2. **其次统一响应格式**（P2.3 + P2.4，向后兼容）
3. **最后统一错误码**（P2.5，需前端配合）
4. **延后执行删除字段**（P2.6，高风险，可选）

---

**文档状态**：📋 规划完成，等待批准后分批执行
**下一步**：请审阅并决定哪些部分优先落地、哪些先搁置。
