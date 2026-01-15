# 代码块注册表 (Code Blocks Registry)

> **版本**: v2.0
> **更新日期**: 2025-12-24
> **基准**: docs/9.code-blocks/README.md v3.0 + BACKEND_CODE_BLOCKS_GITHUB_SEARCH.md

---

## 一、使用原则

### 强制规则 (BLOCKING)

1. **CB-001**: 生成代码前，必须先查询本注册表
2. **CB-002**: 如果存在匹配的代码块，必须使用代码块，禁止重新编写
3. **CB-003**: 代码块只能扩展，不能修改核心逻辑
4. **CB-004**: 使用代码块时必须标注

### 查询流程

用户需求 → 提取关键词 → 查询代码块注册表 → 匹配成功?
                                              ↓
                                         是 → 使用代码块
                                         否 → 进入搜索流程

---

## 二、前端代码块索引

### 2.1 核心代码块 (P0)

| ID | 名称 | 优先级 | 复用页面 | 推荐方案 | 关键词 |
|----|------|--------|---------|---------|--------|
| CB-FE-001 | DataTable | P0 | 8+ | TanStack Table + shadcn | 表格, 列表, table, list, 分页, 排序 |
| CB-FE-002 | StatusBadge | P0 | 5 | CVA + shadcn Badge | 状态, 徽章, badge, status, 标签 |
| CB-FE-003 | DataState | P0 | 10 | Pattern Matching + Skeleton | 加载, loading, empty, skeleton, error |

### 2.2 流程代码块 (P1)

| ID | 名称 | 优先级 | 复用页面 | 推荐方案 | 关键词 |
|----|------|--------|---------|---------|--------|
| CB-FE-004 | ActionButtons | P1 | 3 | shadcn AlertDialog | 操作, 按钮, action, confirm, 审批 |
| CB-FE-005 | GlobalFilters | P1 | 4 | nuqs + date-range-picker | 筛选, filter, 日期, select, 搜索 |

### 2.3 其他前端代码块 (P2)

| ID | 名称 | 优先级 | 复用页面 | 推荐方案 | 关键词 |
|----|------|--------|---------|---------|--------|
| CB-FE-006 | PageHeader | P2 | 10 | shadcn Breadcrumb | 页面标题, header, 面包屑 |
| CB-FE-007 | ApprovalTimeline | P2 | 2 | shadcn-timeline | 时间线, timeline, workflow, stepper |
| CB-FE-008 | FormDialog | P2 | 3 | react-hook-form + Dialog | 表单, form, 弹窗, dialog, modal |

---

## 三、后端代码块索引

### 3.1 核心代码块 (P0)

| ID | 名称 | 优先级 | 复用API | 推荐方案 | 关键词 |
|----|------|--------|---------|---------|--------|
| CB-BE-001 | Pagination | P0 | 8+ | fastapi-pagination | 分页, pagination, list, page |
| CB-BE-002 | ResponseEnvelope | P0 | 全部 | Generic[T] Pydantic | 响应, response, envelope, 封装 |
| CB-BE-003 | ErrorCodes | P0 | 全部 | Enum + BusinessError | 错误, error, 异常, exception |

### 3.2 流程代码块 (P1)

| ID | 名称 | 优先级 | 复用服务 | 推荐方案 | 关键词 |
|----|------|--------|---------|---------|--------|
| CB-BE-004 | PermissionFilter | P1 | 5 | Service层过滤 | 权限, permission, 过滤, role |
| CB-BE-005 | StateMachine | P1 | 4 | transitions库 | 状态机, state, transition, 流程 |

### 3.3 其他后端代码块 (P2)

| ID | 名称 | 优先级 | 复用服务 | 推荐方案 | 关键词 |
|----|------|--------|---------|---------|--------|
| CB-BE-006 | AuditLog | P2 | 5 | SQLAlchemy Event | 审计, audit, 日志, log, history |
| CB-BE-007 | LedgerEntry | P2 | 3 | 双向记账模型 | 账本, ledger, 余额, balance |
| CB-BE-008 | KPICalculator | P2 | 3 | Decimal + dataclass | KPI, ROAS, CPL, CPA, 指标 |

---

## 四、快速查询表 (关键词 → 代码块)

