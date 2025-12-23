# C2 投手管理 - 模块规格书

> **版本**: v1.0
> **更新日期**: 2025-12-22
> **优先级**: P2
> **基准**: MASTER.md v4.4 §6.2 页面 8, DATA_SCHEMA.md v5.2

---

## 1. 模块概述

### 1.1 业务目标

**核心问题**: 有哪些投手？负责什么？

投手管理模块解决人员配置与职责分配问题：
- 公司有哪些投手？属于哪个团队？
- 每个投手的主管是谁？
- 投手负责哪些广告账户？

### 1.2 用户角色

| 角色 | 职责 | 典型操作 |
|------|------|----------|
| `supervisor` | 主管 | 查看团队投手、分配账户 |
| `ceo` | 老板 | 查看全部投手概况 |
| `admin` | 管理员 | 创建/编辑/停用投手账号 |
| `pitcher` | 投手 | 查看自己信息 |

### 1.3 核心用例

| 用例 | 描述 | 主要角色 |
|------|------|----------|
| UC-C2-01 | 查看投手列表 | supervisor, ceo, admin |
| UC-C2-02 | 创建投手账号 | admin |
| UC-C2-03 | 编辑投手信息 | admin, supervisor |
| UC-C2-04 | 停用/启用投手 | admin |
| UC-C2-05 | 分配主管 | admin |
| UC-C2-06 | 分配账户 | admin, supervisor |
| UC-C2-07 | 查看投手负责账户 | supervisor, ceo |
| UC-C2-08 | 查看投手业绩概览 | supervisor, ceo |

### 1.4 Phase 约束

| Phase | 约束 | 说明 |
|-------|------|------|
| **Phase 1 (照亮)** | 信息维护 | 投手信息管理，不与绩效关联 |
| **Phase 2 (问责)** | 绩效关联 | 与 CPL 考核、绩效评分挂钩 |

**Phase 1 特别说明**:
- 投手 KPI（CPL）仅用于「观察与沟通」，不用于问责与考核
- 禁止自动暂停投手账户
- 主管的权力仅限于「沟通反馈」，不包含惩罚性操作

---

## 2. 数据需求

### 2.1 数据源 (SoT)

| 数据源 | 表/模型 | 用途 |
|--------|---------|------|
| users | 用户表 | 投手基本信息 |
| ad_accounts | 广告账户表 | 账户分配 |
| daily_reports | 日报表 | 业绩数据 |
| projects | 项目表 | 项目关联 |

### 2.2 字段清单 (MASTER.md §6.2 页面 8)

**必须字段**:

| 字段 | 来源 | 说明 |
|------|------|------|
| `full_name` | users | 投手姓名 |
| `team_name` | 待扩展 | 所属团队 |
| `supervisor_name` | users (JOIN) | 主管姓名 |
| `assigned_accounts` | ad_accounts (JOIN) | 分配的账户列表 |

**扩展字段**:

| 字段 | 来源 | 说明 |
|------|------|------|
| `username` | users | 用户名 |
| `email` | users | 邮箱 |
| `is_active` | users | 账号状态 |
| `created_at` | users | 入职时间 |
| `last_login` | users | 最后登录 |
| `account_count` | ad_accounts (COUNT) | 负责账户数 |
| `project_count` | projects (COUNT) | 关联项目数 |

**业绩相关字段 (Phase 2)**:

| 字段 | 来源 | 说明 |
|------|------|------|
| `total_spend` | daily_reports (SUM) | 累计消耗 |
| `total_conversions` | daily_reports (SUM) | 累计进粉 |
| `avg_cpl` | 计算字段 | 平均 CPL |
| `cpl_达标率` | 计算字段 | CPL 达标率 |

### 2.3 users 表结构 (DATA_SCHEMA.md v5.2)

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,                    -- FK → auth.users(id)
  username VARCHAR(50) UNIQUE,            -- 用户名
  full_name VARCHAR(100),                 -- 真实姓名
  email VARCHAR(255),                     -- 邮箱
  role VARCHAR(20) NOT NULL,              -- 角色 (pitcher/supervisor/...)
  department VARCHAR(100),                -- 部门
  position VARCHAR(100),                  -- 职位
  account_manager_id UUID FK → users.id,  -- 关联户管/主管
  is_active BOOLEAN DEFAULT true,         -- 账号可用性
  is_verified BOOLEAN DEFAULT false,      -- 资料验证
  last_login TIMESTAMPTZ,                 -- 最后登录
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.4 角色映射

