# 后端模块规划书编写指南

> **文档定位**: 指导 AI 编写完整、准确的后端模块规划书
> **核心原则**: API 优先 + 数据驱动 + 权限明确 + 可测试

---

## 第一章 规划书结构总览

### 1.1 标准目录结构

```
后端模块规划书
│
├── §1 模块概述
│   ├── 1.1 业务目标
│   ├── 1.2 涉及角色
│   └── 1.3 模块边界
│
├── §2 数据模型
│   ├── 2.1 表结构定义
│   ├── 2.2 字段说明
│   ├── 2.3 索引设计
│   └── 2.4 关联关系
│
├── §3 API 设计
│   ├── 3.1 端点清单
│   ├── 3.2 请求/响应格式
│   ├── 3.3 错误码定义
│   └── 3.4 分页/筛选规范
│
├── §4 权限控制
│   ├── 4.1 角色权限矩阵
│   ├── 4.2 数据权限规则
│   └── 4.3 字段级权限
│
├── §5 业务逻辑
│   ├── 5.1 状态机定义
│   ├── 5.2 验证规则
│   ├── 5.3 计算逻辑
│   └── 5.4 业务约束
│
├── §6 前后端接口契约
│   ├── 6.1 字段映射
│   ├── 6.2 枚举值对照
│   └── 6.3 时区/格式约定
│
└── §7 测试要点
    ├── 7.1 单元测试
    ├── 7.2 集成测试
    └── 7.3 权限测试矩阵
```

### 1.2 命名规范

```
文件命名: {序号}-{模块英文名}.md
示例:
  - B1-daily-report-submit.md      # 日报提交
  - B2-daily-report-review.md      # 日报审核
  - C1-topup-request.md            # 充值申请
  - C2-topup-approve.md            # 充值审批
  - D1-project-management.md       # 项目管理
```

---

## 第二章 各章节编写规范

### §1 模块概述

```markdown
## §1 模块概述

### 1.1 业务目标

{用 1-2 句话描述模块的核心业务目标}

示例：
> 本模块实现投手日报的提交功能，投手每日提交各项目的广告投放数据，
> 系统记录原始数据并触发后续审核流程。

### 1.2 涉及角色

| 角色 | 系统角色名 | 本模块权限 |
|------|------------|------------|
| 投手 | media_buyer | 提交自己的日报 |
| 主管 | data_operator | 查看下属日报 |
| CEO | ceo | 查看所有日报 |

### 1.3 模块边界

**本模块负责：**
- 日报数据的创建和保存
- 日报状态的初始化
- 触发审核流程

**本模块不负责：**
- 日报审核（由 B2 模块负责）
- 数据趋势分析（由 B3 模块负责）
- 财务确认（由 B4 模块负责）

### 1.4 依赖关系

```
上游依赖:
  - 用户模块: 获取投手信息
  - 项目模块: 获取项目信息

下游依赖:
  - 审核模块: 触发审核流程
  - 通知模块: 发送提交通知
```
```

---

### §2 数据模型

```markdown
## §2 数据模型

### 2.1 表结构定义

#### 主表: daily_reports

```sql
CREATE TABLE daily_reports (
  -- 主键
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- 业务字段
  date            DATE NOT NULL,                    -- 日报日期
  project_id      UUID NOT NULL REFERENCES projects(id),
  pitcher_id      UUID NOT NULL REFERENCES users(id),
  
  -- 数据字段
  conversions     INTEGER NOT NULL DEFAULT 0,       -- 进粉数
  spend           DECIMAL(12,2) NOT NULL DEFAULT 0, -- 消耗金额
  impressions     BIGINT DEFAULT 0,                 -- 曝光数
  clicks          INTEGER DEFAULT 0,                -- 点击数
  
  -- 计算字段（可选，也可实时计算）
  cpl             DECIMAL(10,2) GENERATED ALWAYS AS (
                    CASE WHEN conversions > 0 
                    THEN spend / conversions 
                    ELSE NULL END
                  ) STORED,
  
  -- 状态字段
  status          VARCHAR(32) NOT NULL DEFAULT 'draft',
  
  -- 审计字段
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by      UUID REFERENCES users(id),
  updated_by      UUID REFERENCES users(id),
  
  -- 约束
  CONSTRAINT uq_daily_report UNIQUE (date, project_id, pitcher_id),
  CONSTRAINT chk_conversions CHECK (conversions >= 0),
  CONSTRAINT chk_spend CHECK (spend >= 0)
);

