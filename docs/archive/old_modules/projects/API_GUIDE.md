# Projects API 开发指南

> **版本**: v1.0 (基于当前代码实现)
> **更新日期**: 2025-11-19
> **状态**: ✅ 已实现（存在已知差异，见第 8 章）
> **维护者**: 后端开发团队

---

## 目录

1. [真相源引用](#1-真相源引用)
2. [API 端点总览](#2-api-端点总览)
3. [详细接口说明](#3-详细接口说明)
4. [权限矩阵](#4-权限矩阵)
5. [状态机与流转](#5-状态机与流转)
6. [错误码](#6-错误码)
7. [分页与筛选规范](#7-分页与筛选规范)
8. [⚠️ 已知差异与待修复项](#8-已知差异与待修复项)

---

## 1. 真相源引用

本文档基于以下真相源文档和代码实现编写：

### SoT 文档

| 文档 | 版本 | 章节 | 说明 |
|------|------|------|------|
| `docs/core/DATA_SCHEMA.md` | v5.0 | 3.2.1-3.2.3 | 项目表结构定义（`projects`, `project_members`, `project_expenses`） |
| `docs/core/STATE_MACHINE.md` | v2.3 | 第 5 章 | 项目状态机（draft → active → suspended → archived） |
| `docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md` | - | 第 3/4 章 | 角色定义与权限模型 |
| `docs/core/API_DEVELOPMENT_FLOW.md` | v7.0 | 第 6 章 | 响应格式规范（Envelope） |

### 代码实现

| 文件 | 说明 |
|------|------|
| `backend/routers/projects.py` | API 路由定义（11 个端点） |
| `backend/services/project_service.py` | 业务逻辑与权限检查 |
| `backend/models/core/project.py` | SQLAlchemy 模型定义 |
| `backend/schemas/project.py` | Pydantic 请求/响应 Schema |
| `backend/models/enums.py` | 项目状态枚举 |
| `backend/core/permissions.py` | RBAC 权限系统 |
| `backend/core/error_codes.py` | 错误码定义 |

---

## 2. API 端点总览

### 2.1 端点列表

| 方法 | 路径 | 功能 | 权限 | 实现状态 |
|------|------|------|------|----------|
| **GET** | `/projects` | 获取项目列表 | 所有已登录用户（RBAC 过滤） | ✅ |
| **POST** | `/projects` | 创建项目 | `admin` | ✅ |
| **GET** | `/projects/{project_id}` | 获取项目详情 | 根据角色过滤 | ✅ |
| **PUT** | `/projects/{project_id}` | 更新项目 | `admin`, `account_manager`（仅管理的项目） | ✅ |
| **DELETE** | `/projects/{project_id}` | 删除项目 | `admin` | ✅ |
| **POST** | `/projects/{project_id}/members` | 分配项目成员 | `admin`, `account_manager` | ✅ |
| **GET** | `/projects/{project_id}/members` | 获取项目成员列表 | 根据角色过滤 | ✅ |
| **DELETE** | `/projects/{project_id}/members/{user_id}` | 移除项目成员 | `admin`, `account_manager` | ✅ |
| **POST** | `/projects/{project_id}/expenses` | 添加项目费用 | `admin`, `account_manager` | ✅ |
| **GET** | `/projects/{project_id}/expenses` | 获取项目费用列表 | 根据角色过滤 | ✅ |
| **GET** | `/projects/statistics` | 获取项目统计 | `admin`, `finance`, `data_operator`, `account_manager` | ✅ |

> **注意**: 路由层的 `@require_role` 装饰器已被注释，权限检查在 Service 层实现。

### 2.2 Base URL

```
{API_URL}/projects
```

例如：`https://api.example.com/v1/projects`

---

## 3. 详细接口说明

### 3.1 获取项目列表

#### 请求

```http
GET /projects?page=1&page_size=20&status=active&manager_id=123&client_name=测试
```

**查询参数**:

| 参数 | 类型 | 必填 | 说明 | 默认值 |
|------|------|------|------|--------|
| `page` | integer | 否 | 页码（从 1 开始） | 1 |
| `page_size` | integer | 否 | 每页数量（1-100） | 20 |
| `status` | string | 否 | 项目状态筛选 | - |
| `manager_id` | integer | 否 | 项目经理 ID 筛选 | - |
| `client_name` | string | 否 | 客户名称模糊搜索 | - |

**权限要求**:
- 所有已登录用户可调用
- 返回结果根据角色自动过滤（见权限矩阵）

#### 响应

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "测试项目",
        "client_name": "张三",
        "client_company": "测试公司",
        "description": "项目描述",
        "status": "active",
        "budget": "100000.00",
        "currency": "CNY",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "account_manager_id": 123,
        "account_manager_name": "李四",
        "total_spent": "50000.00",
        "total_accounts": 5,
        "active_accounts": 3,
        "remaining_budget": "50000.00",
        "budget_usage_percent": "50.00",
        "created_by": 1,
        "created_by_name": "管理员",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-15T10:30:00Z"
      }
    ],
    "meta": {
      "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 100,
        "total_pages": 5
      }
    }
  },
  "message": "获取项目列表成功",
  "code": "SUCCESS"
}
```

**失败响应** (500 Internal Server Error):

```json
{
  "success": false,
  "code": "SYS_500",
  "message": "获取项目列表失败",
  "data": null
}
```

---

### 3.2 创建项目

#### 请求

```http
POST /projects
Content-Type: application/json
```

**请求体**:

```json
{
  "name": "新项目",
  "client_name": "王五",
  "client_company": "示例公司",
  "description": "项目详细描述",
  "budget": "200000.00",
  "currency": "USD",
  "start_date": "2025-02-01",
  "end_date": "2025-12-31",
  "account_manager_id": 456
}
```

**字段说明**:

| 字段 | 类型 | 必填 | 说明 | 约束 |
|------|------|------|------|------|
| `name` | string | ✅ | 项目名称 | 1-200 字符 |
| `client_name` | string | ✅ | 客户联系人姓名 | 1-200 字符 |
| `client_company` | string | ✅ | 客户公司名称 | 1-200 字符 |
| `description` | string | 否 | 项目描述 | 最多 1000 字符 |
| `budget` | decimal | 否 | 项目预算 | >= 0, 两位小数 |
| `currency` | string | 否 | 货币类型 | 默认 "USD" |
| `start_date` | date | 否 | 开始日期 | ISO 8601 格式 |
| `end_date` | date | 否 | 结束日期 | >= start_date |
| `account_manager_id` | integer | 否 | 项目经理 ID | 必须是有效用户 ID |

**权限要求**:
- 仅 `admin` 角色可创建（⚠️ 代码实现与 SoT 不一致，见第 8 章）

#### 响应

**成功响应** (201 Created):

```json
{
  "success": true,
  "data": {
    "id": 2,
    "name": "新项目",
    "client_name": "王五",
    "client_company": "示例公司",
    "description": "项目详细描述",
    "status": "draft",
    "budget": "200000.00",
    "currency": "USD",
    "start_date": "2025-02-01",
    "end_date": "2025-12-31",
    "account_manager_id": 456,
    "account_manager_name": null,
    "total_spent": "0.00",
    "total_accounts": 0,
    "active_accounts": 0,
    "remaining_budget": "200000.00",
    "budget_usage_percent": "0.00",
    "created_by": 1,
    "created_by_name": "管理员",
    "created_at": "2025-01-19T08:00:00Z",
    "updated_at": "2025-01-19T08:00:00Z"
  },
  "message": "项目创建成功",
  "code": "SUCCESS"
}
```

**失败响应**:

```json
// 403 Forbidden - 权限不足
{
  "success": false,
  "code": "PERMISSION_DENIED",
  "message": "只有管理员可以创建项目",
  "data": null
}

// 409 Conflict - 项目名称已存在
{
  "success": false,
  "code": "BIZ_ERROR",
  "message": "项目名称 '新项目' 已存在",
  "data": null
}
```

---

### 3.3 获取项目详情

#### 请求

```http
GET /projects/{project_id}
```

**路径参数**:
- `project_id` (integer): 项目 ID

**权限要求**:
- 所有已登录用户可调用
- Service 层根据角色检查访问权限（见权限矩阵）

#### 响应

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "测试项目",
    "client_name": "张三",
    "client_company": "测试公司",
    "description": "项目描述",
    "status": "active",
    "budget": "100000.00",
    "currency": "CNY",
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "account_manager_id": 123,
    "account_manager_name": "李四",
    "total_spent": "50000.00",
    "total_accounts": 5,
    "active_accounts": 3,
    "remaining_budget": "50000.00",
    "budget_usage_percent": "50.00",
    "created_by": 1,
    "created_by_name": "管理员",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  },
  "message": null,
  "code": "SUCCESS"
}
```

**失败响应**:

```json
// 404 Not Found - 项目不存在
{
  "success": false,
  "code": "SYS_004",
  "message": "项目 999 不存在",
  "data": null
}

// 403 Forbidden - 无权限查看
{
  "success": false,
  "code": "PERMISSION_DENIED",
  "message": "无权限查看该项目",
  "data": null
}
```

---

### 3.4 更新项目

#### 请求

```http
PUT /projects/{project_id}
Content-Type: application/json
```

**路径参数**:
- `project_id` (integer): 项目 ID

**请求体** (所有字段可选):

```json
{
  "name": "更新后的项目名称",
  "client_name": "新联系人",
  "client_company": "新公司",
  "description": "更新后的描述",
  "status": "active",
  "budget": "150000.00",
  "start_date": "2025-02-01",
  "end_date": "2025-12-31",
  "account_manager_id": 789
}
```

**字段说明**:
- 所有字段均为可选，仅更新提供的字段
- `status` 字段必须符合状态机流转规则（见第 5 章）
- ⚠️ Schema 中的状态枚举与 SoT 不一致（见第 8 章）

**权限要求**:
- `admin`: 可更新所有项目
- `account_manager`: 仅可更新自己管理的项目

#### 响应

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "更新后的项目名称",
    // ... 其他字段
  },
  "message": "项目更新成功",
  "code": "SUCCESS"
}
```

**失败响应**:

```json
// 404 Not Found
{
  "success": false,
  "code": "SYS_004",
  "message": "项目 999 不存在",
  "data": null
}

// 403 Forbidden
{
  "success": false,
  "code": "PERMISSION_DENIED",
  "message": "无权限更新该项目",
  "data": null
}

// 409 Conflict - 项目名称冲突
{
  "success": false,
  "code": "BIZ_ERROR",
  "message": "项目名称 '更新后的项目名称' 已存在",
  "data": null
}
```

---

### 3.5 删除项目

#### 请求

```http
DELETE /projects/{project_id}
```

**路径参数**:
- `project_id` (integer): 项目 ID

**权限要求**:
- 仅 `admin` 角色可删除

**删除限制**:
- 项目下存在广告账户时无法删除
- 删除操作会级联删除项目成员和费用记录

#### 响应

**成功响应** (204 No Content):

```
(无响应体)
```

**失败响应**:

```json
// 404 Not Found
{
  "success": false,
  "code": "SYS_004",
  "message": "项目 999 不存在",
  "data": null
}

// 403 Forbidden
{
  "success": false,
  "code": "PERMISSION_DENIED",
  "message": "只有管理员可以删除项目",
  "data": null
}

// 400 Bad Request - 存在关联数据
{
  "success": false,
  "code": "BIZ_ERROR",
  "message": "项目下还有广告账户，无法删除",
  "data": null
}
```

---

### 3.6 分配项目成员

#### 请求

```http
POST /projects/{project_id}/members
Content-Type: application/json
```

**路径参数**:
- `project_id` (integer): 项目 ID

**请求体**:

```json
{
  "user_id": 789,
  "role": "media_buyer"
}
```

**字段说明**:

| 字段 | 类型 | 必填 | 说明 | 约束 |
|------|------|------|------|------|
| `user_id` | integer | ✅ | 用户 ID | 必须是有效用户 |
| `role` | string | ✅ | 项目内角色 | `account_manager`, `media_buyer`, `analyst` |

**权限要求**:
- `admin`: 可分配所有项目成员
- `account_manager`: 可分配自己管理的项目成员

#### 响应

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "id": 10,
    "user_id": 789,
    "user_name": "投手小王",
    "user_email": "wang@example.com",
    "user_role": "media_buyer",
    "project_role": "media_buyer",
    "joined_at": "2025-01-19T08:00:00Z"
  },
  "message": "成员分配成功",
  "code": "SUCCESS"
}
```

**失败响应**:

```json
// 404 Not Found - 用户不存在
{
  "success": false,
  "code": "BIZ_ERROR",
  "message": "用户 789 不存在",
  "data": null
}

// 409 Conflict - 用户已是成员
{
  "success": false,
  "code": "BIZ_ERROR",
  "message": "用户已经是项目成员",
  "data": null
}

// 403 Forbidden
{
  "success": false,
  "code": "PERMISSION_DENIED",
  "message": "无权限分配项目成员",
  "data": null
}
```

---

### 3.7 获取项目成员列表

#### 请求

```http
GET /projects/{project_id}/members
```

**路径参数**:
- `project_id` (integer): 项目 ID

**权限要求**:
- 有权访问该项目的用户可查看成员列表

#### 响应

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": [
    {
      "id": 10,
      "user_id": 789,
      "user_name": "投手小王",
      "user_email": "wang@example.com",
      "user_role": "media_buyer",
      "project_role": "media_buyer",
      "joined_at": "2025-01-19T08:00:00Z"
    },
    {
      "id": 11,
      "user_id": 456,
      "user_name": "项目经理李四",
      "user_email": "li@example.com",
      "user_role": "account_manager",
      "project_role": "account_manager",
      "joined_at": "2025-01-01T00:00:00Z"
    }
  ],
  "message": "获取项目成员列表成功",
  "code": "SUCCESS"
}
```

---

### 3.8 移除项目成员

#### 请求

```http
DELETE /projects/{project_id}/members/{user_id}
```

**路径参数**:
- `project_id` (integer): 项目 ID
- `user_id` (integer): 用户 ID

**权限要求**:
- `admin`: 可移除所有项目成员
- `account_manager`: 可移除自己管理的项目成员（但不能移除项目经理）

#### 响应

**成功响应** (204 No Content):

```
(无响应体)
```

**失败响应**:

```json
// 404 Not Found
{
  "success": false,
  "code": "SYS_004",
  "message": "用户不是项目成员",
  "data": null
}

