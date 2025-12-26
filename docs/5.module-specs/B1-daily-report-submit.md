# B1 日报提交 - 后端模块规格书

> **版本**: v1.0
> **更新日期**: 2025-12-23
> **SoT 基准**: DATA_SCHEMA.md v5.3, STATE_MACHINE.md v2.7, API_SOT.md v9.3
> **参考指南**: docs/3.dev-guides/BACKEND_MODULE_SPEC_GUIDE.md

---

## §1 模块概述

### 1.1 业务目标

本模块实现投手日报的创建、编辑、提交功能。投手每日提交各账户的广告投放数据（消耗、进粉数、成效数、地区），系统记录原始数据并触发后续趋势风控检查流程。

### 1.2 涉及角色

| 角色 | 系统角色名 | 本模块权限 |
|------|------------|------------|
| 老板 | ceo | 查看所有日报（只读） |
| 项目负责人 | project_owner | 查看项目内日报（只读） |
| 主管 | supervisor | 查看下属日报、触发审核、批量导入 |
| 投手 | pitcher | 创建、编辑、删除、提交自己的日报 |
| 户管 | account_manager | 查看管理账户的日报 |
| 管理员 | admin | 所有操作 |

### 1.3 模块边界

**本模块负责：**
- 日报的 CRUD 操作
- 日报状态从 draft → raw_submitted → trend_pending
- 数据验证和异常警告（Phase 1: 只警告不阻断）
- 批量导入 Excel 日报

**本模块不负责：**
- 趋势风控检查（由 TrendRiskControlService 负责）
- 最终粉数确认（由 B2 日报审核模块负责）
- 计费锁定（由系统定时任务负责）

### 1.4 SoT 引用清单 (AI 防幻觉)

| SoT 文档 | 版本 | 引用章节 | 用途 |
|---------|------|---------|------|
| DATA_SCHEMA.md | v5.3 | §6.1 daily_reports | 表结构、字段定义 |
| STATE_MACHINE.md | v2.7 | §8 日报 8 状态机 | 状态流转规则 |
| BUSINESS_RULES.md | v4.1 | BR-RPT-001~008 | 日报业务规则 |
| ERROR_CODES_SOT.md | v2.1 | BIZ_* | 业务错误码 |
| API_SOT.md | v9.3 | §9.2 Daily Reports | API 端点规范 |
| AUTH_SPEC.md | v2.0 | §3 权限矩阵 | 角色权限 |
| MASTER.md | v4.4 | §2.4 七角色 | Phase 边界 |

---

## §2 数据模型

### 2.1 表结构定义

**来源**: DATA_SCHEMA.md v5.3 §6.1, `backend/models/workflow/daily_report.py`

