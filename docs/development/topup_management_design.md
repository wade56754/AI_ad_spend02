# 充值管理模块设计文档

> **模块名称**: 充值管理 (Top-up Management)
> **设计版本**: v1.0
> **设计日期**: 2025-11-12
> **设计人员**: Claude协作开发

---

## 📋 需求分析

### 业务场景
充值管理是AI广告代投系统的资金流转核心模块，负责处理广告账户的充值申请、审批、执行和追踪，确保资金安全和流转透明。

### 核心功能
1. **充值申请** - 投手/户管提交充值需求申请
2. **审核流程** - 数据员审核充值需求的合理性
3. **财务审批** - 财务人员最终审批并执行打款
4. **状态跟踪** - 全程跟踪充值状态和进度
5. **记录管理** - 完整的充值记录和凭证管理
6. **统计分析** - 充值金额、频次、时效性分析

### 参与角色及权限
| 角色 | 权限范围 | 说明 |
|------|----------|------|
| admin | 全部权限 | 查看、审批所有充值申请，查看统计 |
| finance | 审批执行 | 审核充值申请，执行打款，管理充值记录 |
| data_operator | 审核权限 | 审核充值需求的合理性，查看充值记录 |
| account_manager | 申请权限 | 为项目下的账户申请充值，查看自己项目的充值 |
| media_buyer | 申请权限 | 为自己负责的账户申请充值，查看自己的申请 |

### 业务规则
1. 充值金额必须大于0且小于等于设定上限（默认10万）
2. 充值申请必须关联到具体的广告账户
3. 账户余额不能超过设定的上限（默认50万）
4. 同一账户24小时内不能申请超过3次充值
5. 充值申请状态流转：pending → data_review → finance_approve → paid → completed
6. 只有财务人员可以将状态标记为已打款
7. 必须提供打款凭证才能完成充值流程

---

## 🏗️ 数据模型设计

### 表结构

```sql
-- 充值申请主表
CREATE TABLE topup_requests (
    id SERIAL PRIMARY KEY,
    request_no VARCHAR(50) NOT NULL UNIQUE,  -- 申请单号
    ad_account_id INTEGER NOT NULL REFERENCES ad_accounts(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),
    requested_amount DECIMAL(15,2) NOT NULL CHECK (requested_amount > 0),
    actual_amount DECIMAL(15,2),  -- 实际打款金额
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    urgency_level VARCHAR(20) DEFAULT 'normal' CHECK (urgency_level IN ('low', 'normal', 'high', 'urgent')),
    reason TEXT NOT NULL,  -- 充值原因
    notes TEXT,  -- 补充说明
    payment_method VARCHAR(50),  -- 打款方式
    transaction_id VARCHAR(100),  -- 交易流水号
    receipt_url VARCHAR(500),  -- 凭证URL
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'data_review', 'finance_approve', 'rejected', 'paid', 'completed', 'cancelled')
    ),
    requested_by INTEGER NOT NULL REFERENCES users(id),
    data_reviewed_by INTEGER REFERENCES users(id),
    data_reviewed_at TIMESTAMP,
    data_review_notes TEXT,
    finance_approved_by INTEGER REFERENCES users(id),
    finance_approved_at TIMESTAMP,
    finance_approve_notes TEXT,
    paid_at TIMESTAMP,
    completed_at TIMESTAMP,
    expected_date DATE,  -- 期望到账日期
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    INDEX idx_topup_requests_account (ad_account_id),
    INDEX idx_topup_requests_project (project_id),
    INDEX idx_topup_requests_status (status),
    INDEX idx_topup_requests_requested_by (requested_by),
    INDEX idx_topup_requests_created_at (created_at),
    INDEX idx_topup_requests_urgency (urgency_level)
);

-- 充值记录表（实际资金流水）
CREATE TABLE topup_transactions (
    id SERIAL PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES topup_requests(id),
    transaction_no VARCHAR(100) NOT NULL UNIQUE,  -- 交易号
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    payment_method VARCHAR(50) NOT NULL,
    payment_account VARCHAR(100),  -- 付款账户
    transaction_date TIMESTAMP NOT NULL,
    receipt_file VARCHAR(500),  -- 凭证文件路径
    notes TEXT,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    INDEX idx_topup_transactions_request (request_id),
    INDEX idx_topup_transactions_date (transaction_date)
);

-- 充值审批日志表
CREATE TABLE topup_approval_logs (
    id SERIAL PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES topup_requests(id),
    action VARCHAR(50) NOT NULL,  -- submitted, reviewed, approved, rejected, paid, completed
    actor_id INTEGER NOT NULL REFERENCES users(id),
    actor_role VARCHAR(50) NOT NULL,
    notes TEXT,
    previous_status VARCHAR(20),
    new_status VARCHAR(20),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    INDEX idx_topup_approval_logs_request (request_id),
    INDEX idx_topup_approval_logs_action (action),
    INDEX idx_topup_approval_logs_actor (actor_id)
);
```