// 403 Forbidden - 无权移除项目经理
{
  "success": false,
  "code": "PERMISSION_DENIED",
  "message": "只有管理员可以移除项目经理",
  "data": null
}
```

---

### 3.9 添加项目费用

#### 请求

```http
POST /projects/{project_id}/expenses
Content-Type: application/json
```

**路径参数**:
- `project_id` (integer): 项目 ID

**请求体**:

```json
{
  "expense_type": "media_spend",
  "amount": "5000.00",
  "description": "1月广告消耗",
  "expense_date": "2025-01-15"
}
```

**字段说明**:

| 字段 | 类型 | 必填 | 说明 | 约束 |
|------|------|------|------|------|
| `expense_type` | string | ✅ | 费用类型 | `media_spend`, `service_fee`, `other` |
| `amount` | decimal | ✅ | 金额 | > 0, 两位小数 |
| `description` | string | 否 | 费用说明 | 最多 500 字符 |
| `expense_date` | date | ✅ | 费用日期 | ISO 8601 格式 |

**权限要求**:
- `admin`: 可添加所有项目费用
- `account_manager`: 可添加自己管理的项目费用
- ⚠️ 代码中缺少 `finance` 角色权限（见第 8 章）

#### 响应

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "id": 50,
    "expense_type": "media_spend",
    "amount": "5000.00",
    "description": "1月广告消耗",
    "expense_date": "2025-01-15",
    "created_by_name": "李四",
    "created_at": "2025-01-19T08:00:00Z"
  },
  "message": "费用添加成功",
  "code": "SUCCESS"
}
```