| 标准角色 | 历史角色名 | 说明 |
|----------|-----------|------|
| `pitcher` | `media_buyer` | 投手 |
| `supervisor` | `data_operator` | 主管 |

**注意**: 新代码必须使用标准角色名 `pitcher`，禁止使用 `media_buyer`。

---

## 3. UI 规范

### 3.1 页面布局

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [页面头部]                                                                   │
│ 投手管理                                              [刷新] [添加投手]      │
│ 管理投手账号和账户分配                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ [筛选区]                                                                     │
│ ┌───────────────────────────────────────────────────────────────────────┐  │
│ │ [搜索投手名/邮箱...]  [团队▼]  [主管▼]  [状态▼]                       │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│ [KPI 卡片区]                                                                 │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐                │
│ │ 投手总数   │ │ 活跃投手   │ │ 已分配账户 │ │ 待分配账户 │                │
│ │ 25         │ │ 22         │ │ 156        │ │ 12         │                │
│ └────────────┘ └────────────┘ └────────────┘ └────────────┘                │
├─────────────────────────────────────────────────────────────────────────────┤
│ [数据表格]                                                                   │
│ ┌────────┬──────────┬────────┬────────┬────────────┬────────┬────────────┐ │
│ │ 姓名   │ 用户名   │ 团队   │ 主管   │ 负责账户   │ 状态   │ 操作       │ │
│ ├────────┼──────────┼────────┼────────┼────────────┼────────┼────────────┤ │
│ │ 张三   │ zhangsan │ A组    │ 李主管 │ 5 个账户   │ 正常   │ [编辑][分配]│ │
│ │ 李四   │ lisi     │ A组    │ 李主管 │ 3 个账户   │ 正常   │ [编辑][分配]│ │
│ │ 王五   │ wangwu   │ B组    │ 王主管 │ 4 个账户   │ 停用   │ [编辑][启用]│ │
│ └────────┴──────────┴────────┴────────┴────────────┴────────┴────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ [分页]                                                    第 1/3 页 [< >]   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 组件清单

| 组件 | 代码块 | 用途 |
|------|--------|------|
| PitchersPage | 页面容器 | 主页面组件 |
| StatCard × 4 | KPI 卡片 | 统计卡片区 |
| PitchersTable | DataTable | 投手列表 |
| CreatePitcherModal | FormDialog | 创建投手 |
| EditPitcherModal | FormDialog | 编辑投手 |
| AssignAccountsModal | FormDialog | 分配账户 |
| PitcherDetailDrawer | DetailDrawer | 投手详情 |
| StatusBadge | 状态徽章 | 状态展示 |

### 3.3 状态颜色规范

| 状态 | 颜色 | Tailwind Class |
|------|------|----------------|
| 正常 (active) | 绿色 | `bg-green-100 text-green-700` |
| 停用 (inactive) | 灰色 | `bg-gray-100 text-gray-500` |
| 待验证 (pending) | 黄色 | `bg-yellow-100 text-yellow-700` |

### 3.4 交互规则

| 交互 | 触发 | 行为 |
|------|------|------|
| 搜索 | 输入关键词 | 实时筛选列表 |
| 团队筛选 | 选择团队 | 筛选该团队投手 |
| 主管筛选 | 选择主管 | 筛选该主管下属 |
| 添加投手 | 点击按钮 | 打开创建对话框 |
| 编辑 | 点击编辑按钮 | 打开编辑对话框 |
| 分配账户 | 点击分配按钮 | 打开账户分配对话框 |
| 点击姓名 | 点击投手姓名 | 打开详情抽屉 |

---

## 4. API 接口

### 4.1 接口清单