### RLS策略

```sql
-- 启用RLS
ALTER TABLE topup_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE topup_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE topup_approval_logs ENABLE ROW LEVEL SECURITY;

-- 策略1：管理员全权限
CREATE POLICY admin_full_access_topups ON topup_requests
    FOR ALL TO admin_role
    USING (true)
    WITH CHECK (true);

-- 策略2：财务全权限
CREATE POLICY finance_full_access_topups ON topup_requests
    FOR ALL TO finance_role
    USING (true)
    WITH CHECK (true);

-- 策略3：数据员只读和审核权限
CREATE POLICY data_operator_review_topups ON topup_requests
    FOR ALL TO data_operator_role
    USING (true)
    WITH CHECK (true);

-- 策略4：账户管理员查看项目内充值
CREATE POLICY account_manager_view_topups ON topup_requests
    FOR SELECT TO account_manager_role
    USING (
        project_id IN (
            SELECT id FROM projects
            WHERE account_manager_id = current_setting('app.current_user_id')::integer
        )
    );

CREATE POLICY account_manager_create_topups ON topup_requests
    FOR INSERT TO account_manager_role
    WITH CHECK (
        project_id IN (
            SELECT id FROM projects
            WHERE account_manager_id = current_setting('app.current_user_id')::integer
        )
    );

-- 策略5：投手查看自己申请的充值
CREATE POLICY media_buyer_own_topups ON topup_requests
    FOR ALL TO media_buyer_role
    USING (requested_by = current_setting('app.current_user_id')::integer)
    WITH CHECK (requested_by = current_setting('app.current_user_id')::integer);

-- 交易记录策略（财务和管理员可查看）
CREATE POLICY finance_access_transactions ON topup_transactions
    FOR ALL TO finance_role, admin_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY account_manager_view_transactions ON topup_transactions
    FOR SELECT TO account_manager_role
    USING (
        request_id IN (
            SELECT id FROM topup_requests
            WHERE project_id IN (
                SELECT id FROM projects
                WHERE account_manager_id = current_setting('app.current_user_id')::integer
            )
        )
    );

-- 审批日志策略（所有角色可查看自己相关的）
CREATE POLICY view_own_approval_logs ON topup_approval_logs
    FOR SELECT TO media_buyer_role, account_manager_role
    USING (
        request_id IN (
            SELECT id FROM topup_requests
            WHERE requested_by = current_setting('app.current_user_id')::integer
        )
    );
```

---

## 🔌 API端点设计

| 方法 | 路径 | 描述 | 权限要求 | 状态码 |
|------|------|------|----------|--------|
| GET | /api/v1/topups | 获取充值申请列表 | 相关角色 | 200 |
| POST | /api/v1/topups | 创建充值申请 | media_buyer, account_manager | 201 |
| GET | /api/v1/topups/{id} | 获取充值申请详情 | 相关角色 | 200 |
| PUT | /api/v1/topups/{id}/review | 数据员审核 | data_operator | 200 |
| PUT | /api/v1/topups/{id}/approve | 财务审批 | finance | 200 |
| PUT | /api/v1/topups/{id}/pay | 标记已打款 | finance | 200 |
| POST | /api/v1/topups/{id}/receipt | 上传打款凭证 | finance | 201 |
| GET | /api/v1/topups/{id}/logs | 获取审批日志 | 相关角色 | 200 |
| GET | /api/v1/topups/statistics | 获取充值统计 | admin, finance, data_operator | 200 |
| GET | /api/v1/topups/export | 导出充值记录 | finance, admin | 200 |