---

### 3.10 获取项目费用列表

#### 请求

```http
GET /projects/{project_id}/expenses?page=1&page_size=20
```

**路径参数**:
- `project_id` (integer): 项目 ID

**查询参数**:
- `page` (integer, 可选): 页码，默认 1
- `page_size` (integer, 可选): 每页数量，默认 20，最大 100

**权限要求**:
- 有权访问该项目的用户可查看费用列表

#### 响应

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 50,
        "expense_type": "media_spend",
        "amount": "5000.00",
        "description": "1月广告消耗",
        "expense_date": "2025-01-15",
        "created_by_name": "李四",
        "created_at": "2025-01-19T08:00:00Z"
      }
    ],
    "meta": {
      "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 50,
        "total_pages": 3
      }
    }
  },
  "message": "获取费用列表成功",
  "code": "SUCCESS"
}
```

---

### 3.11 获取项目统计

#### 请求

```http
GET /projects/statistics
```

**权限要求**:
- `admin`, `finance`, `data_operator`, `account_manager`
- Service 层根据角色过滤统计范围

#### 响应

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "total_projects": 100,
    "active_projects": 50,
    "paused_projects": 20,
    "completed_projects": 25,
    "cancelled_projects": 5,
    "total_budget": "10000000.00",
    "total_spent": "5000000.00",
    "total_clients": 50,
    "avg_project_value": "100000.00",
    "overall_roi": "0.00"
  },
  "message": null,
  "code": "SUCCESS"
}
```

