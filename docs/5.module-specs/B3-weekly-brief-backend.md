# B3 周度简报 - 后端模块规格书

> **版本**: v1.1
> **更新日期**: 2025-12-24
> **SoT 基准**: DATA_SCHEMA.md v5.3, STATE_MACHINE.md v2.7, API_SOT.md v9.3
> **对应前端规格书**: B3-weekly-brief.md

---

## §1 模块概述

### 1.1 业务目标
提供周度简报管理功能，支持投手按周汇总项目数据、填写工作总结，便于主管/项目负责人/CEO 掌握周级投放效果和团队动态。

### 1.2 涉及角色
| 角色 | 系统角色名 | 本模块权限 |
|------|------------|------------|
| 老板 | ceo | 查看所有周报、导出 |
| 项目负责人 | project_owner | 查看项目内周报、统计 |
| 主管 | supervisor | 查看下属周报、提醒 |
| 投手 | pitcher | 创建/编辑/提交自己的周报 |
| 财务 | finance | 只读查看 |
| 户管 | account_manager | 无权限 |
| 管理员 | admin | 系统配置 |

### 1.3 模块边界
**本模块负责：**
- 周报 CRUD（创建、读取、更新、删除）
- 周报提交（draft → submitted）
- 周数据自动汇总（消耗、进粉、CPL）
- 周报统计信息（提交率、总消耗等）
- 周报列表查询与筛选

**本模块不负责：**
- 日报管理（由 B1/B2 日报模块负责）
- 月度结算（由 E1 月度结算模块负责）
- 项目管理（由 D1 项目管理模块负责）

### 1.4 SoT 引用清单 (AI 防幻觉)
| SoT 文档 | 版本 | 引用章节 | 用途 |
|---------|------|---------|------|
| DATA_SCHEMA.md | v5.3 | §3.4 weekly_briefs | 表结构、字段定义 |
| STATE_MACHINE.md | v2.7 | §13.2 周报状态机 | 2 状态机定义 (draft → submitted) |
| BUSINESS_RULES.md | v4.1 | BR-WB-* | 周报业务规则 |
| ERROR_CODES_SOT.md | v2.1 | VALIDATION_*, BIZ_*, AUTH_* | 错误码 |
| API_SOT.md | v9.3 | §weekly-briefs | API 规范 |
| AUTH_SPEC.md | v2.0 | §4.7 | 权限矩阵 |
| MASTER.md | v4.4 | §4.5.1 | CPL 计算公式 |

---

## §2 数据模型

### 2.1 表结构定义
**来源**: DATA_SCHEMA.md v5.3, B3-weekly-brief.md §2.1

```sql
CREATE TABLE weekly_briefs (
  -- 主键
  id              SERIAL PRIMARY KEY,

  -- 业务字段
  project_id      INTEGER NOT NULL REFERENCES projects(id),
  week_start      DATE NOT NULL,               -- 周一日期
  week_end        DATE NOT NULL,               -- 周日日期
  submitter_id    UUID NOT NULL REFERENCES users(id),

  -- 自动汇总字段 (从 daily_reports 计算)
  weekly_spend        DECIMAL(14,2) NOT NULL DEFAULT 0,  -- 周消耗
  weekly_conversions  INTEGER NOT NULL DEFAULT 0,        -- 周进粉
  weekly_cpl          DECIMAL(10,2),                     -- 周 CPL

  -- 文本字段
  achievements        TEXT,                    -- 本周成果
  issues              TEXT,                    -- 遇到问题
  solutions           TEXT,                    -- 解决方案
  next_week_plan      TEXT,                    -- 下周计划

  -- 状态字段
  status          VARCHAR(32) NOT NULL DEFAULT 'draft',
  submitted_at    TIMESTAMPTZ,               -- 提交时间

  -- 审计字段
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- 约束
  CONSTRAINT chk_weekly_spend CHECK (weekly_spend >= 0),
  CONSTRAINT chk_weekly_conversions CHECK (weekly_conversions >= 0),
  CONSTRAINT chk_status CHECK (status IN ('draft', 'submitted')),
  CONSTRAINT uq_project_week UNIQUE (project_id, week_start, submitter_id)
);

-- 索引
CREATE INDEX idx_weekly_briefs_project ON weekly_briefs(project_id);
CREATE INDEX idx_weekly_briefs_week ON weekly_briefs(week_start);
CREATE INDEX idx_weekly_briefs_submitter ON weekly_briefs(submitter_id);
CREATE INDEX idx_weekly_briefs_status ON weekly_briefs(status);
```

