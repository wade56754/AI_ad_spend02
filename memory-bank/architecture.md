# AI 广告代投管理系统 - 架构说明

> **版本**: v2.3
> **更新日期**: 2026-01-02
> **SoT 基准**: MASTER.md v4.9 | DATA_SCHEMA.md v5.10 | STATE_MACHINE.md v2.9 | BUSINESS_RULES.md v5.1 | API_SOT.md v9.7
> **PRD 对齐**: PRD v5.2 (6 角色模型)

---

## 1. 系统定位

**广告投放业务的"人、账户、项目、钱"管理系统，让账目清清楚楚、有据可查。**

### 1.1 Phase 边界（当前 Phase 1）

| Phase | 目标 | 系统行为 |
|-------|------|---------|
| **Phase 1** (当前) | 照亮问题 | 记录事实、展示状态、提示异常、高亮警告 |
| **Phase 2** (规划) | 问责约束 | 强制审批、自动阻断、考核关联 |

**Phase 1 约束**:
- ❌ 禁止任何自动阻断/拒绝/暂停/冻结功能
- ❌ 禁止自动惩罚机制（扣分、禁用账户等）
- ❌ 禁止强制审批流程（仅记录和提示）
- ✅ 允许：记录事实、展示状态、提示异常、高亮警告

---

## 2. 系统架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Next.js 16)                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │Dashboard│  │ 日报    │  │ 账户    │  │ 财务    │  ...   │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       └────────────┴────────────┴────────────┘              │
│                         │                                    │
│                    API Client (apiFetch)                     │
└─────────────────────────┼───────────────────────────────────┘
                          │ HTTPS
┌─────────────────────────┼───────────────────────────────────┐
│                    后端 (FastAPI)                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Routers │→ │Services │→ │ Models  │→ │   DB    │        │
│  └─────────┘  └─────────┘  └─────────┘  └────┬────┘        │
└──────────────────────────────────────────────┼──────────────┘
                                               │
┌──────────────────────────────────────────────┼──────────────┐
│                    Supabase                   │              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────┴─────┐       │
│  │ PostgreSQL  │  │   Auth      │  │   Storage     │       │
│  └─────────────┘  └─────────────┘  └───────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 角色定义

> **详细定义**: 参见 `quick-reference.md` §2
> **来源**: MASTER.md v4.9 §2.4

**6 角色白名单**: `ceo`, `project_owner`, `finance`, `pitcher`, `account_manager`, `admin`

**废弃角色**: `supervisor` (合并到 project_owner), `data_operator`, `media_buyer`

---

## 4. 后端架构模式

### 4.1 三层分层

```
Router (HTTP 适配) → Service (业务逻辑) → Model (数据持久化)
      ↓                    ↓                    ↓
  依赖注入             事务管理              ORM + Mixin
```

### 4.2 Router 模式

```python
# backend/routers/daily_reports.py
router = APIRouter(prefix="/daily-reports", tags=["daily-reports"])

def get_service(db: Session = Depends(get_db)) -> DailyReportService:
    return DailyReportService(db)

@router.post("/", response_model=StandardResponse[DailyReportResponse])
async def create_report(
    request: DailyReportCreateRequest,
    current_user: User = Depends(get_current_user),
    service: DailyReportService = Depends(get_service),
):
    """创建日报 - SoT: API_SOT.md §9.1"""
    report = service.create_daily_report(request, current_user)
    return success_response(report)
```

### 4.3 Service 模式

```python
# backend/services/daily_report_service.py
class DailyReportService:
    def __init__(self, db: Session):
        self.db = db

    @contextmanager
    def transaction(self):
        """事务上下文 - 自动提交/回滚"""
        try:
            yield
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise

    def create_daily_report(
        self,
        request: DailyReportCreateRequest,
        user: User
    ) -> DailyReport:
        """创建日报 - Phase 感知"""
        with self.transaction():
            report = DailyReport(**request.dict(), created_by=user.id)
            report.status = "raw_submitted"  # 初始状态
            self.db.add(report)
            return report
```

### 4.4 统一响应包装

```python
# 所有 API 必须使用
success_response(data, message="操作成功")
error_response(message, code="BIZ_001")
paginated_response(items, total, page, page_size)
```