```sql
CREATE TABLE daily_reports (
  -- 主键
  id              BIGSERIAL PRIMARY KEY,

  -- 报告日期
  report_date     DATE NOT NULL,

  -- 外键
  ad_account_id   BIGINT NOT NULL REFERENCES ad_accounts(id) ON DELETE RESTRICT,

  -- v2.0 新增字段 (投手提交)
  region          VARCHAR(50),           -- 投放地区 (Turkey/India/Brazil 等)
  platform        VARCHAR(20),           -- 广告平台 (FB/Google/TikTok)
  follows_count   INTEGER NOT NULL DEFAULT 0,   -- 进粉数
  result_count    INTEGER NOT NULL DEFAULT 0,   -- 成效数
  currency        VARCHAR(10) NOT NULL DEFAULT 'USD',  -- 货币类型

  -- 基础指标
  impressions     INTEGER NOT NULL DEFAULT 0,   -- 展示次数
  clicks          INTEGER NOT NULL DEFAULT 0,   -- 点击次数
  conversions     INTEGER NOT NULL DEFAULT 0,   -- 转化数

  -- 三数据流字段 (STATE_MACHINE.md v2.7 §8)
  conversions_raw INTEGER NOT NULL DEFAULT 0,   -- raw 数据流 - 原始粉数
  conversions_final INTEGER NOT NULL DEFAULT 0, -- final 数据流 - 最终粉数
  raw_spend       DECIMAL(15,2) NOT NULL DEFAULT 0.00, -- 原始消耗
  real_spend      DECIMAL(15,2) NOT NULL DEFAULT 0.00, -- 真实消耗
  unit_price      DECIMAL(15,2) NOT NULL DEFAULT 0.00, -- 单粉价格

  -- 8 状态机 (STATE_MACHINE.md v2.7 §8)
  status          VARCHAR(20) NOT NULL DEFAULT 'raw_submitted',

  -- 趋势风控字段
  trend_flag      VARCHAR(20) NOT NULL DEFAULT 'normal',
  trend_flag_reason TEXT,
  trend_resolution_note TEXT,

  -- 锁定时间
  final_locked_at TIMESTAMPTZ,

  -- 广告信息
  campaign_name   VARCHAR(200),
  ad_group_name   VARCHAR(200),
  ad_creative_name VARCHAR(200),
  notes           TEXT,
  attachments     JSONB,

  -- 用户关联
  submitted_by    UUID REFERENCES users(id) ON DELETE SET NULL,
  audit_user_id   UUID REFERENCES users(id) ON DELETE SET NULL,
  created_by      UUID REFERENCES users(id) ON DELETE SET NULL,
  updated_by      UUID REFERENCES users(id) ON DELETE SET NULL,

  -- 时间戳
  submitted_at    TIMESTAMPTZ,
  approved_at     TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- 约束
  CONSTRAINT chk_daily_reports_status CHECK (
    status IN ('raw_submitted', 'trend_pending', 'trend_ok', 'trend_flagged',
               'trend_resolved', 'final_pending', 'final_confirmed', 'final_locked')
  ),
  CONSTRAINT chk_daily_reports_trend_flag CHECK (
    trend_flag IN ('normal', 'flagged', 'resolved')
  ),
  CONSTRAINT uq_daily_reports_date_account UNIQUE (report_date, ad_account_id)
);

-- 索引
CREATE INDEX idx_daily_reports_date ON daily_reports(report_date);
CREATE INDEX idx_daily_reports_account ON daily_reports(ad_account_id);
CREATE INDEX idx_daily_reports_status ON daily_reports(status);
CREATE INDEX idx_daily_reports_created_by ON daily_reports(created_by);
CREATE INDEX idx_daily_reports_date_status ON daily_reports(report_date, status);
```

### 2.2 字段说明

| 字段 | 类型 | 必填 | 说明 | 验证规则 |
|------|------|------|------|----------|
| id | BIGSERIAL | 自动 | 主键 | 系统生成 |
| report_date | DATE | ✅ | 报告日期 | 不能是未来日期 (BIZ_201) |
| ad_account_id | BIGINT | ✅ | 广告账户ID | 必须存在且激活 (BIZ_002) |
| follows_count | INTEGER | ✅ | 进粉数 | ≥ 0 |
| result_count | INTEGER | ✅ | 成效数 | ≥ 0 |
| raw_spend | DECIMAL(15,2) | ✅ | 广告消耗 | ≥ 0, 使用 Decimal |
| region | VARCHAR(50) | ✅ | 投放地区 | 见 REGION_CHOICES |
| status | VARCHAR(20) | 自动 | 状态 | 8 状态机枚举 |

### 2.3 索引设计

| 索引名 | 字段 | 类型 | 用途 |
|--------|------|------|------|
| idx_daily_reports_date | report_date | B-tree | 按日期查询 |
| idx_daily_reports_account | ad_account_id | B-tree | 按账户查询 |
| idx_daily_reports_status | status | B-tree | 按状态筛选 |
| idx_daily_reports_date_status | (report_date, status) | B-tree | 复合查询 |

### 2.4 关联关系

```
daily_reports
    ├──→ ad_accounts (ad_account_id → id) 多对一
    │       └── 一个日报属于一个广告账户
    │
    ├──→ users (submitted_by → id) 多对一
    │       └── 提交人（投手）
    │
    └──→ users (audit_user_id → id) 多对一
            └── 审核人（运营）
```

---

## §3 API 设计

### 3.1 端点清单

**来源**: API_SOT.md v9.3 §9.2, `backend/routers/daily_reports.py`

