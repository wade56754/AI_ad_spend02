# D1 项目管理 - 后端模块规格书

> **版本**: v1.0
> **更新日期**: 2025-12-23
> **SoT 基准**: DATA_SCHEMA.md v5.3, STATE_MACHINE.md v2.7, API_SOT.md v9.3
> **参考指南**: docs/2.dev-guides/BACKEND_MODULE_SPEC_GUIDE.md

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

本模块实现项目全生命周期管理，解答核心管理问题：**"有哪些项目？谁负责？"**。支持项目的 CRUD 操作、成员管理、费用跟踪和统计分析，为责任模型的"谁对结果负责"提供数据支撑。

### 1.2 涉及角色

| 角色 | 系统角色名 | 本模块权限 |
|------|------------|------------|
| 老板 | ceo | 查看所有项目、管理成员、变更状态 |
| 项目负责人 | project_owner | 管理负责项目、成员、费用 |
| 财务 | finance | 查看所有项目（只读）、统计 |
| 主管 | supervisor | 查看下属参与项目 |
| 投手 | pitcher (media_buyer) | 查看参与项目（只读） |
| 户管 | account_manager | 更新负责项目、添加费用 |
| 运营 | data_operator | 查看所有项目 |
| 管理员 | admin | **超级权限**: 所有操作含删除 |

### 1.3 模块边界

**本模块负责：**
- 项目 CRUD 操作
- 项目状态机流转 (5 状态)
- 项目成员管理 (owner/member/viewer)
- 项目费用跟踪
- 项目统计信息

**本模块不负责：**
- 项目盈亏计算（由结算模块负责）
- 消耗数据聚合（由日报/消耗模块负责）
- 广告账户管理（由账户模块负责）

### 1.4 SoT 引用清单 (AI 防幻觉)

| SoT 文档 | 版本 | 引用章节 | 用途 |
|---------|------|---------|------|
| DATA_SCHEMA.md | v5.3 | §3.1 projects, §3.2 project_members | 表结构、字段定义 |
| STATE_MACHINE.md | v2.7 | §5 项目状态机 | 状态流转规则 |
| BUSINESS_RULES.md | v4.1 | BR-PRJ-001~005 | 项目业务规则 |
| ERROR_CODES_SOT.md | v2.1 | BIZ_*, SYS_*, STATE_* | 业务错误码 |
| API_SOT.md | v9.3 | §6 Projects | API 端点规范 |
| AUTH_SPEC.md | v2.0 | §3 权限矩阵 | 角色权限 |
| MASTER.md | v4.4 | §2.4 七角色, §3.2 责任模型 | Phase 边界 |

---

## §2 数据模型

### 2.1 表结构定义

**来源**: DATA_SCHEMA.md v5.3 §3.1, `backend/models/core/project.py`

```sql
-- 项目主表
CREATE TABLE projects (
  -- 主键
  id              BIGSERIAL PRIMARY KEY,

  -- 基本信息
  name            VARCHAR(100) NOT NULL,
  project_code    VARCHAR(50),                    -- 项目代码（可选）
  client_name     VARCHAR(100),                   -- 客户联系人
  client_company  VARCHAR(200),                   -- 客户公司
  description     TEXT,                           -- 项目描述

  -- 状态
  status          VARCHAR(20) NOT NULL DEFAULT 'planning',

  -- 预算相关
  budget          DECIMAL(15,2),                  -- 项目预算
  currency        VARCHAR(3) DEFAULT 'USD',       -- 预算货币

  -- 日期范围
  start_date      DATE,                           -- 开始日期
  end_date        DATE,                           -- 结束日期

  -- 外键
  account_manager_id BIGINT,                      -- 账户管理员
  created_by      UUID REFERENCES users(id),      -- 创建者

  -- 并发控制
  version         INTEGER NOT NULL DEFAULT 1,

  -- 审计字段
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- 约束
  CONSTRAINT chk_projects_status CHECK (
    status IN ('planning', 'active', 'paused', 'completed', 'cancelled')
  )
);

-- 索引
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created_by ON projects(created_by);
CREATE INDEX idx_projects_account_manager_id ON projects(account_manager_id);
```