### 2.2 字段说明
| 字段 | 类型 | 必填 | 说明 | 验证规则 |
|------|------|------|------|----------|
| id | INTEGER | 自动 | 主键 | 系统生成 |
| project_id | INTEGER | ✅ | 项目 ID | 必须存在且用户有权限 |
| week_start | DATE | ✅ | 周一日期 | 必须是周一 |
| week_end | DATE | ✅ | 周日日期 | 自动计算 = week_start + 6 |
| submitter_id | UUID | ✅ | 提交人 ID | 当前用户 |
| weekly_spend | DECIMAL(14,2) | 自动 | 周消耗 | 从 daily_reports 汇总 |
| weekly_conversions | INTEGER | 自动 | 周进粉 | 从 daily_reports 汇总 |
| weekly_cpl | DECIMAL(10,2) | 自动 | 周 CPL | spend/conversions |
| achievements | TEXT | ❌ | 本周成果 | 最大 2000 字符 |
| issues | TEXT | ❌ | 遇到问题 | 最大 2000 字符 |
| solutions | TEXT | ❌ | 解决方案 | 最大 2000 字符 |
| next_week_plan | TEXT | ❌ | 下周计划 | 最大 2000 字符 |
| status | VARCHAR | 自动 | 状态 | draft / submitted |
| submitted_at | TIMESTAMPTZ | ❌ | 提交时间 | 提交时自动填充 |

### 2.3 索引设计
| 索引名 | 字段 | 类型 | 用途 |
|--------|------|------|------|
| idx_weekly_briefs_project | project_id | B-tree | 按项目查询 |
| idx_weekly_briefs_week | week_start | B-tree | 按周次查询 |
| idx_weekly_briefs_submitter | submitter_id | B-tree | 按提交人查询 |
| idx_weekly_briefs_status | status | B-tree | 按状态筛选 |
| uq_project_week | (project_id, week_start, submitter_id) | Unique | 唯一性约束 |

### 2.4 关联关系
```
weekly_briefs
    ├──→ projects (project_id → id) 多对一
    └──→ users (submitter_id → id) 多对一

聚合数据来源:
    daily_reports → weekly_briefs (按周汇总)
```

---

## §3 API 设计

### 3.1 端点清单
**来源**: API_SOT.md v9.3, B3-weekly-brief.md §4.2

| 方法 | 端点 | 描述 | 权限 |
|------|------|------|------|
| GET | /api/v1/weekly-briefs | 周报列表 | 登录用户 |
| GET | /api/v1/weekly-briefs/stats | 统计信息 | 登录用户 |
| GET | /api/v1/weekly-briefs/:id | 周报详情 | 数据所有者/上级 |
| POST | /api/v1/weekly-briefs | 创建周报 | pitcher |
| PUT | /api/v1/weekly-briefs/:id | 更新周报 | 数据所有者(draft) |
| DELETE | /api/v1/weekly-briefs/:id | 删除周报 | 数据所有者(draft) |
| POST | /api/v1/weekly-briefs/:id/submit | 提交周报 | 数据所有者 |
| GET | /api/v1/weekly-briefs/projects/:project_id/weekly-summary | 项目周数据汇总 | 项目成员 |

### 3.2 请求/响应格式

**列表查询参数** (GET /weekly-briefs):
```typescript
interface WeeklyBriefListParams {
  week?: string;              // 周次 (如 "2025-W51")
  week_start?: string;        // 周开始日期 (YYYY-MM-DD)
  project_id?: number;        // 项目 ID
  status?: 'draft' | 'submitted';  // 状态筛选
  page?: number;              // 页码，默认 1
  page_size?: number;         // 每页数量，默认 20
}
```

**创建请求** (POST /weekly-briefs):
```typescript
interface CreateWeeklyBriefRequest {
  project_id: number;         // 必填，项目 ID
  week_start: string;         // 必填，周一日期 (YYYY-MM-DD)
  achievements?: string;      // 本周成果
  issues?: string;            // 遇到问题
  solutions?: string;         // 解决方案
  next_week_plan?: string;    // 下周计划
}
```