-- 索引
CREATE INDEX idx_daily_reports_date ON daily_reports(date);
CREATE INDEX idx_daily_reports_project ON daily_reports(project_id);
CREATE INDEX idx_daily_reports_pitcher ON daily_reports(pitcher_id);
CREATE INDEX idx_daily_reports_status ON daily_reports(status);
CREATE INDEX idx_daily_reports_date_status ON daily_reports(date, status);
```

### 2.2 字段说明

| 字段 | 类型 | 必填 | 说明 | 验证规则 |
|------|------|------|------|----------|
| id | UUID | 自动 | 主键 | 系统生成 |
| date | DATE | ✅ | 日报日期 | 不能是未来日期 |
| project_id | UUID | ✅ | 项目ID | 必须是有效项目 |
| pitcher_id | UUID | ✅ | 投手ID | 必须是当前用户或下属 |
| conversions | INTEGER | ✅ | 进粉数 | ≥ 0 |
| spend | DECIMAL | ✅ | 消耗金额 | ≥ 0, 最多2位小数 |
| status | VARCHAR | 自动 | 状态 | 见状态机定义 |

### 2.3 索引设计

| 索引名 | 字段 | 类型 | 用途 |
|--------|------|------|------|
| idx_daily_reports_date | date | B-tree | 按日期查询 |
| idx_daily_reports_project | project_id | B-tree | 按项目查询 |
| idx_daily_reports_pitcher | pitcher_id | B-tree | 按投手查询 |
| idx_daily_reports_status | status | B-tree | 按状态筛选 |
| idx_daily_reports_date_status | date, status | B-tree | 复合查询 |

### 2.4 关联关系

```
daily_reports
    │
    ├──→ projects (project_id → id)
    │       └── 多对一: 一个日报属于一个项目
    │
    ├──→ users (pitcher_id → id)
    │       └── 多对一: 一个日报属于一个投手
    │
    └──→ daily_report_details (id → daily_report_id)
            └── 一对多: 一个日报可有多个明细
```
```

---

### §3 API 设计

```markdown
## §3 API 设计

### 3.1 端点清单

| 方法 | 端点 | 描述 | 权限 |
|------|------|------|------|
| GET | /api/v1/daily-reports | 获取日报列表 | 登录用户 |
| GET | /api/v1/daily-reports/:id | 获取日报详情 | 数据所有者/上级 |
| POST | /api/v1/daily-reports | 创建日报 | pitcher |
| PATCH | /api/v1/daily-reports/:id | 更新日报 | 数据所有者 |
| DELETE | /api/v1/daily-reports/:id | 删除日报 | 数据所有者(draft状态) |
| POST | /api/v1/daily-reports/:id/submit | 提交日报 | 数据所有者 |

### 3.2 请求/响应格式

#### GET /api/v1/daily-reports

**请求参数 (Query)**
```typescript
interface ListDailyReportsQuery {
  // 分页
  page?: number;          // 页码，默认 1
  page_size?: number;     // 每页数量，默认 20，最大 100
  
  // 筛选
  date_from?: string;     // 开始日期 (YYYY-MM-DD)
  date_to?: string;       // 结束日期 (YYYY-MM-DD)
  project_id?: string;    // 项目ID
  pitcher_id?: string;    // 投手ID
  status?: string;        // 状态，多个用逗号分隔
  
  // 排序
  sort_by?: 'date' | 'created_at' | 'spend';  // 排序字段
  sort_order?: 'asc' | 'desc';                 // 排序方向
}
```

**响应格式**
```typescript
interface ListDailyReportsResponse {
  items: DailyReport[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

interface DailyReport {
  id: string;
  date: string;           // YYYY-MM-DD
  project: {
    id: string;
    name: string;
  };
  pitcher: {
    id: string;
    name: string;
  };
  conversions: number;
  spend: number;          // 字符串或数字，保留2位小数
  cpl: number | null;
  status: DailyReportStatus;
  created_at: string;     // ISO 8601
  updated_at: string;     // ISO 8601
}

type DailyReportStatus = 
  | 'draft'
  | 'raw_submitted'
  | 'trend_pending'
  | 'trend_ok'
  | 'trend_flagged'
  | 'final_pending'
  | 'final_confirmed'
  | 'final_locked';
```

#### POST /api/v1/daily-reports

**请求体**
```typescript
interface CreateDailyReportRequest {
  date: string;           // YYYY-MM-DD, 必填
  project_id: string;     // 必填
  conversions: number;    // 必填, ≥ 0
  spend: number;          // 必填, ≥ 0
  impressions?: number;   // 可选
  clicks?: number;        // 可选
}
```

**响应**
```typescript
// 成功: 201 Created
interface CreateDailyReportResponse {
  id: string;
  // ... 完整的 DailyReport 对象
}

// 失败: 400/409/422
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, string[]>;
  };
}
```

#### POST /api/v1/daily-reports/:id/submit

**请求体**: 无

**响应**
```typescript
// 成功: 200 OK
{
  id: string;
  status: 'raw_submitted';
  submitted_at: string;
}

// 失败: 400
{
  error: {
    code: 'INVALID_STATUS_TRANSITION',
    message: '只有 draft 状态的日报可以提交'
  }
}
```

### 3.3 错误码定义

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| VALIDATION_ERROR | 400 | 请求参数验证失败 |
| UNAUTHORIZED | 401 | 未登录 |
| FORBIDDEN | 403 | 无权限 |
| NOT_FOUND | 404 | 资源不存在 |
| DUPLICATE_ENTRY | 409 | 重复记录 |
| INVALID_STATUS_TRANSITION | 400 | 无效的状态转换 |
| FUTURE_DATE_NOT_ALLOWED | 400 | 不允许未来日期 |

### 3.4 分页/筛选规范

```typescript
// 标准分页参数
interface PaginationParams {
  page: number;       // 从 1 开始
  page_size: number;  // 默认 20, 最大 100
}