```sql
-- 项目成员表
CREATE TABLE project_members (
  -- 主键
  id              BIGSERIAL PRIMARY KEY,

  -- 外键
  project_id      BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  -- 业务字段
  role            VARCHAR(20) NOT NULL DEFAULT 'member',  -- owner/member/viewer
  permissions     JSONB,                                   -- 扩展权限配置
  notes           TEXT,                                    -- 备注

  -- 审计字段
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- 约束
  CONSTRAINT idx_project_members_project_user UNIQUE (project_id, user_id)
);

-- 索引
CREATE INDEX idx_project_members_project_id ON project_members(project_id);
CREATE INDEX idx_project_members_user_id ON project_members(user_id);
```

### 2.2 字段说明

**projects 表**

| 字段 | 类型 | 必填 | 说明 | 验证规则 |
|------|------|------|------|----------|
| id | BIGINT | 自动 | 主键 | 系统生成 |
| name | VARCHAR(100) | ✅ | 项目名称 | 1-100字符，唯一 |
| project_code | VARCHAR(50) | ❌ | 项目代码 | 可选，用于外部系统对接 |
| client_name | VARCHAR(100) | ❌ | 客户联系人 | 1-100字符 |
| client_company | VARCHAR(200) | ❌ | 客户公司 | 1-200字符 |
| description | TEXT | ❌ | 项目描述 | 最多1000字符 |
| status | VARCHAR(20) | 自动 | 项目状态 | 见状态机定义 |
| budget | DECIMAL(15,2) | ❌ | 项目预算 | ≥ 0 |
| currency | VARCHAR(3) | ❌ | 货币类型 | 默认 USD |
| start_date | DATE | ❌ | 开始日期 | - |
| end_date | DATE | ❌ | 结束日期 | ≥ start_date |
| account_manager_id | BIGINT | ❌ | 账户管理员ID | - |
| created_by | UUID | 自动 | 创建者ID | 系统填充 |

**project_members 表**

| 字段 | 类型 | 必填 | 说明 | 验证规则 |
|------|------|------|------|----------|
| id | BIGINT | 自动 | 主键 | 系统生成 |
| project_id | BIGINT | ✅ | 项目ID | 外键 |
| user_id | UUID | ✅ | 用户ID | 外键 |
| role | VARCHAR(20) | ✅ | 项目角色 | owner/member/viewer |
| permissions | JSONB | ❌ | 扩展权限 | JSON 格式 |

### 2.3 索引设计

| 索引名 | 字段 | 类型 | 用途 |
|--------|------|------|------|
| idx_projects_status | status | B-tree | 按状态筛选 |
| idx_projects_created_by | created_by | B-tree | 按创建者查询 |
| idx_projects_account_manager_id | account_manager_id | B-tree | 按管理员查询 |
| idx_project_members_project_id | project_id | B-tree | 按项目查成员 |
| idx_project_members_user_id | user_id | B-tree | 按用户查项目 |
| idx_project_members_project_user | (project_id, user_id) | Unique | 防重复成员 |

### 2.4 关联关系

```
projects
    ├──→ users (created_by → id) 多对一: 创建者
    ├──→ project_members (id → project_id) 一对多: 项目成员
    ├──→ ad_accounts (id → project_id) 一对多: 广告账户
    └──→ project_expenses (id → project_id) 一对多: 项目费用

project_members
    ├──→ projects (project_id → id) 多对一: 所属项目
    └──→ users (user_id → id) 多对一: 成员用户
```

---

## §3 API 设计

### 3.1 端点清单

**来源**: API_SOT.md v9.3 §6, `backend/routers/projects.py`