**更新请求** (PUT /weekly-briefs/:id):
```typescript
interface UpdateWeeklyBriefRequest {
  achievements?: string;
  issues?: string;
  solutions?: string;
  next_week_plan?: string;
}
```

**周报响应**:
```typescript
interface WeeklyBriefResponse {
  id: number;
  project_id: number;
  project_name: string;           // JOIN projects
  week_start: string;             // YYYY-MM-DD
  week_end: string;               // YYYY-MM-DD
  week_label: string;             // 如 "2025年第51周"
  submitter_id: string;
  submitter_name: string;         // JOIN users
  status: 'draft' | 'submitted';
  weekly_spend: number;           // 自动汇总
  weekly_conversions: number;     // 自动汇总
  weekly_cpl: number | null;      // 计算值
  cpl_trend: number | null;       // 环比变化 (%)
  achievements: string | null;
  issues: string | null;
  solutions: string | null;
  next_week_plan: string | null;
  submitted_at: string | null;
  created_at: string;
  updated_at: string;
}
```

**列表响应**:
```typescript
interface WeeklyBriefListResponse {
  items: WeeklyBriefResponse[];
  total: number;
  page: number;
  page_size: number;
  stats?: WeeklyBriefStats;
}
```

**统计响应** (GET /weekly-briefs/stats):
```typescript
interface WeeklyBriefStats {
  total_projects: number;      // 本周项目总数
  submitted_count: number;     // 已提交数
  draft_count: number;         // 草稿数
  submission_rate: number;     // 提交率 (%)
  total_weekly_spend: number;  // 本周总消耗
}
```

**周数据汇总响应** (GET /projects/:project_id/weekly-summary):
```typescript
interface WeeklySummaryResponse {
  project_id: number;
  project_name: string;
  week_start: string;
  week_end: string;
  weekly_spend: number;
  weekly_conversions: number;
  weekly_cpl: number | null;
  target_cpl: number | null;
  cpl_vs_target: number | null;   // CPL vs 目标 (%)
  last_week?: {
    spend: number;
    conversions: number;
    cpl: number;
  } | null;
  trends?: {
    spend_change: number;         // 消耗环比 (%)
    conversions_change: number;   // 进粉环比 (%)
    cpl_change: number;           // CPL 环比 (%)
  } | null;
  daily_breakdown?: Array<{
    date: string;
    spend: number;
    conversions: number;
  }>;
}
```

### 3.3 错误码定义
**来源**: ERROR_CODES_SOT.md v2.1

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| VALIDATION_001 | 400 | 必填字段缺失 |
| VALIDATION_002 | 400 | 格式无效 (week_start 必须是周一) |
| BIZ_003 | 409 | 资源已存在 (同一项目同一周已存在周报) |
| BIZ_002 | 404 | 资源不存在 (周报不存在) |
| BIZ_301 | 400 | 状态转换不允许 (周报已提交，不可修改) |
| AUTH_400 | 401 | 未提供认证令牌 |
| AUTH_500 | 403 | 权限不足 (非周报所有者，无权操作) |
| SYS_001 | 500 | 系统内部错误 |

### 3.4 分页/筛选规范
```yaml
分页:
  页码: 从 1 开始
  默认每页: 20 条
  最大每页: 100 条

筛选:
  周次: week 参数 (ISO 周格式 YYYY-Wxx)
  项目: project_id
  状态: status (draft, submitted)

排序:
  默认: week_start DESC, created_at DESC
```

---

## §4 权限控制

### 4.1 角色权限矩阵 (7 角色)
**来源**: AUTH_SPEC.md v2.0, MASTER.md v4.4 §2.4

| 操作 | ceo | project_owner | finance | supervisor | pitcher | account_manager | admin |
|------|-----|---------------|---------|------------|---------|-----------------|-------|
| 查看所有 | ✅ | ❌ | ✅(只读) | ❌ | ❌ | ❌ | ✅ |
| 查看项目内 | ✅ | ✅ | ✅ | ✅(下属) | ❌ | ❌ | ✅ |
| 查看自己 | N/A | N/A | N/A | ✅ | ✅ | ❌ | ✅ |
| 创建 | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| 编辑(draft) | ❌ | ❌ | ❌ | ❌ | ✅(自己) | ❌ | ❌ |
| 删除(draft) | ❌ | ❌ | ❌ | ❌ | ✅(自己) | ❌ | ❌ |
| 提交 | ❌ | ❌ | ❌ | ❌ | ✅(自己) | ❌ | ❌ |
| 统计 | ✅ | ✅(项目) | ✅ | ✅(下属) | ❌ | ❌ | ✅ |
| 导出 | ✅ | ✅(项目) | ✅ | ❌ | ❌ | ❌ | ✅ |