// 标准分页响应
interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

// 筛选规范
// - 日期范围: date_from, date_to (闭区间)
// - 多值筛选: 用逗号分隔, 如 status=draft,raw_submitted
// - 排序: sort_by + sort_order
```
```

---

### §4 权限控制

```markdown
## §4 权限控制

### 4.1 角色权限矩阵

| 操作 | ceo | finance | supervisor | pitcher | project_owner | account_manager | admin |
|------|-----|---------|------------|---------|---------------|-----------------|-------|
| 查看所有日报 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 查看下属日报 | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| 查看自己日报 | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ |
| 创建日报 | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| 编辑自己日报 | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| 删除自己日报 | ❌ | ❌ | ❌ | ✅* | ❌ | ❌ | ❌ |
| 提交日报 | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |

*注: 只能删除 draft 状态的日报

### 4.2 数据权限规则

```typescript
// 数据权限判断逻辑

function canAccessDailyReport(user: User, report: DailyReport): boolean {
  // CEO 可以看所有
  if (user.role === 'ceo') return true;
  
  // 数据所有者可以看
  if (report.pitcher_id === user.id) return true;
  
  // 主管可以看下属的
  if (user.role === 'data_operator') {
    return isSubordinate(user.id, report.pitcher_id);
  }
  
  // 项目负责人可以看项目内的
  if (user.role === 'project_owner') {
    return isProjectMember(user.id, report.project_id);
  }
  
  return false;
}

function canEditDailyReport(user: User, report: DailyReport): boolean {
  // 只有所有者可以编辑
  if (report.pitcher_id !== user.id) return false;
  
  // 只有 draft 状态可以编辑
  if (report.status !== 'draft') return false;
  
  return true;
}
```

### 4.3 字段级权限

| 字段 | 创建时 | 所有者编辑 | 主管查看 | CEO查看 |
|------|--------|------------|----------|---------|
| date | ✅ 必填 | ❌ 不可改 | ✅ | ✅ |
| project_id | ✅ 必填 | ❌ 不可改 | ✅ | ✅ |
| conversions | ✅ 必填 | ✅ 可改(draft) | ✅ | ✅ |
| spend | ✅ 必填 | ✅ 可改(draft) | ✅ | ✅ |
| status | ❌ 系统控制 | ❌ | ✅ | ✅ |
| internal_note | ❌ | ❌ | ✅ 可写 | ✅ |
```

---

### §5 业务逻辑

```markdown
## §5 业务逻辑

### 5.1 状态机定义

```
                    ┌─────────────────────────────────────────────────┐
                    │               日报状态机                         │
                    └─────────────────────────────────────────────────┘
                    
    ┌─────────┐     submit      ┌──────────────┐
    │  draft  │ ───────────────→│ raw_submitted│
    └─────────┘                 └──────────────┘
         │                             │
         │ delete                      │ auto
         ↓                             ↓
      [删除]                    ┌──────────────┐
                               │trend_pending │
                               └──────────────┘
                                      │
                         ┌────────────┴────────────┐
                         │ approve                 │ flag
                         ↓                         ↓
                  ┌───────────┐            ┌──────────────┐
                  │ trend_ok  │            │trend_flagged │
                  └───────────┘            └──────────────┘
                         │                         │
                         └────────────┬────────────┘
                                      │ auto
                                      ↓
                               ┌──────────────┐
                               │final_pending │
                               └──────────────┘
                                      │
                         ┌────────────┴────────────┐
                         │ confirm                 │ (无 reject)
                         ↓                         
                  ┌────────────────┐
                  │final_confirmed │
                  └────────────────┘
                         │
                         │ lock (月底自动)
                         ↓
                  ┌──────────────┐
                  │ final_locked │ (终态)
                  └──────────────┘
```

**状态转换表**

| 当前状态 | 允许转换到 | 触发条件 | 操作者 |
|----------|------------|----------|--------|
| draft | raw_submitted | 投手提交 | pitcher |
| draft | [删除] | 投手删除 | pitcher |
| raw_submitted | trend_pending | 系统自动 | system |
| trend_pending | trend_ok | 主管审核通过 | supervisor |
| trend_pending | trend_flagged | 主管标记异常 | supervisor |
| trend_ok | final_pending | 系统自动 | system |
| trend_flagged | final_pending | 系统自动 | system |
| final_pending | final_confirmed | 财务确认 | finance |
| final_confirmed | final_locked | 月底锁定 | system |

### 5.2 验证规则

```typescript
// 创建日报验证
const createDailyReportSchema = z.object({
  date: z.string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, '日期格式必须是 YYYY-MM-DD')
    .refine(date => new Date(date) <= new Date(), '不能选择未来日期'),
  
  project_id: z.string().uuid('无效的项目ID'),
  
  conversions: z.number()
    .int('进粉数必须是整数')
    .min(0, '进粉数不能为负'),
  
  spend: z.number()
    .min(0, '消耗金额不能为负')
    .multipleOf(0.01, '金额最多保留2位小数'),
  
  impressions: z.number().int().min(0).optional(),
  clicks: z.number().int().min(0).optional(),
});