### 4.5 异常处理

```python
# 标准异常层次
BusinessLogicError      # 业务规则违反 → 400
ResourceNotFoundError   # 资源不存在 → 404
PermissionDeniedError   # 权限不足 → 403
StateTransitionError    # 状态转换非法 → 400
```

---

## 5. 前端架构模式

### 5.1 Feature 模块结构

```
frontend/src/features/{module}/
├── components/           # UI 组件
│   ├── {Module}Page.tsx      # 主页面
│   ├── {Module}Table.tsx     # 数据表格
│   ├── {Module}Dialog.tsx    # 弹窗
│   └── index.ts
├── hooks/                # React Query hooks
│   ├── use{Module}.ts
│   └── index.ts
├── services/             # API 调用
│   ├── {module}Api.ts
│   └── index.ts
├── types/                # TypeScript 类型
│   ├── {module}.types.ts
│   └── index.ts
└── index.ts              # 模块导出
```

### 5.2 API 三层调用

```typescript
// 1. Service 层 - API 调用
// features/daily-reports/services/dailyReportsApi.ts
export async function getDailyReports(
  params: ListParams
): Promise<PaginatedResponse<DailyReport>> {
  return apiFetchPaginated<DailyReport>(`/api/v1/daily-reports?${buildQuery(params)}`)
}

// 2. Hook 层 - 状态管理
// features/daily-reports/hooks/useDailyReports.ts
export function useDailyReports(params: ListParams) {
  return useQuery({
    queryKey: ['daily-reports', params],
    queryFn: () => getDailyReports(params),
    staleTime: 2 * 60 * 1000,
  })
}

// 3. Component 层 - UI 渲染
// features/daily-reports/components/DailyReportsPage.tsx
'use client'
export function DailyReportsPage() {
  const { data, isLoading } = useDailyReports(params)
  return <DataTable columns={columns} data={data?.items ?? []} loading={isLoading} />
}
```

### 5.3 Mutation Hook 模式

```typescript
export function useCreateDailyReport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createDailyReport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['daily-reports'] })
      toast.success('创建成功')
    },
    onError: (error: ApiError) => {
      toast.error(error.message || '操作失败')
    },
  })
}
```

### 5.4 表单弹窗模式

```typescript
'use client'

export function CreateReportDialog({ open, onOpenChange }: Props) {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { ... },
  })

  const mutation = useCreateDailyReport()

  const onSubmit = (values: FormValues) => {
    mutation.mutate(values, {
      onSuccess: () => onOpenChange(false),
    })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            {/* FormField components */}
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? '保存中...' : '保存'}
            </Button>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
```

---

## 6. 目录结构

```
AI_Ads/
├── frontend/                    # 前端应用 (Next.js 16)
│   └── src/
│       ├── app/                 # App Router 页面
│       │   ├── (dashboard)/     # 后台路由组
│       │   ├── layout.tsx       # 根布局
│       │   └── providers.tsx    # 全局 Providers
│       ├── features/            # 功能模块 (按业务划分)
│       │   ├── auth/            # 认证
│       │   ├── dashboard/       # 仪表盘
│       │   ├── daily-reports/   # 日报管理
│       │   ├── ad-accounts/     # 广告账户
│       │   ├── projects/        # 项目管理
│       │   ├── finance/         # 财务管理
│       │   ├── topups/          # 充值管理
│       │   └── users/           # 用户管理
│       ├── components/          # 通用组件
│       │   ├── ui/              # shadcn/ui (54+ 组件)
│       │   ├── layout/          # 布局组件
│       │   └── shared/          # 共享组件
│       ├── hooks/               # 自定义 Hooks
│       ├── lib/                 # 工具库
│       │   └── api.ts           # API 客户端 (唯一 HTTP 入口)
│       └── types/               # TypeScript 类型
│
├── backend/                     # 后端应用 (FastAPI)
│   ├── routers/                 # API 路由定义
│   ├── services/                # 业务逻辑层
│   ├── models/                  # SQLAlchemy 模型
│   ├── schemas/                 # Pydantic 模型
│   ├── core/                    # 核心配置
│   │   ├── config.py            # 配置管理
│   │   ├── deps.py              # 依赖注入
│   │   ├── security.py          # 安全相关
│   │   └── state_machine.py     # 状态机
│   ├── exceptions/              # 自定义异常
│   └── tests/                   # 测试
│       ├── api/                 # API 测试
│       ├── services/            # 服务测试
│       ├── core/                # 核心测试
│       └── conftest.py          # 共享 fixtures
│
├── docs/                        # 文档
│   ├── sot/                     # 真相源文档 (SoT)
│   └── guides/                  # 开发指南
│
├── memory-bank/                 # 项目记忆库
│   ├── progress.md              # 进度记录
│   └── architecture.md          # 架构说明 (本文件)
│
└── scripts/                     # 工具脚本
    └── sot-scan.sh              # SoT 5秒扫描
```

