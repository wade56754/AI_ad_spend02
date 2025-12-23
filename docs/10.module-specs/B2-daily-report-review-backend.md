# B2 日报审核 - 后端模块规格书

> **版本**: v1.0
> **更新日期**: 2025-12-23
> **SoT 基准**: DATA_SCHEMA.md v5.2, STATE_MACHINE.md v2.6, API_SOT.md v9.3
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

本模块实现日报的趋势风控检查和人工审核功能。运营人员对投手提交的日报进行趋势分析、异常复核、真实消耗录入和最终粉数确认，完成日报从"原始数据"到"计费锁定"的完整审核流程。

### 1.2 涉及角色

| 角色 | 系统角色名 | 本模块权限 |
|------|------------|------------|
| 老板 | ceo | 查看审核进度统计（只读） |
| 项目负责人 | project_owner | 查看项目内审核进度（只读） |
| 财务 | finance | 查看已锁定日报、导出数据 |
| 主管 | supervisor | 查看下属日报审核状态 |
| 投手 | pitcher (media_buyer) | 查看自己日报的审核状态（只读） |
| 运营 | data_operator | **核心操作者**: 执行所有审核操作 |
| 管理员 | admin | 所有操作 |

### 1.3 模块边界

**本模块负责：**
- 趋势风控检查 (TF-001/TF-002/TF-003)
- 异常标记和人工复核 (trend_flagged → trend_resolved)
- 录入真实消耗 (real_spend)
- 最终粉数确认 (final_pending → final_confirmed)
- 月底计费锁定 (final_confirmed → final_locked)
- 异常日报列表查询

**本模块不负责：**
- 日报的创建、编辑、删除（由 B1 日报提交模块负责）
- 日报的批量导入（由 B1 日报提交模块负责）
- 账本记账（由 LEDGER_SOT.md 账本模块负责）

### 1.4 SoT 引用清单 (AI 防幻觉)

| SoT 文档 | 版本 | 引用章节 | 用途 |
|---------|------|---------|------|
| DATA_SCHEMA.md | v5.2 | §6.1 daily_reports | 表结构、字段定义 |
| STATE_MACHINE.md | v2.6 | §8 日报 8 状态机 | 状态流转规则 |
| STATE_MACHINE.md | v2.6 | §8.3 趋势风控规则 | TF-001/002/003 定义 |
| BUSINESS_RULES.md | v3.2 | BR-RPT-001~005 | 日报业务规则 |
| ERROR_CODES_SOT.md | v2.1 | BIZ_*, STATE_* | 业务错误码 |
| API_SOT.md | v9.0 | §9.2-9.5 Daily Reports | API 端点规范 |
| AUTH_SPEC.md | v2.0 | §3 权限矩阵 | 角色权限 |
| MASTER.md | v4.4 | §2.4 七角色, §5 Phase 1 | Phase 边界 |

---

## §2 数据模型

### 2.1 表结构定义

**来源**: DATA_SCHEMA.md v5.2 §6.1, `backend/models/workflow/daily_report.py`

本模块复用 B1 模块的 `daily_reports` 表，重点关注审核相关字段：

```sql
-- 审核相关字段 (daily_reports 表的子集)
ALTER TABLE daily_reports ADD COLUMN IF NOT EXISTS (
  -- 三数据流字段 (STATE_MACHINE.md v2.6 §8)
  conversions_raw   INTEGER NOT NULL DEFAULT 0,   -- raw 数据流 - 原始粉数
  conversions_final INTEGER NOT NULL DEFAULT 0,   -- final 数据流 - 最终粉数
  raw_spend         DECIMAL(15,2) NOT NULL DEFAULT 0.00, -- 原始消耗
  real_spend        DECIMAL(15,2) NOT NULL DEFAULT 0.00, -- 真实消耗
  unit_price        DECIMAL(15,2) NOT NULL DEFAULT 0.00, -- 单粉价格

  -- 8 状态机 (STATE_MACHINE.md v2.6 §8)
  status            VARCHAR(20) NOT NULL DEFAULT 'raw_submitted',

  -- 趋势风控字段 (STATE_MACHINE.md v2.6 §8.3)
  trend_flag        VARCHAR(20) NOT NULL DEFAULT 'normal',
  trend_flag_reason TEXT,             -- 风控触发原因 (如 TF-001; TF-002)
  trend_resolution_note TEXT,         -- 运营复核说明

  -- 锁定时间
  final_locked_at   TIMESTAMPTZ,

  -- 审核人关联
  audit_user_id     UUID REFERENCES users(id) ON DELETE SET NULL,
  approved_at       TIMESTAMPTZ
);
```