> ⚠️ **已知问题**: Service 层使用的状态枚举（`paused`, `completed`, `cancelled`）与 SoT 不一致，应为 `draft`, `suspended`, `archived`（见第 8 章）

---

## 4. 权限矩阵

### 4.1 操作权限

| 操作 | admin | account_manager | finance | data_operator | media_buyer |
|------|-------|----------------|---------|---------------|-------------|
| **创建项目** | ✅ | ❌ (⚠️ 应为 ✅) | ❌ | ❌ | ❌ |
| **查看项目列表** | ✅ 全部 | ✅ 管理的项目 | ✅ 全部 | ✅ 全部 | ✅ 参与的项目 |
| **查看项目详情** | ✅ | ✅ 管理的项目 | ✅ | ✅ | ✅ 参与的项目 |
| **更新项目** | ✅ | ✅ 管理的项目 | ❌ | ❌ | ❌ |
| **删除项目** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **分配成员** | ✅ | ✅ 管理的项目 | ❌ | ❌ | ❌ |
| **移除成员** | ✅ | ✅ 管理的项目（非经理） | ❌ | ❌ | ❌ |
| **添加费用** | ✅ | ✅ 管理的项目 | ❌ (⚠️ 应为 ✅) | ❌ | ❌ |
| **查看费用** | ✅ | ✅ 管理的项目 | ✅ | ✅ | ✅ 参与的项目 |
| **查看统计** | ✅ | ✅ | ✅ | ✅ | ❌ |