// 业务验证
async function validateCreateDailyReport(data: CreateDailyReportRequest, user: User) {
  // 1. 检查项目是否存在且激活
  const project = await getProject(data.project_id);
  if (!project || project.status !== 'active') {
    throw new ValidationError('项目不存在或未激活');
  }
  
  // 2. 检查用户是否是该项目的投手
  const isMember = await isProjectMember(user.id, data.project_id);
  if (!isMember) {
    throw new ForbiddenError('您不是该项目的成员');
  }
  
  // 3. 检查是否已存在同日同项目的日报
  const existing = await getDailyReport({
    date: data.date,
    project_id: data.project_id,
    pitcher_id: user.id,
  });
  if (existing) {
    throw new DuplicateError('该日期已存在日报，请编辑现有日报');
  }
}
```

### 5.3 计算逻辑

```typescript
// CPL 计算
function calculateCPL(conversions: number, spend: number): number | null {
  if (conversions === 0) return null;
  return Math.round((spend / conversions) * 100) / 100;  // 保留2位小数
}

// CPR (Cost Per Result) 计算
function calculateCPR(clicks: number, spend: number): number | null {
  if (clicks === 0) return null;
  return Math.round((spend / clicks) * 100) / 100;
}

// CTR (Click Through Rate) 计算
function calculateCTR(clicks: number, impressions: number): number | null {
  if (impressions === 0) return null;
  return Math.round((clicks / impressions) * 10000) / 100;  // 百分比，保留2位小数
}

// 异常检测
function detectAnomalies(report: DailyReport, thresholds: Thresholds): Anomaly[] {
  const anomalies: Anomaly[] = [];
  
  // CPL 异常检测
  if (report.cpl && report.cpl > thresholds.cpl_max) {
    anomalies.push({
      field: 'cpl',
      type: 'HIGH_CPL',
      message: `CPL ${report.cpl} 超过阈值 ${thresholds.cpl_max}`,
      severity: 'warning',
    });
  }
  
  // 零转化检测
  if (report.conversions === 0 && report.spend > 0) {
    anomalies.push({
      field: 'conversions',
      type: 'ZERO_CONVERSION',
      message: '有消耗但无转化',
      severity: 'warning',
    });
  }
  
  return anomalies;
}
```

### 5.4 业务约束

```yaml
约束规则:
  日期约束:
    - 不能提交未来日期的日报
    - 已锁定月份的日报不能修改
    
  唯一性约束:
    - 同一投手同一项目同一日期只能有一条日报
    
  状态约束:
    - 只有 draft 状态可以编辑
    - 只有 draft 状态可以删除
    - 状态只能按状态机定义的路径转换
    
  数据约束:
    - conversions >= 0
    - spend >= 0
    - 提交后不能修改核心数据字段
    
  Phase 1 约束:
    - 异常数据只警告，不阻断提交
    - 异常数据高亮显示但可继续操作
```

---

### §6 前后端接口契约

```markdown
## §6 前后端接口契约

### 6.1 字段映射

| 后端字段 | 前端字段 | 说明 |
|----------|----------|------|
| id | id | UUID 字符串 |
| date | date | YYYY-MM-DD 字符串 |
| project_id | projectId | camelCase |
| pitcher_id | pitcherId | camelCase |
| conversions | conversions | 整数 |
| spend | spend | 数字，2位小数 |
| cpl | cpl | 数字或 null |
| status | status | 状态枚举字符串 |
| created_at | createdAt | ISO 8601 字符串 |
| updated_at | updatedAt | ISO 8601 字符串 |

### 6.2 枚举值对照

```typescript
// 日报状态
// 后端和前端使用相同的值
type DailyReportStatus =
  | 'draft'           // 草稿
  | 'raw_submitted'   // 已提交
  | 'trend_pending'   // 待趋势审核
  | 'trend_ok'        // 趋势通过
  | 'trend_flagged'   // 趋势异常
  | 'final_pending'   // 待最终确认
  | 'final_confirmed' // 已确认
  | 'final_locked';   // 已锁定

// 状态中文映射（前端使用）
const STATUS_LABELS: Record<DailyReportStatus, string> = {
  draft: '草稿',
  raw_submitted: '已提交',
  trend_pending: '待审核',
  trend_ok: '审核通过',
  trend_flagged: '异常',
  final_pending: '待确认',
  final_confirmed: '已确认',
  final_locked: '已锁定',
};
```

### 6.3 时区/格式约定

```yaml
时间格式:
  日期: YYYY-MM-DD (不含时区)
  时间戳: ISO 8601 (含时区)
  
时区处理:
  存储: UTC
  传输: UTC (ISO 8601 格式)
  显示: 前端转换为本地时区
  
数字格式:
  金额: 数字类型，保留2位小数
  百分比: 数字类型，如 12.34 表示 12.34%
  整数: number 类型，无小数
  
空值处理:
  null: 表示无值/未知
  0: 表示实际值为零
  
分页:
  页码: 从 1 开始
  默认每页: 20 条
  最大每页: 100 条
```

---

### §7 测试要点