### 2.2 审核相关字段说明

| 字段 | 类型 | 说明 | 操作时机 |
|------|------|------|----------|
| status | VARCHAR(20) | 8 状态机状态 | 每次状态流转 |
| trend_flag | VARCHAR(20) | 趋势标记 (normal/flagged/resolved) | 风控检查后 |
| trend_flag_reason | TEXT | 触发的风控规则 (TF-001/002/003) | trend_flagged 时写入 |
| trend_resolution_note | TEXT | 运营复核说明 | trend_resolved 时写入 |
| real_spend | DECIMAL(15,2) | 真实消耗（供应商后台） | final_pending 前录入 |
| conversions_final | INTEGER | 最终粉数（运营确认） | final_confirmed 时写入 |
| audit_user_id | UUID | 审核人ID | 每次审核操作 |
| approved_at | TIMESTAMPTZ | 审批时间 | final_confirmed 时写入 |
| final_locked_at | TIMESTAMPTZ | 锁定时间 | final_locked 时写入 |

### 2.3 风控规则表

**来源**: STATE_MACHINE.md v2.6 §8.3

| 规则ID | 规则名称 | 触发条件 | 阈值 |
|--------|----------|----------|------|
| TF-001 | 粉数骤降检查 | conversions_raw < 昨日 × threshold | 0.5 (降50%) |
| TF-002 | 粉数骤增检查 | conversions_raw > 昨日 × threshold | 3.0 (增300%) |
| TF-003 | 消耗异常检查 | raw_spend > 昨日 × threshold | 2.0 (增200%) |

```python
# backend/services/trend_risk_control_service.py

@dataclass
class TrendRiskThresholds:
    """风控阈值配置"""
    conversions_drop_threshold: float = 0.5   # TF-001
    conversions_spike_threshold: float = 3.0  # TF-002
    spend_spike_threshold: float = 2.0        # TF-003
```

---

## §3 API 设计

### 3.1 端点清单

**来源**: API_SOT.md v9.3 §9.2-9.5, `backend/routers/daily_reports.py`

| 方法 | 端点 | 描述 | 权限 |
|------|------|------|------|
| POST | /api/v1/daily-reports/{id}/trigger-trend-check | 触发趋势风控检查 | media_buyer, data_operator, admin |
| POST | /api/v1/daily-reports/{id}/trend-flag | 标记趋势异常 | data_operator, admin |
| POST | /api/v1/daily-reports/{id}/trend-resolve | 解决趋势异常 | data_operator, admin |
| PUT | /api/v1/daily-reports/{id}/real-spend | 录入真实消耗 | data_operator, admin |
| POST | /api/v1/daily-reports/{id}/final-confirm | 确认最终粉数 | data_operator, admin |
| POST | /api/v1/daily-reports/{id}/final-lock | 锁定日报 | data_operator, admin |
| GET | /api/v1/daily-reports/trend-flagged | 获取异常日报列表 | data_operator, admin, finance |
| GET | /api/v1/daily-reports/trend-pending-count | 获取待检查数量 | data_operator, admin, finance |
| POST | /api/v1/daily-reports/batch-trend-check | 批量执行风控检查 | data_operator, admin |