表格/列表 → CB-FE-001 (DataTable)
状态/徽章 → CB-FE-002 (StatusBadge)
加载/空状态 → CB-FE-003 (DataState)
操作/按钮 → CB-FE-004 (ActionButtons)
筛选/日期 → CB-FE-005 (GlobalFilters)
页面标题 → CB-FE-006 (PageHeader)
时间线/流程 → CB-FE-007 (ApprovalTimeline)
表单/弹窗 → CB-FE-008 (FormDialog)
分页 → CB-BE-001 (Pagination)
响应格式 → CB-BE-002 (ResponseEnvelope)
错误处理 → CB-BE-003 (ErrorCodes)
数据权限 → CB-BE-004 (PermissionFilter)
状态机 → CB-BE-005 (StateMachine)
审计日志 → CB-BE-006 (AuditLog)
账本记账 → CB-BE-007 (LedgerEntry)
KPI计算 → CB-BE-008 (KPICalculator)


---

## 五、后端代码块详细模板

### CB-BE-001: Pagination (分页)

**推荐库**: `fastapi-pagination` (1k+ stars)

```python
# backend/core/pagination.py
from pydantic import BaseModel, ConfigDict
from fastapi import Query
from sqlalchemy import select, func

class PaginationParams(BaseModel):
    page: int = Query(1, ge=1)
    page_size: int = Query(20, ge=1, le=100)

class PaginatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list
    total: int
    page: int
    pages: int

def paginate(db, query, params):
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    offset = (params.page - 1) * params.page_size
    items = db.scalars(query.offset(offset).limit(params.page_size)).all()
    return PaginatedResponse(items=items, total=total, page=params.page,
        pages=(total + params.page_size - 1) // params.page_size)
```

---

### CB-BE-002: ResponseEnvelope (响应封装)

```python
# backend/core/response.py
from pydantic import BaseModel, ConfigDict
from typing import Generic, TypeVar, Any

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)
    code: int = 0
    message: str = "success"
    data: T | None = None

def success_response(data=None, message="操作成功"):
    return {"code": 0, "message": message, "data": data}

def error_response(code, message, data=None):
    return {"code": code, "message": message, "data": data}
```

---

### CB-BE-003: ErrorCodes (错误码)

**基准**: ERROR_CODES_SOT.md v2.1

```python
# backend/core/error_codes.py
ERROR_HTTP_STATUS = {
    "VAL": 400, "AUTH": 401, "PERM": 403,
    "RES": 404, "STATE": 409, "BIZ": 422, "SYS": 500
}

class BusinessError(Exception):
    def __init__(self, code: str, message: str, data=None):
        self.code = code
        self.message = message
        self.data = data
        self.status_code = ERROR_HTTP_STATUS.get(code.split("-")[0], 400)
```

| 错误码 | 含义 | HTTP |
|--------|------|------|
| VAL-001 | 参数验证失败 | 400 |
| AUTH-001 | 未登录 | 401 |
| PERM-001 | 无权限 | 403 |
| RES-001 | 资源不存在 | 404 |
| STATE-001 | 状态转换非法 | 409 |

---

### CB-BE-004: PermissionFilter (权限过滤)

| 角色 | 数据范围 | 技术层判断 |
|------|---------|-----------|
| ceo/finance/admin | 全部数据 | role IN (admin, finance) |
| project_owner | 本项目 | is_project_owner=true |
| pitcher/account_manager | 本人 | role IN (media_buyer, account_manager) |

```python
# backend/core/permissions.py
def apply_permission_filter(query, model, user, project_field="project_id", user_field="created_by"):
    if user.role in ["admin", "finance"]:
        return query
    if user.is_project_owner:  # 业务属性判断
        return query.filter(getattr(model, project_field).in_([p.id for p in user.managed_projects]))
    return query.filter(getattr(model, user_field) == user.id)
```

---

### CB-BE-005: StateMachine (状态机)

**推荐库**: `transitions` (5k+ stars)
**日报状态机**: `raw_submitted → trend_pending → trend_ok/trend_flagged → trend_resolved → final_pending → final_confirmed → final_locked`