```markdown
## §7 测试要点

### 7.1 单元测试

```typescript
// 验证函数测试
describe('validateCreateDailyReport', () => {
  it('应拒绝未来日期', async () => {
    const futureDate = '2099-12-31';
    await expect(validate({ date: futureDate }))
      .rejects.toThrow('不能选择未来日期');
  });
  
  it('应拒绝负数转化', async () => {
    await expect(validate({ conversions: -1 }))
      .rejects.toThrow('进粉数不能为负');
  });
  
  it('应拒绝负数消耗', async () => {
    await expect(validate({ spend: -100 }))
      .rejects.toThrow('消耗金额不能为负');
  });
});

// 计算函数测试
describe('calculateCPL', () => {
  it('正常计算 CPL', () => {
    expect(calculateCPL(100, 5000)).toBe(50);
  });
  
  it('零转化返回 null', () => {
    expect(calculateCPL(0, 5000)).toBeNull();
  });
  
  it('保留2位小数', () => {
    expect(calculateCPL(3, 100)).toBe(33.33);
  });
});

// 状态机测试
describe('状态转换', () => {
  it('draft → raw_submitted 允许', () => {
    expect(canTransition('draft', 'raw_submitted')).toBe(true);
  });
  
  it('raw_submitted → draft 禁止', () => {
    expect(canTransition('raw_submitted', 'draft')).toBe(false);
  });
  
  it('final_locked 是终态', () => {
    expect(getNextStates('final_locked')).toEqual([]);
  });
});
```

### 7.2 集成测试

```typescript
describe('POST /api/v1/daily-reports', () => {
  it('投手可以创建日报', async () => {
    const response = await request(app)
      .post('/api/v1/daily-reports')
      .set('Authorization', `Bearer ${pitcherToken}`)
      .send({
        date: '2024-12-23',
        project_id: testProjectId,
        conversions: 100,
        spend: 5000,
      });
    
    expect(response.status).toBe(201);
    expect(response.body.id).toBeDefined();
    expect(response.body.status).toBe('draft');
  });
  
  it('非投手不能创建日报', async () => {
    const response = await request(app)
      .post('/api/v1/daily-reports')
      .set('Authorization', `Bearer ${financeToken}`)
      .send({ /* ... */ });
    
    expect(response.status).toBe(403);
  });
  
  it('重复日报返回 409', async () => {
    // 先创建一条
    await createDailyReport({ date: '2024-12-23', project_id: testProjectId });
    
    // 再创建相同的
    const response = await request(app)
      .post('/api/v1/daily-reports')
      .set('Authorization', `Bearer ${pitcherToken}`)
      .send({
        date: '2024-12-23',
        project_id: testProjectId,
        conversions: 100,
        spend: 5000,
      });
    
    expect(response.status).toBe(409);
    expect(response.body.error.code).toBe('DUPLICATE_ENTRY');
  });
});
```

### 7.3 权限测试矩阵

```typescript
describe('权限测试', () => {
  const testCases = [
    // [角色, 操作, 预期结果]
    ['ceo', 'list_all', 200],
    ['ceo', 'view_any', 200],
    ['ceo', 'create', 403],
    
    ['finance', 'list_all', 403],
    ['finance', 'view_any', 403],
    ['finance', 'create', 403],
    
    ['supervisor', 'list_subordinates', 200],
    ['supervisor', 'view_subordinate', 200],
    ['supervisor', 'view_other', 403],
    ['supervisor', 'create', 403],
    
    ['pitcher', 'list_own', 200],
    ['pitcher', 'view_own', 200],
    ['pitcher', 'view_other', 403],
    ['pitcher', 'create', 201],
    ['pitcher', 'edit_own_draft', 200],
    ['pitcher', 'edit_own_submitted', 403],
    ['pitcher', 'delete_own_draft', 200],
    ['pitcher', 'delete_own_submitted', 403],
  ];
  
  test.each(testCases)('%s 执行 %s 应返回 %s', async (role, action, expected) => {
    const response = await executeAction(role, action);
    expect(response.status).toBe(expected);
  });
});
```
```

---

## 第三章 完整示例

### 3.1 日报提交模块规划书