### 4.2 数据过滤规则

**实现位置**: `backend/services/project_service.py::_apply_permission_filter()`

```python
def _apply_permission_filter(self, query, current_user: User):
    """应用权限过滤"""
    if current_user.role == "admin":
        return query  # 查看所有项目
    elif current_user.role == "account_manager":
        return query.filter(Project.account_manager_id == current_user.id)
    elif current_user.role == "media_buyer":
        # 投手只能看到自己参与的项目
        return query.join(ProjectMember).filter(ProjectMember.user_id == current_user.id)
    else:
        # finance和data_operator可以查看所有项目
        return query
```

---

## 5. 状态机与流转

### 5.1 项目状态定义

根据 `docs/core/STATE_MACHINE.md` 第 5 章，项目状态机定义如下：

```
draft → active → suspended → archived（终态）
```

**合法状态**:
- `draft`: 草稿
- `active`: 活跃
- `suspended`: 暂停
- `archived`: 已归档（终态）

**状态流转规则**:
- `draft` 可转换为: `active`
- `active` 可转换为: `suspended`, `archived`
- `suspended` 可转换为: `active`, `archived`
- `archived` 为终态，**仅 admin 可回退**，必须记录审计日志

**触发角色**: `account_manager`, `admin`

### 5.2 模型层实现

**文件**: `backend/models/core/project.py`

```python
def can_transition_to(self, new_status: ProjectStatus) -> bool:
    """检查是否可以转换到新状态"""
    current = ProjectStatus(self.status)
    transitions = {
        ProjectStatus.DRAFT: [ProjectStatus.ACTIVE, ProjectStatus.SUSPENDED, ProjectStatus.ARCHIVED],
        ProjectStatus.ACTIVE: [ProjectStatus.SUSPENDED, ProjectStatus.ARCHIVED],
        ProjectStatus.SUSPENDED: [ProjectStatus.ACTIVE, ProjectStatus.ARCHIVED],
        ProjectStatus.ARCHIVED: [],
    }
    return new_status in transitions.get(current, [])

def transition_to(self, new_status: ProjectStatus, operator_id, reason: str = None):
    """安全地转换项目状态"""
    if not self.can_transition_to(new_status):
        raise ValueError(f"不允许从 {self.status} 转换到 {new_status.value}")

    old_status = self.status
    self.status = new_status.value

    # TODO: 记录状态变更历史
    return True
```

