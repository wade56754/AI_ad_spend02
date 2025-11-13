# 对账管理模块设计文档

> **模块名称**: 对账管理 (Reconciliation Management)
> **设计版本**: v1.0
> **设计日期**: 2025-11-12
> **设计人员**: Claude协作开发

---

## 📋 需求分析

### 业务场景
对账管理是AI广告代投系统的财务核心模块，负责核对广告平台消耗数据与实际充值、支出数据的一致性，确保资金使用透明、准确，及时发现并处理差异。

### 核心功能
1. **自动对账** - 定期自动获取广告平台数据与内部数据比对
2. **差异管理** - 记录、分析、跟踪所有对账差异
3. **对账报告** - 生成详细的对账报告和分析
4. **差异处理** - 差异调整、原因追溯、责任认定
5. **统计分析** - 对账效率、差异率等指标分析
6. **历史追踪** - 完整的对账历史记录和审计轨迹

### 参与角色及权限
| 角色 | 权限范围 | 说明 |
|------|----------|------|
| admin | 全部权限 | 查看所有对账数据，处理差异，生成报告 |
| finance | 核心权限 | 查看所有对账数据，处理差异，调整记录 |
| data_operator | 分析权限 | 查看对账报告，协助分析差异原因 |
| account_manager | 只读权限 | 查看自己项目的对账数据 |
| media_buyer | 只读权限 | 查看自己相关账户的对账数据 |

### 业务规则
1. 对账周期：每日自动对账前日数据
2. 数据来源：广告平台API + 内部充值记录 + 消耗数据
3. 差异阈值：单日差异超过100USD需人工审核
4. 对账状态：pending → processing → completed → exception → resolved
5. 差异类型：金额差异、时间差异、数据缺失
6. 自动化率：目标80%对账自动完成

---

## 🏗️ 数据模型设计

### 表结构

