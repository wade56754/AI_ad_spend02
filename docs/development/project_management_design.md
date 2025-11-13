# 项目管理模块设计文档

> **模块名称**: 项目管理 (Project Management)
> **设计版本**: v1.0
> **设计日期**: 2025-11-12
> **设计人员**: Claude协作开发

---

## 📋 需求分析

### 业务场景
项目管理是AI广告代投系统的基础模块，用于管理客户的广告投放项目，包括项目创建、配置、状态跟踪等。

### 核心功能
1. **项目创建** - 管理员创建新项目，配置基本信息
2. **项目列表** - 所有角色可查看项目列表（权限过滤）
3. **项目详情** - 查看项目详细信息、统计数据
4. **项目更新** - 管理员更新项目信息
5. **项目状态管理** - 项目生命周期管理
6. **项目分配** - 分配给项目经理管理

### 参与角色及权限
| 角色 | 权限范围 | 说明 |
|------|----------|------|
| admin | 全部权限 | 创建、编辑、删除、查看所有项目 |
| finance | 只读权限 | 查看所有项目信息（用于财务分析） |
| data_operator | 只读权限 | 查看所有项目信息（用于数据统计） |
| account_manager | 管理权限 | 查看和管理自己负责的项目 |
| media_buyer | 只读权限 | 查看自己参与的项目 |

### 业务规则
1. 每个项目必须有客户名称
2. 项目状态：planning → active → paused → completed → cancelled
3. 只有admin可以创建和删除项目
4. account_manager可以查看和更新自己管理的项目
5. 项目预算不能为负数

---

## 🏗️ 数据模型设计

### 表结构

```sql
-- 项目主表
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    client_name VARCHAR(200) NOT NULL,
    client_company VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'planning' CHECK (status IN ('planning', 'active', 'paused', 'completed', 'cancelled')),
    budget DECIMAL(15,2) DEFAULT 0.00,
    currency VARCHAR(10) DEFAULT 'USD',
    start_date DATE,
    end_date DATE,
    account_manager_id INTEGER REFERENCES users(id),
    created_by INTEGER NOT NULL REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    INDEX idx_projects_status (status),
    INDEX idx_projects_client (client_name),
    INDEX idx_projects_manager (account_manager_id),
    INDEX idx_projects_created_by (created_by)
);

-- 项目成员关联表
CREATE TABLE project_members (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,  -- account_manager, media_buyer, analyst
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(project_id, user_id),
    INDEX idx_project_members_project (project_id),
    INDEX idx_project_members_user (user_id)
);

-- 项目费用记录表
CREATE TABLE project_expenses (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    expense_type VARCHAR(50) NOT NULL,  -- media_spend, service_fee, other
    amount DECIMAL(15,2) NOT NULL,
    description TEXT,
    expense_date DATE NOT NULL,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_expenses_project (project_id),
    INDEX idx_expenses_date (expense_date),
    INDEX idx_expenses_type (expense_type)
);
```

### RLS策略

```sql
-- 启用RLS
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_expenses ENABLE ROW LEVEL SECURITY;

-- 策略：管理员全权限
CREATE POLICY admin_full_access_projects ON projects
    FOR ALL TO admin_role
    USING (true)
    WITH CHECK (true);

-- 策略：财务和数据员只读
CREATE POLICY read_only_projects ON projects
    FOR SELECT TO finance_role, data_operator_role
    USING (true);

-- 策略：账户管理员管理自己的项目
CREATE POLICY manager_manage_projects ON projects
    FOR ALL TO account_manager_role
    USING (account_manager_id = current_user_id())
    WITH CHECK (account_manager_id = current_user_id());

-- 策略：投手查看参与的项目
CREATE POLICY media_buyer_view_projects ON projects
    FOR SELECT TO media_buyer_role
    USING (
        id IN (
            SELECT project_id FROM project_members
            WHERE user_id = current_user_id()
        )
    );
```

---

## 🔌 API端点设计