```markdown
# B1 日报提交模块规划书

## §1 模块概述

### 1.1 业务目标

本模块实现投手日报的创建、编辑、提交功能。投手每日提交各项目的广告投放数据，系统记录原始数据并触发后续审核流程。

### 1.2 涉及角色

| 角色 | 系统角色名 | 本模块权限 |
|------|------------|------------|
| 投手 | media_buyer | 创建、编辑、删除、提交自己的日报 |
| 主管 | data_operator | 查看下属日报（只读） |
| CEO | ceo | 查看所有日报（只读） |

### 1.3 模块边界

**本模块负责：**
- 日报的 CRUD 操作
- 日报状态从 draft → raw_submitted
- 数据验证和异常检测（Phase 1: 只警告不阻断）

**本模块不负责：**
- 日报审核（B2 模块）
- 趋势分析（B3 模块）
- 财务确认（B4 模块）

---

## §2 数据模型

### 2.1 表结构

```sql
CREATE TABLE daily_reports (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date            DATE NOT NULL,
  project_id      UUID NOT NULL REFERENCES projects(id),
  pitcher_id      UUID NOT NULL REFERENCES users(id),
  conversions     INTEGER NOT NULL DEFAULT 0,
  spend           DECIMAL(12,2) NOT NULL DEFAULT 0,
  impressions     BIGINT DEFAULT 0,
  clicks          INTEGER DEFAULT 0,
  status          VARCHAR(32) NOT NULL DEFAULT 'draft',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  CONSTRAINT uq_daily_report UNIQUE (date, project_id, pitcher_id),
  CONSTRAINT chk_conversions CHECK (conversions >= 0),
  CONSTRAINT chk_spend CHECK (spend >= 0)
);
```

### 2.2 字段说明

| 字段 | 类型 | 必填 | 验证规则 |
|------|------|------|----------|
| date | DATE | ✅ | 不能是未来日期 |
| project_id | UUID | ✅ | 必须是有效且激活的项目 |
| conversions | INTEGER | ✅ | ≥ 0 |
| spend | DECIMAL(12,2) | ✅ | ≥ 0 |

---

## §3 API 设计

### 3.1 端点清单

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | /api/v1/daily-reports | 列表查询 |
| GET | /api/v1/daily-reports/:id | 详情查询 |
| POST | /api/v1/daily-reports | 创建 |
| PATCH | /api/v1/daily-reports/:id | 更新 |
| DELETE | /api/v1/daily-reports/:id | 删除(仅draft) |
| POST | /api/v1/daily-reports/:id/submit | 提交 |

### 3.2 创建日报 API

**POST /api/v1/daily-reports**

请求:
```json
{
  "date": "2024-12-23",
  "project_id": "uuid",
  "conversions": 100,
  "spend": 5000.00
}
```

成功响应 (201):
```json
{
  "id": "uuid",
  "date": "2024-12-23",
  "project": { "id": "uuid", "name": "项目A" },
  "pitcher": { "id": "uuid", "name": "张三" },
  "conversions": 100,
  "spend": 5000.00,
  "cpl": 50.00,
  "status": "draft",
  "warnings": [],
  "createdAt": "2024-12-23T10:00:00Z"
}
```

### 3.3 提交日报 API

**POST /api/v1/daily-reports/:id/submit**

成功响应 (200):
```json
{
  "id": "uuid",
  "status": "raw_submitted",
  "submittedAt": "2024-12-23T10:30:00Z",
  "warnings": [
    {
      "field": "cpl",
      "type": "HIGH_CPL",
      "message": "CPL 50.00 高于项目平均值"
    }
  ]
}
```

> **Phase 1 规则**: 即使有 warnings，也允许提交成功

---

## §4 权限控制

### 4.1 角色权限矩阵

| 操作 | ceo | supervisor | pitcher |
|------|-----|------------|---------|
| 查看所有 | ✅ | ❌ | ❌ |
| 查看下属 | ✅ | ✅ | ❌ |
| 查看自己 | N/A | N/A | ✅ |
| 创建 | ❌ | ❌ | ✅ |
| 编辑(draft) | ❌ | ❌ | ✅(自己) |
| 删除(draft) | ❌ | ❌ | ✅(自己) |
| 提交 | ❌ | ❌ | ✅(自己) |

---

## §5 业务逻辑

### 5.1 状态机

```
draft ──submit──→ raw_submitted ──auto──→ [进入审核流程]
  │
  └──delete──→ [删除]
```

### 5.2 验证规则

1. 日期不能是未来
2. 项目必须存在且激活
3. 用户必须是项目成员
4. 同日同项目不能重复提交

### 5.3 Phase 1 规则

| 异常类型 | 处理方式 |
|----------|----------|
| CPL 超标 | 警告，不阻断 |
| 零转化 | 警告，不阻断 |
| 数据缺失 | 警告，不阻断 |

---

## §6 前后端契约

### 6.1 字段映射

后端 snake_case → 前端 camelCase

### 6.2 状态值

使用相同的 snake_case 字符串

---

## §7 测试要点

### 7.1 必测场景

- [ ] 投手创建日报成功
- [ ] 投手提交日报成功
- [ ] 非投手创建被拒绝 (403)
- [ ] 重复日报被拒绝 (409)
- [ ] 未来日期被拒绝 (400)
- [ ] 已提交日报不能编辑 (400)
- [ ] 已提交日报不能删除 (400)
- [ ] 异常数据可以提交（Phase 1）
```

---

## 附录 A: 规划书模板

```markdown
# {模块编号} {模块名称}模块规划书

## §1 模块概述

### 1.1 业务目标
{1-2句话描述}

### 1.2 涉及角色
| 角色 | 系统角色名 | 本模块权限 |
|------|------------|------------|
| | | |

### 1.3 模块边界
**负责:** 
**不负责:**

---

## §2 数据模型

### 2.1 表结构
```sql
-- 建表语句
```

### 2.2 字段说明
| 字段 | 类型 | 必填 | 验证规则 |
|------|------|------|----------|
| | | | |

---

## §3 API 设计

### 3.1 端点清单
| 方法 | 端点 | 描述 |
|------|------|------|
| | | |

### 3.2 请求/响应格式
{详细定义}

---

## §4 权限控制

### 4.1 角色权限矩阵
| 操作 | ceo | finance | supervisor | pitcher | project_owner | account_manager | admin |
|------|-----|---------|------------|---------|---------------|-----------------|-------|
| | | | | | | | |

---

## §5 业务逻辑

### 5.1 状态机
{状态转换图}

### 5.2 验证规则
{验证逻辑}

### 5.3 Phase 1 规则
{不阻断规则}

---

## §6 前后端契约

### 6.1 字段映射
{映射关系}

---

## §7 测试要点

### 7.1 必测场景
- [ ] {场景1}
- [ ] {场景2}
```