```sql
-- 对账批次表
CREATE TABLE reconciliation_batches (
    id SERIAL PRIMARY KEY,
    batch_no VARCHAR(50) NOT NULL UNIQUE,  -- 对账批次号
    reconciliation_date DATE NOT NULL,  -- 对账日期
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'processing', 'completed', 'exception', 'resolved')
    ),
    total_accounts INTEGER NOT NULL DEFAULT 0,  -- 总账户数
    matched_accounts INTEGER NOT NULL DEFAULT 0,  -- 匹配账户数
    mismatched_accounts INTEGER NOT NULL DEFAULT 0,  -- 差异账户数
    total_platform_spend DECIMAL(15,2) DEFAULT 0.00,  -- 平台总消耗
    total_internal_spend DECIMAL(15,2) DEFAULT 0.00,  -- 内部总消耗
    total_difference DECIMAL(15,2) DEFAULT 0.00,  -- 总差异金额
    auto_matched INTEGER DEFAULT 0,  -- 自动匹配数
    manual_reviewed INTEGER DEFAULT 0,  -- 人工审核数
    started_at TIMESTAMP,  -- 开始时间
    completed_at TIMESTAMP,  -- 完成时间
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    INDEX idx_reconciliation_batches_date (reconciliation_date),
    INDEX idx_reconciliation_batches_status (status),
    INDEX idx_reconciliation_batches_created_at (created_at)
);

-- 对账详情表
CREATE TABLE reconciliation_details (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES reconciliation_batches(id) ON DELETE CASCADE,
    ad_account_id INTEGER NOT NULL REFERENCES ad_accounts(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),
    channel_id INTEGER NOT NULL REFERENCES channels(id),

    -- 平台数据
    platform_spend DECIMAL(15,2) DEFAULT 0.00,  -- 平台消耗
    platform_currency VARCHAR(10) DEFAULT 'USD',
    platform_data_date DATE,  -- 平台数据日期

    -- 内部数据
    internal_spend DECIMAL(15,2) DEFAULT 0.00,  -- 内部消耗
    internal_currency VARCHAR(10) DEFAULT 'USD',
    internal_data_date DATE,  -- 内部数据日期

    -- 差异信息
    spend_difference DECIMAL(15,2) DEFAULT 0.00,  -- 消耗差异
    exchange_rate DECIMAL(10,4) DEFAULT 1.0000,  -- 汇率
    is_matched BOOLEAN DEFAULT false,  -- 是否匹配
    match_status VARCHAR(20) DEFAULT 'pending' CHECK (
        match_status IN ('pending', 'matched', 'auto_matched', 'manual_review', 'exception', 'resolved')
    ),

    -- 差异原因
    difference_type VARCHAR(50),  -- amount_mismatch, date_mismatch, missing_data
    difference_reason TEXT,  -- 差异原因描述
    auto_confidence DECIMAL(3,2) DEFAULT 0.00,  -- 自动匹配置信度

    -- 处理信息
    reviewed_by INTEGER REFERENCES users(id),  -- 审核人
    reviewed_at TIMESTAMP,  -- 审核时间
    review_notes TEXT,  -- 审核说明
    resolved_by INTEGER REFERENCES users(id),  -- 处理人
    resolved_at TIMESTAMP,  -- 处理时间
    resolution_method VARCHAR(50),  -- adjust, waive, investigate
    resolution_notes TEXT,  -- 处理说明

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    INDEX idx_reconciliation_details_batch (batch_id),
    INDEX idx_reconciliation_details_account (ad_account_id),
    INDEX idx_reconciliation_details_status (match_status),
    INDEX idx_reconciliation_details_date (platform_data_date)
);

-- 对账调整记录表
CREATE TABLE reconciliation_adjustments (
    id SERIAL PRIMARY KEY,
    detail_id INTEGER NOT NULL REFERENCES reconciliation_details(id) ON DELETE CASCADE,
    batch_id INTEGER NOT NULL REFERENCES reconciliation_batches(id) ON DELETE CASCADE,

    -- 调整信息
    adjustment_type VARCHAR(50) NOT NULL,  -- spend_adjustment, date_adjustment
    original_amount DECIMAL(15,2) NOT NULL,  -- 原始金额
    adjustment_amount DECIMAL(15,2) NOT NULL,  -- 调整金额
    adjusted_amount DECIMAL(15,2) NOT NULL,  -- 调整后金额

    -- 调整原因
    adjustment_reason VARCHAR(100) NOT NULL,  -- data_error, currency_fluctuation, other
    detailed_reason TEXT NOT NULL,  -- 详细原因说明
    evidence_url VARCHAR(500),  -- 证据文件URL

    -- 审批信息
    approved_by INTEGER NOT NULL REFERENCES users(id),  -- 审批人
    approved_at TIMESTAMP NOT NULL,  -- 审批时间
    finance_approve BOOLEAN DEFAULT false,  -- 财务确认
    finance_approved_by INTEGER REFERENCES users(id),  -- 财务审批人
    finance_approved_at TIMESTAMP,  -- 财务审批时间

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    INDEX idx_reconciliation_adjustments_detail (detail_id),
    INDEX idx_reconciliation_adjustments_batch (batch_id),
    INDEX idx_reconciliation_adjustments_type (adjustment_type)
);

-- 对账报告表
CREATE TABLE reconciliation_reports (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER REFERENCES reconciliation_batches(id),
    report_type VARCHAR(50) NOT NULL,  -- daily, weekly, monthly
    report_period_start DATE NOT NULL,
    report_period_end DATE NOT NULL,

    -- 报告内容
    report_data JSONB NOT NULL,  -- 报告数据
    chart_data JSONB,  -- 图表数据
    summary_data JSONB NOT NULL,  -- 摘要数据

    -- 生成信息
    generated_by INTEGER NOT NULL REFERENCES users(id),
    generated_at TIMESTAMP NOT NULL,
    file_path VARCHAR(500),  -- 报告文件路径

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    INDEX idx_reconciliation_reports_batch (batch_id),
    INDEX idx_reconciliation_reports_type (report_type),
    INDEX idx_reconciliation_reports_period (report_period_start)
);
```