---

## 7. 技术栈

### 后端
| 组件 | 技术 | 版本 |
|------|------|------|
| 框架 | FastAPI | 0.100+ |
| ORM | SQLAlchemy | 2.x |
| 验证 | Pydantic | v2 |
| 数据库 | PostgreSQL | 15+ (Supabase) |
| 认证 | Supabase Auth + JWT | - |
| 缓存 | Redis | 7.x |

### 前端
| 组件 | 技术 | 版本 |
|------|------|------|
| 框架 | Next.js (App Router) | 16 |
| 语言 | TypeScript | 5.6+ (strict) |
| UI | shadcn/ui + Tailwind CSS | - |
| 状态 | TanStack Query | v5 |
| 表单 | react-hook-form + zod | - |
| HTTP | apiFetch (lib/api.ts) | - |
| 通知 | sonner | - |

---

## 8. SoT 裁判链（优先级）

> 冲突时高优先级覆盖低优先级

| 优先级 | 文件 | 版本 | 说明 |
|--------|------|------|------|
| 1 | `docs/sot/MASTER.md` | v4.9 | 系统宪法，最高优先级 |
| 2 | `docs/sot/DATA_SCHEMA.md` | v5.10 | 数据模型、字段定义 |
| 3 | `docs/sot/STATE_MACHINE.md` | v2.9 | 状态机规范 |
| 4 | `docs/sot/BUSINESS_RULES.md` | v5.1 | 业务规则索引 |
| 5 | `docs/sot/API_SOT.md` | v9.7 | API 规范 |
| 6 | `docs/sot/AUTH_SPEC.md` | v2.2 | 认证授权规范 |
| 7 | `docs/sot/ERROR_CODES_SOT.md` | v2.2 | 错误码定义 |

### 业务规则子模块

| 文件 | 说明 |
|------|------|
| `BR-AUTH.md` | 认证授权规则 |
| `BR-USER.md` | 用户角色规则 |
| `BR-PROJ.md` | 项目管理规则 |
| `BR-ACCT.md` | 广告账户规则 |
| `BR-FIN.md` | 财务流程规则 |
| `BR-RPT.md` | 日报管理规则 |
| `BR-RECON.md` | 对账流程规则 |
| `BR-PROFIT.md` | 利润统计规则 |
| `BR-DATA.md` | 数据完整性规则 |

---

## 9. 状态机设计

> **详细定义**: 参见 `quick-reference.md` §3
> **来源**: STATE_MACHINE.md v2.9

### 9.1 状态机使用

```python
# 检查状态转换是否合法
from backend.core.state_machine import DAILY_REPORT_STATE_MACHINE

if not DAILY_REPORT_STATE_MACHINE.can_transition(
    current_status,
    new_status,
    user.role
):
    raise StateTransitionError(f"Cannot transition from {current_status} to {new_status}")

# 执行状态转换
report = DAILY_REPORT_STATE_MACHINE.transition(report, current_status, new_status)
```

### 9.2 状态机速查

| 实体 | Phase 1 状态数 | 关键状态 |
|------|---------------|----------|
| 日报 | 3 | `raw_submitted` → `trend_ok` → `final_confirmed` |
| 充值 | 7 | `draft` → `pending_review` → `finance_approve` → `paid` → `completed` |
| 项目 | 4 | `draft` → `active` → `suspended` → `archived` |
| 账户 | 6 | `new` → `testing` → `active` → `suspended` → `dead` → `archived` |