---

## 第四章 补充章节规范

### §8 性能要求

```markdown
## §8 性能要求

### 8.1 数据量预估

| 指标 | 预估值 | 说明 |
|------|--------|------|
| 日增量 | {N} 条/天 | 正常业务增长 |
| 月增量 | {N} 条/月 | |
| 年存量 | {N} 条/年 | 预计1年后数据量 |
| 峰值 QPS | {N} | 业务高峰期 |

### 8.2 响应时间要求

| API | 目标 | 最大容忍 |
|-----|------|----------|
| 列表查询 | < 200ms | < 500ms |
| 详情查询 | < 100ms | < 300ms |
| 创建/更新 | < 300ms | < 1s |
| 批量操作 | < 1s | < 3s |

### 8.3 缓存策略

| 数据类型 | 缓存方式 | TTL | 失效策略 |
|----------|----------|-----|----------|
| 用户信息 | Redis | 30min | 更新时失效 |
| 项目列表 | Redis | 10min | 更新时失效 |
| 配置数据 | 本地缓存 | 5min | 定时刷新 |
| 热点数据 | Redis | 1h | LRU |

### 8.4 查询优化

```sql
-- 必须的索引
CREATE INDEX idx_{table}_xxx ON {table}(field1, field2);

-- 分页策略
-- 小数据量: OFFSET + LIMIT
-- 大数据量: 游标分页 (WHERE id > last_id LIMIT N)

-- 查询限制
-- 单次查询最大返回: 100 条
-- 批量操作最大: 50 条
```

### 8.5 批量操作限制

| 操作 | 单次上限 | 说明 |
|------|----------|------|
| 批量创建 | 50 条 | 超出需分批 |
| 批量更新 | 50 条 | 超出需分批 |
| 批量删除 | 20 条 | 需二次确认 |
| 导出 | 10000 条 | 超出走异步 |
```

**简化版（MVP 阶段）**：

```markdown
## §8 性能要求

### 8.1 基本指标

| 指标 | 要求 |
|------|------|
| 列表查询响应 | < 500ms |
| 单条操作响应 | < 300ms |
| 单次查询上限 | 100 条 |
| 批量操作上限 | 50 条 |

### 8.2 索引要求

必须为以下查询场景建立索引：
- 按日期范围查询
- 按状态筛选
- 按所属用户查询
- 常用组合查询

### 8.3 注意事项

- 大数据量导出走异步任务
- 避免 N+1 查询
- 分页使用游标分页（数据量大时）
```

---

### §9 安全规范

```markdown
## §9 安全规范

### 9.1 认证授权

| 项目 | 要求 |
|------|------|
| 认证方式 | JWT Token |
| Token 有效期 | 24 小时 |
| 刷新机制 | Refresh Token |
| 权限校验 | 每个 API 必须校验 |

### 9.2 敏感数据处理

| 数据类型 | 处理方式 | 示例 |
|----------|----------|------|
| 密码 | 不返回 | password: undefined |
| 手机号 | 中间4位脱敏 | 138****1234 |
| 邮箱 | 部分脱敏 | z***@example.com |
| 身份证 | 中间8位脱敏 | 110***********1234 |
| 银行卡 | 只显示后4位 | **** **** **** 1234 |

```typescript
// 脱敏函数示例
function maskPhone(phone: string): string {
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2');
}

function maskEmail(email: string): string {
  const [name, domain] = email.split('@');
  return `${name[0]}***@${domain}`;
}
```

### 9.3 审计日志

必须记录以下操作：

| 操作类型 | 记录内容 |
|----------|----------|
| 登录/登出 | 用户ID、时间、IP、设备 |
| 创建 | 操作人、时间、创建内容摘要 |
| 更新 | 操作人、时间、变更前后对比 |
| 删除 | 操作人、时间、删除内容备份 |
| 敏感操作 | 操作人、时间、操作详情 |

```typescript
interface AuditLog {
  id: string;
  user_id: string;
  action: 'create' | 'update' | 'delete' | 'login' | 'logout' | 'sensitive';
  resource_type: string;      // 'daily_report', 'project', etc.
  resource_id: string;
  changes?: {
    before: Record<string, any>;
    after: Record<string, any>;
  };
  ip_address: string;
  user_agent: string;
  created_at: string;
}
```

### 9.4 输入验证

| 验证项 | 规则 |
|--------|------|
| SQL 注入 | 使用参数化查询，禁止拼接 SQL |
| XSS | 输出时转义 HTML 特殊字符 |
| 长度限制 | 所有字符串字段必须有最大长度 |
| 类型校验 | 使用 Zod 强类型验证 |
| 枚举校验 | 必须在允许值范围内 |

```typescript
// 输入验证示例
const createReportSchema = z.object({
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  project_id: z.string().uuid(),
  conversions: z.number().int().min(0).max(1000000),
  spend: z.number().min(0).max(100000000),
  // 字符串长度限制
  notes: z.string().max(1000).optional(),
});
```

### 9.5 防护措施

| 攻击类型 | 防护措施 |
|----------|----------|
| 暴力破解 | 登录失败5次锁定15分钟 |
| 重放攻击 | 请求加时间戳 + 签名 |
| CSRF | 使用 CSRF Token |
| 越权访问 | 数据权限校验 |
| 批量爬取 | 接口限流 |

### 9.6 接口限流

| 接口类型 | 限流规则 |
|----------|----------|
| 登录接口 | 10 次/分钟/IP |
| 普通查询 | 100 次/分钟/用户 |
| 写入操作 | 30 次/分钟/用户 |
| 导出接口 | 5 次/分钟/用户 |
```