### 3.2 请求/响应格式

#### 3.2.1 触发趋势风控检查

**POST /api/v1/daily-reports/{report_id}/trigger-trend-check**

状态转换: `raw_submitted → trend_pending`

```typescript
// 请求 - 无 body

// 响应 200
interface TriggerTrendCheckResponse {
  data: DailyReportResponse;
  message: "已触发趋势风控检查";
}
```

#### 3.2.2 标记趋势异常

**POST /api/v1/daily-reports/{report_id}/trend-flag**

状态转换: `trend_pending → trend_flagged`

```typescript
// 请求
interface DailyReportAuditRequest {
  audit_notes?: string;  // 审核说明，最大 500 字符
}

// 响应 200
interface TrendFlagResponse {
  data: DailyReportResponse;
  message: "日报已标记为趋势异常";
}
```

#### 3.2.3 解决趋势异常

**POST /api/v1/daily-reports/{report_id}/trend-resolve**

状态转换: `trend_flagged → trend_resolved`

```typescript
// 请求
interface DailyReportAuditRequest {
  audit_notes?: string;  // 复核说明 (写入 trend_resolution_note)
}

// 响应 200
interface TrendResolveResponse {
  data: DailyReportResponse;
  message: "趋势异常已解决";
}
```

#### 3.2.4 录入真实消耗

**PUT /api/v1/daily-reports/{report_id}/real-spend**

状态转换: `trend_ok/trend_resolved → final_pending`

```typescript
// 请求
interface RealSpendRequest {
  real_spend: number;   // 真实消耗（从供应商后台获取）, ≥ 0
  fee?: number;         // 手续费，默认 0.00
}

// 响应 200
interface RealSpendResponse {
  data: DailyReportResponse;
  message: "真实消耗已录入，等待确认final粉数";
}
```

#### 3.2.5 确认最终粉数

**POST /api/v1/daily-reports/{report_id}/final-confirm**

状态转换: `final_pending → final_confirmed`

```typescript
// 请求
interface DailyReportAuditRequest {
  audit_notes?: string;  // 确认说明
}

// 响应 200
interface FinalConfirmResponse {
  data: DailyReportResponse;
  message: "最终粉数已确认";
}
```

#### 3.2.6 锁定日报

**POST /api/v1/daily-reports/{report_id}/final-lock**

状态转换: `final_confirmed → final_locked` (终态)

```typescript
// 请求
interface DailyReportAuditRequest {
  audit_notes?: string;  // 锁定说明
}

// 响应 200
interface FinalLockResponse {
  data: DailyReportResponse;
  message: "日报已锁定，进入计费";
}
```

#### 3.2.7 获取异常日报列表

**GET /api/v1/daily-reports/trend-flagged**

```typescript
// 查询参数
interface TrendFlaggedQueryParams {
  page?: number;              // 页码，默认 1
  page_size?: number;         // 每页数量，默认 20
  ad_account_id?: number;     // 广告账户ID筛选
  report_date_start?: string; // 开始日期 YYYY-MM-DD
  report_date_end?: string;   // 结束日期 YYYY-MM-DD
}

// 响应 200
interface TrendFlaggedListResponse {
  data: {
    items: DailyReportResponse[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  };
  message: string;
}
```

### 3.3 错误码定义

**来源**: ERROR_CODES_SOT.md v2.1

| 错误码 | HTTP 状态 | 场景 |
|--------|-----------|------|
| VALIDATION_ERROR | 400 | 请求参数验证失败 |
| UNAUTHORIZED | 401 | 未登录 |
| AUTH_500 (FORBIDDEN) | 403 | 无权限执行审核操作 |
| BIZ-002 | 404 | 日报不存在 |
| STATE-400 | 400 | 无效的状态转换 |
| STATE-401 | 400 | 当前状态不允许该操作 |
| SYS-500 | 500 | 系统内部错误 |

---

## §4 权限控制

