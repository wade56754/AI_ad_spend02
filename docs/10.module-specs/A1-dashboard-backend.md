# A1 老板驾驶舱 - 后端模块规格书

> **版本**: v1.0
> **更新日期**: 2025-12-23
> **SoT 基准**: DATA_SCHEMA.md v5.2, MASTER.md v4.4 §6.5
> **参考指南**: docs/3.dev-guides/BACKEND_MODULE_SPEC_GUIDE.md
> **前端规格书**: docs/10.module-specs/A1-dashboard.md

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

本模块提供老板驾驶舱聚合数据 API，解答核心管理问题：**"今天公司怎么样？"**。通过聚合消耗、进粉、收入、毛利等核心指标，让老板在 5 秒内掌握公司运营状况。

**核心价值**:
- 全局视角：一眼看到公司今日核心 KPI
- 趋势洞察：发现异常趋势，提前预警
- 行动闭环：从数据 → 归因对象 → 操作入口

### 1.2 涉及角色

| 角色 | 系统角色名 | 本模块权限 |
|------|------------|------------|
| 老板 | ceo | **核心用户**: 全公司数据 |
| 财务 | finance | 全公司数据 (只读) |
| 项目负责人 | project_owner | 自己项目数据 |
| 主管 | supervisor | 自己团队数据 |
| 投手 | pitcher | 自己数据 |
| 户管 | account_manager | 账户相关数据 |
| 管理员 | admin | 全公司数据 |

### 1.3 模块边界

**本模块负责：**
- KPI 指标聚合计算
- 趋势数据聚合
- Top N 项目排名
- 待处理事项计数
- 异常告警生成

**本模块不负责：**
- 日报数据 CRUD（由 B1/B2 模块负责）
- 消耗数据导入（由 C3 模块负责）
- 充值审批流程（由 C1 模块负责）

### 1.4 SoT 引用清单 (AI 防幻觉)

| SoT 文档 | 版本 | 引用章节 | 用途 |
|---------|------|---------|------|
| MASTER.md | v4.4 | §6.5 核心页面最小字段集 | 必须字段定义 |
| MASTER.md | v4.4 | §4.5.1-4.5.4 | 计算公式 |
| DATA_SCHEMA.md | v5.2 | §3 daily_reports | 进粉数据源 |
| DATA_SCHEMA.md | v5.2 | §4.1 ad_spend_daily | 消耗数据源 |
| STATE_MACHINE.md | v2.6 | §1 日报状态机 | 待处理状态判定 |
| API_SOT.md | v9.0 | §1 Dashboard | API 端点规范 |
| AUTH_SPEC.md | v2.0 | §3 权限矩阵 | 角色权限 |

### 1.5 MASTER.md §6.5 必须字段

**页面 1：老板驾驶舱**

| 字段 | 来源 | 口径 | 说明 |
|------|------|------|------|
| 本月总消耗 | ad_spend_daily | `SUM(spend)` | 消耗 SoT |
| 本月总进粉 | daily_report | `SUM(conversions)` | 进粉 SoT |
| 整体 CPL | 计算 | `总消耗/总进粉` | §4.5.2 规则 |
| 预计毛利 | 计算 | §4.5.4 公式 | revenue - spend |
| 活跃项目数 | project | `COUNT(status='active')` | 项目统计 |
| 异常项目数 | 计算 | `CPL > target × 1.3` | 风险预警 |
| 待审批充值数 | topup_request | `COUNT(status='pending')` | 待处理项 |

---

## §2 数据模型

### 2.1 聚合数据源

本模块不创建新表，通过聚合查询现有表生成数据。

**数据源表**:

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| daily_reports | 进粉、消耗数据 | raw_spend, conversions, conversions_final, status |
| ad_spend_daily | 消耗明细 | spend, event_date |
| projects | 项目信息 | status, owner_id, unit_price |
| topup_requests | 充值申请 | status, created_at |
| ad_accounts | 账户信息 | project_id, balance |

### 2.2 聚合查询模式