| 方法 | 端点 | 描述 | 权限 |
|------|------|------|------|
| GET | /api/v1/daily-reports | 列表查询 | 登录用户 |
| GET | /api/v1/daily-reports/:id | 详情查询 | 数据所有者/上级 |
| POST | /api/v1/daily-reports | 创建日报 | pitcher, admin |
| PUT | /api/v1/daily-reports/:id | 更新日报 | pitcher, admin |
| DELETE | /api/v1/daily-reports/:id | 删除日报 | admin |
| POST | /api/v1/daily-reports/:id/trigger-trend-check | 触发风控 | pitcher, supervisor, admin |
| POST | /api/v1/daily-reports/batch-import | 批量导入 | supervisor, admin |
| POST | /api/v1/daily-reports/import-file | Excel导入 | supervisor, admin |
| GET | /api/v1/daily-reports/export | 导出Excel | finance, supervisor, admin |
| GET | /api/v1/daily-reports/stats | 状态统计 | 登录用户 |

### 3.2 请求/响应格式

**创建日报请求** (POST /api/v1/daily-reports):
```typescript
interface DailyReportCreateRequest {
  // 必填字段
  report_date: string;        // YYYY-MM-DD, 不能是未来日期
  ad_account_id: number;      // 广告账户ID
  raw_spend: number;          // 广告消耗 (Decimal)
  follows_count: number;      // 进粉数 ≥ 0
  result_count: number;       // 成效数 ≥ 0
  region: string;             // 投放地区

  // 可选字段
  platform?: string;          // 广告平台 (FB/Google/TikTok)
  currency?: string;          // 货币类型，默认 USD
  campaign_name?: string;     // 广告系列名称
  ad_group_name?: string;     // 广告组名称
  impressions?: number;       // 展示次数，默认 0
  clicks?: number;            // 点击次数，默认 0
  notes?: string;             // 备注
}
```

**成功响应** (201 Created):
```typescript
interface SuccessResponse<DailyReportResponse> {
  data: {
    id: number;
    report_date: string;
    ad_account_id: number;
    status: 'raw_submitted';   // 创建后默认状态
    raw_spend: number;
    follows_count: number;
    result_count: number;
    region: string;
    cost_per_follow: number;   // 计算字段
    cost_per_result: number;   // 计算字段
    created_at: string;        // ISO 8601
    // ... 其他字段
  };
  message: string;
}
```

### 3.3 错误码定义

**来源**: ERROR_CODES_SOT.md v2.1

| 错误码 | HTTP 状态 | 场景 |
|--------|-----------|------|
| VALIDATION_001 | 400 | 必填字段缺失 |
| VALIDATION_002 | 400 | 字段格式无效 |
| AUTH_401 | 401 | 未登录 |
| AUTH_500 | 403 | 无权限 |
| BIZ_002 | 404 | 广告账户不存在 |
| BIZ_003 | 409 | 日报已存在（重复） |
| BIZ_201 | 400 | 报表日期为未来日期 |
| STATE_400 | 400 | 当前状态不允许该操作 |

### 3.4 分页/筛选规范

```typescript
interface DailyReportQueryParams {
  // 分页
  page?: number;              // 页码，默认 1
  page_size?: number;         // 每页数量，默认 20，最大 100

  // 筛选
  report_date_start?: string; // 开始日期 (YYYY-MM-DD)
  report_date_end?: string;   // 结束日期
  ad_account_id?: number;     // 广告账户ID
  status?: string;            // 状态，8 状态机枚举
  project_id?: number;        // 项目ID
  region?: string;            // 投放地区
  platform?: string;          // 广告平台
  team_id?: string;           // 团队ID (UUID)
  submitter_name?: string;    // 投手名称（模糊匹配）

  // 排序
  sort_by?: string;           // 排序字段
  sort_order?: 'asc' | 'desc';
}
```

---

## §4 权限控制

### 4.1 角色权限矩阵 (7 角色)

**来源**: AUTH_SPEC.md v2.0, MASTER.md v4.4 §2.4

| 操作 | ceo | project_owner | finance | supervisor | pitcher | account_manager | admin |
|------|-----|---------------|---------|------------|---------|-----------------|-------|
| 查看所有 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 查看项目内 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 查看下属 | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |
| 查看自己 | N/A | N/A | ❌ | ✅ | ✅ | ❌ | ✅ |
| 创建 | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| 编辑(raw_submitted) | ❌ | ❌ | ❌ | ❌ | ✅(自己) | ❌ | ✅ |
| 删除 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 触发风控 | ❌ | ❌ | ❌ | ✅ | ✅(自己) | ❌ | ✅ |
| 批量导入 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 导出 | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ |

**说明**:
- ✅ = 允许操作
- ❌ = 禁止操作
- supervisor 承担原 data_operator 的审核和导入权限

### 4.2 数据权限规则

```python
# backend/models/workflow/daily_report.py

def can_be_edited_by(self, user_id: UUID, user_role: UserRole) -> bool:
    """检查用户是否可以编辑此日报"""
    # 管理员和主管可以编辑所有未锁定的日报
    if user_role in [UserRole.ADMIN, UserRole.SUPERVISOR]:
        return not self.is_final_locked

    # 投手只能编辑自己的原始提交状态日报
    if user_role == UserRole.PITCHER:
        if self.submitted_by != user_id:
            return False
        return self.status == DailyReportStatus.RAW_SUBMITTED.value

    return False
```

### 4.3 字段级权限

| 字段 | 创建时 | 所有者编辑 | 运营编辑 |
|------|--------|------------|----------|
| report_date | ✅ 必填 | ❌ 不可改 | ❌ |
| ad_account_id | ✅ 必填 | ❌ 不可改 | ❌ |
| raw_spend | ✅ 必填 | ✅ 可改(raw_submitted) | ✅ |
| follows_count | ✅ 必填 | ✅ 可改(raw_submitted) | ✅ |
| status | ❌ 系统控制 | ❌ | ❌ |
| real_spend | ❌ | ❌ | ✅ (trend_ok 后) |
| conversions_final | ❌ | ❌ | ✅ (final_pending) |

---

## §5 业务逻辑

### 5.1 状态机定义

**来源**: STATE_MACHINE.md v2.7 §8 日报 8 状态机

```
┌──────────────┐     auto       ┌──────────────┐
│raw_submitted │ ─────────────→ │trend_pending │
└──────────────┘                └──────────────┘
                                       │
                          ┌────────────┴────────────┐
                          │ TF-* 通过               │ TF-* 触发
                          ↓                         ↓
                   ┌───────────┐            ┌──────────────┐
                   │ trend_ok  │            │trend_flagged │
                   └───────────┘            └──────────────┘
                          │                         │
                          │                         │ 运营确认
                          │                         ↓
                          │                 ┌──────────────┐
                          │                 │trend_resolved│
                          │                 └──────────────┘
                          │                         │
                          └────────────┬────────────┘
                                       ↓
                               ┌──────────────┐
                               │final_pending │
                               └──────────────┘
                                       │
                                       │ 运营确认 final
                                       ↓
                              ┌────────────────┐
                              │final_confirmed │
                              └────────────────┘
                                       │
                                       │ 月底锁定
                                       ↓
                               ┌──────────────┐
                               │ final_locked │ (终态)
                               └──────────────┘
```

**状态转换表**:

| 当前状态 | 目标状态 | 触发条件 | 操作者 |
|----------|----------|----------|--------|
| raw_submitted | trend_pending | 系统自动/手动触发 | system/pitcher |
| trend_pending | trend_ok | TF-* 规则全部通过 | system |
| trend_pending | trend_flagged | TF-* 规则触发 | system |
| trend_flagged | trend_resolved | 主管确认 | supervisor |
| trend_flagged | raw_submitted | 主管退回 | supervisor |
| trend_ok | final_pending | 录入 real_spend | supervisor |
| trend_resolved | final_pending | 录入 real_spend | supervisor |
| final_pending | final_confirmed | 主管确认 final | supervisor |
| final_confirmed | final_locked | 月底自动锁定 | system |

### 5.2 验证规则 (Zod/Pydantic)

**来源**: `backend/schemas/daily_report.py`

