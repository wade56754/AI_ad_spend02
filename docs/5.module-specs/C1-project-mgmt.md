# C1: 项目管理 (Project Management)

> **模块类型**: 数据管理模块
> **优先级**: P0
> **源码位置**: `frontend/src/features/projects/`
> **最后更新**: 2025-12-22
> **状态**: :white_check_mark: 核心已实现，需补充字段

---

## 1. 业务目标

### 1.1 核心问题

**"有哪些项目？谁负责？"**

老板/项目负责人需要：
1. 查看所有项目清单及状态
2. 明确每个项目的负责人
3. 了解项目预算和消耗进度
4. 管理项目生命周期（创建、启动、暂停、完成）

### 1.2 用例清单

| 用例ID | 用例名 | Actor | 触发条件 | 预期结果 |
|--------|--------|-------|---------|---------|
| UC-C1-01 | 查看项目列表 | all | 进入页面 | 显示有权限的项目列表 |
| UC-C1-02 | 创建新项目 | ceo, project_owner | 点击新建 | 打开创建表单，填写后保存 |
| UC-C1-03 | 编辑项目信息 | ceo, project_owner | 点击编辑 | 修改项目基本信息 |
| UC-C1-04 | 变更项目状态 | ceo, project_owner | 选择状态 | 执行状态流转 |
| UC-C1-05 | 管理项目成员 | ceo, project_owner | 点击成员 | 分配/移除投手 |
| UC-C1-06 | 筛选项目 | all | 选择筛选条件 | 按状态/负责人过滤 |
| UC-C1-07 | 查看统计 | ceo, finance | 切换统计标签 | 显示项目统计数据 |

### 1.3 Phase 1 vs Phase 2

| 功能 | Phase 1 | Phase 2 |
|------|---------|---------|
| 项目 CRUD | ✓ 全功能 | - |
| 预算设置 | 可选填写 | 必填 + 超预算阻断 |
| 成员管理 | ✓ 全功能 | - |
| 状态流转 | 无限制 | 需审批 |
| 目标 CPL | 可选 | 必填 |

---

## 2. 数据需求

### 2.1 数据源 (SoT)

| 数据 | SoT 表 | SoT 字段 | 说明 |
|------|--------|---------|------|
| 项目基础 | `projects` | 全部字段 | 项目主表 |
| 项目成员 | `project_members` | `user_id`, `role` | 成员关联 |
| 用户信息 | `users` | `full_name`, `role` | 负责人/成员姓名 |
| 消耗统计 | `ad_spend_daily` | `SUM(spend)` | 项目消耗汇总 |

### 2.2 字段清单 (MASTER.md §6.2)

**页面 7：项目管理 - 核心字段**

| 字段 | 来源 | 说明 | 必须 | 当前状态 |
|------|------|------|------|---------|
| 项目名 | projects.name | 项目标识 | :white_check_mark: | :white_check_mark: 已实现 |
| 项目负责人 | projects.owner_id → user.full_name | 对盈亏负责的人 | :white_check_mark: | :x: 缺失 (用 account_manager_id) |
| 预算 | projects.budget | 项目总预算 | :white_check_mark: | :white_check_mark: 已实现 |
| 目标 CPL | projects.target_cpl | CPL 考核目标 | :white_check_mark: | :x: 缺失 |
| 单粉价格 | projects.unit_price | 收入计算单价 | :white_check_mark: | :x: DB有/前端缺 |
| 状态 | projects.status | 项目状态 | :white_check_mark: | :white_check_mark: 已实现 |
| 客户名称 | projects.client_name | 客户信息 | :yellow_circle: | :white_check_mark: 已实现 |
| 开始/结束日期 | projects.start_date/end_date | 项目周期 | :yellow_circle: | :white_check_mark: 已实现 |

### 2.3 项目状态机

来源: STATE_MACHINE.md v2.7 Section 5