**KPI 聚合**:
```sql
-- 消耗汇总 (Phase 1: 从 daily_reports)
SELECT
    COALESCE(SUM(raw_spend), 0) AS total_spend,
    COALESCE(SUM(conversions_final), 0) AS total_conversions
FROM daily_reports
WHERE report_date BETWEEN :start_date AND :end_date;

-- 收入计算 (仅 final_locked 状态)
SELECT
    COALESCE(SUM(conversions_final * unit_price), 0) AS total_revenue
FROM daily_reports
WHERE report_date BETWEEN :start_date AND :end_date
  AND status = 'final_locked';

-- 活跃项目数
SELECT COUNT(*) AS active_projects
FROM projects
WHERE status = 'active';

-- 待审批充值数
SELECT COUNT(*) AS pending_topups
FROM topup_requests
WHERE status IN ('pending_review', 'finance_approve');
```

**趋势聚合**:
```sql
-- 按日趋势
SELECT
    report_date AS date,
    SUM(raw_spend) AS spend,
    SUM(conversions_final) AS conversions,
    SUM(conversions_final * unit_price) AS revenue
FROM daily_reports
WHERE report_date BETWEEN :start_date AND :end_date
GROUP BY report_date
ORDER BY report_date;
```

**Top N 排名**:
```sql
-- 消耗 Top N
SELECT
    p.id AS project_id,
    p.name AS project_name,
    SUM(dr.raw_spend) AS total_spend,
    SUM(dr.follows_count) AS total_follows
FROM daily_reports dr
JOIN ad_accounts aa ON dr.ad_account_id = aa.id
JOIN projects p ON aa.project_id = p.id
WHERE dr.report_date BETWEEN :start_date AND :end_date
GROUP BY p.id, p.name
ORDER BY total_spend DESC
LIMIT :top_n;
```

### 2.3 缓存策略

| 数据类型 | 缓存时间 | 失效条件 |
|---------|---------|---------|
| KPI 概览 | 5 分钟 | 新日报提交 |
| 趋势数据 | 10 分钟 | 日期切换 |
| Top 列表 | 10 分钟 | 无 |
| 待处理数 | 1 分钟 | 状态变更 |

---

## §3 API 设计

### 3.1 端点清单

**来源**: A1-dashboard.md §5.1, dashboard.types.ts

| 方法 | 端点 | 描述 | 权限 | 实现状态 |
|------|------|------|------|---------|
| GET | /api/v1/dashboard/overview | KPI 概览 | 登录用户 | ⚠️ 映射到 /dashboards/ceo/summary |
| GET | /api/v1/dashboard/trend | 趋势数据 | 登录用户 | ❌ 待实现 |
| GET | /api/v1/dashboard/top-projects | Top N 项目 | ceo/finance | ⚠️ 部分在 /dashboards/ceo/detail |
| GET | /api/v1/dashboard/pending-counts | 待处理计数 | 登录用户 | ⚠️ 合并在 overview |

**现有实现 (dashboard.py)**:

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | /dashboards/ceo/summary | CEO 驾驶舱汇总 |
| GET | /dashboards/ceo/detail | CEO 驾驶舱详情 + Top N |

### 3.2 请求/响应格式

**GET /api/v1/dashboard/overview**

请求参数:
```typescript
interface DashboardOverviewParams {
  date_from: string;  // YYYY-MM-DD
  date_to: string;    // YYYY-MM-DD
}
```

响应 (对齐 dashboard.types.ts):
```typescript
interface DashboardOverviewResponse {
  success: boolean;
  data: {
    // MASTER.md §6.5 必须字段
    total_spend: number;           // 本月总消耗
    total_conversions: number;     // 本月总进粉
    total_revenue: number;         // 本月总收入
    total_profit: number;          // 预计毛利
    cpl: number;                   // 整体 CPL
    // 变化率
    spend_change: number;
    conversions_change: number;
    revenue_change: number;
    profit_change: number;
    // 运营状态
    active_projects: number;       // 活跃项目数
    abnormal_projects: number;     // 异常项目数 (CPL > target × 1.3)
    pending_topups: number;        // 待审批充值数
    // 扩展字段
    cpl_target?: number;
    today_spend?: number;
    today_conversions?: number;
    today_revenue?: number;
    today_profit?: number;
  };
  message: string;
}
```