| 方法 | 端点 | 描述 | 权限 |
|------|------|------|------|
| GET | /api/v1/projects | 项目列表 | 登录用户 |
| POST | /api/v1/projects | 创建项目 | admin |
| GET | /api/v1/projects/statistics | 项目统计 | admin, finance, data_operator |
| GET | /api/v1/projects/:id | 项目详情 | 项目可访问者 |
| PUT | /api/v1/projects/:id | 更新项目 | admin, account_manager(负责人) |
| DELETE | /api/v1/projects/:id | 删除项目 | admin |
| POST | /api/v1/projects/:id/members | 添加成员 | admin, account_manager |
| GET | /api/v1/projects/:id/members | 成员列表 | 项目可访问者 |
| DELETE | /api/v1/projects/:id/members/:user_id | 移除成员 | admin, account_manager |
| POST | /api/v1/projects/:id/expenses | 添加费用 | admin, account_manager |
| GET | /api/v1/projects/:id/expenses | 费用列表 | 项目可访问者 |

### 3.2 请求/响应格式

**列表查询参数**:
```typescript
interface ProjectListQuery {
  page?: number;          // 页码，默认 1
  page_size?: number;     // 每页数量，默认 20，最大 100
  status?: string;        // 状态筛选
  manager_id?: number;    // 账户管理员筛选
  client_name?: string;   // 客户名称模糊搜索
}
```

**创建请求**:
```typescript
interface ProjectCreateRequest {
  name: string;                    // 必填，1-200字符
  client_name: string;             // 必填，1-200字符
  client_company: string;          // 必填，1-200字符
  description?: string;            // 可选，最多1000字符
  budget?: number;                 // 可选，≥0
  currency?: string;               // 可选，默认 USD
  start_date?: string;             // 可选，YYYY-MM-DD
  end_date?: string;               // 可选，YYYY-MM-DD
  account_manager_id?: number;     // 可选
}
```

**更新请求**:
```typescript
interface ProjectUpdateRequest {
  name?: string;
  client_name?: string;
  client_company?: string;
  description?: string;
  status?: 'planning' | 'active' | 'paused' | 'completed' | 'cancelled';
  budget?: number;
  start_date?: string;
  end_date?: string;
  account_manager_id?: number;
}
```

**成员分配请求**:
```typescript
interface ProjectMemberAssignRequest {
  user_id: string | number;        // 用户ID（UUID 或 int）
  role: 'account_manager' | 'media_buyer' | 'analyst';
}
```

**响应格式**:
```typescript
interface ProjectResponse {
  id: number;
  name: string;
  client_name: string;
  client_company: string;
  description?: string;
  status: string;
  budget: number;
  currency: string;
  start_date?: string;
  end_date?: string;
  account_manager_id?: number;
  account_manager_name?: string;
  total_spent: number;
  total_accounts: number;
  active_accounts: number;
  created_by?: string;
  created_by_name: string;
  created_at: string;
  updated_at: string;
  // 计算字段
  remaining_budget: number;
  budget_usage_percent: number;
}

interface ProjectMemberResponse {
  id: number;
  user_id: string;
  user_name: string;
  user_email: string;
  user_role: string;         // 用户全局角色
  project_role: string;      // 项目内角色
  joined_at: string;
}
```

### 3.3 错误码定义

**来源**: ERROR_CODES_SOT.md v2.1

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| BIZ_002 | 404 | 项目不存在 |
| BIZ_001 | 400 | 业务逻辑错误（如日期范围无效） |
| AUTH_500 | 403 | 无权限操作 |
| BIZ_003 | 409 | 项目名称重复 |
| STATE_400 | 400 | 无效的状态转换 |

### 3.4 分页/筛选规范

```yaml
分页:
  页码: 从 1 开始
  默认每页: 20 条
  最大每页: 100 条

筛选:
  status: 精确匹配 (planning/active/paused/completed/cancelled)
  manager_id: 精确匹配
  client_name: 模糊匹配 (ILIKE)

排序:
  默认: created_at DESC
```

---

## §4 权限控制

### 4.1 角色权限矩阵 (8 角色)

**来源**: AUTH_SPEC.md v2.0, MASTER.md v4.4 §2.4