### 5.3 数据库约束

**文件**: `backend/models/core/project.py::__table_args__`

```python
CheckConstraint(
    "status IN ('draft', 'active', 'suspended', 'archived')",
    name='projects_status_check'
)
```

---

## 6. 错误码

### 6.1 错误码规范

根据 `docs/core/API_DEVELOPMENT_FLOW.md` 和 `backend/core/error_codes.py`：

**命名规则**: `{MODULE}_{ACTION}_{REASON}`

| 错误码 | HTTP 状态码 | 说明 | 使用场景 |
|--------|------------|------|----------|
| `AUTH_500` | 403 | 权限不足 | 用户无权限执行操作 |
| `BIZ_002` | 404 | 资源不存在 | 项目/用户不存在 |
| `BIZ_003` | 409 | 资源已存在 | 项目名称重复、成员已分配 |
| `BIZ_001` | 400 | 无效的操作 | 业务逻辑错误 |
| `BIZ_301` | 400 | 状态转换不允许 | 违反状态机规则 |
| `SYS_004` | 404 | 资源不存在 | 通用 404 错误（Router 层使用） |
| `SYS_500` | 500 | 系统内部错误 | 未预期的系统错误 |
| `VALIDATION_xxx` | 400 | 参数验证错误 | Pydantic 验证失败 |

### 6.2 响应格式

**成功响应**:

```python
success_response(data, message="操作成功", code="SUCCESS")
```

**错误响应**:

```python
error_response(code="BIZ_002", message="项目不存在", status_code=404)
```

**响应结构**:

```json
{
  "success": true/false,
  "code": "错误码",
  "message": "错误描述",
  "data": null  // 错误时为 null
}
```

---

## 7. 分页与筛选规范

### 7.1 分页参数

| 参数 | 类型 | 默认值 | 约束 | 说明 |
|------|------|--------|------|------|
| `page` | integer | 1 | >= 1 | 页码（从 1 开始） |
| `page_size` | integer | 20 | 1-100 | 每页数量 |

### 7.2 分页元数据

```json
{
  "pagination": {
    "page": 1,           // 当前页码
    "page_size": 20,     // 每页数量
    "total": 100,        // 总记录数
    "total_pages": 5     // 总页数
  }
}
```

### 7.3 排序规则

**默认排序**: 按 `created_at` 降序（最新创建的在前）

**实现**:

```python
query.order_by(desc(Project.created_at))
```

### 7.4 筛选字段

支持的筛选参数（`/projects` 端点）:

| 参数 | 类型 | 匹配方式 | 示例 |
|------|------|---------|------|
| `status` | string | 精确匹配 | `?status=active` |
| `manager_id` | integer | 精确匹配 | `?manager_id=123` |
| `client_name` | string | 模糊搜索 | `?client_name=测试` |

---

## 8. ⚠️ 已知差异与待修复项

### 8.1 P0 级别问题（高优先级）

#### 8.1.1 字段名不一致

**问题**:
- **Model 层** (`backend/models/core/project.py`): 使用 `project_name`, `project_code`
- **SoT** (`DATA_SCHEMA.md` 3.2.1): 定义为 `name`, `client_name`, `client_company`
- **Schema 层** (`backend/schemas/project.py`): 使用 `name` ✅ 正确

**影响**:
- Model 与 SoT 不一致，可能导致数据迁移问题
- Service 层使用 `request.name` 创建项目，但 Model 字段为 `project_name`

**修复建议**:
1. 创建 Alembic 迁移脚本重命名字段
2. 更新 Model 定义为 `name`
3. 运行测试确保无破坏性变更

#### 8.1.2 状态枚举值不匹配

**问题**:
- **SoT** (`STATE_MACHINE.md`): `draft`, `active`, `suspended`, `archived`
- **Schema** (`ProjectUpdateRequest`): pattern 使用 `planning`, `active`, `paused`, `completed`, `cancelled`
- **Service 统计方法**: 使用 `paused`, `completed`, `cancelled`

**影响**:
- 前端/API 使用的状态值与数据库 CHECK 约束冲突
- 统计功能返回错误的数据