### 4.2 数据权限规则
```python
def can_access_weekly_brief(user: User, brief: WeeklyBrief) -> bool:
    # CEO 可以看所有
    if user.role == 'ceo':
        return True

    # Admin 可以看所有
    if user.role == 'admin':
        return True

    # 财务可以只读查看所有
    if user.role == 'finance':
        return True

    # 数据所有者可以看
    if brief.submitter_id == user.id:
        return True

    # 项目负责人可以看项目内的
    if user.role == 'project_owner':
        return is_project_owner(user.id, brief.project_id)

    # 主管可以看下属的
    if user.role == 'supervisor':
        return is_subordinate(user.id, brief.submitter_id)

    return False

def can_edit_weekly_brief(user: User, brief: WeeklyBrief) -> bool:
    # 只有所有者可以编辑
    if brief.submitter_id != user.id:
        return False

    # 只有 draft 状态可以编辑
    if brief.status != 'draft':
        return False

    return True
```

### 4.3 字段级权限
| 字段 | 创建时 | 所有者编辑 | 上级查看 |
|------|--------|------------|----------|
| project_id | ✅ 必填 | ❌ 不可改 | ✅ |
| week_start | ✅ 必填 | ❌ 不可改 | ✅ |
| achievements | ❌ 可选 | ✅ 可改(draft) | ✅ |
| issues | ❌ 可选 | ✅ 可改(draft) | ✅ |
| solutions | ❌ 可选 | ✅ 可改(draft) | ✅ |
| next_week_plan | ❌ 可选 | ✅ 可改(draft) | ✅ |
| status | ❌ 系统控制 | ❌ | ✅ |
| weekly_spend | ❌ 自动计算 | ❌ | ✅ |
| weekly_conversions | ❌ 自动计算 | ❌ | ✅ |
| weekly_cpl | ❌ 自动计算 | ❌ | ✅ |

---

## §5 业务逻辑

### 5.1 状态机定义
**来源**: STATE_MACHINE.md v2.7 §12, B3-weekly-brief.md §2.5

```
                    ┌─────────┐
                    │  draft  │
                    └────┬────┘
                         │ submit
                         ↓
                   ┌───────────┐
                   │ submitted │ (终态)
                   └───────────┘
```

**状态转换表**:
| 当前状态 | 目标状态 | 触发条件 | 操作者 | 验证规则 |
|----------|----------|----------|--------|----------|
| draft | submitted | POST /:id/submit | pitcher(所有者) | 无强制验证 |
| draft | [删除] | DELETE /:id | pitcher(所有者) | 无 |

**Phase 1 规则**:
- ❌ 禁止: 强制要求填写 achievements/issues 等字段
- ❌ 禁止: 自动阻断空字段提交
- ✅ 允许: 提示未填写字段（前端高亮）
- ✅ 允许: 记录提交时间

### 5.2 验证规则 (Zod Schema)
```typescript
const createSchema = z.object({
  project_id: z.number()
    .int('项目 ID 必须是整数')
    .positive('项目 ID 必须为正数'),

  week_start: z.string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, '日期格式必须是 YYYY-MM-DD')
    .refine(date => {
      const d = new Date(date);
      return d.getDay() === 1; // 必须是周一
    }, 'week_start 必须是周一'),

  achievements: z.string()
    .max(2000, '本周成果最多 2000 字符')
    .optional(),

  issues: z.string()
    .max(2000, '遇到问题最多 2000 字符')
    .optional(),

  solutions: z.string()
    .max(2000, '解决方案最多 2000 字符')
    .optional(),

  next_week_plan: z.string()
    .max(2000, '下周计划最多 2000 字符')
    .optional(),
});
```

### 5.3 计算逻辑