| 操作 | ceo | project_owner | finance | supervisor | pitcher | account_manager | data_operator | admin |
|------|-----|---------------|---------|------------|---------|-----------------|---------------|-------|
| 查看所有 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| 查看负责 | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| 查看参与 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 创建 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 更新 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅(负责) | ❌ | ✅ |
| 删除 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 管理成员 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| 添加费用 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| 统计 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |

### 4.2 数据权限规则

```typescript
function canAccessProject(user: User, project: Project): boolean {
  // Admin 和 data_operator 可以看所有
  if (['admin', 'data_operator'].includes(user.role)) return true;

  // account_manager 可以看负责的项目
  if (user.role === 'account_manager') {
    return project.account_manager_id === user.id;
  }

  // media_buyer 只能看参与的项目
  if (user.role === 'media_buyer') {
    return project.members.some(m => m.user_id === user.id);
  }

  // finance 可以查看所有项目
  if (user.role === 'finance') return true;

  return false;
}

function canUpdateProject(user: User, project: Project): boolean {
  if (user.role === 'admin') return true;
  if (user.role === 'account_manager') {
    return project.account_manager_id === user.id;
  }
  return false;
}
```

### 4.3 字段级权限

| 字段 | 创建时 | 更新时 | 查看 |
|------|--------|--------|------|
| name | ✅ 必填 | ✅ 可改 | ✅ 所有角色 |
| status | ❌ 系统默认 | ✅ admin/account_manager | ✅ 所有角色 |
| budget | ❌ 可选 | ✅ 可改 | ✅ 所有角色 |
| created_by | ❌ 系统填充 | ❌ 不可改 | ✅ 所有角色 |

---

## §5 业务逻辑

### 5.1 状态机定义

**来源**: STATE_MACHINE.md v2.7 §5, `backend/models/core/project.py`

```
┌───────────────────────────────────────────────────────────────────────────┐
│                          项目状态流转图 (5 状态)                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│                          ┌──────────┐                                     │
│                          │ planning │ (初始状态)                          │
│                          └────┬─────┘                                     │
│                               │                                           │
│              ┌────────────────┼────────────────┐                          │
│              ▼                ▼                ▼                          │
│        ┌──────────┐     ┌──────────┐     ┌───────────┐                   │
│        │  active  │◄───►│  paused  │     │ cancelled │ (终态)            │
│        └────┬─────┘     └────┬─────┘     └───────────┘                   │
│             │                │                                            │
│             ▼                ▼                                            │
│        ┌───────────┐   ┌───────────┐                                     │
│        │ completed │   │ cancelled │                                     │
│        └───────────┘   └───────────┘                                     │
│           (终态)          (终态)                                          │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

**状态转换表**:

| 当前状态 | 可转换到 | 触发条件 | 操作者 |
|----------|----------|----------|--------|
| planning | active, paused, cancelled | 手动触发 | admin, account_manager |
| active | paused, completed, cancelled | 手动触发 | admin, account_manager |
| paused | active, completed, cancelled | 手动触发 | admin, account_manager |
| completed | - | 终态 | - |
| cancelled | - | 终态 | - |

### 5.2 验证规则 (Pydantic Schema)

```python
class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    client_name: str = Field(..., min_length=1, max_length=200)
    client_company: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: str = Field("USD", max_length=10)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    account_manager_id: Optional[int] = Field(None, gt=0)

    @field_validator('end_date')
    def validate_end_date(cls, v, values):
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError('结束日期不能早于开始日期')
        return v
```

### 5.3 计算逻辑

```python
# 剩余预算
def remaining_budget(budget: Decimal, total_spent: Decimal) -> Decimal:
    return max(Decimal('0'), budget - total_spent)

# 预算使用百分比
def budget_usage_percent(budget: Decimal, total_spent: Decimal) -> Decimal:
    if budget == 0:
        return Decimal('0')
    return (total_spent / budget) * 100