### RLS策略

```sql
-- 启用RLS
ALTER TABLE reconciliation_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE reconciliation_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE reconciliation_adjustments ENABLE ROW LEVEL SECURITY;
ALTER TABLE reconciliation_reports ENABLE ROW LEVEL SECURITY;

-- 策略1：管理员和财务全权限
CREATE POLICY finance_full_access_reconciliation ON reconciliation_batches
    FOR ALL TO admin_role, finance_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY finance_full_access_reconciliation_details ON reconciliation_details
    FOR ALL TO admin_role, finance_role
    USING (true)
    WITH CHECK (true);

-- 策略2：数据员只读权限
CREATE POLICY data_operator_read_reconciliation ON reconciliation_batches
    FOR SELECT TO data_operator_role
    USING (true);

CREATE POLICY data_operator_read_reconciliation_details ON reconciliation_details
    FOR SELECT TO data_operator_role
    USING (true);

-- 策略3：账户管理员查看项目内数据
CREATE POLICY account_manager_view_reconciliation ON reconciliation_batches
    FOR SELECT TO account_manager_role
    USING (
        EXISTS (
            SELECT 1 FROM reconciliation_details rd
            JOIN ad_accounts aa ON rd.ad_account_id = aa.id
            WHERE rd.batch_id = reconciliation_batches.id
            AND aa.project_id IN (
                SELECT id FROM projects
                WHERE account_manager_id = current_setting('app.current_user_id')::integer
            )
        )
    );

-- 策略4：投手查看自己相关账户数据
CREATE POLICY media_buyer_view_reconciliation ON reconciliation_batches
    FOR SELECT TO media_buyer_role
    USING (
        EXISTS (
            SELECT 1 FROM reconciliation_details rd
            JOIN ad_accounts aa ON rd.ad_account_id = aa.id
            WHERE rd.batch_id = reconciliation_batches.id
            AND aa.assigned_user_id = current_setting('app.current_user_id')::integer
        )
    );
```

---

## 🔌 API端点设计

| 方法 | 路径 | 描述 | 权限要求 | 状态码 |
|------|------|------|----------|--------|
| GET | /api/v1/reconciliations | 获取对账列表 | 相关角色 | 200 |
| POST | /api/v1/reconciliations/batches | 创建对账批次 | admin, finance | 201 |
| GET | /api/v1/reconciliations/batches/{id} | 获取对账详情 | 相关角色 | 200 |
| POST | /api/v1/reconciliations/batches/{id}/run | 执行对账 | admin, finance | 200 |
| PUT | /api/v1/reconciliations/details/{id}/review | 审核对账差异 | admin, finance | 200 |
| POST | /api/v1/reconciliations/details/{id}/adjust | 创建调整记录 | admin, finance | 201 |
| GET | /api/v1/reconciliations/statistics | 获取对账统计 | admin, finance, data_operator | 200 |
| GET | /api/v1/reconciliations/reports | 获取对账报告 | 相关角色 | 200 |
| POST | /api/v1/reconciliations/reports | 生成对账报告 | admin, finance | 201 |
| GET | /api/v1/reconciliations/export | 导出对账数据 | admin, finance | 200 |

---

## 📝 Schema设计

### 请求Schema