---

## 10. 开发工作流

### 10.1 新增 API 端点（5 步）

```
1. 更新 API_SOT.md → 定义端点规范
2. Schema (Pydantic) → 请求/响应模型
3. Service → 业务逻辑实现
4. Router → HTTP 端点封装
5. Tests → 测试用例
```

### 10.2 新增前端模块（5 步）

```
1. types/ → 类型定义 (同步自 API_SOT.md)
2. services/ → API 调用 (使用 apiFetch)
3. hooks/ → Query/Mutation hooks
4. components/ → UI 组件 (使用 shadcn/ui)
5. app/ → 路由页面
```

### 10.3 状态转换开发（4 步）

```
1. 查阅 STATE_MACHINE.md → 确认合法转换
2. Service 层调用 can_transition() → 验证
3. 执行 transition() → 更新状态
4. 测试 → 覆盖 happy path + 非法转换
```

---

## 11. 代码规范速查

### 11.1 正确 ✅ vs 错误 ❌

| 正确 ✅ | 错误 ❌ |
|---------|---------|
| `apiGet('/api/v1/...')` | `fetch()` / `axios` |
| `<DataTable />` | `<table>` |
| `<Button />` | `<button>` |
| `<Input />` | `<input>` |
| `<Select />` | `<select>` |
| 6 角色白名单 | `supervisor` / `media_buyer` |
| `'use client'` 开头 | 缺少指令 |
| TanStack Query | Redux / Zustand |
| `toast.success()` | `alert()` |
| 明确类型定义 | `any` |

### 11.2 必须使用的组件

| 场景 | 组件 | 来源 |
|------|------|------|
| 按钮 | `Button` | `@/components/ui/button` |
| 输入框 | `Input` | `@/components/ui/input` |
| 表格 | `DataTable` | `@/components/ui/data-table` |
| 弹窗 | `Dialog` | `@/components/ui/dialog` |
| 表单 | `Form` + `FormField` | `@/components/ui/form` |
| 状态标签 | `StatusBadge` | `@/components/ui/status-badge` |
| 通知 | `toast` | `sonner` |

---

## 12. 核心公式

```python
# 收入计算 (按粉结算)
revenue = conversions_final × unit_price

# 收入计算 (按服务费)
revenue = ad_spend × (1 + service_fee_rate)

# 成本计算
cost = real_spend + platform_fee

# 毛利计算
gross_profit = revenue - cost

# CPL 计算
cpl = ad_spend / conversions_final

# 押款计算
fund_occupied = Σtopup - Σad_spend
```

---

## 13. 不变量（绝对不能违反）

| ID | 规则 | 说明 |
|----|------|------|
| INV-01 | 预收款 ≠ 收入 | 履约完成前是负债 |
| INV-02 | 平台消耗不含手续费 | 广告费和手续费分开核算 |
| INV-03 | 可用资金公式 | `opening_balance + Σtopup - Σad_spend` |
| INV-04 | 锁定后不可改 | 只能红冲（ref_id + reason） |
| INV-05 | 数据域隔离 | 投手只看自己账户，项目负责人只看自己项目 |
| INV-06 | 角色白名单 | 仅 6 个角色，禁止使用废弃角色 |
| INV-07 | Phase 边界 | Phase 1 禁止自动阻断 |

---

## 14. AI 防幻觉原则

| ID | 原则 | 说明 |
|----|------|------|
| AH-01 | 禁止假设数据一致 | 遇到缺失标记"待确认" |
| AH-02 | 禁止自动做管理裁决 | 不生成自动拒绝/暂停代码 |
| AH-03 | 禁止引入 SoT 未定义概念 | 发现缺失→停止→询问 |
| AH-04 | 必须遵循 Phase 1 软性原则 | 提示+高亮+记录 |
| AH-05 | 遇到歧义必须停止并询问 | 停止→列出歧义→询问 |

---

## 15. 防幻觉检查清单

### 开发前检查