| 方法 | 路径 | 描述 | 权限要求 | 状态码 |
|------|------|------|----------|--------|
| GET | /api/v1/projects | 获取项目列表 | 所有角色 | 200 |
| POST | /api/v1/projects | 创建项目 | admin | 201 |
| GET | /api/v1/projects/{id} | 获取项目详情 | 相关角色 | 200 |
| PUT | /api/v1/projects/{id} | 更新项目 | admin, manager | 200 |
| DELETE | /api/v1/projects/{id} | 删除项目 | admin | 204 |
| POST | /api/v1/projects/{id}/assign | 分配项目成员 | admin | 200 |
| GET | /api/v1/projects/{id}/members | 获取项目成员 | 相关角色 | 200 |
| DELETE | /api/v1/projects/{id}/members/{user_id} | 移除项目成员 | admin | 204 |
| GET | /api/v1/projects/{id}/expenses | 获取项目费用 | 相关角色 | 200 |
| POST | /api/v1/projects/{id}/expenses | 添加项目费用 | admin, manager | 201 |
| GET | /api/v1/projects/statistics | 获取项目统计 | admin, finance, data_operator | 200 |

---

## 📝 Schema设计

### 请求Schema

```python
# 创建项目请求
class ProjectCreateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=200)
    client_name: str = Field(..., min_length=1, max_length=200)
    client_company: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    budget: Decimal = Field(0, ge=0, decimal_places=2)
    currency: str = Field("USD", max_length=10)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    account_manager_id: Optional[int] = None

    @field_validator('end_date')
    def validate_dates(cls, v, info):
        if v and 'start_date' in info.data and info.data['start_date']:
            if v < info.data['start_date']:
                raise ValueError('结束日期不能小于开始日期')
        return v

# 更新项目请求
class ProjectUpdateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    client_name: Optional[str] = Field(None, min_length=1, max_length=200)
    client_company: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, pattern="^(planning|active|paused|completed|cancelled)$")
    budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    account_manager_id: Optional[int] = None

# 分配成员请求
class ProjectMemberAssignRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(..., gt=0)
    role: str = Field(..., pattern="^(account_manager|media_buyer|analyst)$")

# 费用记录请求
class ProjectExpenseRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    expense_type: str = Field(..., pattern="^(media_spend|service_fee|other)$")
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    description: Optional[str] = Field(None, max_length=500)
    expense_date: date = Field(...)
```

### 响应Schema

```python
# 项目响应
class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    client_name: str
    client_company: str
    description: Optional[str]
    status: str
    budget: Decimal
    currency: str
    start_date: Optional[date]
    end_date: Optional[date]
    account_manager_id: Optional[int]
    account_manager_name: Optional[str]
    total_spent: Decimal
    total_accounts: int
    active_accounts: int
    created_by: int
    created_by_name: str
    created_at: datetime
    updated_at: datetime

# 项目成员响应
class ProjectMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_name: str
    user_email: str
    user_role: str
    project_role: str
    joined_at: datetime

# 项目费用响应
class ProjectExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    expense_type: str
    amount: Decimal
    description: Optional[str]
    expense_date: date
    created_by_name: str
    created_at: datetime

# 项目统计响应
class ProjectStatisticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_projects: int
    active_projects: int
    paused_projects: int
    completed_projects: int
    total_budget: Decimal
    total_spent: Decimal
    total_clients: int
    avg_project_value: Decimal
    top_performers: List[Dict]  # 前5个项目
```

---

## ⚠️ 错误码设计

| 错误码 | HTTP状态码 | 描述 | 触发条件 |
|--------|------------|------|----------|
| SYS_004 | 404 | 项目不存在 | ID不存在 |
| BIZ_101 | 400 | 项目名称已存在 | 重复名称 |
| BIZ_102 | 422 | 项目状态转换无效 | 非法状态转换 |
| BIZ_103 | 400 | 结束日期无效 | 小于开始日期 |
| BIZ_104 | 403 | 无权限操作项目 | 权限不足 |
| BIZ_105 | 400 | 预算不能为负 | 负数预算 |

---

## 🎯 阶段一交付检查

- [x] 业务需求分析完成
- [x] API端点清单设计完成（11个端点）
- [x] 数据模型设计完成（3张表）
- [x] RLS策略设计完成
- [x] Schema设计完成（4个请求/响应模型）
- [x] 错误码定义完成
- [x] 权限矩阵确认

---

**下一步**: 进入阶段二 - 代码实现