```
┌─────────────────────────────────────────────────────────────────┐
│                    项目状态流转图                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                       ┌─────────┐                               │
│                       │ planning│ (初始状态)                    │
│                       └────┬────┘                               │
│                            │                                    │
│              ┌─────────────┼─────────────┐                      │
│              ▼             ▼             ▼                      │
│         ┌────────┐   ┌─────────┐   ┌──────────┐                │
│         │ active │◄──│ paused  │   │cancelled │ (终态)         │
│         └───┬────┘   └────┬────┘   └──────────┘                │
│             │             │                                     │
│             │◄────────────┘                                     │
│             │                                                   │
│             ▼                                                   │
│       ┌──────────┐                                              │
│       │completed │ (终态)                                       │
│       └──────────┘                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**状态定义**:

| 状态 | 中文名 | 说明 | 允许操作 |
|------|--------|------|---------|
| `planning` | 规划中 | 项目准备阶段 | 编辑、启动、取消 |
| `active` | 进行中 | 正常投放 | 编辑、暂停、完成、取消 |
| `paused` | 已暂停 | 暂停投放 | 编辑、恢复、完成、取消 |
| `completed` | 已完成 | 项目结束（终态） | 只读 |
| `cancelled` | 已取消 | 项目取消（终态） | 只读 |

### 2.4 项目成员角色

| 角色 | 中文名 | 权限 |
|------|--------|------|
| `project_owner` | 项目负责人 | 项目全部权限，对盈亏负责 |
| `pitcher` | 投手 | 填报日报，查看分配的账户 |
| `account_manager` | 户管 | 管理账户分配 |

---

## 3. UI 规范

### 3.1 页面布局

```
┌─────────────────────────────────────────────────────────────────────────┐
│ [PageHeader: 项目管理]                    [刷新] [导出] [新建项目]      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【统计卡片】                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│  │ 项目总数  │ │ 进行中   │ │ 总预算   │ │ 总消耗   │                   │
│  │    25    │ │   12    │ │ ¥500万   │ │ ¥285万   │                   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                   │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【筛选区】                                                              │
│  [状态下拉▼]  [搜索客户名称...]  [搜索]  [清除筛选]  [表格|看板]        │
│                                                                         │
│  状态说明: 🟢进行中  🟡已暂停  ⬜已完成  🔴已取消                        │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【内容标签】 [项目列表] [统计分析]                                      │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐
│  │ # │ 项目名 │ 负责人 │ 客户 │ 预算 │ 消耗 │ 进度 │ 目标CPL│ 状态 │操作│
│  ├───┼────────┼────────┼──────┼──────┼──────┼──────┼────────┼──────┼────┤
│  │ 1 │ 项目A  │ 张三   │ 客户X│¥100w │¥56w  │ 56%  │ ¥35    │ 🟢   │ ⋯ │
│  │ 2 │ 项目B  │ 李四   │ 客户Y│¥80w  │¥72w  │ 90%  │ ¥40    │ 🟡   │ ⋯ │
│  │ 3 │ 项目C  │ 王五   │ 客户Z│¥50w  │¥48w  │ 96%  │ ¥30    │ 🔴   │ ⋯ │
│  └──────────────────────────────────────────────────────────────────────┘
│                                                                         │
│  [< 上一页]  第 1 页 / 共 3 页  [下一页 >]                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 组件清单

| 组件 | 位置 | 职责 | 状态 |
|------|------|------|------|
| `ProjectsPage` | 主容器 | 页面布局、状态管理 | :white_check_mark: 已实现 |
| `ProjectsTable` | 列表区 | 项目表格展示 | :white_check_mark: 已实现 |
| `ProjectForm` | 弹窗 | 创建/编辑项目 | :white_check_mark: 已实现 |
| `ProjectMembersDialog` | 弹窗 | 成员管理 | :white_check_mark: 已实现 |
| `ProjectStatusBadge` | 表格内 | 状态徽章 | :white_check_mark: 已实现 |
| `ProjectStatsCard` | 统计区 | KPI 卡片 | :white_check_mark: 已实现 |
| `ProjectStatusLegend` | 筛选区 | 状态图例 | :white_check_mark: 已实现 |
| `ProjectKanban` | 看板区 | 看板视图 | :construction: 开发中 |

### 3.3 表格列定义