**GET /api/v1/dashboard/trend**

请求参数:
```typescript
interface DashboardTrendParams {
  date_from: string;
  date_to: string;
  metrics?: ('spend' | 'revenue' | 'profit' | 'conversions')[];
}
```

响应:
```typescript
interface DashboardTrendResponse {
  success: boolean;
  data: {
    points: Array<{
      date: string;
      spend: number;
      revenue: number;
      profit: number;
      conversions: number;
    }>;
    summary: {
      trend: 'up' | 'down' | 'stable';
      change_percent: number;
      description: string;
    };
  };
  message: string;
}
```

**GET /api/v1/dashboard/top-projects**

响应:
```typescript
interface DashboardTopProjectsResponse {
  success: boolean;
  data: {
    top_spend: Array<{
      id: string;
      name: string;
      spend: number;
      change: number;
    }>;
    worst_roas: Array<{
      id: string;
      name: string;
      roas: number;
      spend: number;
    }>;
  };
  message: string;
}
```

**GET /api/v1/dashboard/pending-counts**

响应:
```typescript
interface DashboardPendingCountsResponse {
  success: boolean;
  data: {
    pending_topups: number;
    pending_settlements: number;
    pending_reconciliations: number;
    pending_imports: number;
  };
  message: string;
}
```

### 3.3 错误码定义

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| AUTH_500 | 403 | CEO 驾驶舱仅限老板和管理员访问 |
| VAL_001 | 400 | 日期格式无效 |
| VAL_002 | 400 | 日期范围无效 (end < start) |
| SYS_001 | 500 | 内部服务错误 |

### 3.4 分页/筛选规范

```yaml
日期范围:
  默认: 当月 1 日至今日
  格式: YYYY-MM-DD
  最大跨度: 365 天

Top N:
  默认: 5
  最小: 1
  最大: 20
```

---

## §4 权限控制

### 4.1 角色权限矩阵 (7 角色)

**来源**: AUTH_SPEC.md v2.0, A1-dashboard.md §6.2

| 操作 | ceo | project_owner | finance | supervisor | pitcher | account_manager | admin |
|------|-----|---------------|---------|------------|---------|-----------------|-------|
| 查看全公司 KPI | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 查看自己项目 KPI | N/A | ✅ | N/A | ❌ | ❌ | ❌ | N/A |
| 查看自己团队 KPI | N/A | ❌ | N/A | ✅ | ❌ | ❌ | N/A |
| 查看自己 KPI | N/A | ❌ | N/A | ❌ | ✅ | ❌ | N/A |
| 查看 Top 列表 | ✅ | 部分 | ✅ | 部分 | ❌ | ❌ | ✅ |
| 查看待处理数 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |

### 4.2 数据权限规则

```python
def get_dashboard_data_filter(user: User) -> dict:
    """
    根据用户角色返回数据过滤条件

    Returns:
        dict: 过滤条件，用于 SQLAlchemy filter
    """
    if user.role in ['ceo', 'admin', 'finance']:
        # 全公司数据
        return {}

    if user.role == 'project_owner':
        # 自己负责的项目
        return {'project_owner_id': user.id}

    if user.role == 'supervisor':
        # 自己团队的数据
        team_member_ids = get_team_member_ids(user.id)
        return {'pitcher_id__in': team_member_ids}

    if user.role == 'pitcher':
        # 自己的数据
        return {'pitcher_id': user.id}

    if user.role == 'account_manager':
        # 自己管理的账户数据
        account_ids = get_managed_account_ids(user.id)
        return {'ad_account_id__in': account_ids}

    return {'id': -1}  # 无权限，返回空
```

### 4.3 CEO 驾驶舱专属权限

```python
def require_ceo_access(current_user: User) -> User:
    """
    CEO 驾驶舱权限检查

    仅允许以下角色访问:
    - admin
    - ceo

    其他角色应使用通用 dashboard 端点
    """
    allowed_roles = ["admin", "ceo"]

    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "AUTH_500",
                "message": "CEO 驾驶舱仅限老板和管理员访问"
            }
        )

    return current_user
```