### 4.1 角色权限矩阵 (7 角色)

**来源**: AUTH_SPEC.md v2.0, MASTER.md v4.4 §2.4

| 操作 | ceo | project_owner | finance | supervisor | pitcher | account_manager | admin |
|------|-----|---------------|---------|------------|---------|-----------------|-------|
| 查看异常列表 | ✅ | ✅(项目内) | ✅ | ✅(下属) | ❌ | ❌ | ✅ |
| 触发风控检查 | ❌ | ❌ | ❌ | ❌ | ✅(自己) | ❌ | ✅ |
| 标记趋势异常 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 解决趋势异常 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 录入真实消耗 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 确认最终粉数 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 锁定日报 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 批量风控检查 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

**说明**:
- `data_operator` 角色拥有与 `admin` 相同的审核操作权限
- `finance` 仅能查看已锁定日报，不能执行审核操作

### 4.2 数据权限规则

```python
# backend/models/workflow/daily_report.py

def can_be_reviewed_by(self, user_id: UUID, user_role: UserRole) -> bool:
    """检查用户是否可以审核此日报"""
    # 只有管理员和运营可以审核
    if user_role not in [UserRole.ADMIN, UserRole.DATA_OPERATOR]:
        return False

    # 可审核状态：trend_flagged, final_pending
    reviewable_statuses = [
        DailyReportStatus.TREND_FLAGGED.value,
        DailyReportStatus.FINAL_PENDING.value,
    ]
    return self.status in reviewable_statuses
```

### 4.3 操作级权限

| 操作 | 允许的前置状态 | 操作角色 |
|------|---------------|----------|
| trigger-trend-check | raw_submitted | media_buyer, data_operator, admin |
| trend-flag | trend_pending | data_operator, admin |
| trend-resolve | trend_flagged | data_operator, admin |
| real-spend | trend_ok, trend_resolved | data_operator, admin |
| final-confirm | final_pending | data_operator, admin |
| final-lock | final_confirmed | data_operator, admin |

---

## §5 业务逻辑

### 5.1 审核流程状态机

**来源**: STATE_MACHINE.md v2.6 §8 日报 8 状态机

本模块负责的状态流转（从 B1 提交后开始）：