**周数据汇总**:
```python
def calculate_weekly_summary(project_id: int, week_start: date, week_end: date) -> dict:
    """从 daily_reports 汇总周数据"""
    # 查询该周的日报数据
    daily_data = db.query(
        func.sum(DailyReport.spend).label('total_spend'),
        func.sum(DailyReport.conversions).label('total_conversions')
    ).filter(
        DailyReport.project_id == project_id,
        DailyReport.date >= week_start,
        DailyReport.date <= week_end
    ).first()

    spend = daily_data.total_spend or 0
    conversions = daily_data.total_conversions or 0

    return {
        'weekly_spend': spend,
        'weekly_conversions': conversions,
        'weekly_cpl': round(spend / conversions, 2) if conversions > 0 else None
    }
```

**CPL 计算** (来源: MASTER.md §4.5.1):
```python
def calculate_cpl(spend: Decimal, conversions: int) -> Decimal | None:
    """CPL = 消耗 / 进粉数"""
    if conversions == 0:
        return None
    return round(spend / conversions, 2)
```

**CPL 环比变化**:
```python
def calculate_cpl_trend(current_cpl: Decimal, last_week_cpl: Decimal) -> float | None:
    """CPL 环比 = (本周CPL - 上周CPL) / 上周CPL × 100%"""
    if last_week_cpl is None or last_week_cpl == 0:
        return None
    return round((current_cpl - last_week_cpl) / last_week_cpl * 100, 2)
```

**周标签生成**:
```python
def generate_week_label(week_start: date) -> str:
    """生成周标签，如 '2025年第51周'"""
    year, week_num, _ = week_start.isocalendar()
    return f"{year}年第{week_num}周"
```

### 5.4 业务约束 + Phase 1 规则

```yaml
约束规则:
  日期约束:
    - week_start 必须是周一
    - week_end 自动计算 = week_start + 6 天

  唯一性约束:
    - 同一用户同一项目同一周只能有一条周报
    - 违反时返回 WB_DUPLICATE_ENTRY

  状态约束:
    - 只有 draft 状态可以编辑/删除
    - submitted 是终态，不可回退

  数据自动汇总:
    - 创建周报时自动从 daily_reports 汇总周数据
    - 提交前重新计算确保数据最新

Phase 1 规则 (照亮阶段):
  ❌ 禁止: 强制填写所有文本字段
  ❌ 禁止: 周报未提交阻断日报提交
  ❌ 禁止: 自动催交或惩罚机制
  ✅ 允许: 提示本周有项目未提交周报
  ✅ 允许: 高亮显示草稿状态周报
  ✅ 允许: 统计提交率，供管理参考
```

---

## §6 前后端接口契约

### 6.1 字段映射
| 后端字段 (snake_case) | 前端字段 (camelCase) | 说明 |
|----------------------|---------------------|------|
| project_id | projectId | 整数 |
| week_start | weekStart | YYYY-MM-DD 字符串 |
| week_end | weekEnd | YYYY-MM-DD 字符串 |
| week_label | weekLabel | 如 "2025年第51周" |
| submitter_id | submitterId | UUID 字符串 |
| submitter_name | submitterName | 字符串 |
| weekly_spend | weeklySpend | 数字 |
| weekly_conversions | weeklyConversions | 整数 |
| weekly_cpl | weeklyCpl | 数字或 null |
| cpl_trend | cplTrend | 数字或 null |
| next_week_plan | nextWeekPlan | 字符串或 null |
| submitted_at | submittedAt | ISO 8601 或 null |
| created_at | createdAt | ISO 8601 字符串 |
| updated_at | updatedAt | ISO 8601 字符串 |

### 6.2 枚举值对照
```typescript
// 后端和前端使用相同的值
type WeeklyBriefStatus = 'draft' | 'submitted';

// 前端中文映射
const STATUS_LABELS: Record<WeeklyBriefStatus, string> = {
  draft: '草稿',
  submitted: '已提交',
};

const STATUS_COLORS: Record<WeeklyBriefStatus, string> = {
  draft: 'gray',      // 灰色
  submitted: 'green', // 绿色
};
```

### 6.3 时区/格式约定
```yaml
时间格式:
  日期: YYYY-MM-DD (不含时区)
  时间戳: ISO 8601 (含时区，如 2024-12-23T10:00:00Z)

时区处理:
  存储: UTC
  传输: UTC
  显示: 前端转换为本地时区

数字格式:
  金额: 数字类型，保留2位小数
  百分比: 数字类型，如 12.34 表示 12.34%

空值:
  null: 表示无值/未知
  0: 表示实际值为零
```

---

## §7 测试要点