---

## §5 业务逻辑

### 5.1 KPI 计算公式

**来源**: MASTER.md v4.4 §4.5.1-4.5.4

**CPL 计算** (§4.5.1):
```python
def calculate_cpl(spend: Decimal, conversions: int) -> Optional[Decimal]:
    """
    计算 CPL (Cost Per Lead)

    规则:
    - conversions = 0: 返回 None (前端显示 "--")
    - conversions < 5: 标记 "(低量)"
    - 正常计算: spend / conversions
    """
    if conversions == 0:
        return None
    return Decimal(str(spend)) / Decimal(conversions)
```

**预计毛利** (§4.5.4 Phase 1):
```python
def calculate_profit(
    total_conversions: int,
    unit_price: Decimal,
    total_spend: Decimal
) -> Decimal:
    """
    Phase 1 预计毛利公式

    预计收入 = conversions × unit_price
    预计成本 = SUM(spend)
    预计毛利 = 预计收入 - 预计成本
    """
    revenue = Decimal(total_conversions) * unit_price
    profit = revenue - total_spend
    return profit
```

**异常项目判定**:
```python
def is_abnormal_project(
    project_cpl: Decimal,
    target_cpl: Decimal
) -> bool:
    """
    判断项目是否异常

    异常标准: CPL > target × 1.3
    """
    if target_cpl <= 0:
        return False
    return project_cpl > target_cpl * Decimal('1.3')
```

**变化率计算**:
```python
def calculate_change_rate(
    current: Decimal,
    previous: Decimal
) -> Optional[float]:
    """
    计算环比变化率

    公式: (current - previous) / previous × 100%
    """
    if previous == 0:
        return None
    change = (current - previous) / previous * 100
    return round(float(change), 2)
```

### 5.2 趋势分析

```python
def analyze_trend(points: List[dict]) -> dict:
    """
    分析趋势数据

    Returns:
        {
            'trend': 'up' | 'down' | 'stable',
            'change_percent': float,
            'description': str
        }
    """
    if len(points) < 2:
        return {
            'trend': 'stable',
            'change_percent': 0,
            'description': '数据不足'
        }

    first_value = points[0].get('spend', 0)
    last_value = points[-1].get('spend', 0)

    if first_value == 0:
        change_percent = 0
    else:
        change_percent = (last_value - first_value) / first_value * 100

    if change_percent > 1:
        trend = 'up'
        description = f"近{len(points)}日消耗稳定上升"
    elif change_percent < -1:
        trend = 'down'
        description = f"近{len(points)}日消耗下降"
    else:
        trend = 'stable'
        description = f"近{len(points)}日消耗平稳"

    return {
        'trend': trend,
        'change_percent': round(change_percent, 1),
        'description': description
    }
```

### 5.3 待处理事项统计

```python
def get_pending_counts(db: Session) -> dict:
    """
    获取各类待处理事项数量
    """
    # 待审批充值
    pending_topups = db.query(func.count(TopupRequest.id)).filter(
        TopupRequest.status.in_([
            TopupRequestStatus.PENDING_REVIEW.value,
            TopupRequestStatus.FINANCE_APPROVE.value
        ])
    ).scalar() or 0

    # 待审核日报
    pending_reports = db.query(func.count(DailyReport.id)).filter(
        DailyReport.status.in_([
            DailyReportStatus.TREND_PENDING.value,
            DailyReportStatus.TREND_FLAGGED.value,
            DailyReportStatus.FINAL_PENDING.value
        ])
    ).scalar() or 0

    # 趋势异常数
    trend_flagged = db.query(func.count(DailyReport.id)).filter(
        DailyReport.status == DailyReportStatus.TREND_FLAGGED.value
    ).scalar() or 0

    return {
        'pending_topups': pending_topups,
        'pending_reports': pending_reports,
        'trend_flagged_count': trend_flagged,
        'pending_settlements': 0,  # 待实现
        'pending_reconciliations': 0,  # 待实现
        'pending_imports': 0,  # 待实现
    }
```