| 方法 | 路径 | 用途 | 权限 |
|------|------|------|------|
| GET | `/api/v1/users` | 获取用户列表 | 登录用户 |
| GET | `/api/v1/users/{id}` | 获取用户详情 | 登录用户 |
| POST | `/api/v1/users` | 创建用户 | admin |
| PUT | `/api/v1/users/{id}` | 更新用户 | admin |
| DELETE | `/api/v1/users/{id}` | 删除/停用用户 | admin |
| PUT | `/api/v1/users/{id}/toggle-status` | 切换用户状态 | admin |
| GET | `/api/v1/users/pitchers` | 获取投手列表 | supervisor, admin |
| GET | `/api/v1/users/{id}/accounts` | 获取投手负责账户 | supervisor, admin |
| PUT | `/api/v1/users/{id}/accounts` | 分配账户给投手 | admin, supervisor |
| GET | `/api/v1/users/stats` | 获取用户统计 | admin |

### 4.2 请求/响应示例

**获取投手列表**:
```http
GET /api/v1/users?role=pitcher&page=1&page_size=20
Authorization: Bearer {token}
```

```json
{
  "code": "SUCCESS",
  "message": "获取成功",
  "data": {
    "items": [
      {
        "id": "uuid-001",
        "username": "zhangsan",
        "full_name": "张三",
        "email": "zhangsan@example.com",
        "role": "pitcher",
        "is_active": true,
        "supervisor_id": "uuid-100",
        "supervisor_name": "李主管",
        "team_name": "A组",
        "account_count": 5,
        "created_at": "2025-01-01T00:00:00Z",
        "last_login": "2025-12-22T10:00:00Z"
      }
    ],
    "total": 25,
    "page": 1,
    "page_size": 20
  }
}
```

**分配账户**:
```http
PUT /api/v1/users/uuid-001/accounts
Authorization: Bearer {token}
Content-Type: application/json

{
  "account_ids": [101, 102, 103]
}
```

```json
{
  "code": "SUCCESS",
  "message": "账户分配成功",
  "data": {
    "user_id": "uuid-001",
    "assigned_accounts": 3,
    "total_accounts": 5
  }
}
```

---

## 5. 权限矩阵

### 5.1 功能权限

| 功能 | ceo | supervisor | pitcher | admin |
|------|-----|------------|---------|-------|
| 查看列表 | ✓ | ✓ | - | ✓ |
| 查看详情 | ✓ | ✓ | ○ | ✓ |
| 创建投手 | - | - | - | ✓ |
| 编辑投手 | - | ○ | - | ✓ |
| 停用/启用 | - | - | - | ✓ |
| 分配账户 | - | ✓ | - | ✓ |

**说明**: ✓ = 全部可见, ○ = 仅自己/下属, - = 无权限

### 5.2 数据权限

| 角色 | 数据范围 |
|------|----------|
| `ceo` | 全部投手 |
| `supervisor` | 仅自己团队的投手 |
| `pitcher` | 仅自己 |
| `admin` | 全部投手 |

---

## 6. 代码块组合

### 6.1 前端代码块

```
PitchersPage (待开发，基于 UsersPage 改造)
├── 页头组件
│   ├── PageTitle
│   └── ActionButtons (刷新, 添加投手)
├── 筛选区
│   ├── SearchInput
│   ├── SelectTeam
│   ├── SelectSupervisor
│   └── SelectStatus
├── StatCard × 4
├── PitchersTable
│   ├── DataTable
│   ├── StatusBadge
│   └── ActionButtons
├── CreatePitcherModal
├── EditPitcherModal
├── AssignAccountsModal
└── PitcherDetailDrawer
```

### 6.2 后端代码块

```
UsersRouter (已实现，需扩展)
├── users_service
│   ├── list_users()
│   ├── get_pitcher_stats()
│   └── assign_accounts()
└── permission_filter
```

### 6.3 组合图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           投手管理模块组合图                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [前端]                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ PitchersPage (基于 UsersPage 改造)                                  │   │
│  │  ├── useUsers({ role: 'pitcher' }) ───────────────────────┐         │   │
│  │  ├── useUserStats() ──────────────────────────────────────┤         │   │
│  │  └── useAssignAccounts() ─────────────────────────────────┤         │   │
│  └───────────────────────────────────────────────────────────┼─────────┘   │
│                                                              │              │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─   │
│                                                              │              │
│  [后端]                                                      ↓              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ UsersRouter (/api/v1/users)                                         │   │
│  │  ├── GET /?role=pitcher → users_service.list()                      │   │
│  │  ├── GET /pitchers      → users_service.list_pitchers()             │   │
│  │  ├── GET /{id}/accounts → users_service.get_accounts()              │   │
│  │  └── PUT /{id}/accounts → users_service.assign_accounts()           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [数据关联]                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ users (投手信息)                                                    │   │
│  │   ↓ account_manager_id                                              │   │
│  │ users (主管信息)                                                    │   │
│  │   ↓ owner_id                                                        │   │
│  │ ad_accounts (负责账户)                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. 测试检查点