| # | 列名 | 字段 | 对齐 | 格式化 | 状态 |
|---|------|------|------|--------|------|
| 1 | 项目名 | name | 左 | 文本 | :white_check_mark: |
| 2 | 负责人 | owner_name | 左 | 文本 | :x: 缺失 |
| 3 | 客户 | client_name | 左 | 文本 | :white_check_mark: |
| 4 | 预算 | budget | 右 | ¥XX万 | :white_check_mark: |
| 5 | 消耗 | total_spent | 右 | ¥XX万 | :white_check_mark: |
| 6 | 进度 | budget_usage_percent | 中 | 进度条 | :white_check_mark: |
| 7 | 目标CPL | target_cpl | 右 | ¥XX | :x: 缺失 |
| 8 | 单价 | unit_price | 右 | ¥XX | :x: 缺失 |
| 9 | 状态 | status | 中 | Badge | :white_check_mark: |
| 10 | 操作 | - | 中 | 按钮组 | :white_check_mark: |

### 3.4 交互规则

| 交互 | 触发 | 行为 |
|------|------|------|
| 新建项目 | 点击按钮 | 打开 ProjectForm 弹窗 |
| 编辑项目 | 点击操作菜单 | 打开 ProjectForm 弹窗（预填数据） |
| 管理成员 | 点击操作菜单 | 打开 ProjectMembersDialog |
| 变更状态 | 选择状态 | 调用状态流转 API |
| 筛选 | 选择/输入 | 重新加载列表 |
| 排序 | 点击表头 | 按列排序 |
| 分页 | 点击分页 | 加载对应页数据 |

### 3.5 预算进度颜色规则

| 条件 | 颜色 | 说明 |
|------|------|------|
| usage < 70% | green | 正常 |
| 70% <= usage < 90% | yellow | 预警 |
| usage >= 90% | red | 告警 |

---

## 4. API 接口

### 4.1 现有接口

| 端点 | 方法 | 说明 | 状态 |
|------|------|------|------|
| `/api/v1/projects` | GET | 项目列表 | :white_check_mark: |
| `/api/v1/projects` | POST | 创建项目 | :white_check_mark: |
| `/api/v1/projects/{id}` | GET | 项目详情 | :white_check_mark: |
| `/api/v1/projects/{id}` | PUT | 更新项目 | :white_check_mark: |
| `/api/v1/projects/{id}` | DELETE | 删除项目 | :white_check_mark: |
| `/api/v1/projects/statistics` | GET | 项目统计 | :white_check_mark: |
| `/api/v1/projects/{id}/members` | GET | 成员列表 | :white_check_mark: |
| `/api/v1/projects/{id}/members` | POST | 添加成员 | :white_check_mark: |
| `/api/v1/projects/{id}/members/{user_id}` | DELETE | 移除成员 | :white_check_mark: |

### 4.2 需要增强的接口

#### POST/PUT `/api/v1/projects`

**当前请求体:**
```json
{
  "name": "项目A",
  "client_name": "客户X",
  "client_company": "XX公司",
  "description": "项目描述",
  "budget": 1000000,
  "currency": "CNY",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "account_manager_id": 5
}
```

**需要增强为:**
```json
{
  "name": "项目A",
  "client_name": "客户X",
  "client_company": "XX公司",
  "description": "项目描述",
  "budget": 1000000,
  "currency": "CNY",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "owner_id": 5,              // 新增: 项目负责人 (替代 account_manager_id)
  "target_cpl": 35.00,        // 新增: 目标 CPL
  "unit_price": 50.00         // 新增: 单粉价格
}
```

#### GET `/api/v1/projects`

**需要返回增强:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "项目A",
      "owner_id": 5,
      "owner_name": "张三",          // 新增
      "target_cpl": 35.00,           // 新增
      "unit_price": 50.00,           // 新增
      "budget": 1000000,
      "total_spent": 560000,
      "status": "active",
      // ... 其他字段
    }
  ]
}
```

---

## 5. 权限控制

### 5.1 权限矩阵

| 角色 | 查看全部 | 查看自己 | 创建 | 编辑 | 删除 | 管理成员 |
|------|---------|---------|------|------|------|---------|
| ceo | :white_check_mark: | - | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| project_owner | :x: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :x: | :white_check_mark: |
| finance | :white_check_mark: | - | :x: | :x: | :x: | :x: |
| supervisor | :x: | :white_check_mark: | :x: | :x: | :x: | :x: |
| pitcher | :x: | :white_check_mark: | :x: | :x: | :x: | :x: |
| admin | :white_check_mark: | - | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |

### 5.2 数据过滤规则

```python
# RLS 策略
def get_accessible_projects(user):
    if user.role in ['ceo', 'admin', 'finance']:
        return Project.query.all()

    if user.role == 'project_owner':
        return Project.query.filter(Project.owner_id == user.id)

    if user.role in ['supervisor', 'pitcher']:
        # 通过项目成员关联查询
        return Project.query.join(ProjectMember).filter(
            ProjectMember.user_id == user.id
        )