---

## 📝 Schema设计

### 请求Schema

```python
# 创建充值申请请求
class TopupRequestCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ad_account_id: int = Field(..., gt=0, description="广告账户ID")
    requested_amount: Decimal = Field(..., gt=0, le=100000, description="申请金额")
    currency: str = Field("USD", max_length=10, description="货币")
    urgency_level: str = Field("normal", pattern="^(low|normal|high|urgent)$", description="紧急程度")
    reason: str = Field(..., min_length=1, max_length=1000, description="充值原因")
    notes: Optional[str] = Field(None, max_length=1000, description="补充说明")
    expected_date: Optional[date] = Field(None, description="期望到账日期")

# 数据员审核请求
class TopupDataReviewRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action: str = Field(..., pattern="^(approve|reject)$", description="审核动作")
    notes: Optional[str] = Field(None, max_length=1000, description="审核说明")

# 财务审批请求
class TopupFinanceApprovalRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action: str = Field(..., pattern="^(approve|reject)$", description="审批动作")
    actual_amount: Optional[Decimal] = Field(None, gt=0, description="实际打款金额")
    payment_method: Optional[str] = Field(None, max_length=50, description="打款方式")
    notes: Optional[str] = Field(None, max_length=1000, description="审批说明")

# 上传打款凭证请求
class TopupReceiptUploadRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    receipt_url: str = Field(..., max_length=500, description="凭证URL")
    transaction_id: Optional[str] = Field(None, max_length=100, description="交易流水号")
    notes: Optional[str] = Field(None, max_length=1000, description="备注")
```

### 响应Schema

```python
# 充值申请响应
class TopupRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_no: str
    ad_account_id: int
    ad_account_name: str
    project_id: int
    project_name: str
    requested_amount: Decimal
    actual_amount: Optional[Decimal]
    currency: str
    urgency_level: str
    reason: str
    notes: Optional[str]
    status: str
    requested_by: int
    requested_by_name: str
    data_reviewed_by: Optional[int]
    data_reviewed_by_name: Optional[str]
    data_reviewed_at: Optional[datetime]
    finance_approved_by: Optional[int]
    finance_approved_by_name: Optional[str]
    finance_approved_at: Optional[datetime]
    paid_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

# 充值交易响应
class TopupTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    request_no: str
    transaction_no: str
    amount: Decimal
    currency: str
    payment_method: str
    transaction_date: datetime
    receipt_file: Optional[str]
    notes: Optional[str]
    created_by_name: str
    created_at: datetime

# 充值统计响应
class TopupStatisticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_requests: int
    pending_requests: int
    approved_requests: int
    paid_requests: int
    completed_requests: int
    total_amount_requested: Decimal
    total_amount_paid: Decimal
    avg_processing_time: float  # 平均处理时间（小时）
    success_rate: float  # 成功率百分比
    urgent_requests: int
    overdue_requests: int  # 逾期未处理的申请

# 审批日志响应
class TopupApprovalLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    actor_name: str
    actor_role: str
    notes: Optional[str]
    previous_status: Optional[str]
    new_status: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
```

---

## ⚠️ 错误码设计

| 错误码 | HTTP状态码 | 描述 | 触发条件 |
|--------|------------|------|----------|
| SYS_004 | 404 | 充值申请不存在 | ID不存在 |
| BIZ_201 | 400 | 充值金额超出限制 | 金额>10万或<0 |
| BIZ_202 | 400 | 账户余额超出上限 | 充值后>50万 |
| BIZ_203 | 422 | 状态转换无效 | 非法状态转换 |
| BIZ_204 | 403 | 超出申请频次限制 | 24h内>3次 |
| BIZ_205 | 400 | 期望日期过早 | 早于明天 |
| BIZ_206 | 400 | 无权限操作该申请 | 权限不足 |
| BIZ_207 | 409 | 重复打款 | 已标记为paid |

---

## 🎯 阶段一交付检查

- [x] 业务需求分析完成
- [x] API端点清单设计完成（10个端点）
- [x] 数据模型设计完成（3张表）
- [x] RLS策略设计完成
- [x] Schema设计完成（6个请求/响应模型）
- [x] 错误码定义完成
- [x] 权限矩阵确认

---

**下一步**: 进入阶段二 - 代码实现