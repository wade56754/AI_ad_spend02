# C2 投手管理 - 后端模块规格书

> **版本**: v1.0
> **更新日期**: 2025-12-23
> **SoT 基准**: DATA_SCHEMA.md v5.3, API_SOT.md v9.3, MASTER.md v4.4
> **参考指南**: docs/3.dev-guides/BACKEND_MODULE_SPEC_GUIDE.md

---

## 目录

- [§1 模块概述](#1-模块概述)
- [§2 数据模型](#2-数据模型)
- [§3 API 设计](#3-api-设计)
- [§4 权限控制](#4-权限控制)
- [§5 业务逻辑](#5-业务逻辑)
- [§6 前后端接口契约](#6-前后端接口契约)
- [§7 测试要点](#7-测试要点)
- [§8 性能要求](#8-性能要求)
- [§9 安全规范](#9-安全规范)

---

## §1 模块概述

### 1.1 业务目标

本模块实现投手（media_buyer）账号管理，解答核心管理问题：**"有哪些投手？负责什么？"**。支持投手账号的 CRUD 操作、主管分配、账户关联查询，为责任模型提供人员管理支撑。

**注意**: 投手管理通过通用用户管理 API 实现，筛选 `role=media_buyer` 即可获取投手列表。

### 1.2 涉及角色

| 角色 | 系统角色名 | 本模块权限 |
|------|------------|------------|
| 老板 | ceo | 查看全部投手概况 |
| 项目负责人 | project_owner | 查看项目内投手 |
| 财务 | finance | 查看投手列表（只读）|
| 主管 | supervisor (data_operator) | 查看团队投手、分配账户 |
| 投手 | pitcher (media_buyer) | 查看自己信息 |
| 户管 | account_manager | 查看/分配投手账户 |
| 管理员 | admin | **超级权限**: 创建/编辑/停用投手账号 |

### 1.3 模块边界

**本模块负责：**
- 投手账号 CRUD（基于 users 表，role=media_buyer）
- 投手账号启用/停用
- 投手与主管关系管理（通过 project_members 或扩展字段）
- 投手负责账户查询

**本模块不负责：**
- 投手绩效考核（Phase 2）
- 日报审核（由 B2 模块负责）
- 广告账户 CRUD（由账户管理模块负责）

### 1.4 SoT 引用清单 (AI 防幻觉)

| SoT 文档 | 版本 | 引用章节 | 用途 |
|---------|------|---------|------|
| DATA_SCHEMA.md | v5.3 | §3.1.1 users | 表结构、字段定义 |
| BUSINESS_RULES.md | v4.1 | BR-USER-001~003 | 用户业务规则 |
| ERROR_CODES_SOT.md | v2.1 | AUTH_*, BIZ_*, DB_* | 业务错误码 |
| API_SOT.md | v9.3 | §5 Users | API 端点规范 |
| AUTH_SPEC.md | v2.0 | §3 权限矩阵 | 角色权限 |
| MASTER.md | v4.4 | §2.4 七角色 | 角色定义、Phase 边界 |

### 1.5 角色映射表

**重要**: 代码中使用技术角色名，前端显示业务角色名

| 业务角色 | 技术角色名 | 说明 |
|----------|-----------|------|
| 投手 | `media_buyer` | 广告投放执行者 |
| 主管 | `data_operator` | 团队管理、日报审核 |
| 户管 | `account_manager` | 账户分配、监控 |

---

## §2 数据模型

### 2.1 表结构定义

**来源**: DATA_SCHEMA.md v5.3 §3.1.1, `backend/models/core/user.py`

```sql
CREATE TABLE users (
  -- 主键
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- 基本信息
  username        VARCHAR(50) NOT NULL UNIQUE,
  email           VARCHAR(100) NOT NULL UNIQUE,
  password_hash   VARCHAR(255),               -- bcrypt 哈希

  -- 角色与状态
  role            VARCHAR(20) NOT NULL,       -- admin/finance/data_operator/account_manager/media_buyer/project_owner
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,

  -- 审计字段
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE UNIQUE INDEX idx_users_username ON users(username);
CREATE UNIQUE INDEX idx_users_email ON users(email);
```

### 2.2 字段说明

| 字段 | 类型 | 必填 | 说明 | 验证规则 |
|------|------|------|------|----------|
| id | UUID | 自动 | 主键 | 系统生成 |
| username | VARCHAR(50) | ✅ | 用户名 | 2-50字符，唯一 |
| email | VARCHAR(100) | ✅ | 邮箱 | 有效邮箱，唯一 |
| password_hash | VARCHAR(255) | ✅ | 密码哈希 | bcrypt 加密 |
| role | VARCHAR(20) | ✅ | 角色 | 6 个合法值之一 |
| is_active | BOOLEAN | 自动 | 账号状态 | 默认 true |

### 2.3 扩展字段 (Schema 层)

以下字段在 Schema 层定义，用于 API 交互，模型层可能未实现：

| 字段 | 类型 | 说明 | 当前状态 |
|------|------|------|----------|
| full_name | VARCHAR(100) | 真实姓名 | Schema 有，Model 待扩展 |
| department | VARCHAR(100) | 部门 | Schema 有，Model 待扩展 |
| supervisor_id | UUID | 主管 ID | 待扩展 |
| team_name | VARCHAR(100) | 团队名称 | 待扩展 |

### 2.4 关联关系

```
users (role=media_buyer)
    ├──→ project_members (user_id → id) 一对多: 参与的项目
    ├──→ ad_accounts (pitcher_id → id) 一对多: 负责的账户
    ├──→ daily_reports (pitcher_id → id) 一对多: 提交的日报
    └──→ topup_requests (requested_by → id) 一对多: 充值申请
```

---

## §3 API 设计

### 3.1 端点清单

**来源**: API_SOT.md v9.3 §5, `backend/routers/users.py`

| 方法 | 端点 | 描述 | 权限 |
|------|------|------|------|
| GET | /api/v1/users | 用户列表（可筛选 role=media_buyer） | admin |
| POST | /api/v1/users | 创建用户（投手） | admin |
| GET | /api/v1/users/:id | 用户详情 | admin/self |
| PUT | /api/v1/users/:id | 更新用户 | admin |
| DELETE | /api/v1/users/:id | 软删除用户 | admin |
| GET | /api/v1/users/statistics/summary | 用户统计 | admin, finance, data_operator |

### 3.2 请求/响应格式

**列表查询参数**:
```typescript
interface UserListQuery {
  page?: number;          // 页码，默认 1
  page_size?: number;     // 每页数量，默认 20，最大 100
  role?: string;          // 角色筛选 (media_buyer 获取投手)
  is_active?: boolean;    // 状态筛选
  search?: string;        // 搜索用户名或邮箱
}
```

**创建投手请求**:
```typescript
interface UserCreateRequest {
  username: string;        // 必填，2-50字符
  email: string;           // 必填，有效邮箱
  password: string;        // 必填，最少8位
  role: 'media_buyer';     // 必填，指定为投手
  full_name?: string;      // 可选，真实姓名
  department?: string;     // 可选，部门
  is_active?: boolean;     // 可选，默认 true
}
```

**更新投手请求**:
```typescript
interface UserUpdateRequest {
  username?: string;
  email?: string;
  password?: string;       // 新密码
  role?: string;           // 角色变更
  full_name?: string;
  department?: string;
  is_active?: boolean;
}
```

**响应格式**:
```typescript
interface UserResponse {
  id: string;              // UUID
  username: string;
  email: string;
  full_name?: string;
  role: string;
  department?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

interface UserListResponse {
  id: string;
  username: string;
  full_name?: string;
  email: string;
  role: string;
  department?: string;
  is_active: boolean;
  created_at: string;
}
```

### 3.3 错误码定义

**来源**: ERROR_CODES_SOT.md v2.1

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| AUTH_500 | 403 | 权限不足 |
| BIZ_002 | 404 | 用户不存在 |
| DB_004 | 409 | 用户名或邮箱已存在 |
| VALIDATION_002 | 400 | 参数验证失败 |

### 3.4 分页/筛选规范

```yaml
分页:
  页码: 从 1 开始
  默认每页: 20 条
  最大每页: 100 条

筛选:
  role: 精确匹配 (media_buyer 获取投手)
  is_active: 精确匹配
  search: 模糊匹配 (username ILIKE 或 email ILIKE)

排序:
  默认: created_at DESC
```

---

## §4 权限控制

### 4.1 角色权限矩阵 (7 角色)

**来源**: AUTH_SPEC.md v2.0, MASTER.md v4.4 §2.4

| 操作 | ceo | project_owner | finance | supervisor | pitcher | account_manager | admin |
|------|-----|---------------|---------|------------|---------|-----------------|-------|
| 列表 (全部) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 列表 (团队) | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| 查看详情 | ✅ | ✅ (项目内) | ✅ | ✅ (团队) | ✅ (自己) | ✅ | ✅ |
| 创建 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 更新 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 停用/启用 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 统计 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |

### 4.2 数据权限规则

```typescript
function canAccessUser(currentUser: User, targetUser: User): boolean {
  // Admin 可以访问所有用户
  if (currentUser.role === 'admin') return true;

  // 用户可以访问自己
  if (currentUser.id === targetUser.id) return true;

  // Finance 和 data_operator 可以查看列表
  if (['finance', 'data_operator'].includes(currentUser.role)) return true;

  // 其他角色暂不支持
  return false;
}

function canModifyUser(currentUser: User, targetUser: User): boolean {
  // 仅 Admin 可以修改用户
  return currentUser.role === 'admin';
}
```

### 4.3 字段级权限

| 字段 | 创建时 | 更新时 | 查看 |
|------|--------|--------|------|
| username | ✅ 必填 | ✅ 可改 | ✅ 所有角色 |
| email | ✅ 必填 | ✅ 可改 | ✅ 所有角色 |
| password | ✅ 必填 | ✅ 可改 | ❌ 不可见 |
| role | ✅ 必填 | ✅ admin 可改 | ✅ 所有角色 |
| is_active | ❌ 默认 true | ✅ admin 可改 | ✅ 所有角色 |

---

## §5 业务逻辑

### 5.1 业务规则

**来源**: BUSINESS_RULES.md v4.1

| 规则编号 | 规则描述 | 验证方式 |
|----------|----------|----------|
| BR-USER-001 | 用户名必须唯一 | DB UNIQUE 约束 + 代码校验 |
| BR-USER-002 | 邮箱必须唯一 | DB UNIQUE 约束 + 代码校验 |
| BR-USER-003 | 角色必须是 6 个合法值之一 | Schema 验证 |
| BR-USER-004 | 不能删除自己 | Service 层校验 |
| BR-USER-005 | 密码最少 8 位 | Schema 验证 |

### 5.2 验证规则 (Pydantic Schema)

```python
# 合法角色列表
VALID_ROLES = ["admin", "finance", "data_operator", "account_manager", "media_buyer", "project_owner"]

class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=8, max_length=128)
    role: Literal["admin", "finance", "data_operator", "account_manager", "media_buyer"] = Field(...)
    full_name: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    is_active: bool = Field(default=True)

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in VALID_ROLES:
            raise ValueError(f"无效的角色: {v}")
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度不能少于8位")
        return v
```

### 5.3 软删除逻辑

```python
def delete_user(user_id: UUID, current_user: User) -> bool:
    """软删除用户"""
    # 权限检查
    if current_user.role != "admin":
        raise PermissionDeniedError("仅管理员可删除用户")

    # 不能删除自己
    if current_user.id == user_id:
        raise PermissionDeniedError("不能删除当前登录用户")

    # 软删除：设置 is_active=False
    user = get_user(user_id)
    user.is_active = False
    db.commit()
    return True
```

### 5.4 Phase 1 规则 (照亮阶段)

```yaml
Phase 1 规则:
  ❌ 禁止: 自动停用投手、绩效考核关联、CPL 阻断
  ✅ 允许: 信息维护、手动停用、账户分配查看

  投手管理约束:
    - 投手 KPI（CPL）仅用于"观察与沟通"
    - 主管的权力仅限于"沟通反馈"
    - 禁止自动暂停投手账户
    - 停用投手必须手动操作（admin）
```

---

## §6 前后端接口契约

### 6.1 字段映射

| 后端字段 (snake_case) | 前端字段 (camelCase) | 说明 |
|----------------------|---------------------|------|
| user_id | userId | UUID 字符串 |
| full_name | fullName | 真实姓名 |
| is_active | isActive | 布尔值 |
| created_at | createdAt | ISO 8601 字符串 |
| updated_at | updatedAt | ISO 8601 字符串 |
| password_hash | - | 不传输 |

### 6.2 角色枚举对照

```typescript
// 技术角色值 (后端存储)
type TechRole = 'admin' | 'finance' | 'data_operator' | 'account_manager' | 'media_buyer' | 'project_owner';

// 业务角色显示 (前端)
const ROLE_LABELS: Record<TechRole, string> = {
  admin: '管理员',
  finance: '财务',
  data_operator: '主管',      // supervisor 映射
  account_manager: '户管',
  media_buyer: '投手',        // pitcher 映射
  project_owner: '项目负责人',
};

// 角色颜色
const ROLE_COLORS: Record<TechRole, string> = {
  admin: 'red',
  finance: 'blue',
  data_operator: 'green',
  account_manager: 'orange',
  media_buyer: 'purple',
  project_owner: 'cyan',
};
```

### 6.3 时区/格式约定

```yaml
时间格式:
  时间戳: ISO 8601 (含时区，如 2024-12-23T10:00:00Z)

时区处理:
  存储: UTC
  传输: UTC
  显示: 前端转换为本地时区

ID 格式:
  用户 ID: UUID 字符串

空值:
  null: 表示无值/未知
  "": 空字符串表示已设置但为空
```

---

## §7 测试要点

### 7.1 单元测试

```python
describe('UserService', () => {
    describe('create_user', () => {
        it('应创建投手成功', async () => {
            user = service.create_user(
                UserCreate(
                    username='pitcher1',
                    email='pitcher1@test.com',
                    password='password123',
                    role='media_buyer'
                ),
                admin_user
            )
            assert user.role == 'media_buyer'
            assert user.is_active == True
        });

        it('应拒绝非 admin 创建', async () => {
            with pytest.raises(PermissionDeniedError):
                service.create_user(user_data, pitcher_user)
        });

        it('应拒绝重复用户名 (BR-USER-001)', async () => {
            service.create_user(user_data, admin_user)
            with pytest.raises(ResourceConflictError):
                service.create_user(same_username_data, admin_user)
        });

        it('应拒绝重复邮箱 (BR-USER-002)', async () => {
            service.create_user(user_data, admin_user)
            with pytest.raises(ResourceConflictError):
                service.create_user(same_email_data, admin_user)
        });

        it('应拒绝无效角色 (BR-USER-003)', async () => {
            with pytest.raises(ValidationError):
                UserCreate(..., role='invalid_role')
        });

        it('应拒绝短密码 (BR-USER-005)', async () => {
            with pytest.raises(ValidationError):
                UserCreate(..., password='short')
        });
    });

    describe('delete_user', () => {
        it('应软删除用户', async () => {
            service.delete_user(user_id, admin_user)
            user = get_user(user_id)
            assert user.is_active == False
        });

        it('不能删除自己 (BR-USER-004)', async () => {
            with pytest.raises(PermissionDeniedError):
                service.delete_user(admin_user.id, admin_user)
        });
    });
});
```

### 7.2 集成测试

```python
describe('GET /api/v1/users?role=media_buyer', () => {
    it('应返回投手列表', async () => {
        response = await client.get(
            '/api/v1/users?role=media_buyer',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        for user in response.json()['data']['items']:
            assert user['role'] == 'media_buyer'
    });

    it('非 admin 不能访问', async () => {
        response = await client.get(
            '/api/v1/users',
            headers={'Authorization': f'Bearer {pitcher_token}'}
        )
        assert response.status_code == 403
    });
});

describe('POST /api/v1/users', () => {
    it('创建投手', async () => {
        response = await client.post(
            '/api/v1/users',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'username': 'new_pitcher',
                'email': 'pitcher@test.com',
                'password': 'password123',
                'role': 'media_buyer'
            }
        )
        assert response.status_code == 201
        assert response.json()['data']['role'] == 'media_buyer'
    });
});
```

### 7.3 权限测试矩阵

```python
test_cases = [
    # [角色, 操作, 预期结果]
    ('admin', 'list_all', 200),
    ('admin', 'create', 201),
    ('admin', 'update', 200),
    ('admin', 'delete', 200),
    ('admin', 'delete_self', 403),
    ('finance', 'list_all', 403),
    ('data_operator', 'list_all', 403),
    ('media_buyer', 'list_all', 403),
    ('media_buyer', 'get_self', 200),
    ('media_buyer', 'get_other', 403),
    ('media_buyer', 'create', 403),
]

@pytest.mark.parametrize('role,action,expected', test_cases)
def test_permissions(role, action, expected):
    response = execute_action(role, action)
    assert response.status_code == expected
```

---

## §8 性能要求

### 8.1 响应时间要求

| API | 目标 | 最大容忍 |
|-----|------|----------|
| 列表查询 | < 200ms | < 500ms |
| 详情查询 | < 100ms | < 300ms |
| 创建/更新 | < 300ms | < 1s |
| 统计查询 | < 500ms | < 1s |

### 8.2 索引要求

必须为以下查询场景建立索引：
- 按角色筛选 (idx_users_role)
- 按状态筛选 (idx_users_is_active)
- 用户名唯一约束 (idx_users_username)
- 邮箱唯一约束 (idx_users_email)

### 8.3 批量操作限制

| 操作 | 单次上限 | 说明 |
|------|----------|------|
| 批量创建 | 20 个 | 超出需分批 |
| 导出列表 | 1000 条 | 超出走异步 |

---

## §9 安全规范

### 9.1 认证授权

- 所有 API 需要 JWT Token
- 密码使用 bcrypt 哈希存储
- 用户 CRUD 仅 admin 可操作
- 用户只能查看自己的详情（非 admin）

### 9.2 输入验证

- [x] 使用 Pydantic 验证所有输入
- [x] 用户名 2-50 字符
- [x] 邮箱格式验证 (EmailStr)
- [x] 密码最少 8 位
- [x] 角色必须是合法枚举值

### 9.3 敏感数据保护

| 字段 | 存储 | API 响应 |
|------|------|----------|
| password | bcrypt 哈希 | 不返回 |
| password_hash | 数据库 | 不返回 |
| email | 明文 | 返回（需权限） |

### 9.4 审计日志

必须记录以下操作：

| 操作类型 | 记录内容 |
|----------|----------|
| 创建用户 | 操作人、时间、新用户信息 |
| 更新用户 | 操作人、时间、变更字段 |
| 停用用户 | 操作人、时间、目标用户 |
| 启用用户 | 操作人、时间、目标用户 |
| 角色变更 | 操作人、时间、旧角色→新角色 |

---

## 附录: AI 代码工厂禁止行为清单

### A.1 禁止行为

| 禁止行为 | 正确做法 | 检查方式 |
|---------|---------|---------|
| 自定义角色值 | 使用 6 个标准角色 | 枚举检查 |
| 明文存储密码 | bcrypt 哈希 | 代码审查 |
| 返回密码字段 | password_hash 不返回 | API 测试 |
| 跳过权限检查 | Service 层必须检查 | 代码审查 |
| 自动停用投手 | 仅手动停用 (Phase 1) | 逻辑审查 |
| 使用废弃角色名 | pitcher→media_buyer | grep 检查 |

### A.2 SoT 追溯验证 Checklist

生成代码后必须验证：
- [ ] 所有角色值来自 MASTER.md v4.4 §2.4 (6 个技术角色)
- [ ] 所有字段来自 DATA_SCHEMA.md
- [ ] 所有错误码来自 ERROR_CODES_SOT.md
- [ ] 密码使用 bcrypt 哈希
- [ ] API 响应不包含 password_hash
- [ ] 遵循 Phase 1 规则（无自动停用）

---

## 源码位置

| 层 | 文件路径 |
|----|---------|
| Model | `backend/models/core/user.py` |
| Service | `backend/services/user_service.py` |
| Router | `backend/routers/users.py` |
| Schema | `backend/schemas/user.py` |
| Enum | `backend/models/enums.py` (UserRole) |
| Test | `backend/tests/test_users_api.py` |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-23 | 初始版本，基于现有用户管理代码提取规格 |

---

**维护者**: AI 广告代投系统开发团队
**关联文档**: C2-pitcher-mgmt.md (前端规格)