```python
class DailyReportCreateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # 必填字段
    report_date: date = Field(..., description="报表日期（≤今天）")
    ad_account_id: int = Field(..., gt=0, description="广告账户ID")
    raw_spend: Decimal = Field(..., ge=0, description="广告消耗（USD）DECIMAL(15,2)")
    follows_count: int = Field(..., ge=0, description="进粉数")
    result_count: int = Field(..., ge=0, description="成效数")
    region: str = Field(..., max_length=50, description="投放地区")

    # 可选字段
    platform: Optional[str] = Field(None, max_length=20)
    currency: str = Field("USD", max_length=10)
    impressions: int = Field(0, ge=0)
    clicks: int = Field(0, ge=0)
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator('clicks')
    def validate_clicks_vs_impressions(cls, v, info):
        """验证点击次数不能大于展示次数"""
        if 'impressions' in info.data and info.data['impressions'] is not None:
            if v > info.data['impressions']:
                raise ValueError('点击次数不能大于展示次数')
        return v
```

### 5.3 计算逻辑

```python
# backend/models/workflow/daily_report.py

@property
def cost_per_follow(self) -> Decimal:
    """单粉成本 = 广告消耗 / 进粉数"""
    if self.follows_count and self.follows_count > 0:
        return Decimal(str(self.raw_spend)) / Decimal(self.follows_count)
    return Decimal('0.00')

@property
def cost_per_result(self) -> Decimal:
    """单次成效费用 = 广告消耗 / 成效数"""
    if self.result_count and self.result_count > 0:
        return Decimal(str(self.raw_spend)) / Decimal(self.result_count)
    return Decimal('0.00')

@computed_field
@property
def ctr(self) -> Decimal:
    """点击率 = 点击数 / 展示数 * 100%"""
    if self.impressions == 0:
        return Decimal('0')
    return Decimal(self.clicks) / Decimal(self.impressions) * 100
```

### 5.4 业务约束 + Phase 1 规则

```yaml
约束规则:
  日期约束:
    - 不能提交未来日期 (BIZ_201)
    - 已锁定月份不能修改 (final_locked 终态保护)

  唯一性约束:
    - 同一账户同一日期只能有一条日报 (BIZ_003)
    - UNIQUE (report_date, ad_account_id)

  状态约束:
    - 只有 raw_submitted 状态可以编辑
    - 状态只能按状态机定义的路径转换
    - 终态 (final_locked) 不可回退

  数据约束:
    - follows_count >= 0
    - result_count >= 0
    - raw_spend >= 0 (必须使用 Decimal)
    - clicks <= impressions

Phase 1 规则 (照亮阶段):
  ❌ 禁止: 自动阻断、自动拒绝、自动暂停
  ✅ 允许: 记录异常、警告提示、高亮显示

  异常处理:
    - 高 CPL: 警告但不阻断提交 (TF-001/002/003)
    - 零进粉: 警告但不阻断提交
    - 数据异常: 标记 trend_flagged，人工复核
```

---

## §6 前后端接口契约

### 6.1 字段映射

| 后端字段 (snake_case) | 前端字段 (camelCase) | 说明 |
|----------------------|---------------------|------|
| report_date | reportDate | YYYY-MM-DD 字符串 |
| ad_account_id | adAccountId | 整数 |
| raw_spend | rawSpend | Decimal 字符串 |
| follows_count | followsCount | 整数 |
| result_count | resultCount | 整数 |
| cost_per_follow | costPerFollow | 计算字段 |
| cost_per_result | costPerResult | 计算字段 |
| created_at | createdAt | ISO 8601 字符串 |

### 6.2 枚举值对照

```typescript
// 8 状态机 (STATE_MACHINE.md v2.7 §8)
type DailyReportStatus =
  | 'raw_submitted'    // 已提交
  | 'trend_pending'    // 待趋势审核
  | 'trend_ok'         // 趋势通过
  | 'trend_flagged'    // 趋势异常
  | 'trend_resolved'   // 异常已解决
  | 'final_pending'    // 待最终确认
  | 'final_confirmed'  // 已确认
  | 'final_locked';    // 已锁定 (终态)

// 状态中文映射
const STATUS_LABELS: Record<DailyReportStatus, string> = {
  raw_submitted: '已提交',
  trend_pending: '待审核',
  trend_ok: '审核通过',
  trend_flagged: '趋势异常',
  trend_resolved: '异常已处理',
  final_pending: '待确认',
  final_confirmed: '已确认',
  final_locked: '已锁定',
};

// 趋势标记
type TrendFlag = 'normal' | 'flagged' | 'resolved';

// 平台枚举
type Platform = 'FB' | 'Google' | 'TikTok' | 'Other';
```