```python
# backend/core/state_machine.py
from transitions import Machine

class DailyReportStateMachine:
    states = ["raw_submitted", "trend_pending", "trend_ok", "trend_flagged",
              "trend_resolved", "final_pending", "final_confirmed", "final_locked"]
    transitions = [
        {"trigger": "start_trend_review", "source": "raw_submitted", "dest": "trend_pending"},
        {"trigger": "approve_trend", "source": "trend_pending", "dest": "trend_ok"},
        {"trigger": "flag_trend", "source": "trend_pending", "dest": "trend_flagged"},
        {"trigger": "resolve_trend", "source": "trend_flagged", "dest": "trend_resolved"},
        {"trigger": "start_final_review", "source": ["trend_ok", "trend_resolved"], "dest": "final_pending"},
        {"trigger": "confirm_final", "source": "final_pending", "dest": "final_confirmed"},
        {"trigger": "lock", "source": "final_confirmed", "dest": "final_locked"},
    ]
```

---

### CB-BE-006: AuditLog (审计日志)

```python
# backend/models/audit_log.py
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)
    action = Column(String(20))  # create/update/delete
    changes = Column(JSON)
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
```

---

### CB-BE-007: LedgerEntry (账本记账)

**基准**: DATA_SCHEMA.md v5.11 §3.4.4

```python
# backend/models/ledger_entry.py
class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("ad_accounts.id"))
    entry_type = Column(String(20))  # topup/spend/refund/adjust
    direction = Column(String(10))   # debit/credit
    amount = Column(Numeric(12, 2))
    balance_after = Column(Numeric(12, 2))
    reference_type = Column(String(50))
    reference_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
```

---

### CB-BE-008: KPICalculator (KPI计算)

```python
# backend/services/kpi_calculator.py
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass

@dataclass
class KPIResult:
    cpl: Decimal | None  # Cost Per Lead = spend / conversions
    roas: Decimal | None # Return On Ad Spend = revenue / spend
    roi: Decimal | None  # ROI = (revenue - cost) / cost

class KPICalculator:
    @staticmethod
    def calculate(spend, conversions, revenue=Decimal("0")):
        cpl = (spend / conversions).quantize(Decimal("0.01")) if conversions > 0 else None
        roas = (revenue / spend).quantize(Decimal("0.01")) if spend > 0 else None
        return KPIResult(cpl=cpl, roas=roas, roi=None)
```

---

## 六、代码块使用矩阵

| 模块 | Pagination | Response | ErrorCodes | Permission | StateMachine | Audit | Ledger | KPI |
|------|------------|----------|------------|------------|--------------|-------|--------|-----|
| 日报 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ |
| 充值 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| 账户 | ✅ | ✅ | ✅ | ✅ | - | ✅ | ✅ | - |
| 项目 | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ |
| 用户 | ✅ | ✅ | ✅ | - | - | ✅ | - | - |
| 驾驶舱 | - | ✅ | ✅ | ✅ | - | - | - | ✅ |
| 结算 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |

---

## 七、GitHub 搜索参考

| 代码块 | 搜索词 | 推荐库 |
|--------|--------|--------|
| Pagination | `fastapi pagination sqlalchemy` | fastapi-pagination |
| StateMachine | `python transitions state machine` | transitions |
| AuditLog | `sqlalchemy audit trail history` | sqlalchemy-continuum |

---

**详细代码模板**: 见 `D:\project\AI_ad_spend02iles\BACKEND_CODE_BLOCKS_GITHUB_SEARCH.md`
**维护者**: AI 广告代投系统开发团队


---

## 五、后端代码块详细模板

### CB-BE-001: Pagination (分页)

**推荐库**: \ (1k+ stars)
**安装**: 
---

### CB-BE-002: ResponseEnvelope (响应封装)

**核心文件**: 
---

### CB-BE-003: ErrorCodes (错误码)

**基准**: ERROR_CODES_SOT.md v2.1

**常用错误码**:
| 错误码 | 含义 | HTTP |
|--------|------|------|
| VAL-001 | 参数验证失败 | 400 |
| AUTH-001 | 未登录 | 401 |
| PERM-001 | 无权限访问 | 403 |
| RES-001 | 资源不存在 | 404 |
| STATE-001 | 状态转换非法 | 409 |
| BIZ-001 | 业务规则冲突 | 422 |