### 5.4 告警生成

```python
def generate_alerts(
    trend_flagged_count: int,
    pending_topups: int,
    abnormal_projects: List[dict]
) -> List[dict]:
    """
    生成告警列表

    告警类型:
    - trend_anomaly: 趋势异常
    - pending_approval: 待审批积压
    - budget_warning: 预算超支
    """
    alerts = []

    # 告警 1: 趋势异常日报
    if trend_flagged_count > 0:
        alerts.append({
            'type': 'trend_anomaly',
            'severity': 'high',
            'message': f"有 {trend_flagged_count} 个日报存在趋势异常，需人工复核"
        })

    # 告警 2: 待审批充值积压
    if pending_topups > 5:
        alerts.append({
            'type': 'pending_approval',
            'severity': 'medium',
            'message': f"有 {pending_topups} 个充值申请待审批"
        })

    # 告警 3: 异常项目
    for project in abnormal_projects:
        alerts.append({
            'type': 'budget_warning',
            'severity': 'high',
            'project_id': project['id'],
            'project_name': project['name'],
            'message': f"项目 {project['name']} CPL 超标 30%+"
        })

    return alerts
```

### 5.5 Phase 1 规则

```yaml
Phase 1 行为 (照亮阶段):
  ✅ 允许:
    - 展示所有 KPI 数据
    - 展示异常告警 (仅提示，不阻断)
    - 展示趋势分析

  ❌ 禁止:
    - 自动发送告警通知
    - 自动暂停异常项目
    - 强制要求处理

  异常处理:
    - CPL 超标: 高亮显示，不阻断
    - 零转化: 显示 "--"
    - 数据缺失: 显示 "待确认"
```

---

## §6 前后端接口契约

### 6.1 字段映射

| 后端字段 (snake_case) | 前端字段 (camelCase) | 说明 |
|----------------------|---------------------|------|
| total_spend | totalSpend | number |
| total_conversions | totalConversions | number |
| total_revenue | totalRevenue | number |
| total_profit | totalProfit | number |
| cpl | cpl | number | null |
| spend_change | spendChange | number | null |
| conversions_change | conversionsChange | number | null |
| active_projects | activeProjects | number |
| abnormal_projects | abnormalProjects | number |
| pending_topups | pendingTopups | number |
| cpl_target | cplTarget | number | null |

### 6.2 数字格式约定

```yaml
金额:
  单位: 元 (CNY)
  精度: 2 位小数
  显示: 前端格式化为 ¥XX.Xw (万)

百分比:
  精度: 1 位小数
  格式: 12.5 表示 12.5%
  正负: 正数表示增长，负数表示下降

数量:
  类型: 整数
  显示: 千分位分隔
```

### 6.3 时区约定

```yaml
日期:
  格式: YYYY-MM-DD
  时区: 服务器本地时区 (CST)

时间戳:
  格式: ISO 8601
  时区: UTC
```

---

## §7 测试要点

### 7.1 单元测试

```python
describe('DashboardService', () => {

    describe('calculate_cpl', () => {
        it('正常计算 CPL', () => {
            result = calculate_cpl(Decimal('10000'), 250)
            expect(result).toBe(Decimal('40.00'))

        it('零转化返回 None', () => {
            result = calculate_cpl(Decimal('10000'), 0)
            expect(result).toBeNone()

        it('低量标记', () => {
            result = calculate_cpl(Decimal('100'), 3)
            expect(result).toBe(Decimal('33.33'))
            # 前端应显示 "(低量)"

    describe('is_abnormal_project', () => {
        it('CPL 超标 30% 判定为异常', () => {
            result = is_abnormal_project(Decimal('45.5'), Decimal('35'))
            expect(result).toBe(True)

        it('CPL 正常不判定为异常', () => {
            result = is_abnormal_project(Decimal('40'), Decimal('35'))
            expect(result).toBe(False)

    describe('analyze_trend', () => {
        it('上升趋势识别', () => {
            points = [
                {'date': '2025-12-01', 'spend': 100},
                {'date': '2025-12-07', 'spend': 120},
            ]
            result = analyze_trend(points)
            expect(result['trend']).toBe('up')
})
```