```
                     ┌─────────────────────────────────┐
                     │        B1 日报提交模块          │
                     │  (创建 → raw_submitted)        │
                     └─────────────┬───────────────────┘
                                   │
                                   │ trigger-trend-check
                                   ↓
┌──────────────────────────────────────────────────────────────────────┐
│                     B2 日报审核模块 (本模块)                          │
│                                                                      │
│  ┌──────────────┐                                                   │
│  │trend_pending │                                                   │
│  └──────┬───────┘                                                   │
│         │                                                           │
│         │ TrendRiskControlService.execute_trend_check()            │
│         │                                                           │
│         ├─────────────────────────┐                                 │
│         │ 通过 (TF-* 规则全过)    │ 触发 (TF-* 任一触发)            │
│         ↓                         ↓                                 │
│  ┌───────────┐            ┌──────────────┐                         │
│  │ trend_ok  │            │trend_flagged │←─────────────┐          │
│  └─────┬─────┘            └──────┬───────┘              │          │
│        │                         │                       │          │
│        │                         │ trend-resolve         │ 退回     │
│        │                         ↓                       │          │
│        │                 ┌──────────────┐               │          │
│        │                 │trend_resolved│───────────────┘          │
│        │                 └──────┬───────┘  (可选: 退回重审)        │
│        │                        │                                   │
│        │        real-spend      │                                   │
│        └────────────────────────┤                                   │
│                                 ↓                                   │
│                         ┌──────────────┐                           │
│                         │final_pending │                           │
│                         └──────┬───────┘                           │
│                                │                                    │
│                                │ final-confirm                      │
│                                ↓                                    │
│                        ┌────────────────┐                          │
│                        │final_confirmed │                          │
│                        └───────┬────────┘                          │
│                                │                                    │
│                                │ final-lock (月底)                  │
│                                ↓                                    │
│                         ┌──────────────┐                           │
│                         │ final_locked │ (终态)                    │
│                         └──────────────┘                           │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 5.2 状态转换表

| 当前状态 | 目标状态 | API 端点 | 触发条件 | 操作者 |
|----------|----------|----------|----------|--------|
| raw_submitted | trend_pending | trigger-trend-check | 手动触发 | pitcher/data_operator |
| trend_pending | trend_ok | (自动) | TF-* 规则全部通过 | system |
| trend_pending | trend_flagged | (自动) | TF-* 任一规则触发 | system |
| trend_flagged | trend_resolved | trend-resolve | 运营确认 | data_operator |
| trend_flagged | raw_submitted | (退回) | 运营退回重填 | data_operator |
| trend_ok | final_pending | real-spend | 录入 real_spend | data_operator |
| trend_resolved | final_pending | real-spend | 录入 real_spend | data_operator |
| final_pending | final_confirmed | final-confirm | 运营确认 | data_operator |
| final_confirmed | final_locked | final-lock | 月底锁定 | data_operator/system |

### 5.3 风控检查逻辑

**来源**: `backend/services/trend_risk_control_service.py`

```python
class TrendRiskControlService:
    """趋势风控服务"""

    def check_trend_risk(self, report: DailyReport) -> TrendRiskCheckResult:
        """
        执行趋势风控检查

        返回:
        - passed: True = 通过, False = 触发异常
        - triggered_rules: 触发的规则列表
        - trend_flag_reason: 异常原因描述
        """
        # 获取昨日数据
        yesterday_data = self._get_yesterday_data(
            ad_account_id=report.ad_account_id,
            report_date=report.report_date
        )

        # 如果没有昨日数据，视为通过
        if not yesterday_data:
            return TrendRiskCheckResult(passed=True, triggered_rules=[])

        triggered_rules = []

        # TF-001: 粉数骤降检查
        if self._check_tf001(report, yesterday_data)["triggered"]:
            triggered_rules.append(TrendRiskRule.TF_001)

        # TF-002: 粉数骤增检查
        if self._check_tf002(report, yesterday_data)["triggered"]:
            triggered_rules.append(TrendRiskRule.TF_002)

        # TF-003: 消耗异常检查
        if self._check_tf003(report, yesterday_data)["triggered"]:
            triggered_rules.append(TrendRiskRule.TF_003)

        passed = len(triggered_rules) == 0
        return TrendRiskCheckResult(
            passed=passed,
            triggered_rules=triggered_rules,
            trend_flag_reason=self._build_reason(triggered_rules)
        )

    def _check_tf001(self, report, yesterday_data) -> dict:
        """TF-001: 粉数骤降检查 (< 昨日 × 0.5)"""
        current = report.conversions_raw or 0
        yesterday = yesterday_data.conversions_raw or 0
        threshold = yesterday * 0.5

        triggered = yesterday > 0 and current < threshold
        return {"triggered": triggered, "current": current, "threshold": threshold}

    def _check_tf002(self, report, yesterday_data) -> dict:
        """TF-002: 粉数骤增检查 (> 昨日 × 3.0)"""
        current = report.conversions_raw or 0
        yesterday = yesterday_data.conversions_raw or 0
        threshold = yesterday * 3.0

        triggered = yesterday > 0 and current > threshold
        return {"triggered": triggered, "current": current, "threshold": threshold}

    def _check_tf003(self, report, yesterday_data) -> dict:
        """TF-003: 消耗异常检查 (> 昨日 × 2.0)"""
        current = float(report.raw_spend or 0)
        yesterday = float(yesterday_data.raw_spend or 0)
        threshold = yesterday * 2.0

        triggered = yesterday > 0 and current > threshold
        return {"triggered": triggered, "current": current, "threshold": threshold}
