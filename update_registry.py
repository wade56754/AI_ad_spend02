#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Update code-blocks-registry.md with backend code block templates"""

import os

os.chdir(r'D:\project\AI_ad_spend02')

# The backend code blocks detail content (summary version)
backend_templates = '''

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

| 角色 | 数据范围 |
|------|---------|
| ceo/finance/admin | 全部数据 |
| project_owner | 本项目 |
| supervisor | 本团队 |
| pitcher/account_manager | 本人 |

```python
# backend/core/permissions.py
def apply_permission_filter(query, model, user, project_field="project_id", user_field="created_by"):
    if user.role in ["ceo", "finance", "admin"]:
        return query
    if user.role == "project_owner":
        return query.filter(getattr(model, project_field).in_([p.id for p in user.managed_projects]))
    if user.role == "supervisor":
        return query.filter(getattr(model, user_field).in_([u.id for u in user.team_members]))
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

**基准**: LEDGER_SOT.md v1.1

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

**详细代码模板**: 见 `D:\project\AI_ad_spend02\files\BACKEND_CODE_BLOCKS_GITHUB_SEARCH.md`
**维护者**: AI 广告代投系统开发团队
'''

# Append to the registry file
registry_path = r'.claude\skills\ai-ad-code-factory\knowledge\code-blocks-registry.md'
with open(registry_path, 'a', encoding='utf-8') as f:
    f.write(backend_templates)

print(f"Updated {registry_path}")

# Verify
with open(registry_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(f"Total lines: {len(lines)}")