**修复建议**:
1. 更新 Schema 的 `status` 字段 pattern 为 `^(draft|active|suspended|archived)$`
2. 更新 Service 层 `get_project_statistics()` 方法中的状态值
3. 数据迁移：将旧状态值映射到新状态值

#### 8.1.3 外键类型不一致

**问题**:
- **SoT** (`DATA_SCHEMA.md` 3.2.1): `created_by`, `updated_by`, `account_manager_id` 应为 UUID
- **Schema** (`ProjectResponse`): `created_by: int`, `account_manager_id: Optional[int]`

**影响**:
- 响应数据类型与数据库不一致
- 可能导致类型错误

**修复建议**:
1. 更新 Schema 定义：
   ```python
   created_by: UUID
   account_manager_id: Optional[UUID]
   ```

#### 8.1.4 创建项目权限限制过严

**问题**:
- **代码实现** (`project_service.py:44`): 仅允许 `admin` 创建项目
- **预期行为**: `admin` 和 `account_manager` 都应该能创建项目

**影响**:
- `account_manager` 无法创建项目

**修复建议**:
```python
if current_user.role not in ["admin", "account_manager"]:
    raise PermissionDeniedError("只有管理员和项目经理可以创建项目")
```

#### 8.1.5 添加费用权限不完整

**问题**:
- **代码实现** (`_can_user_add_expense`): 仅允许 `admin`, `account_manager`
- **预期行为**: `finance` 角色也应该能添加费用

**影响**:
- 财务人员无法添加项目费用

**修复建议**:
```python
def _can_user_add_expense(self, user: User, project: Project) -> bool:
    if user.role in ["admin", "account_manager", "finance"]:
        return True
    else:
        return False
```

### 8.2 P1 级别问题（中优先级）

#### 8.2.1 审计日志未实现

**问题**:
- `_create_audit_log()` 方法仅为占位符（TODO 标注）

**影响**:
- 无法追溯项目的创建、更新、删除操作

**修复建议**:
1. 设计 `audit_logs` 表结构（如不存在）
2. 实现审计日志写入逻辑
3. 关键操作添加审计记录

#### 8.2.2 删除限制检查不完整

**问题**:
- 仅检查 `ad_accounts` 依赖
- 未检查 `daily_reports`, `topup_requests`, `reconciliation_details`

**影响**:
- 可能删除仍有关联数据的项目

**修复建议**:
- 补全所有外键依赖检查

#### 8.2.3 计算字段性能问题

**问题**:
- `total_spent`, `total_accounts`, `active_accounts` 在 Service 层手动计算
- 每次查询详情都需要计算

**影响**:
- 查询性能下降

**修复建议**:
- 添加数据库视图
- 或使用 SQLAlchemy `column_property`

### 8.3 P2 级别问题（低优先级）

#### 8.3.1 分页元数据不完整

**问题**:
- 缺少 `has_next`, `has_prev` 字段

**影响**:
- 前端需要自行计算是否有下一页

**修复建议**:
```python
"pagination": {
    "page": page,
    "page_size": page_size,
    "total": total,
    "total_pages": total_pages,
    "has_next": page < total_pages,
    "has_prev": page > 1
}
```

#### 8.3.2 路由层权限装饰器被注释

**问题**:
- `@require_role` 装饰器在多个端点被注释

**影响**:
- 权限检查完全依赖 Service 层
- 无法在 API 文档中自动显示权限要求

**修复建议**:
- 启用路由层权限装饰器作为第一道防线
- Service 层保留详细权限检查

---

## 9. 相关文档

- [项目模块概览](./OVERVIEW.md)
- [数据结构说明](./DATA_NOTES.md)
- [状态机定义](../../core/STATE_MACHINE.md)
- [数据库表结构](../../core/DATA_SCHEMA.md)
- [API 开发流程](../../core/API_DEVELOPMENT_FLOW.md)
- [错误码定义](../../ERROR_CODES.md)
- [权限系统设计](../../security/RLS_POLICIES.md)

---

## 10. 更新日志

| 版本 | 日期 | 作者 | 说明 |
|------|------|------|------|
| v1.0 | 2025-11-19 | Claude | 基于当前代码实现生成，标注已知差异 |

---

**文档状态**: ✅ 已完成
**实现状态**: ⚠️ 部分实现（存在已知差异）
**下一步行动**: 参考第 8 章修复已知问题