```

### 5.4 业务约束 + Phase 1 规则

```yaml
约束规则:
  状态约束:
    - 只能按状态机定义的路径转换
    - 终态 (final_locked) 不可回退
    - 每个操作必须检查前置状态

  数据约束:
    - real_spend >= 0 (必须使用 Decimal)
    - conversions_final >= 0
    - audit_notes 最大 500 字符

  审计约束:
    - 每次状态转换必须记录 audit_user_id
    - final_confirmed 时写入 approved_at
    - final_locked 时写入 final_locked_at

Phase 1 规则 (照亮阶段):
  ❌ 禁止: 自动阻断提交、自动拒绝日报
  ✅ 允许: 标记异常、人工复核、高亮显示

  异常处理:
    - TF-001/002/003 触发: 标记 trend_flagged，等待人工复核
    - 不自动拒绝，不阻断业务流程
    - 运营可以确认异常后继续流程 (trend_resolved)
```

---

## §6 前后端接口契约

### 6.1 字段映射

| 后端字段 (snake_case) | 前端字段 (camelCase) | 说明 |
|----------------------|---------------------|------|
| trend_flag | trendFlag | 趋势标记 |
| trend_flag_reason | trendFlagReason | 异常原因 |
| trend_resolution_note | trendResolutionNote | 复核说明 |
| real_spend | realSpend | 真实消耗 |
| conversions_final | conversionsFinal | 最终粉数 |
| audit_user_id | auditUserId | 审核人ID |
| approved_at | approvedAt | 审批时间 |
| final_locked_at | finalLockedAt | 锁定时间 |

### 6.2 枚举值对照

```typescript
// 趋势标记 (trend_flag)
type TrendFlag = 'normal' | 'flagged' | 'resolved';

const TREND_FLAG_LABELS: Record<TrendFlag, string> = {
  normal: '正常',
  flagged: '异常',
  resolved: '已解决',
};

// 风控规则
type TrendRiskRule = 'TF-001' | 'TF-002' | 'TF-003';

const TREND_RISK_RULE_LABELS: Record<TrendRiskRule, string> = {
  'TF-001': '粉数骤降',
  'TF-002': '粉数骤增',
  'TF-003': '消耗异常',
};

// 审核相关状态 (8 状态机的后半段)
type ReviewStatus =
  | 'trend_pending'     // 待风控检查
  | 'trend_ok'          // 风控通过
  | 'trend_flagged'     // 趋势异常
  | 'trend_resolved'    // 异常已解决
  | 'final_pending'     // 待最终确认
  | 'final_confirmed'   // 已确认
  | 'final_locked';     // 已锁定 (终态)
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
  金额 (real_spend): Decimal 类型，保留2位小数
  粉数 (conversions_final): 整数

空值:
  null: 表示未填写
  0: 表示实际值为零
```

---

## §7 测试要点

### 7.1 单元测试

```python
# backend/tests/test_trend_risk_control_service.py

class TestTrendRiskCheck:
    """风控规则测试"""

    def test_tf001_triggers_on_drop(self, db, yesterday_report):
        """TF-001: 粉数下降超过50%应触发"""
        yesterday_report.conversions_raw = 100
        today_report = create_report(conversions_raw=40)  # 下降60%

        service = TrendRiskControlService(db)
        result = service.check_trend_risk(today_report)

        assert not result.passed
        assert TrendRiskRule.TF_001 in result.triggered_rules

    def test_tf002_triggers_on_spike(self, db, yesterday_report):
        """TF-002: 粉数增长超过300%应触发"""
        yesterday_report.conversions_raw = 100
        today_report = create_report(conversions_raw=400)  # 增长400%

        service = TrendRiskControlService(db)
        result = service.check_trend_risk(today_report)

        assert not result.passed
        assert TrendRiskRule.TF_002 in result.triggered_rules

    def test_tf003_triggers_on_spend_spike(self, db, yesterday_report):
        """TF-003: 消耗增长超过200%应触发"""
        yesterday_report.raw_spend = Decimal("1000.00")
        today_report = create_report(raw_spend=Decimal("2500.00"))  # 增长250%

        service = TrendRiskControlService(db)
        result = service.check_trend_risk(today_report)

        assert not result.passed
        assert TrendRiskRule.TF_003 in result.triggered_rules

    def test_no_yesterday_data_passes(self, db):
        """无昨日数据时应直接通过"""
        today_report = create_report(conversions_raw=100)

        service = TrendRiskControlService(db)
        result = service.check_trend_risk(today_report)

        assert result.passed
        assert len(result.triggered_rules) == 0