### 6.3 时区/格式约定

```yaml
时间格式:
  日期: YYYY-MM-DD (不含时区)
  时间戳: ISO 8601 (含时区，如 2024-12-23T10:00:00Z)

时区处理:
  存储: UTC (TIMESTAMPTZ)
  传输: UTC
  显示: 前端转换为本地时区

数字格式:
  金额: Decimal 类型，保留2位小数
  百分比: 数字类型，如 12.34 表示 12.34%

空值:
  null: 表示无值/未知
  0: 表示实际值为零

分页:
  页码: 从 1 开始
  默认每页: 20 条
  最大每页: 100 条
```

---

## §7 测试要点

### 7.1 单元测试

```python
# backend/tests/test_daily_report_service.py

class TestCreateDailyReport:
    """创建日报测试"""

    def test_create_success(self, db, pitcher_user):
        """投手可以创建日报"""
        request = DailyReportCreateRequest(
            report_date=date.today(),
            ad_account_id=1,
            raw_spend=Decimal("5000.00"),
            follows_count=100,
            result_count=50,
            region="Turkey"
        )
        report = service.create_daily_report(request, pitcher_user)
        assert report.status == "raw_submitted"
        assert report.cost_per_follow == Decimal("50.00")

    def test_reject_future_date(self, db, pitcher_user):
        """拒绝未来日期 (BIZ_201)"""
        request = DailyReportCreateRequest(
            report_date=date.today() + timedelta(days=1),
            ...
        )
        with pytest.raises(BusinessLogicError) as exc:
            service.create_daily_report(request, pitcher_user)
        assert "BIZ_201" in str(exc.value)

    def test_reject_duplicate(self, db, pitcher_user):
        """拒绝重复日报 (BIZ_003)"""
        # 先创建一条
        service.create_daily_report(request, pitcher_user)
        # 再创建相同的
        with pytest.raises(ResourceConflictError):
            service.create_daily_report(request, pitcher_user)


class TestStateMachine:
    """状态机测试"""

    def test_raw_submitted_to_trend_pending(self, report):
        """raw_submitted → trend_pending 允许"""
        report.trigger_trend_check()
        assert report.status == "trend_pending"

    def test_final_locked_is_terminal(self, locked_report):
        """final_locked 是终态"""
        with pytest.raises(ValueError):
            locked_report.can_transition_to(DailyReportStatus.FINAL_CONFIRMED)
```

### 7.2 集成测试

```python
# backend/tests/test_daily_report_api.py

class TestDailyReportAPI:
    """API 集成测试"""

    async def test_pitcher_can_create(self, client, pitcher_token):
        """投手可以创建日报"""
        response = await client.post(
            "/api/v1/daily-reports",
            headers={"Authorization": f"Bearer {pitcher_token}"},
            json={
                "report_date": "2024-12-23",
                "ad_account_id": 1,
                "raw_spend": 5000,
                "follows_count": 100,
                "result_count": 50,
                "region": "Turkey"
            }
        )
        assert response.status_code == 201
        assert response.json()["data"]["status"] == "raw_submitted"

    async def test_finance_cannot_create(self, client, finance_token):
        """财务不能创建日报"""
        response = await client.post(
            "/api/v1/daily-reports",
            headers={"Authorization": f"Bearer {finance_token}"},
            json={...}
        )
        assert response.status_code == 403
```

### 7.3 权限测试矩阵

```python
@pytest.mark.parametrize("role,action,expected", [
    # [角色, 操作, 预期状态码]
    ("ceo", "list_all", 200),
    ("ceo", "create", 403),
    ("pitcher", "list_own", 200),
    ("pitcher", "create", 201),
    ("pitcher", "edit_own_raw_submitted", 200),
    ("pitcher", "edit_own_trend_pending", 403),
    ("finance", "create", 403),
    ("finance", "export", 200),
    ("supervisor", "batch_import", 200),
    ("admin", "delete", 204),
])
async def test_role_permissions(client, role, action, expected):
    """角色权限矩阵测试"""
    response = await execute_action(client, role, action)
    assert response.status_code == expected
```