### 7.1 单元测试
```python
class TestWeeklyBriefService:
    def test_create_weekly_brief(self):
        """测试创建周报"""
        brief = service.create_weekly_brief(
            project_id=1,
            week_start=date(2025, 12, 23),  # 周一
            submitter_id=user_id
        )
        assert brief.status == 'draft'
        assert brief.week_end == date(2025, 12, 29)

    def test_create_duplicate_rejected(self):
        """测试重复创建被拒绝"""
        service.create_weekly_brief(project_id=1, week_start=date(2025, 12, 23), ...)
        with pytest.raises(DuplicateEntryError):
            service.create_weekly_brief(project_id=1, week_start=date(2025, 12, 23), ...)

    def test_week_start_must_be_monday(self):
        """测试 week_start 必须是周一"""
        with pytest.raises(ValidationError):
            service.create_weekly_brief(
                project_id=1,
                week_start=date(2025, 12, 24),  # 周二
                ...
            )

    def test_submit_changes_status(self):
        """测试提交改变状态"""
        brief = service.create_weekly_brief(...)
        result = service.submit_weekly_brief(brief.id, user_id)
        assert result.status == 'submitted'
        assert result.submitted_at is not None

    def test_cannot_edit_submitted(self):
        """测试已提交不能编辑"""
        brief = service.create_weekly_brief(...)
        service.submit_weekly_brief(brief.id, user_id)
        with pytest.raises(InvalidStateError):
            service.update_weekly_brief(brief.id, {'achievements': 'new'}, user_id)

class TestWeeklySummaryCalculation:
    def test_calculate_weekly_summary(self):
        """测试周数据汇总"""
        # 准备日报数据
        create_daily_report(date=date(2025, 12, 23), spend=1000, conversions=10)
        create_daily_report(date=date(2025, 12, 24), spend=1500, conversions=15)

        summary = service.calculate_weekly_summary(
            project_id=1,
            week_start=date(2025, 12, 23),
            week_end=date(2025, 12, 29)
        )

        assert summary['weekly_spend'] == 2500
        assert summary['weekly_conversions'] == 25
        assert summary['weekly_cpl'] == 100.0

    def test_cpl_with_zero_conversions(self):
        """测试零转化时 CPL 为 null"""
        summary = service.calculate_weekly_summary(...)
        assert summary['weekly_cpl'] is None
```

### 7.2 集成测试
```python
class TestWeeklyBriefAPI:
    def test_list_weekly_briefs(self):
        """测试列表查询"""
        response = client.get(
            '/api/v1/weekly-briefs',
            params={'week': '2025-W51'},
            headers={'Authorization': f'Bearer {pitcher_token}'}
        )
        assert response.status_code == 200
        assert 'items' in response.json()
        assert 'stats' in response.json()

    def test_create_weekly_brief(self):
        """测试创建周报"""
        response = client.post(
            '/api/v1/weekly-briefs',
            json={
                'project_id': 1,
                'week_start': '2025-12-23',
                'achievements': '完成投放优化'
            },
            headers={'Authorization': f'Bearer {pitcher_token}'}
        )
        assert response.status_code == 201
        assert response.json()['data']['status'] == 'draft'

    def test_submit_weekly_brief(self):
        """测试提交周报"""
        # 先创建
        create_response = client.post('/api/v1/weekly-briefs', ...)
        brief_id = create_response.json()['data']['id']

        # 再提交
        response = client.post(
            f'/api/v1/weekly-briefs/{brief_id}/submit',
            headers={'Authorization': f'Bearer {pitcher_token}'}
        )
        assert response.status_code == 200
        assert response.json()['data']['status'] == 'submitted'

    def test_non_owner_cannot_edit(self):
        """测试非所有者不能编辑"""
        response = client.put(
            f'/api/v1/weekly-briefs/{brief_id}',
            json={'achievements': 'hacked'},
            headers={'Authorization': f'Bearer {other_user_token}'}
        )
        assert response.status_code == 403
```