```python
# 创建对账批次请求
class ReconciliationBatchCreateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reconciliation_date: date = Field(..., description="对账日期")
    channel_ids: Optional[List[int]] = Field(None, description="渠道ID列表，为空则对所有渠道")
    auto_match: bool = Field(True, description="是否自动匹配")
    threshold: Optional[Decimal] = Field(None, description="差异阈值")

# 审核对账差异请求
class ReconciliationDetailReviewRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action: str = Field(..., pattern="^(approve|reject|investigate)$")
    is_matched: bool = Field(..., description="是否确认匹配")
    match_status: Optional[str] = Field(None, pattern="^(matched|exception|resolved)$")
    review_notes: Optional[str] = Field(None, max_length=1000)
    auto_confidence: Optional[Decimal] = Field(None, ge=0, le=1, decimal_places=2)

# 创建调整记录请求
class ReconciliationAdjustmentCreateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    adjustment_type: str = Field(..., pattern="^(spend_adjustment|date_adjustment)$")
    original_amount: Decimal = Field(..., decimal_places=2)
    adjustment_amount: Decimal = Field(..., decimal_places=2)
    adjustment_reason: str = Field(..., max_length=100)
    detailed_reason: str = Field(..., max_length=1000)
    evidence_url: Optional[str] = Field(None, max_length=500)
```

### 响应Schema

```python
# 对账批次响应
class ReconciliationBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_no: str
    reconciliation_date: date
    status: str
    total_accounts: int
    matched_accounts: int
    mismatched_accounts: int
    total_platform_spend: Decimal
    total_internal_spend: Decimal
    total_difference: Decimal
    auto_matched: int
    manual_reviewed: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by_name: str
    created_at: datetime
    updated_at: datetime

# 对账详情响应
class ReconciliationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    ad_account_id: int
    ad_account_name: str
    project_id: int
    project_name: str
    channel_id: int
    channel_name: str

    # 平台数据
    platform_spend: Decimal
    platform_currency: str
    platform_data_date: Optional[date]

    # 内部数据
    internal_spend: Decimal
    internal_currency: str
    internal_data_date: Optional[date]

    # 差异信息
    spend_difference: Decimal
    exchange_rate: Decimal
    is_matched: bool
    match_status: str
    difference_type: Optional[str]
    difference_reason: Optional[str]
    auto_confidence: Decimal

    # 审核信息
    reviewed_by_name: Optional[str]
    reviewed_at: Optional[datetime]
    review_notes: Optional[str]
    resolved_by_name: Optional[str]
    resolved_at: Optional[datetime]
    resolution_method: Optional[str]

    created_at: datetime
    updated_at: datetime

# 对账统计响应
class ReconciliationStatisticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # 总体统计
    total_batches: int
    completed_batches: int
    exception_batches: int
    total_accounts: int
    matched_accounts: int
    mismatched_accounts: int

    # 金额统计
    total_platform_spend: Decimal
    total_internal_spend: Decimal
    total_difference: Decimal
    total_adjustments: Decimal

    # 效率统计
    auto_match_rate: float
    manual_review_rate: float
    avg_processing_time_hours: float
    difference_rate: float

    # 趋势数据
    monthly_trends: List[dict]
    top_difference_reasons: List[dict]
    channel_performance: List[dict]

# 对账报告响应
class ReconciliationReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    report_type: str
    report_period_start: date
    report_period_end: date
    summary_data: dict
    file_path: Optional[str]
    generated_by_name: str
    generated_at: datetime
```

---

## ⚠️ 错误码设计

| 错误码 | HTTP状态码 | 描述 | 触发条件 |
|--------|------------|------|----------|
| SYS_004 | 404 | 对账记录不存在 | ID不存在 |
| BIZ_301 | 400 | 对账日期无效 | 日期在未来或过早 |
| BIZ_302 | 400 | 重复对账 | 相同日期已对账 |
| BIZ_303 | 403 | 无权限操作对账 | 权限不足 |
| BIZ_304 | 400 | 差异超阈值 | 超过设定阈值 |
| BIZ_305 | 400 | 调整金额无效 | 调整金额不合理 |
| BIZ_306 | 422 | 状态转换无效 | 非法状态转换 |

---

## 🎯 阶段一交付检查

- [x] 业务需求分析完成
- [x] API端点清单设计完成（10个端点）
- [x] 数据模型设计完成（4张表）
- [x] RLS策略设计完成
- [x] Schema设计完成（8个请求/响应模型）
- [x] 错误码定义完成
- [x] 权限矩阵确认

---

**下一步**: 进入阶段二 - 代码实现