---

## §8 性能要求

### 8.1 响应时间要求

| API | 目标 | 最大容忍 |
|-----|------|----------|
| 列表查询 | < 200ms | < 500ms |
| 详情查询 | < 100ms | < 300ms |
| 创建日报 | < 300ms | < 1s |
| 批量导入 (100条) | < 5s | < 10s |
| 导出 (5000条) | < 10s | < 30s |

### 8.2 索引要求

必须为以下查询场景建立索引：
- 按日期范围查询: `idx_daily_reports_date`
- 按状态筛选: `idx_daily_reports_status`
- 按账户查询: `idx_daily_reports_account`
- 复合查询: `idx_daily_reports_date_status`

### 8.3 批量操作限制

| 操作 | 单次上限 | 说明 |
|------|----------|------|
| 批量导入 | 100 条 | 超出需分批 |
| 导出 | 5000 条 | 超出需缩小筛选范围 |
| Excel 文件 | 5 MB | 超出拒绝上传 |

---

## §9 安全规范

### 9.1 认证授权

- 所有 API 需要 JWT Token
- 使用 `get_current_user` 依赖注入获取当前用户
- 使用 `require_role([...])` 校验角色权限
- 数据权限通过 RLS 和 Service 层双重检查

### 9.2 输入验证

- [x] 使用 Pydantic v2 验证所有输入
- [x] 字符串字段有最大长度限制 (max_length)
- [x] 数字字段有范围限制 (ge=0, gt=0)
- [x] 使用 ORM 参数化查询，禁止拼接 SQL
- [x] 日期验证: report_date <= today

### 9.3 审计日志

必须记录以下操作：

| 操作类型 | 记录内容 |
|----------|----------|
| 创建 | 操作人、时间、创建内容摘要 |
| 更新 | 操作人、时间、变更前后对比 |
| 删除 | 操作人、时间、删除内容备份 |
| 状态变更 | 操作人、时间、old_status → new_status |
| 批量导入 | 操作人、时间、成功/失败数量 |

---

## 附录: AI 代码工厂禁止行为清单

### A.1 禁止行为

| 禁止行为 | 正确做法 | 检查方式 |
|---------|---------|---------|
| 自定义错误码 | 使用 ERROR_CODES_SOT.md | grep "BIZ_" |
| 发明新状态 | 使用 8 状态机 | 枚举对比 |
| 自创字段 | 使用 DATA_SCHEMA.md §6.1 | Schema 对比 |
| 使用 Float 存金额 | 使用 Decimal(15,2) | 类型检查 |
| 物理删除日报 | 走归档/状态变更 | 删除操作审查 |
| 跳过权限检查 | Service 层必须检查 | 代码审查 |
| Phase 1 自动阻断 | 仅记录+提示 | 逻辑审查 |
| 终态回退 | final_locked 不可修改 | 状态机测试 |

### A.2 SoT 追溯验证 Checklist

生成代码后必须验证：
- [ ] 所有状态值来自 STATE_MACHINE.md v2.7 §8 (8 状态)
- [ ] 所有字段来自 DATA_SCHEMA.md v5.3 §6.1
- [ ] 所有错误码来自 ERROR_CODES_SOT.md v2.1
- [ ] 所有角色来自 MASTER.md v4.4 §2.4 (7 个)
- [ ] 金额字段使用 Decimal(15,2) 类型
- [ ] 时间字段使用 TIMESTAMPTZ + UTC

---

## 源码位置

| 层 | 文件路径 |
|----|---------|
| Model | `backend/models/workflow/daily_report.py` |
| Schema | `backend/schemas/daily_report.py` |
| Service | `backend/services/daily_report_service.py` |
| Router | `backend/routers/daily_reports.py` |
| Test | `backend/tests/test_daily_report_service.py` |
| Test | `backend/tests/test_daily_report_api.py` |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-23 | 初始版本，基于现有代码创建后端规格书 |

---

**维护者**: AI 广告代投系统开发团队
**参考文档**:
- `docs/3.dev-guides/BACKEND_MODULE_SPEC_GUIDE.md`
- `docs/sot/STATE_MACHINE.md` v2.6 §8
- `docs/sot/DATA_SCHEMA.md` v5.2 §6.1