### 7.2 集成测试

```python
describe('GET /api/v1/dashboard/overview', () => {

    it('ceo 可获取全公司数据', async () => {
        response = await request(app)
            .get('/api/v1/dashboard/overview')
            .set('Authorization', f'Bearer {ceo_token}')
            .query({'date_from': '2025-12-01', 'date_to': '2025-12-23'})

        expect(response.status).toBe(200)
        expect(response.body.data.total_spend).toBeGreaterThanOrEqual(0)
        expect(response.body.data.active_projects).toBeGreaterThanOrEqual(0)

    it('pitcher 只能看自己数据', async () => {
        response = await request(app)
            .get('/api/v1/dashboard/overview')
            .set('Authorization', f'Bearer {pitcher_token}')

        expect(response.status).toBe(200)
        # 数据应已过滤

    it('未登录返回 401', async () => {
        response = await request(app)
            .get('/api/v1/dashboard/overview')

        expect(response.status).toBe(401)
})

describe('GET /dashboards/ceo/summary', () => {

    it('ceo 可访问', async () => {
        response = await request(app)
            .get('/dashboards/ceo/summary')
            .set('Authorization', f'Bearer {ceo_token}')

        expect(response.status).toBe(200)

    it('pitcher 不能访问 CEO 驾驶舱', async () => {
        response = await request(app)
            .get('/dashboards/ceo/summary')
            .set('Authorization', f'Bearer {pitcher_token}')

        expect(response.status).toBe(403)
        expect(response.body.detail.code).toBe('AUTH_500')
})
```

### 7.3 权限测试矩阵

```python
test_cases = [
    # [角色, 端点, 预期结果]
    ['ceo', '/dashboard/overview', 200],
    ['ceo', '/dashboards/ceo/summary', 200],
    ['admin', '/dashboard/overview', 200],
    ['admin', '/dashboards/ceo/summary', 200],
    ['finance', '/dashboard/overview', 200],
    ['finance', '/dashboards/ceo/summary', 403],  # 仅 admin/ceo
    ['pitcher', '/dashboard/overview', 200],  # 看自己数据
    ['pitcher', '/dashboards/ceo/summary', 403],
]

@pytest.mark.parametrize("role,endpoint,expected", test_cases)
def test_permissions(role, endpoint, expected):
    response = execute_request(role, endpoint)
    assert response.status == expected
```

---

## §8 性能要求

### 8.1 响应时间要求

| API | 目标 | 最大容忍 |
|-----|------|----------|
| /dashboard/overview | < 200ms | < 500ms |
| /dashboard/trend | < 300ms | < 800ms |
| /dashboard/top-projects | < 200ms | < 500ms |
| /dashboard/pending-counts | < 100ms | < 300ms |
| /dashboards/ceo/summary | < 300ms | < 800ms |
| /dashboards/ceo/detail | < 500ms | < 1s |

### 8.2 索引要求

必须为以下查询场景建立索引:

| 表 | 索引 | 用途 |
|---|------|------|
| daily_reports | (report_date) | 日期范围查询 |
| daily_reports | (status) | 状态筛选 |
| daily_reports | (ad_account_id, report_date) | 账户+日期聚合 |
| projects | (status) | 活跃项目统计 |
| topup_requests | (status) | 待处理统计 |

### 8.3 缓存策略

```python
# Redis 缓存配置
CACHE_CONFIG = {
    'dashboard_overview': {
        'ttl': 300,  # 5 分钟
        'key_pattern': 'dashboard:overview:{user_id}:{date_from}:{date_to}'
    },
    'dashboard_trend': {
        'ttl': 600,  # 10 分钟
        'key_pattern': 'dashboard:trend:{date_from}:{date_to}'
    },
    'pending_counts': {
        'ttl': 60,  # 1 分钟
        'key_pattern': 'dashboard:pending:{user_id}'
    }
}
```

---

## §9 安全规范

### 9.1 认证授权