```

---

## 6. 代码块依赖

### 6.1 前端代码块

| 代码块 | 来源 | 用途 |
|--------|------|------|
| `DataTable` | core | 项目列表表格 |
| `StatusBadge` | core | 状态徽章 |
| `FormDialog` | workflow | 创建/编辑表单 |
| `StatCard` | core | 统计卡片 |
| `Pagination` | core | 分页组件 |

### 6.2 后端代码块

| 代码块 | 来源 | 用途 |
|--------|------|------|
| `pagination_helper` | core | 列表分页 |
| `permission_filter` | core | 权限过滤 |
| `state_machine` | workflow | 状态流转 |
| `audit_log` | workflow | 操作审计 |

---

## 7. 测试要点

### 7.1 测试用例清单

- [ ] 页面加载：显示统计卡片和项目列表
- [ ] 创建项目：填写表单后成功创建
- [ ] 编辑项目：修改信息后成功保存
- [ ] 状态流转：active → paused → active 正确执行
- [ ] 终态限制：completed/cancelled 状态无法编辑
- [ ] 成员管理：添加/移除成员正常
- [ ] 筛选功能：按状态/客户名筛选正确
- [ ] 分页功能：翻页后数据正确
- [ ] 权限控制：非管理员无法删除项目
- [ ] 预算进度：进度条颜色正确

### 7.2 边界条件

| 场景 | 处理方式 |
|------|---------|
| budget = 0 | 进度显示 0% |
| budget = null | 进度显示 "--" |
| owner_id = null | 负责人显示 "未分配" |
| target_cpl = null | CPL 目标显示 "--" |
| 终态项目 | 禁用编辑/删除按钮 |

---

## 8. 对齐任务清单

### 8.1 数据库任务

- [ ] `projects` 表添加 `owner_id` 字段 (FK → users.id)
- [ ] `projects` 表添加 `target_cpl` 字段 (DECIMAL(15,2))
- [ ] 确认 `unit_price` 字段可用
- [ ] 创建 Alembic 迁移脚本

### 8.2 后端任务

- [ ] ProjectSchema 添加 `owner_id`, `owner_name`, `target_cpl`, `unit_price`
- [ ] ProjectService 联表查询 owner 信息
- [ ] ProjectCreateInput 添加新字段
- [ ] 更新 API 文档

### 8.3 前端任务

- [ ] Project 类型添加 `owner_id`, `owner_name`, `target_cpl`, `unit_price`
- [ ] ProjectsTable 添加"负责人"、"目标CPL"、"单价"列
- [ ] ProjectForm 添加负责人选择、目标CPL输入、单价输入
- [ ] 更新用户选择器支持按角色筛选

### 8.4 优先级

| 任务 | 优先级 | 原因 |
|------|--------|------|
| 添加 owner_id 字段 | P0 | MASTER.md 要求"谁对结果负责" |
| 添加 target_cpl 字段 | P0 | CPL 异常判定依赖此字段 |
| 添加 unit_price 显示 | P1 | 盈亏计算依赖此字段 |

---

## 9. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-22 | 初始版本，基于现有实现分析 |

---

## 10. 相关文档

- [MASTER.md §6.2 页面职责](../sot/MASTER.md)
- [DATA_SCHEMA.md projects 表](../sot/DATA_SCHEMA.md)
- [STATE_MACHINE.md §5 项目状态机](../sot/STATE_MACHINE.md)
- [A3-project-pnl 项目盈亏看板](./A3-project-pnl.md)
- [B1-topup-approval 充值审批](./B1-topup-approval.md)
