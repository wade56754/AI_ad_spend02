# 数据库设计文档 (实际版)

> **文档目的**: 提供AI广告代投系统的真实数据库设计文档
> **目标读者**: 后端开发工程师、数据库管理员、架构师
> **更新日期**: 2025-11-16
> **版本**: v4.0 - 基于实际代码生成

---

## 📋 目录

1. [数据库设计概览](#数据库设计概览)
2. [核心表结构](#核心表结构)
3. [关联关系图](#关联关系图)
4. [权限控制说明](#权限控制说明)
5. [索引优化策略](#索引优化策略)
6. [最佳实践](#最佳实践)

---

## 数据库设计概览

### 技术栈

- **数据库**: PostgreSQL (Supabase托管)
- **ORM**: SQLAlchemy (同步版)
- **迁移工具**: Alembic
- **权限控制**: 应用层实现 (Service层 + @require_role装饰器)

### 设计特点

1. **混合主键类型**:
   - 用户相关表使用 **UUID** (users, channels)
   - 业务表使用 **Integer自增** (projects, ad_accounts, topups等)

2. **应用层权限**: 不使用PostgreSQL RLS，所有权限在Service层控制

3. **完整审计**: 主要业务表都有关联的历史/审计表

4. **关系映射**: 使用SQLAlchemy relationship定义表关系

---

## 核心表结构

### 1. 用户与角色管理

#### 1.1 users (用户表)

```python
class User(Base):
    __tablename__ = "users"

    # 主键 - UUID类型
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # 基本信息
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=True)

    # 角色信息
    role = Column(String(64), nullable=False, default="trader")
    role_id = Column(GUID(), ForeignKey("roles.id"), nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**字段说明**:
- `id`: UUID主键，使用`uuid.uuid4()`生成
- `email`: 用户邮箱，唯一约束
- `name`: 用户姓名
- `role`: 角色名称，枚举值：`admin`, `manager`, `data_clerk`, `finance`, `media_buyer`
- `role_id`: 关联roles表（如使用）

**索引**:
```sql
CREATE UNIQUE INDEX users_email_key ON users(email);
```

**说明**:
- ✅ 使用 **Supabase Auth** 进行身份验证，users表不存储密码
- ✅ 简化的用户表，扩展信息在其他表

---

#### 1.2 roles (角色表)

```python
class Role(Base):
    __tablename__ = "roles"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(32), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**内置角色**:
| 角色 | 说明 | 权限范围 |
|------|------|---------|
| `admin` | 系统管理员 | 全部权限 |
| `manager` | 项目经理 | 管理自己的项目 |
| `data_clerk` | 数据员/户管 | 管理账户和日报 |
| `finance` | 财务人员 | 财务审批和对账 |
| `media_buyer` | 投手 | 提交日报和充值申请 |

---

### 2. 项目管理

#### 2.1 projects (项目表)

```python
class Project(Base):
    __tablename__ = "projects"

    # 主键 - Integer自增
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 基本信息
    name = Column(String(200), nullable=False, index=True, comment="项目名称")
    client_name = Column(String(200), nullable=False, comment="客户联系人姓名")
    client_company = Column(String(200), nullable=False, comment="客户公司名称")
    description = Column(Text, nullable=True, comment="项目描述")

    # 项目状态
    status = Column(String(20), default="planning", nullable=False, index=True)
    # 状态枚举: planning, active, paused, completed, cancelled

    # 预算信息
    budget = Column(Numeric(15, 2), default=0.00, comment="项目预算")
    currency = Column(String(10), default="USD", comment="货币类型")

    # 时间信息
    start_date = Column(Date, nullable=True, comment="项目开始日期")
    end_date = Column(Date, nullable=True, comment="项目结束日期")

    # 管理信息
    account_manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**索引**:
```sql
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_client ON projects(client_name);
CREATE INDEX idx_projects_manager ON projects(account_manager_id);
CREATE INDEX idx_projects_created_by ON projects(created_by);
CREATE INDEX idx_projects_dates ON projects(start_date, end_date);
```

**关联关系**:
- `ad_accounts`: 一对多，项目下的广告账户
- `members`: 一对多，项目成员
- `expenses`: 一对多，项目费用记录

---

#### 2.2 project_members (项目成员表)

```python
class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    role = Column(String(50), nullable=False)
    # 角色枚举: account_manager, media_buyer, analyst
    joined_at = Column(DateTime, default=datetime.utcnow)
```

**唯一约束**:
```sql
CREATE UNIQUE INDEX uq_project_members ON project_members(project_id, user_id);
```

---

#### 2.3 project_expenses (项目费用表)

```python
class ProjectExpense(Base):
    __tablename__ = "project_expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    expense_type = Column(String(50), nullable=False)
    # 费用类型: media_spend, service_fee, other
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(Text, nullable=True)
    expense_date = Column(Date, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

### 3. 渠道管理

#### 3.1 channels (渠道表)

```python
class Channel(Base):
    __tablename__ = "channels"

    # 主键 - UUID类型
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # 基本信息
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)

    # 联系信息
    contact_person = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    contact_wechat = Column(String(100), nullable=True)

    # 费用结构
    service_fee_rate = Column(Numeric(5, 4), nullable=False)  # 例如: 0.0800 = 8%
    account_setup_fee = Column(Numeric(10, 2), default=0)
    minimum_topup = Column(Numeric(10, 2), default=0)
    fee_structure = Column(JSON, nullable=True)
    payment_terms = Column(Text, nullable=True)

    # 渠道状态
    status = Column(String(20), default="active")  # active, inactive, suspended
    priority = Column(Integer, default=1)

    # 质量评估
    quality_score = Column(Numeric(3, 2), nullable=True)  # 0-10
    reliability_score = Column(Numeric(3, 2), nullable=True)
    price_competitiveness = Column(Numeric(3, 2), nullable=True)

    # 统计数据
    total_accounts = Column(Integer, default=0)
    active_accounts = Column(Integer, default=0)
    dead_accounts = Column(Integer, default=0)
    total_spend = Column(Numeric(15, 2), default=0)

    # 管理信息
    notes = Column(Text, nullable=True)
    created_by = Column(GUID(), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**关联表**:
- `channel_reviews`: 渠道评价
- `channel_account_requests`: 账户申请记录
- `channel_performance`: 渠道表现统计
- `channel_contacts`: 渠道联系人

---

### 4. 广告账户管理

#### 4.1 ad_accounts (广告账户表)

```python
class AdAccount(Base):
    __tablename__ = "ad_accounts"

    # 主键 - Integer自增
    id = Column(Integer, primary_key=True, index=True)

    # 账户标识
    account_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)

    # 平台信息
    platform = Column(String(50), nullable=False)
    # 平台枚举: facebook, instagram, google, tiktok
    platform_account_id = Column(String(255), nullable=True)
    platform_business_id = Column(String(255), nullable=True)

    # 关联信息 (核心外键)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 账户状态
    status = Column(String(20), nullable=False, default="new")
    # 状态枚举: new, testing, active, suspended, dead, archived
    status_reason = Column(Text, nullable=True)
    last_status_change = Column(DateTime, nullable=True)

    # 生命周期时间戳
    created_date = Column(DateTime, nullable=True)
    activated_date = Column(DateTime, nullable=True)
    suspended_date = Column(DateTime, nullable=True)
    dead_date = Column(DateTime, nullable=True)
    archived_date = Column(DateTime, nullable=True)

    # 预算信息
    daily_budget = Column(DECIMAL(10, 2), nullable=True)
    total_budget = Column(DECIMAL(12, 2), nullable=True)
    remaining_budget = Column(DECIMAL(12, 2), nullable=True)

    # 账户配置
    currency = Column(String(3), default="USD")
    timezone = Column(String(50), nullable=True)
    country = Column(String(2), nullable=True)

    # 性能数据
    total_spend = Column(DECIMAL(15, 2), default=0)
    total_leads = Column(Integer, default=0)
    avg_cpl = Column(DECIMAL(10, 2), nullable=True)
    best_cpl = Column(DECIMAL(10, 2), nullable=True)

    # 开户费用
    setup_fee = Column(DECIMAL(10, 2), default=0)
    setup_fee_paid = Column(Boolean, default=False)

    # 账户配置
    account_type = Column(String(50), nullable=True)
    payment_method = Column(String(50), nullable=True)
    billing_information = Column(JSON, nullable=True)

    # 监控设置
    auto_monitoring = Column(Boolean, default=True)
    alert_thresholds = Column(JSON, nullable=True)

    # 管理信息
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    account_metadata = Column(JSON, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

**约束**:
```sql
ALTER TABLE ad_accounts ADD CONSTRAINT check_account_status
    CHECK (status IN ('new', 'testing', 'active', 'suspended', 'dead', 'archived'));

ALTER TABLE ad_accounts ADD CONSTRAINT check_daily_budget_non_negative
    CHECK (daily_budget >= 0);

ALTER TABLE ad_accounts ADD CONSTRAINT check_total_budget_non_negative
    CHECK (total_budget >= 0);

ALTER TABLE ad_accounts ADD CONSTRAINT check_total_spend_non_negative
    CHECK (total_spend >= 0);
```

**索引**:
```sql
CREATE INDEX idx_ad_accounts_platform ON ad_accounts(platform);
CREATE INDEX idx_ad_accounts_status ON ad_accounts(status);
CREATE INDEX idx_ad_accounts_project ON ad_accounts(project_id);
CREATE INDEX idx_ad_accounts_channel ON ad_accounts(channel_id);
CREATE INDEX idx_ad_accounts_assigned_user ON ad_accounts(assigned_user_id);
CREATE INDEX idx_ad_accounts_created_at ON ad_accounts(created_at);
```

**关联表**:
- `account_status_history`: 状态变更历史
- `account_performance`: 性能统计
- `account_alerts`: 预警记录
- `account_documents`: 文档附件
- `account_notes`: 备注记录

---

#### 4.2 account_status_history (账户状态历史表)

```python
class AccountStatusHistory(Base):
    __tablename__ = "account_status_history"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("ad_accounts.id"), nullable=False)

    # 状态变更信息
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=False)
    change_reason = Column(Text, nullable=True)

    # 变更时间和人员
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    change_source = Column(String(50), default="manual")
    # 来源枚举: manual, automatic, system, api

    # 相关数据
    performance_data = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
```

**索引**:
```sql
CREATE INDEX idx_account_status_history_account ON account_status_history(account_id);
CREATE INDEX idx_account_status_history_changed_at ON account_status_history(changed_at);
```

---

#### 4.3 account_performance (账户表现表)

```python
class AccountPerformance(Base):
    __tablename__ = "account_performance"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("ad_accounts.id"), nullable=False)

    # 统计周期
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # 消耗数据
    spend = Column(DECIMAL(15, 2), nullable=False)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    ctr = Column(DECIMAL(5, 4), nullable=True)

    # 转化数据
    leads = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    conversion_rate = Column(DECIMAL(5, 4), nullable=True)

    # 成本数据
    cpl = Column(DECIMAL(10, 2), nullable=True)
    cpa = Column(DECIMAL(10, 2), nullable=True)
    roas = Column(DECIMAL(5, 2), nullable=True)

    # 质量指标
    lead_quality_score = Column(DECIMAL(3, 2), nullable=True)
    account_health_score = Column(DECIMAL(3, 2), nullable=True)

    # 详细数据
    breakdown_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**约束**:
```sql
ALTER TABLE account_performance ADD CONSTRAINT check_period_type
    CHECK (period_type IN ('daily', 'weekly', 'monthly'));

ALTER TABLE account_performance ADD CONSTRAINT check_period_date_valid
    CHECK (period_end >= period_start);
```

---

#### 4.4 account_alerts (账户预警表)

```python
class AccountAlert(Base):
    __tablename__ = "account_alerts"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("ad_accounts.id"), nullable=False)

    # 预警信息
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # 预警状态
    status = Column(String(20), default="active")
    # 状态枚举: active, acknowledged, resolved, ignored

    # 触发条件
    trigger_condition = Column(JSON, nullable=True)
    trigger_value = Column(DECIMAL(15, 2), nullable=True)
    threshold_value = Column(DECIMAL(15, 2), nullable=True)

    # 处理信息
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolution = Column(Text, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # 通知设置
    notify_users = Column(JSON, nullable=True)
    notification_sent = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

---

### 5. 充值管理

#### 5.1 topup_requests (充值申请表)

```python
class TopupRequest(Base):
    __tablename__ = "topup_requests"

    # 主键 - Integer自增
    id = Column(Integer, primary_key=True, index=True)
    request_no = Column(String(50), unique=True, nullable=False, index=True)

    # 关联信息
    ad_account_id = Column(Integer, ForeignKey("ad_accounts.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # 金额相关
    requested_amount = Column(DECIMAL(15, 2), nullable=False)
    actual_amount = Column(DECIMAL(15, 2), nullable=True)
    currency = Column(String(10), nullable=False, default="USD")

    # 申请信息
    urgency_level = Column(String(20), nullable=False, default="normal")
    # 紧急程度: normal, urgent
    reason = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    expected_date = Column(DATE, nullable=True)

    # 状态信息
    status = Column(String(20), nullable=False, default="pending")
    # 状态流转: pending -> data_reviewed -> finance_approved -> paid -> completed

    # 支付信息
    payment_method = Column(String(50), nullable=True)
    transaction_id = Column(String(100), nullable=True)
    receipt_url = Column(String(500), nullable=True)

    # 申请人信息
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 数据审核信息
    data_reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    data_reviewed_at = Column(TIMESTAMP, nullable=True)
    data_review_notes = Column(Text, nullable=True)

    # 财务审批信息
    finance_approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    finance_approved_at = Column(TIMESTAMP, nullable=True)
    finance_approve_notes = Column(Text, nullable=True)

    # 支付完成时间
    paid_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)

    # 时间戳
    created_at = Column(TIMESTAMP, default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
```

**索引**:
```sql
CREATE INDEX idx_topup_requests_account ON topup_requests(ad_account_id);
CREATE INDEX idx_topup_requests_project ON topup_requests(project_id);
CREATE INDEX idx_topup_requests_status ON topup_requests(status);
CREATE INDEX idx_topup_requests_requested_by ON topup_requests(requested_by);
CREATE INDEX idx_topup_requests_created_at ON topup_requests(created_at);
CREATE INDEX idx_topup_requests_urgency ON topup_requests(urgency_level);
```

**关联表**:
- `topup_transactions`: 交易流水记录
- `topup_approval_logs`: 审批日志

---

#### 5.2 topup_transactions (充值交易记录表)

```python
class TopupTransaction(Base):
    __tablename__ = "topup_transactions"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("topup_requests.id"), nullable=False)
    transaction_no = Column(String(100), unique=True, nullable=False, index=True)

    # 交易信息
    amount = Column(DECIMAL(15, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    payment_method = Column(String(50), nullable=False)
    payment_account = Column(String(100), nullable=True)

    # 时间信息
    transaction_date = Column(TIMESTAMP, nullable=False)

    # 凭证信息
    receipt_file = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    # 创建信息
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())
```

---

#### 5.3 topup_approval_logs (充值审批日志表)

```python
class TopupApprovalLog(Base):
    __tablename__ = "topup_approval_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("topup_requests.id"), nullable=False)

    # 操作信息
    action = Column(String(50), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    actor_role = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)

    # 状态变更
    previous_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=True)

    # 请求信息
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)

    # 时间
    created_at = Column(TIMESTAMP, default=func.now())
```

---

### 6. 日报管理

#### 6.1 ad_spend_daily (广告日消耗表)

```python
class AdSpendDaily(Base):
    __tablename__ = "ad_spend_daily"

    # 主键 - UUID类型
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # 关联信息
    ad_account_id = Column(Integer, ForeignKey("ad_accounts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 日期
    date = Column(Date, nullable=False)

    # 消耗数据
    spend = Column(Numeric(18, 2), nullable=False, server_default="0")
    leads_count = Column(Integer, nullable=False, server_default="0")
    cost_per_lead = Column(Numeric(18, 2), nullable=False, server_default="0")

    # 异常标记
    is_anomaly = Column(Boolean, nullable=False, server_default="false")
    anomaly_reason = Column(Text, nullable=True)

    # 备注
    note = Column(Text, nullable=True)

    # 创建和更新信息
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

**唯一约束**:
```sql
CREATE UNIQUE INDEX ad_spend_daily_unique_account_date
    ON ad_spend_daily(ad_account_id, date);
```

---

#### 6.2 daily_reports (日报表)

```python
class DailyReport(Base):
    __tablename__ = "daily_reports"

    # 主键 - Integer自增
    id = Column(Integer, primary_key=True, index=True)

    # 关联信息
    report_date = Column(Date, nullable=False)
    ad_account_id = Column(Integer, ForeignKey("ad_accounts.id"), nullable=False)

    # 广告信息
    campaign_name = Column(String(200), nullable=True)
    ad_group_name = Column(String(200), nullable=True)
    ad_creative_name = Column(String(200), nullable=True)

    # 投放数据
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    spend = Column(DECIMAL(12, 2), default=0.00)
    conversions = Column(Integer, default=0)
    new_follows = Column(Integer, default=0)
    cpa = Column(DECIMAL(10, 2), nullable=True)
    roas = Column(DECIMAL(10, 2), nullable=True)

    # 状态和备注
    status = Column(String(20), default="pending")
    # 状态枚举: pending, approved, rejected
    notes = Column(Text, nullable=True)
    audit_notes = Column(Text, nullable=True)
    audit_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    audit_time = Column(DateTime, nullable=True)

    # 创建和更新信息
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

**唯一约束**:
```sql
CREATE UNIQUE INDEX uq_daily_reports_date_account
    ON daily_reports(report_date, ad_account_id);
```

**索引**:
```sql
CREATE INDEX idx_daily_reports_date ON daily_reports(report_date);
CREATE INDEX idx_daily_reports_account ON daily_reports(ad_account_id);
CREATE INDEX idx_daily_reports_status ON daily_reports(status);
CREATE INDEX idx_daily_reports_created_by ON daily_reports(created_by);
CREATE INDEX idx_daily_reports_audit_user ON daily_reports(audit_user_id);
CREATE INDEX idx_daily_reports_date_status ON daily_reports(report_date, status);
CREATE INDEX idx_daily_reports_account_date ON daily_reports(ad_account_id, report_date);
```

**关联表**:
- `daily_report_audit_logs`: 审核日志

---

#### 6.3 daily_report_audit_logs (日报审核日志表)

```python
class DailyReportAuditLog(Base):
    __tablename__ = "daily_report_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    daily_report_id = Column(
        Integer,
        ForeignKey("daily_reports.id", ondelete="CASCADE"),
        nullable=False
    )

    # 操作信息
    action = Column(String(20), nullable=False)
    # 操作类型: created, updated, approved, rejected
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=True)

    # 审核信息
    audit_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    audit_time = Column(DateTime, default=func.now())
    audit_notes = Column(Text, nullable=True)

    # 审计信息
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
```

---

### 7. 对账管理

#### 7.1 reconciliation_batches (对账批次表)

```python
class ReconciliationBatch(Base):
    __tablename__ = "reconciliation_batches"

    # 主键 - Integer自增
    id = Column(Integer, primary_key=True, index=True)
    batch_no = Column(String(50), unique=True, nullable=False)
    reconciliation_date = Column(Date, nullable=False)

    # 对账状态
    status = Column(String(20), nullable=False, default="pending")
    # 状态枚举: pending, processing, completed, exception, resolved

    # 统计信息
    total_accounts = Column(Integer, nullable=False, default=0)
    matched_accounts = Column(Integer, nullable=False, default=0)
    mismatched_accounts = Column(Integer, nullable=False, default=0)

    # 金额统计
    total_platform_spend = Column(DECIMAL(15, 2), nullable=False, default=Decimal('0.00'))
    total_internal_spend = Column(DECIMAL(15, 2), nullable=False, default=Decimal('0.00'))
    total_difference = Column(DECIMAL(15, 2), nullable=False, default=Decimal('0.00'))

    # 效率统计
    auto_matched = Column(Integer, nullable=True)
    manual_reviewed = Column(Integer, nullable=True)

    # 时间信息
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    notes = Column(Text, nullable=True)
```

**约束**:
```sql
ALTER TABLE reconciliation_batches ADD CONSTRAINT check_batch_status
    CHECK (status IN ('pending', 'processing', 'completed', 'exception', 'resolved'));

ALTER TABLE reconciliation_batches ADD CONSTRAINT check_total_accounts_non_negative
    CHECK (total_accounts >= 0);
```

**索引**:
```sql
CREATE INDEX idx_reconciliation_batches_date ON reconciliation_batches(reconciliation_date);
CREATE INDEX idx_reconciliation_batches_status ON reconciliation_batches(status);
CREATE INDEX idx_reconciliation_batches_created_at ON reconciliation_batches(created_at);
```

**关联表**:
- `reconciliation_details`: 对账明细
- `reconciliation_adjustments`: 调整记录
- `reconciliation_reports`: 对账报告

---

#### 7.2 reconciliation_details (对账详情表)

```python
class ReconciliationDetail(Base):
    __tablename__ = "reconciliation_details"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("reconciliation_batches.id", ondelete="CASCADE"))
    ad_account_id = Column(Integer, ForeignKey("ad_accounts.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)

    # 平台数据
    platform_spend = Column(DECIMAL(15, 2), nullable=False, default=Decimal('0.00'))
    platform_currency = Column(String(10), nullable=False, default="USD")
    platform_data_date = Column(Date, nullable=True)

    # 内部数据
    internal_spend = Column(DECIMAL(15, 2), nullable=False, default=Decimal('0.00'))
    internal_currency = Column(String(10), nullable=False, default="USD")
    internal_data_date = Column(Date, nullable=True)

    # 差异信息
    spend_difference = Column(DECIMAL(15, 2), nullable=False, default=Decimal('0.00'))
    exchange_rate = Column(DECIMAL(10, 4), nullable=False, default=Decimal('1.0000'))
    is_matched = Column(Boolean, nullable=False, default=False)
    match_status = Column(String(20), nullable=False, default="pending")
    # 匹配状态: pending, matched, auto_matched, manual_review, exception, resolved

    # 差异原因
    difference_type = Column(String(50), nullable=True)
    difference_reason = Column(Text, nullable=True)
    auto_confidence = Column(DECIMAL(3, 2), nullable=False, default=Decimal('0.00'))

    # 处理信息
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_method = Column(String(50), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

**约束**:
```sql
ALTER TABLE reconciliation_details ADD CONSTRAINT check_match_status
    CHECK (match_status IN ('pending', 'matched', 'auto_matched', 'manual_review', 'exception', 'resolved'));

ALTER TABLE reconciliation_details ADD CONSTRAINT check_auto_confidence_range
    CHECK (auto_confidence >= 0 AND auto_confidence <= 1);
```

---

#### 7.3 reconciliation_adjustments (对账调整记录表)

```python
class ReconciliationAdjustment(Base):
    __tablename__ = "reconciliation_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    detail_id = Column(Integer, ForeignKey("reconciliation_details.id", ondelete="CASCADE"))
    batch_id = Column(Integer, ForeignKey("reconciliation_batches.id", ondelete="CASCADE"))

    # 调整信息
    adjustment_type = Column(String(50), nullable=False)
    # 调整类型: spend_adjustment, date_adjustment
    original_amount = Column(DECIMAL(15, 2), nullable=False)
    adjustment_amount = Column(DECIMAL(15, 2), nullable=False)
    adjusted_amount = Column(DECIMAL(15, 2), nullable=False)

    # 调整原因
    adjustment_reason = Column(String(100), nullable=False)
    detailed_reason = Column(Text, nullable=False)
    evidence_url = Column(String(500), nullable=True)

    # 审批信息
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finance_approve = Column(Boolean, nullable=False, default=False)
    finance_approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    finance_approved_at = Column(DateTime, nullable=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    notes = Column(Text, nullable=True)
```

---

#### 7.4 reconciliation_reports (对账报告表)

```python
class ReconciliationReport(Base):
    __tablename__ = "reconciliation_reports"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("reconciliation_batches.id"), nullable=True)
    report_type = Column(String(50), nullable=False)
    # 报告类型: daily, weekly, monthly
    report_period_start = Column(Date, nullable=False)
    report_period_end = Column(Date, nullable=False)

    # 报告内容
    report_data = Column(JSON, nullable=False)
    chart_data = Column(JSON, nullable=True)
    summary_data = Column(JSON, nullable=False)

    # 生成信息
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

---

## 关联关系图

### 核心数据流

```
用户 (users)
    ├── 创建项目 (projects)
    │       ├── 分配成员 (project_members)
    │       ├── 记录费用 (project_expenses)
    │       └── 关联账户 (ad_accounts)
    │               ├── 所属渠道 (channels)
    │               ├── 分配投手 (users)
    │               ├── 状态历史 (account_status_history)
    │               ├── 性能数据 (account_performance)
    │               ├── 预警记录 (account_alerts)
    │               ├── 日消耗 (ad_spend_daily)
    │               ├── 日报 (daily_reports)
    │               │       └── 审核日志 (daily_report_audit_logs)
    │               └── 充值申请 (topup_requests)
    │                       ├── 交易记录 (topup_transactions)
    │                       └── 审批日志 (topup_approval_logs)
    └── 对账批次 (reconciliation_batches)
            ├── 对账明细 (reconciliation_details)
            ├── 调整记录 (reconciliation_adjustments)
            └── 对账报告 (reconciliation_reports)
```

### 外键关系总结

| 子表 | 外键字段 | 父表 | 级联删除 |
|------|---------|------|---------|
| project_members | project_id | projects | CASCADE |
| project_members | user_id | users | CASCADE |
| project_expenses | project_id | projects | CASCADE |
| ad_accounts | project_id | projects | - |
| ad_accounts | channel_id | channels | - |
| ad_accounts | assigned_user_id | users | - |
| account_status_history | account_id | ad_accounts | - |
| topup_requests | ad_account_id | ad_accounts | - |
| topup_requests | project_id | projects | - |
| daily_reports | ad_account_id | ad_accounts | - |
| reconciliation_details | batch_id | reconciliation_batches | CASCADE |
| reconciliation_adjustments | detail_id | reconciliation_details | CASCADE |

---

## 权限控制说明

### 应用层权限实现

本系统**不使用PostgreSQL RLS**，所有权限在应用层实现。

#### Service层权限控制

```python
class ProjectService:
    def _apply_permission_filter(self, query, current_user: User):
        """根据用户角色过滤数据"""
        if current_user.role == "admin":
            return query  # 管理员查看所有
        elif current_user.role == "manager":
            return query.filter(Project.account_manager_id == current_user.id)
        elif current_user.role == "media_buyer":
            return query.join(ProjectMember).filter(
                ProjectMember.user_id == current_user.id
            )
        else:
            return query  # finance和data_clerk查看所有

    def _can_user_access(self, user: User, project: Project) -> bool:
        """检查用户是否可以访问项目"""
        if user.role == "admin":
            return True
        elif user.role == "manager":
            return project.account_manager_id == user.id
        elif user.role == "media_buyer":
            return any(m.user_id == user.id for m in project.members)
        else:
            return True
```

#### Router层权限装饰器

```python
@router.post("/projects", status_code=201)
@require_role(["admin", "manager"])  # 接口级权限
async def create_project(
    request: ProjectCreateRequest,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)  # JWT认证
):
    # Service层会进一步检查数据级权限
    project = service.create_project(request, current_user)
    return success_response(data=project)
```

### 角色权限矩阵

| 功能 | admin | manager | data_clerk | finance | media_buyer |
|------|-------|---------|------------|---------|-------------|
| **项目管理** |
| 创建项目 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 查看所有项目 | ✅ | ❌ | ✅ | ✅ | ❌ |
| 查看自己项目 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 更新项目 | ✅ | ✅(自己的) | ❌ | ❌ | ❌ |
| 删除项目 | ✅ | ❌ | ❌ | ❌ | ❌ |
| **账户管理** |
| 创建账户 | ✅ | ❌ | ✅ | ❌ | ❌ |
| 查看所有账户 | ✅ | ❌ | ✅ | ✅ | ❌ |
| 查看分配账户 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 更新账户 | ✅ | ❌ | ✅ | ❌ | ❌ |
| **日报管理** |
| 提交日报 | ✅ | ✅ | ✅ | ❌ | ✅ |
| 审核日报 | ✅ | ❌ | ✅ | ❌ | ❌ |
| 查看日报 | ✅ | ✅ | ✅ | ✅ | ✅(自己的) |
| **充值管理** |
| 申请充值 | ✅ | ✅ | ✅ | ❌ | ✅ |
| 数据审核 | ✅ | ❌ | ✅ | ❌ | ❌ |
| 财务审批 | ✅ | ❌ | ❌ | ✅ | ❌ |
| **对账管理** |
| 创建对账 | ✅ | ❌ | ❌ | ✅ | ❌ |
| 查看对账 | ✅ | ✅ | ❌ | ✅ | ❌ |
| 审核调整 | ✅ | ❌ | ❌ | ✅ | ❌ |

---

## 索引优化策略

### 单列索引

```sql
-- 高频查询字段
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_ad_accounts_status ON ad_accounts(status);
CREATE INDEX idx_topup_requests_status ON topup_requests(status);

-- 外键字段
CREATE INDEX idx_ad_accounts_project ON ad_accounts(project_id);
CREATE INDEX idx_ad_accounts_channel ON ad_accounts(channel_id);
CREATE INDEX idx_topup_requests_account ON topup_requests(ad_account_id);

-- 时间字段
CREATE INDEX idx_daily_reports_date ON daily_reports(report_date);
CREATE INDEX idx_reconciliation_batches_date ON reconciliation_batches(reconciliation_date);
```

### 复合索引

```sql
-- 优化常见组合查询
CREATE INDEX idx_daily_reports_account_date ON daily_reports(ad_account_id, report_date);
CREATE INDEX idx_daily_reports_date_status ON daily_reports(report_date, status);
CREATE INDEX idx_ad_accounts_project_status ON ad_accounts(project_id, status);
```

### 部分索引

```sql
-- 只索引活跃数据
CREATE INDEX idx_ad_accounts_active ON ad_accounts(status) WHERE status = 'active';
CREATE INDEX idx_topup_requests_pending ON topup_requests(status) WHERE status IN ('pending', 'data_reviewed');
```

### 唯一索引

```sql
-- 业务唯一约束
CREATE UNIQUE INDEX users_email_key ON users(email);
CREATE UNIQUE INDEX uq_project_members ON project_members(project_id, user_id);
CREATE UNIQUE INDEX ad_spend_daily_unique_account_date ON ad_spend_daily(ad_account_id, date);
CREATE UNIQUE INDEX uq_daily_reports_date_account ON daily_reports(report_date, ad_account_id);
```

---

## 最佳实践

### 1. 数据类型选择

✅ **正确做法**:
```python
# 金额字段 - 使用DECIMAL
amount = Column(DECIMAL(15, 2), nullable=False)

# 时间字段 - 使用DateTime with timezone
created_at = Column(DateTime(timezone=True), server_default=func.now())

# 状态字段 - String + CheckConstraint
status = Column(String(20), nullable=False)
__table_args__ = (
    CheckConstraint("status IN ('active', 'inactive')"),
)
```

❌ **避免做法**:
```python
# 金额使用Float - 精度问题
amount = Column(Float, nullable=False)  # ❌

# 没有时区的时间
created_at = Column(DateTime)  # ❌

# 状态没有约束
status = Column(String(20))  # ❌
```

---

### 2. 外键约束

✅ **明确级联策略**:
```python
# 级联删除 - 用于强依赖关系
project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))

# SET NULL - 用于可选关联
manager_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

# RESTRICT - 用于需要保护的关联
channel_id = Column(Integer, ForeignKey("channels.id", ondelete="RESTRICT"))
```

---

### 3. 默认值和约束

✅ **使用数据库默认值**:
```python
created_at = Column(DateTime(timezone=True), server_default=func.now())
status = Column(String(20), default="pending", server_default="pending")
is_active = Column(Boolean, default=True, server_default="true")
```

✅ **添加业务约束**:
```python
__table_args__ = (
    CheckConstraint("daily_budget >= 0", name="check_daily_budget_non_negative"),
    CheckConstraint("period_end >= period_start", name="check_period_valid"),
)
```

---

### 4. 审计字段

✅ **所有业务表必须包含**:
```python
created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
created_at = Column(DateTime(timezone=True), server_default=func.now())
updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

✅ **关键操作需要审计日志表**:
```python
class DailyReportAuditLog(Base):
    daily_report_id = Column(Integer, ForeignKey("daily_reports.id", ondelete="CASCADE"))
    action = Column(String(20), nullable=False)  # created, updated, approved
    audit_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    audit_time = Column(DateTime, default=func.now())
    ip_address = Column(INET, nullable=True)
```

---

### 5. 关系定义

✅ **使用relationship定义关系**:
```python
class Project(Base):
    # 一对多
    ad_accounts = relationship("AdAccount", back_populates="project")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")

    # 多对一
    account_manager = relationship("User", foreign_keys=[account_manager_id])
    creator = relationship("User", foreign_keys=[created_by])
```

✅ **指定foreign_keys避免歧义**:
```python
# 当多个字段引用同一表时，必须指定foreign_keys
class Project(Base):
    account_manager_id = Column(Integer, ForeignKey("users.id"))
    created_by = Column(Integer, ForeignKey("users.id"))

    account_manager = relationship("User", foreign_keys=[account_manager_id])
    creator = relationship("User", foreign_keys=[created_by])
```

---

### 6. JSON字段使用

✅ **适合存储非结构化数据**:
```python
# 动态配置
alert_thresholds = Column(JSON, nullable=True)  # {"cpl": 15, "daily_budget": 500}

# 扩展元数据
account_metadata = Column(JSON, nullable=True)

# 详细分解数据
breakdown_data = Column(JSON, nullable=True)
```

❌ **不要用JSON替代关系表**:
```python
# ❌ 错误 - 应该用关系表
members = Column(JSON)  # [{"user_id": 1, "role": "admin"}]

# ✅ 正确 - 使用关系表
class ProjectMember(Base):
    project_id = Column(Integer, ForeignKey("projects.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String(50))
```

---

### 7. 性能优化建议

✅ **查询优化**:
```python
# 使用joinedload避免N+1查询
projects = db.query(Project).options(
    joinedload(Project.account_manager),
    joinedload(Project.members).joinedload(ProjectMember.user)
).all()

# 只查询需要的字段
projects = db.query(Project.id, Project.name, Project.status).all()

# 使用分页
projects = db.query(Project).offset(skip).limit(limit).all()
```

✅ **索引使用**:
```python
# 确保WHERE条件字段有索引
query = db.query(Project).filter(
    Project.status == "active",  # ✅ 有索引
    Project.created_at >= start_date  # ✅ 有索引
)

# 复合索引顺序很重要
# 索引: (date, status)
# ✅ 好 - 能用到索引
query.filter(DailyReport.report_date == date, DailyReport.status == "pending")
# ❌ 差 - 只能用到status，无法充分利用索引
query.filter(DailyReport.status == "pending")
```

---

## 数据迁移

### Alembic迁移命令

```bash
# 生成迁移脚本
alembic revision --autogenerate -m "add new column"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看迁移历史
alembic history
```

### 迁移脚本示例

```python
"""add status reason to ad_accounts

Revision ID: 20251116_001
"""

def upgrade():
    op.add_column('ad_accounts',
        sa.Column('status_reason', sa.Text(), nullable=True, comment='状态变更原因')
    )

def downgrade():
    op.drop_column('ad_accounts', 'status_reason')
```

---

## 常见问题

### Q1: 为什么主键类型不统一？

**A**: 历史原因导致混用UUID和Integer：
- **users, channels** 使用UUID（早期设计）
- **projects, ad_accounts等** 使用Integer（后期优化）

**建议**: 保持现状，新表统一使用Integer自增主键（性能更好）。

---

### Q2: 为什么不使用PostgreSQL RLS？

**A**:
1. 使用Supabase托管，权限在应用层更灵活
2. Service层权限控制更易测试和维护
3. 避免数据库层和应用层权限逻辑冲突

---

### Q3: 软删除如何实现？

**A**: 目前**未实现软删除**（没有`deleted_at`字段）。

如需添加软删除：
```python
deleted_at = Column(DateTime, nullable=True)

# 查询时过滤
query.filter(Model.deleted_at.is_(None))

# 软删除
model.deleted_at = datetime.utcnow()
db.commit()
```

---

### Q4: 如何处理时区问题？

**A**:
```python
# ✅ 使用timezone-aware类型
created_at = Column(DateTime(timezone=True), server_default=func.now())

# ✅ Python代码使用UTC
from datetime import datetime, timezone
now = datetime.now(timezone.utc)

# ❌ 避免使用
now = datetime.utcnow()  # 返回naive datetime
```

---

## 附录

### A. 完整ER图

由于表结构复杂，建议使用工具生成ER图：

```bash
# 使用SQLAlchemy自动生成
pip install sqlalchemy_schemadisplay
python generate_er_diagram.py
```

---

### B. 表清单

| 序号 | 表名 | 主键类型 | 说明 |
|-----|------|---------|------|
| 1 | users | UUID | 用户表 |
| 2 | roles | UUID | 角色表 |
| 3 | projects | Integer | 项目表 |
| 4 | project_members | Integer | 项目成员 |
| 5 | project_expenses | Integer | 项目费用 |
| 6 | channels | UUID | 渠道表 |
| 7 | channel_reviews | UUID | 渠道评价 |
| 8 | channel_account_requests | UUID | 账户申请 |
| 9 | channel_performance | UUID | 渠道表现 |
| 10 | channel_contacts | UUID | 渠道联系人 |
| 11 | ad_accounts | Integer | 广告账户 |
| 12 | account_status_history | Integer | 状态历史 |
| 13 | account_performance | Integer | 账户表现 |
| 14 | account_alerts | Integer | 账户预警 |
| 15 | account_documents | Integer | 账户文档 |
| 16 | account_notes | Integer | 账户备注 |
| 17 | topup_requests | Integer | 充值申请 |
| 18 | topup_transactions | Integer | 充值交易 |
| 19 | topup_approval_logs | Integer | 充值审批日志 |
| 20 | ad_spend_daily | UUID | 广告日消耗 |
| 21 | daily_reports | Integer | 日报表 |
| 22 | daily_report_audit_logs | Integer | 日报审核日志 |
| 23 | reconciliation_batches | Integer | 对账批次 |
| 24 | reconciliation_details | Integer | 对账明细 |
| 25 | reconciliation_adjustments | Integer | 对账调整 |
| 26 | reconciliation_reports | Integer | 对账报告 |

**总计**: 26张核心表

---

**文档版本**: v4.0
**最后更新**: 2025-11-16
**维护责任人**: 后端开发团队
**基于代码**: backend/models/*.py
**下次审查**: 数据库结构变更时