- 所有 API 需要 JWT Token
- 每个 API 校验角色权限
- CEO 驾驶舱需要特殊权限检查
- 数据按角色过滤

### 9.2 输入验证

- [ ] 日期格式验证 (YYYY-MM-DD)
- [ ] 日期范围验证 (end >= start)
- [ ] 日期跨度限制 (≤ 365 天)
- [ ] top_n 参数范围验证 (1-20)

### 9.3 审计日志

| 操作 | 记录内容 |
|------|----------|
| 访问驾驶舱 | 用户ID、角色、时间、IP |
| 导出数据 | 用户ID、导出范围、时间 |

---

## 附录 A: 现有实现与目标对比

### A.1 当前实现状态

**已实现 (dashboard.py)**:

| 端点 | 功能 | Schema |
|------|------|--------|
| GET /dashboards/ceo/summary | CEO 汇总 | CEODashboardSummary |
| GET /dashboards/ceo/detail | CEO 详情 + Top N | CEODashboardDetail |

**现有 Schema**:
- `AlertItem`: 告警项
- `CEODashboardSummary`: 汇总数据
- `ProjectRankingItem`: 项目排名
- `CEODashboardDetail`: 详情数据

### A.2 目标实现

**需要新增/调整**:

| 端点 | 动作 | 说明 |
|------|------|------|
| /api/v1/dashboard/overview | 新增别名 | 映射到现有 /dashboards/ceo/summary |
| /api/v1/dashboard/trend | 新增 | 趋势数据专用端点 |
| /api/v1/dashboard/top-projects | 新增 | 拆分自 /dashboards/ceo/detail |
| /api/v1/dashboard/pending-counts | 新增 | 待处理计数专用端点 |

### A.3 迁移计划

1. **Phase 1**: 保持现有 /dashboards/* 端点
2. **Phase 2**: 新增 /dashboard/* 端点 (对齐前端)
3. **Phase 3**: 前端切换到新端点
4. **Phase 4**: 废弃旧端点

---

## 附录 B: AI 代码工厂禁止行为清单

### B.1 禁止行为

| 禁止行为 | 正确做法 | 检查方式 |
|---------|---------|---------|
| 硬编码权限列表 | 使用 role_in_list() | 代码审查 |
| 跳过数据过滤 | 按角色过滤数据 | 代码审查 |
| 直接返回全部数据 | 检查用户权限后返回 | 代码审查 |
| 使用浮点计算金额 | 使用 Decimal | 类型检查 |
| 自定义错误码 | 使用 ERROR_CODES_SOT.md | grep 检查 |
| Phase 1 自动阻断 | 仅记录+提示 | 逻辑审查 |

### B.2 SoT 追溯验证 Checklist

- [ ] 必须字段来自 MASTER.md §6.5
- [ ] CPL 计算公式来自 §4.5.1
- [ ] 毛利公式来自 §4.5.4
- [ ] 异常判定标准来自 §4.5.2
- [ ] 角色来自 MASTER.md v4.4 §2.4 (7 个)
- [ ] 错误码来自 ERROR_CODES_SOT.md
- [ ] 金额字段使用 Decimal 类型

---

## 源码位置

| 层 | 文件路径 | 状态 |
|----|---------|------|
| Router | `backend/routers/dashboard.py` | ✅ 已实现 |
| Service | `backend/services/dashboard_service.py` | ❌ 待创建 |
| Schema | `backend/routers/dashboard.py` (内嵌) | ⚠️ 建议拆分 |
| Test | `backend/tests/routers/test_dashboard.py` | ❌ 待创建 |

**前端对接文件**:
| 文件 | 路径 |
|------|------|
| Types | `frontend/src/features/dashboard/types/dashboard.types.ts` |
| API Service | `frontend/src/features/dashboard/services/dashboardApi.ts` |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-23 | 初始版本 |

---

**维护者**: AI 广告代投系统开发团队
**关联文档**:
- A1-dashboard.md (前端规格书)
- MASTER.md v4.4 §6.5 (必须字段)
- dashboard.types.ts (前端类型定义)