```

### 5.4 业务约束 + Phase 1 规则

```yaml
约束规则:
  名称唯一性:
    - 项目名称全局唯一

  日期约束:
    - end_date >= start_date

  删除约束:
    - 有广告账户时不能删除
    - 有费用记录时不能删除

  成员约束:
    - 同一用户不能重复加入同一项目
    - 只有 admin 可以移除项目经理

Phase 1 规则 (照亮阶段):
  ❌ 禁止: 超预算自动阻断、状态转换强制审批
  ✅ 允许: 预算使用百分比警告、状态变更提示

  超预算处理:
    - 显示"超预算"标签
    - 不阻断任何操作
```

---

## §6 前后端接口契约

### 6.1 字段映射

| 后端字段 (snake_case) | 前端字段 (camelCase) | 说明 |
|----------------------|---------------------|------|
| account_manager_id | accountManagerId | 数字类型 |
| account_manager_name | accountManagerName | 字符串 |
| created_by | createdBy | UUID 字符串 |
| created_by_name | createdByName | 用户名 |
| client_company | clientCompany | 公司名 |
| total_spent | totalSpent | 数字，两位小数 |
| remaining_budget | remainingBudget | 计算字段 |

### 6.2 枚举值对照

```typescript
// 项目状态
type ProjectStatus = 'planning' | 'active' | 'paused' | 'completed' | 'cancelled';

const PROJECT_STATUS_LABELS: Record<ProjectStatus, string> = {
  planning: '规划中',
  active: '进行中',
  paused: '已暂停',
  completed: '已完成',
  cancelled: '已取消',
};

// 项目成员角色
type ProjectMemberRole = 'owner' | 'member' | 'viewer';

const MEMBER_ROLE_LABELS: Record<ProjectMemberRole, string> = {
  owner: '负责人',
  member: '成员',
  viewer: '观察者',
};
```

### 6.3 时区/格式约定

```yaml
时间格式:
  日期: YYYY-MM-DD (不含时区)
  时间戳: ISO 8601 (含时区，如 2024-12-23T10:00:00Z)

时区处理:
  存储: UTC
  传输: UTC
  显示: 前端转换为本地时区

数字格式:
  金额: 数字类型，保留2位小数
  百分比: 数字类型，如 12.34 表示 12.34%

空值:
  null: 表示无值/未知
  0: 表示实际值为零
  "": 前端显示空字符串
```

---

## §7 测试要点

### 7.1 单元测试

```python
describe('ProjectService', () => {
    describe('create_project', () => {
        it('应拒绝非 admin 创建项目', async () => {
            # pitcher 尝试创建项目
            with pytest.raises(PermissionDeniedError):
                service.create_project(request, pitcher_user)
        });

        it('应拒绝重复项目名称', async () => {
            service.create_project(request1, admin_user)
            with pytest.raises(ResourceConflictError):
                service.create_project(request_same_name, admin_user)
        });

        it('应拒绝结束日期早于开始日期', async () => {
            request.end_date = date(2024, 1, 1)
            request.start_date = date(2024, 12, 31)
            with pytest.raises(BusinessLogicError):
                service.create_project(request, admin_user)
        });
    });

    describe('状态转换', () => {
        it('planning → active 允许', () => {
            assert project.can_transition_to(ProjectStatus.ACTIVE) == True
        });

        it('completed 是终态', () => {
            project.status = 'completed'
            assert project.can_transition_to(ProjectStatus.ACTIVE) == False
        });
    });
});
```

### 7.2 集成测试

```python
describe('POST /api/v1/projects', () => {
    it('admin 可以创建项目', async () => {
        response = await client.post(
            '/api/v1/projects',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'name': 'Test Project',
                'client_name': 'Test Client',
                'client_company': 'Test Company'
            }
        )
        assert response.status_code == 201
        assert response.json()['data']['status'] == 'planning'
    });

    it('非 admin 不能创建', async () => {
        response = await client.post(
            '/api/v1/projects',
            headers={'Authorization': f'Bearer {pitcher_token}'},
            json={...}
        )
        assert response.status_code == 403
    });
});