class TestStateTransitions:
    """状态转换测试"""

    def test_trend_pending_to_trend_ok(self, report):
        """trend_pending → trend_ok 允许"""
        report.status = 'trend_pending'
        assert report.can_transition_to(DailyReportStatus.TREND_OK)

    def test_trend_pending_to_trend_flagged(self, report):
        """trend_pending → trend_flagged 允许"""
        report.status = 'trend_pending'
        assert report.can_transition_to(DailyReportStatus.TREND_FLAGGED)

    def test_final_locked_is_terminal(self, locked_report):
        """final_locked 是终态，不允许任何转换"""
        locked_report.status = 'final_locked'
        assert not locked_report.can_transition_to(DailyReportStatus.FINAL_CONFIRMED)
```

### 7.2 集成测试

```python
# backend/tests/test_daily_report_review_api.py

class TestReviewAPI:
    """审核 API 集成测试"""

    async def test_data_operator_can_resolve_trend(self, client, data_operator_token):
        """运营可以解决趋势异常"""
        # 准备 trend_flagged 状态的日报
        report = create_flagged_report()

        response = await client.post(
            f"/api/v1/daily-reports/{report.id}/trend-resolve",
            headers={"Authorization": f"Bearer {data_operator_token}"},
            json={"audit_notes": "已与投手确认，数据正确"}
        )

        assert response.status_code == 200
        assert response.json()["data"]["status"] == "trend_resolved"

    async def test_pitcher_cannot_resolve_trend(self, client, pitcher_token):
        """投手不能解决趋势异常"""
        report = create_flagged_report()

        response = await client.post(
            f"/api/v1/daily-reports/{report.id}/trend-resolve",
            headers={"Authorization": f"Bearer {pitcher_token}"},
            json={"audit_notes": "..."}
        )

        assert response.status_code == 403

    async def test_invalid_state_transition_rejected(self, client, data_operator_token):
        """无效状态转换应被拒绝"""
        # 尝试从 raw_submitted 直接跳到 final_confirm
        report = create_report(status='raw_submitted')

        response = await client.post(
            f"/api/v1/daily-reports/{report.id}/final-confirm",
            headers={"Authorization": f"Bearer {data_operator_token}"},
            json={}
        )

        assert response.status_code == 400
        assert "STATE-400" in response.json()["error"]["code"]