### 7.3 权限测试矩阵
```python
permission_test_cases = [
    # [角色, 操作, 预期结果]
    ('ceo', 'list_all', 200),
    ('ceo', 'view_any', 200),
    ('ceo', 'create', 403),
    ('project_owner', 'list_project', 200),
    ('project_owner', 'view_project_brief', 200),
    ('project_owner', 'create', 403),
    ('supervisor', 'list_subordinates', 200),
    ('supervisor', 'view_subordinate_brief', 200),
    ('supervisor', 'create', 403),
    ('pitcher', 'list_own', 200),
    ('pitcher', 'create', 201),
    ('pitcher', 'edit_own_draft', 200),
    ('pitcher', 'edit_own_submitted', 403),
    ('pitcher', 'submit_own', 200),
    ('pitcher', 'view_others', 403),
    ('finance', 'list_all', 200),
    ('finance', 'create', 403),
    ('account_manager', 'list', 403),
]

@pytest.mark.parametrize('role,action,expected', permission_test_cases)
def test_permissions(role, action, expected):
    response = execute_action(role, action)
    assert response.status_code == expected
```

---

## §8 性能要求

### 8.1 响应时间要求
| API | 目标 | 最大容忍 |
|-----|------|----------|
| 列表查询 | < 200ms | < 500ms |
| 详情查询 | < 100ms | < 300ms |
| 创建 | < 300ms | < 1s |
| 提交 | < 300ms | < 1s |
| 统计 | < 300ms | < 800ms |
| 周数据汇总 | < 500ms | < 1s |

### 8.2 索引要求
必须为以下查询场景建立索引：
- 按周次范围查询 (week_start)
- 按项目筛选 (project_id)
- 按提交人查询 (submitter_id)
- 按状态筛选 (status)
- 唯一性约束 (project_id, week_start, submitter_id)

### 8.3 批量操作限制
| 操作 | 单次上限 | 说明 |
|------|----------|------|
| 列表查询 | 100 条/页 | 超出截断 |
| 导出 | 1000 条 | 超出走异步 |

---

## §9 安全规范

### 9.1 认证授权
- 所有 API 需要 JWT Token
- 每个 API 校验角色权限
- 只能访问自己有权限的数据
- 编辑/删除操作需验证所有者

### 9.2 输入验证
- [x] 使用 Pydantic 验证所有输入
- [x] 字符串字段最大 2000 字符
- [x] week_start 必须是有效日期且为周一
- [x] project_id 必须存在且用户有权限

### 9.3 审计日志
必须记录以下操作：
| 操作类型 | 记录内容 |
|----------|----------|
| 创建 | 操作人、时间、项目、周次 |
| 更新 | 操作人、时间、变更字段 |
| 删除 | 操作人、时间、删除内容备份 |
| 提交 | 操作人、时间、周报摘要 |

---

## 附录: AI 代码工厂禁止行为清单

### A.1 禁止行为
| 禁止行为 | 正确做法 | 检查方式 |
|---------|---------|---------|
| 自定义错误码 | 使用 ERROR_CODES_SOT.md | grep 检查 |
| 发明新状态 | 只用 draft/submitted | 枚举对比 |
| 自创字段 | 使用 DATA_SCHEMA.md | Schema 对比 |
| 强制字段验证 | Phase 1 只提示不阻断 | 逻辑审查 |
| 自动催交机制 | 仅记录统计 | 代码审查 |
| 跳过权限检查 | Service 层必须检查 | 代码审查 |

### A.2 SoT 追溯验证 Checklist
生成代码后必须验证：
- [ ] 状态值仅为 draft/submitted
- [ ] 所有字段来自 DATA_SCHEMA.md
- [ ] 所有错误码来自 ERROR_CODES_SOT.md
- [ ] 角色来自 MASTER.md v4.4 §2.4 (7 个)
- [ ] CPL 计算公式来自 MASTER.md §4.5.1
- [ ] 金额字段使用 Decimal 类型
- [ ] 时间字段使用 TIMESTAMPTZ + UTC

---

## 源码位置

| 层 | 文件路径 |
|----|---------|
| Service | `backend/services/weekly_brief_service.py` |
| Router | `backend/routers/weekly_briefs.py` |
| Schema | `backend/schemas/weekly_brief.py` |
| Model | `backend/models/workflow/weekly_brief.py` |
| Test | `backend/tests/services/test_weekly_brief_service.py` |
| 前端类型 | `frontend/src/features/weekly-briefs/types/weeklyBrief.types.ts` |
| 前端 API | `frontend/src/features/weekly-briefs/services/weeklyBriefApi.ts` |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-23 | 初始版本 |

---

**维护者**: AI 广告代投系统开发团队