describe('DELETE /api/v1/projects/:id', () => {
    it('有广告账户时不能删除', async () => {
        # 项目下有账户
        response = await client.delete(
            f'/api/v1/projects/{project_with_accounts.id}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 400
    });
});
```

### 7.3 权限测试矩阵

```python
test_cases = [
    # [角色, 操作, 预期结果]
    ('admin', 'create', 201),
    ('admin', 'delete', 204),
    ('admin', 'update', 200),
    ('admin', 'list_all', 200),
    ('account_manager', 'create', 403),
    ('account_manager', 'update_own', 200),
    ('account_manager', 'update_other', 403),
    ('media_buyer', 'list_member_projects', 200),
    ('media_buyer', 'update', 403),
    ('finance', 'list_all', 200),
    ('finance', 'statistics', 200),
    ('finance', 'create', 403),
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
- 按状态筛选
- 按管理员查询
- 按创建者查询
- 项目成员查询

### 8.3 批量操作限制

| 操作 | 单次上限 | 说明 |
|------|----------|------|
| 批量添加成员 | 20 个 | 超出需分批 |
| 导出项目列表 | 1000 条 | 超出走异步 |

---

## §9 安全规范

### 9.1 认证授权

- 所有 API 需要 JWT Token
- 每个 API 校验角色权限
- 只能访问自己有权限的项目数据

### 9.2 输入验证

- [x] 使用 Pydantic 验证所有输入
- [x] 字符串字段有最大长度限制 (name: 200, description: 1000)
- [x] 数字字段有范围限制 (budget >= 0)
- [x] 使用参数化查询，禁止拼接 SQL

### 9.3 审计日志

必须记录以下操作：

| 操作类型 | 记录内容 |
|----------|----------|
| 创建 | 操作人、时间、项目名称 |
| 更新 | 操作人、时间、变更字段 |
| 删除 | 操作人、时间、项目ID |
| 状态变更 | 操作人、时间、旧状态→新状态 |
| 成员变更 | 操作人、时间、添加/移除的用户 |

---

## 附录: AI 代码工厂禁止行为清单

### A.1 禁止行为

| 禁止行为 | 正确做法 | 检查方式 |
|---------|---------|---------|
| 自定义项目状态 | 使用 5 个标准状态 | 枚举检查 |
| 发明新错误码 | 使用 ERROR_CODES_SOT.md | grep 检查 |
| 自创字段 | 使用 DATA_SCHEMA.md | Schema 对比 |
| 跳过权限检查 | Service 层必须检查 | 代码审查 |
| Phase 1 自动阻断 | 仅警告+高亮+记录 | 逻辑审查 |
| 物理删除有子记录的项目 | 返回错误提示 | 集成测试 |

### A.2 SoT 追溯验证 Checklist

生成代码后必须验证：
- [ ] 所有状态值来自 STATE_MACHINE.md (5 个)
- [ ] 所有字段来自 DATA_SCHEMA.md
- [ ] 所有错误码来自 ERROR_CODES_SOT.md
- [ ] 所有角色来自 MASTER.md v4.4 §2.4 (7+1 个)
- [ ] 所有 API 端点来自 API_SOT.md
- [ ] 金额字段使用 Decimal 类型
- [ ] 时间字段使用 TIMESTAMPTZ + UTC

---

## 源码位置

| 层 | 文件路径 |
|----|---------|
| Model | `backend/models/core/project.py` |
| Model | `backend/models/core/project_member.py` |
| Service | `backend/services/project_service.py` |
| Router | `backend/routers/projects.py` |
| Schema | `backend/schemas/project.py` |
| Test | `backend/tests/test_project_service.py` |
| Test | `backend/tests/test_api_projects.py` |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-23 | 初始版本，基于现有代码提取规格 |

---

**维护者**: AI 广告代投系统开发团队
**关联文档**: C1-project-mgmt.md (前端规格)