```

### 7.3 权限测试矩阵

```python
@pytest.mark.parametrize("role,action,expected", [
    # [角色, 操作, 预期状态码]
    ("ceo", "view_flagged_list", 200),
    ("ceo", "trend_resolve", 403),
    ("finance", "view_flagged_list", 200),
    ("finance", "trend_resolve", 403),
    ("pitcher", "trigger_trend_check_own", 200),
    ("pitcher", "trend_resolve", 403),
    ("data_operator", "trend_flag", 200),
    ("data_operator", "trend_resolve", 200),
    ("data_operator", "real_spend", 200),
    ("data_operator", "final_confirm", 200),
    ("data_operator", "final_lock", 200),
    ("admin", "all_operations", 200),
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
| 单个风控检查 | < 200ms | < 500ms |
| 状态转换操作 | < 300ms | < 1s |
| 异常列表查询 | < 200ms | < 500ms |
| 批量风控检查 (100条) | < 10s | < 30s |

### 8.2 索引要求

必须为以下查询场景建立索引（复用 B1 模块索引）：
- 按状态筛选: `idx_daily_reports_status`
- 按日期范围查询: `idx_daily_reports_date`
- 按账户查询: `idx_daily_reports_account`
- 复合查询: `idx_daily_reports_date_status`

### 8.3 批量操作限制

| 操作 | 单次上限 | 说明 |
|------|----------|------|
| 批量风控检查 | 100 条 | 超出需分批 |
| 异常列表查询 | 100 条/页 | 分页返回 |

---

## §9 安全规范

### 9.1 认证授权

- 所有 API 需要 JWT Token
- 使用 `require_role(["data_operator", "admin"])` 校验角色权限
- 状态转换必须验证前置状态

### 9.2 输入验证

- [x] 使用 Pydantic v2 验证所有输入
- [x] audit_notes 最大 500 字符
- [x] real_spend 必须 >= 0
- [x] 使用 ORM 参数化查询，禁止拼接 SQL

### 9.3 审计日志

必须记录以下操作：

| 操作类型 | 记录内容 |
|----------|----------|
| 风控检查 | 检查结果、触发规则、操作人 |
| 异常标记 | trend_flag_reason、操作人、时间 |
| 异常解决 | trend_resolution_note、操作人、时间 |
| 录入消耗 | old_value → new_value、操作人、时间 |
| 状态变更 | old_status → new_status、操作人、时间 |
| 锁定 | final_locked_at、操作人 |

---

## 附录: AI 代码工厂禁止行为清单

### A.1 禁止行为

| 禁止行为 | 正确做法 | 检查方式 |
|---------|---------|---------|
| 自定义风控规则 | 使用 TF-001/002/003 | grep "TF-" |
| 发明新状态 | 使用 8 状态机 | 枚举对比 |
| 跳过状态验证 | 使用 can_transition_to() | 代码审查 |
| 自动拒绝日报 | Phase 1 只标记不阻断 | 逻辑审查 |
| 跳过权限检查 | require_role() 装饰器 | 代码审查 |
| 终态回退 | final_locked 不可修改 | 状态机测试 |

### A.2 SoT 追溯验证 Checklist

生成代码后必须验证：
- [ ] 所有状态值来自 STATE_MACHINE.md v2.6 §8 (8 状态)
- [ ] 风控规则来自 STATE_MACHINE.md v2.6 §8.3 (TF-001/002/003)
- [ ] 所有错误码来自 ERROR_CODES_SOT.md v2.1
- [ ] 所有角色来自 MASTER.md v4.4 §2.4 (7 个)
- [ ] 金额字段使用 Decimal(15,2) 类型
- [ ] 时间字段使用 TIMESTAMPTZ + UTC
- [ ] Phase 1 规则: 只标记不阻断

---

## 源码位置

| 层 | 文件路径 |
|----|---------|
| Model | `backend/models/workflow/daily_report.py` |
| Schema | `backend/schemas/daily_report.py` |
| Service | `backend/services/daily_report_service.py` |
| Service | `backend/services/trend_risk_control_service.py` |
| Router | `backend/routers/daily_reports.py` |
| Test | `backend/tests/test_daily_report_service.py` |
| Test | `backend/tests/test_daily_report_api.py` |
| Test | `backend/tests/api/test_trend_risk_flow_generated.py` |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-23 | 初始版本，基于现有代码创建后端规格书 |

---

**维护者**: AI 广告代投系统开发团队
**参考文档**:
- `docs/3.dev-guides/BACKEND_MODULE_SPEC_GUIDE.md`
- `docs/10.module-specs/B1-daily-report-submit.md`
- `docs/2.sot/STATE_MACHINE.md` v2.6 §8
- `docs/2.sot/DATA_SCHEMA.md` v5.2 §6.1