**简化版（MVP 阶段）**：

```markdown
## §9 安全规范

### 9.1 基本要求

| 项目 | 要求 |
|------|------|
| 认证 | 所有 API 需要 JWT Token |
| 权限 | 每个 API 校验角色权限 |
| 数据权限 | 只能访问自己有权限的数据 |

### 9.2 输入验证（必须）

- [ ] 使用 Zod 验证所有输入
- [ ] 字符串字段有最大长度限制
- [ ] 数字字段有范围限制
- [ ] 使用参数化查询，禁止拼接 SQL

### 9.3 敏感数据（必须）

- [ ] 密码不返回给前端
- [ ] 手机号、邮箱脱敏显示
- [ ] 敏感操作记录审计日志

### 9.4 接口限流（建议）

| 接口 | 限制 |
|------|------|
| 登录 | 10次/分钟 |
| 普通接口 | 100次/分钟 |
```

---

## 第五章 更新后的目录结构

```
后端模块规划书（完整版）
│
├── §1 模块概述
│   ├── 1.1 业务目标
│   ├── 1.2 涉及角色
│   └── 1.3 模块边界
│
├── §2 数据模型
│   ├── 2.1 表结构定义
│   ├── 2.2 字段说明
│   ├── 2.3 索引设计
│   └── 2.4 关联关系
│
├── §3 API 设计
│   ├── 3.1 端点清单
│   ├── 3.2 请求/响应格式
│   ├── 3.3 错误码定义
│   └── 3.4 分页/筛选规范
│
├── §4 权限控制
│   ├── 4.1 角色权限矩阵
│   ├── 4.2 数据权限规则
│   └── 4.3 字段级权限
│
├── §5 业务逻辑
│   ├── 5.1 状态机定义
│   ├── 5.2 验证规则
│   ├── 5.3 计算逻辑
│   └── 5.4 业务约束
│
├── §6 前后端接口契约
│   ├── 6.1 字段映射
│   ├── 6.2 枚举值对照
│   └── 6.3 时区/格式约定
│
├── §7 测试要点
│   ├── 7.1 单元测试
│   ├── 7.2 集成测试
│   └── 7.3 权限测试矩阵
│
├── §8 性能要求 ✨ NEW
│   ├── 8.1 数据量预估
│   ├── 8.2 响应时间要求
│   ├── 8.3 缓存策略
│   ├── 8.4 查询优化
│   └── 8.5 批量操作限制
│
└── §9 安全规范 ✨ NEW
    ├── 9.1 认证授权
    ├── 9.2 敏感数据处理
    ├── 9.3 审计日志
    ├── 9.4 输入验证
    ├── 9.5 防护措施
    └── 9.6 接口限流
```

---

## 附录 B: 更新后的规划书模板

```markdown
# {模块编号} {模块名称}模块规划书

## §1 模块概述
### 1.1 业务目标
### 1.2 涉及角色
### 1.3 模块边界

## §2 数据模型
### 2.1 表结构
### 2.2 字段说明
### 2.3 索引设计

## §3 API 设计
### 3.1 端点清单
### 3.2 请求/响应格式
### 3.3 错误码定义

## §4 权限控制
### 4.1 角色权限矩阵（7角色）
### 4.2 数据权限规则

## §5 业务逻辑
### 5.1 状态机
### 5.2 验证规则
### 5.3 Phase 1 规则

## §6 前后端契约
### 6.1 字段映射

## §7 测试要点
### 7.1 必测场景

## §8 性能要求
### 8.1 基本指标
| 指标 | 要求 |
|------|------|
| 列表查询响应 | < 500ms |
| 单条操作响应 | < 300ms |
| 单次查询上限 | 100 条 |
| 批量操作上限 | 50 条 |

### 8.2 索引要求
{列出必须的索引}

## §9 安全规范
### 9.1 基本要求
- [ ] 所有 API 需要认证
- [ ] 权限校验
- [ ] 数据权限校验

### 9.2 输入验证
- [ ] Zod 验证
- [ ] 长度限制
- [ ] 参数化查询

### 9.3 敏感数据
- [ ] 密码不返回
- [ ] 手机号脱敏
- [ ] 审计日志
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-23 | 初始版本 |
| v1.1 | 2025-12-23 | 增加 §8 性能要求、§9 安全规范 |