### 7.1 功能测试

| 检查点 | 预期结果 |
|--------|----------|
| 列表加载 | 仅显示 role=pitcher 的用户 |
| 搜索 | 按姓名/用户名/邮箱筛选 |
| 团队筛选 | 按团队过滤 |
| 主管筛选 | 按主管过滤 |
| 创建投手 | admin 可创建，role 固定为 pitcher |
| 编辑投手 | 正确更新信息 |
| 停用/启用 | 状态正确切换 |
| 分配账户 | 正确关联账户 |

### 7.2 权限测试

| 检查点 | 预期结果 |
|--------|----------|
| supervisor 查看 | 仅看到自己团队 |
| pitcher 查看 | 仅看到自己 |
| supervisor 分配账户 | 可以分配 |
| pitcher 分配账户 | 被拒绝 |

### 7.3 数据完整性测试

| 检查点 | 预期结果 |
|--------|----------|
| 账户分配 | ad_accounts.owner_id 正确更新 |
| 统计数据 | account_count 正确计算 |

---

## 8. 源码位置

### 8.1 前端

| 文件 | 路径 | 状态 |
|------|------|------|
| 页面组件 | `frontend/src/features/users/components/UsersPage.tsx` | ⚠️ 通用用户页面 |
| 类型定义 | `frontend/src/features/users/types/user.types.ts` | ⚠️ 需更新角色名 |
| API 服务 | `frontend/src/features/users/services/usersApi.ts` | ✅ 已实现 |
| Hooks | `frontend/src/features/users/hooks/useUsers.ts` | ✅ 已实现 |

### 8.2 后端

| 文件 | 路径 |
|------|------|
| 路由 | `backend/routers/users.py` |
| 服务 | `backend/services/users_service.py` |
| 模型 | `backend/models/user.py` |
| Schema | `backend/schemas/user.py` |

---

## 9. 实现状态 & Gap 分析

### 9.1 当前实现状态

| 功能点 | 状态 | 说明 |
|--------|------|------|
| 用户列表 | ✅ 已实现 | 通用用户管理页面 |
| CRUD 操作 | ✅ 已实现 | 创建/编辑/删除 |
| 角色筛选 | ✅ 已实现 | 可按角色筛选 |
| React Query | ✅ 已实现 | useUsers 等 hooks |
| 分页 | ✅ 已实现 | 分页功能 |

### 9.2 Gap 分析

| Gap | 优先级 | 说明 |
|-----|--------|------|
| 角色名称更新 | P0 | `media_buyer` → `pitcher` |
| 专用投手页面 | P1 | 当前是通用用户页面 |
| 账户分配功能 | P1 | 需新增分配账户功能 |
| 团队字段 | P1 | 需扩展 team_name 字段 |
| 主管关联 | P1 | 需完善 supervisor_id 关联 |
| KPI 卡片 | P2 | 需添加统计卡片 |
| 投手详情抽屉 | P2 | 需新增详情抽屉 |

### 9.3 后续开发任务

| 任务 | 优先级 | 预计工作量 |
|------|--------|------------|
| 更新角色枚举 | P0 | 1h |
| 创建专用 PitchersPage | P1 | 4h |
| 实现账户分配 API | P1 | 3h |
| 实现账户分配 UI | P1 | 3h |
| 添加团队/主管筛选 | P1 | 2h |
| 添加 KPI 统计卡片 | P2 | 2h |
| 添加投手详情抽屉 | P2 | 2h |

---

## 10. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-22 | 初始版本 |

---

**维护者**: AI 广告代投系统开发团队
**关联文档**: MASTER.md v4.4, DATA_SCHEMA.md v5.2, user.types.ts