```
□ 确认 Phase 1 (日报只用 3 状态)
□ 确认角色在 6 角色白名单内 (无 supervisor)
□ 确认 API 端点在 API_SOT.md 中存在
□ 确认数据字段在 DATA_SCHEMA.md 中定义
□ 确认状态转换在 STATE_MACHINE.md 中合法
```

### 开发后检查

```
□ 第一行是否为 'use client' (交互页面)
□ 是否使用了禁止的角色 (supervisor)
□ 是否使用了 Phase 2 日报状态
□ 是否手写了 table/fetch (禁止)
□ 错误处理是否完整 (try-catch/onError)
□ toast 通知是否完整 (成功/失败)
□ 错误码是否来自 ERROR_CODES_SOT.md
```

---

## 16. 测试策略

### 16.1 测试金字塔

```
              ▲
             / \  E2E (5%)
            /───\
           /     \  Integration (15%)
          /───────\
         /         \  Unit (80%)
        /───────────\
```

### 16.2 测试分类

```python
@pytest.mark.unit           # 单元测试
@pytest.mark.integration    # 集成测试
@pytest.mark.state_machine  # 状态机测试
@pytest.mark.phase1         # Phase 1 功能
@pytest.mark.phase2         # Phase 2 功能
```

### 16.3 运行测试

```bash
pytest -m unit                    # 仅单元测试
pytest -m "not slow"              # 跳过慢速测试
pytest -m state_machine           # 状态机测试
pytest backend/tests/api/         # API 测试
```

---

## 17. 模块依赖关系

```
M0 认证 ──► M1 用户 ──► M2 项目 ──► M3 账户
                │              │           │
                │              │           ▼
                │              └──────► M4 日报
                │                          │
                └──────────► M5 充值 ◄─────┘
                                 │
                                 ▼
                             M6 账本
                              │   │
                              ▼   ▼
                        M7 对账   M8 利润
```

---

## 18. 关键文件索引

### 后端核心文件

| 路径 | 说明 |
|------|------|
| `backend/main.py` | FastAPI 应用入口 |
| `backend/core/config.py` | 配置管理 |
| `backend/core/deps.py` | 依赖注入 (认证、数据库) |
| `backend/core/state_machine.py` | 状态机实现 |
| `backend/routers/daily_reports.py` | 日报 API |
| `backend/services/daily_report_service.py` | 日报服务 |
| `backend/services/trend_risk_control_service.py` | 趋势风控服务 |

### 前端核心文件

| 路径 | 说明 |
|------|------|
| `frontend/src/app/layout.tsx` | 根布局 |
| `frontend/src/lib/api.ts` | API 客户端 (唯一 HTTP 入口) |
| `frontend/src/features/daily-reports/` | 日报模块 |
| `frontend/src/features/dashboard/` | 仪表盘模块 |
| `frontend/src/features/finance/` | 财务模块 |

---

## 19. 安全架构

### 认证
- Supabase Auth (JWT)
- Token 有效期: 24 小时
- 刷新机制: 自动刷新

### 授权
- 基于角色的访问控制 (RBAC)
- 6 角色: ceo, project_owner, finance, pitcher, account_manager, admin
- 数据域隔离: 投手只看自己账户

### 数据安全
- HTTPS 传输加密
- 敏感数据脱敏
- 审计日志记录

---

## 20. 扩展点

| 扩展点 | 当前状态 | 未来计划 |
|--------|----------|----------|
| 缓存层 | ✅ Redis | 已完成 |
| 消息队列 | 无 | RabbitMQ/Celery |
| 监控 | ✅ Sentry + Prometheus | 已完成 |
| 搜索 | PostgreSQL | Elasticsearch |

---

## 更新日志

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-01-02 | v2.3 | 去重角色/状态机定义，引用 quick-reference.md |
| 2026-01-02 | v2.2 | 统一 SoT 版本引用 |
| 2026-01-02 | v2.1 | 添加代码模式示例、开发工作流、防幻觉检查清单 |
| 2026-01-02 | v2.0 | 重构对齐 PRD v5.2，更新 SoT 版本引用，添加 Phase 边界 |
| 2025-12-29 | v1.1 | 添加 AI 代码工厂、APM 监控 |
| 2025-12-15 | v1.0 | 初始版本 |
