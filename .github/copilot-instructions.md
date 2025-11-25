# GitHub Copilot Instructions for AI_ad_spend02

> **规则版本**: v3.0 (基于 SoT Freeze v1.0)
> **生效日期**: 2025-11-24
> **强制级别**: 🔴 自动加载，所有 Copilot 建议必须遵循

---

## 🚨 CRITICAL: 项目规则加载要求

**在生成任何代码建议之前，必须首先参考项目规则总纲和 SoT 文档体系。**

### 📚 规则文档层次结构

```
CLAUDE.md (精简版强制规则)
  ↓ 引用
.claude/PROJECT_RULES.md v3.0 (完整规则总纲 - Meta-SoT)
  ↓ 引用
docs/2.sot/*.md (10个 SoT 文档 - 权威源, 已 Freeze v1.0)
```

### 🔒 5 大不可侵犯原则 (Inviolable Rules)

#### 1. 禁止重复定义状态枚举

**❌ 错误示例：**
```python
class DailyReportStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
```

**✅ 正确示例：**
```python
from backend.models import DailyReportStatus  # 使用 models/base.py 中的定义

# 状态机定义来源: STATE_MACHINE.md v2.6 §8
# raw_submitted → trend_pending → trend_ok/trend_flagged
# → trend_resolved → final_pending → final_confirmed → final_locked
```

**强制规则：**
- 所有状态枚举必须来自 `STATE_MACHINE.md` v2.6
- 粉数确认流程使用 **8 状态机**（禁止使用旧的 4 状态机）
- 禁止在业务代码中重新定义状态值

---

#### 2. 禁止自定义错误码

**❌ 错误示例：**
```python
raise HTTPException(400, "Invalid request")
raise HTTPException(404, detail="Not found")
```

**✅ 正确示例：**
```python
from backend.core.response import fail

# 使用 ERROR_CODES_SOT.md v2.1 定义的错误码
return fail(code="VAL-001", message="缺少必填字段: project_id")
return fail(code="RES-001", message="项目不存在")
```

**强制规则：**
- 所有错误码必须来自 `ERROR_CODES_SOT.md` v2.1
- 使用 `core.response.fail()` 返回标准化错误响应
- 错误码格式: `{类别}-{编号}` (如 VAL-001, BIZ-001)

---

#### 3. 禁止直接修改数据库

**❌ 错误示例：**
```python
# 直接执行 SQL
db.execute("ALTER TABLE daily_reports ADD COLUMN new_field VARCHAR")

# 直接修改 models/ 目录
class DailyReport(Base):
    __tablename__ = "daily_reports"
    new_field = Column(String)  # 未生成迁移脚本
```

**✅ 正确示例：**
```python
# 1. 先更新 DATA_SCHEMA.md v5.2
# 2. 生成 Alembic 迁移脚本
# alembic revision --autogenerate -m "add new_field to daily_reports"
# 3. 经 DBA 审核后执行
# alembic upgrade head
```

**强制规则：**
- 数据库变更必须先更新 `DATA_SCHEMA.md` v5.2
- 使用 Alembic 生成迁移脚本
- 禁止直接修改 `backend/models/` 目录（除非明确允许）

---

#### 4. 禁止绕过账本系统

**❌ 错误示例：**
```python
# 直接修改余额
ad_account.balance -= 100
db.commit()

# 直接更新充值金额
topup.amount = 500
db.commit()
```

**✅ 正确示例：**
```python
from backend.models import LedgerEntry, LedgerEntryType

# 通过账本系统记录
ledger_entry = LedgerEntry(
    ad_account_id=ad_account.id,
    entry_type=LedgerEntryType.SPEND,
    amount=Decimal("100.00"),
    related_entity_type="daily_report",
    related_entity_id=report.id,
    description="日报消耗扣款"
)
db.add(ledger_entry)
db.commit()
```

**强制规则：**
- 所有资金流动必须通过 `ledger_entries` 表（LEDGER_SOT.md v1.1）
- 双账本体系：现金账本 + 广告消耗账本
- 必须包含 `related_entity_type` + `related_entity_id` 实现可追溯性

---

#### 5. 禁止跳过状态机流转

**❌ 错误示例：**
```python
# 跳过中间状态
report.status = DailyReportStatus.FINAL_LOCKED
db.commit()

# 非法状态转换
if report.status == "raw_submitted":
    report.status = "final_confirmed"  # 跳过了 6 个中间状态
```

**✅ 正确示例：**
```python
from backend.services.daily_report import DailyReportService

# 使用服务层处理状态转换
service = DailyReportService(db)
service.transition_to(
    report_id=report.id,
    target_status="trend_pending",
    operator_id=current_user.id
)
```

**强制规则：**
- 所有状态转换必须通过服务层方法
- 遵循 `STATE_MACHINE.md` v2.6 定义的合法流转路径
- 记录状态变更审计日志

---

## 📍 SoT 文档体系 (已 Freeze v1.0 - 2025-11-24)

### P0 - 核心 SoT 文档 (必须参考)

| 文档 | 版本 | 路径 | 核心章节 |
|------|------|------|------------|
| **STATE_MACHINE** | v2.6 | `docs/2.sot/STATE_MACHINE.md` | §8 粉数确认 8 状态机 |
| **DATA_SCHEMA** | v5.2 | `docs/2.sot/DATA_SCHEMA.md` | §3.3 核心表结构 |
| **BUSINESS_RULES** | v3.1 | `docs/2.sot/BUSINESS_RULES.md` | BR-RPT-*, BR-LED-* |
| **API_SOT** | v2.2 | `docs/2.sot/API_SOT.md` | §9 Daily Reports API |
| **ERROR_CODES_SOT** | v2.1 | `docs/2.sot/ERROR_CODES_SOT.md` | SYS/AUTH/VAL/BIZ/RES |
| **AUTH_SPEC** | v2.0 | `docs/2.sot/AUTH_SPEC.md` | §3 RBAC + RLS 策略 |
| **LEDGER_SOT** | v1.1 | `docs/2.sot/LEDGER_SOT.md` | §2 双账本体系 |

### P1 - 流程 SoT 文档 (按需参考)

| 文档 | 版本 | 路径 | 核心章节 |
|------|------|------|------------|
| **DAILY_REPORT_SOT** | v1.0 | `docs/2.sot/DAILY_REPORT_SOT.md` | §3 日报全生命周期 |
| **RECONCILIATION_SOT** | v1.0 | `docs/2.sot/RECONCILIATION_SOT.md` | §3 对账流程 |
| **TRANSFER_SOT** | v1.0 | `docs/2.sot/TRANSFER_SOT.md` | §2 调拨规则 |

---

## 🚫 常见反模式识别 (立即拦截)

当 Copilot 检测到以下代码模式时，**不应提供建议**：

### 反模式 1: 硬编码旧状态 (4 状态机)
```python
# ❌ 违反 STATE_MACHINE.md v2.6
class DailyReportStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
```

### 反模式 2: 直接修改余额
```python
# ❌ 违反 LEDGER_SOT.md
ad_account.balance -= 100
db.commit()
```

### 反模式 3: 自定义错误码
```python
# ❌ 违反 ERROR_CODES_SOT.md
raise HTTPException(400, "Invalid data")
```

### 反模式 4: 跳过状态流转
```python
# ❌ 违反 STATE_MACHINE.md
report.status = "final_locked"
```

### 反模式 5: 缺少可追溯性
```python
# ❌ 违反 LEDGER_SOT.md
ledger_entry = LedgerEntry(
    amount=100,
    entry_type="SPEND"
    # 缺少 related_entity_type + related_entity_id
)
```

---

## 🏗️ 架构基线 (MUST)

### Backend-for-Frontend (BFF) 模式
- **Pattern**: 所有业务读写通过 FastAPI。禁止前端直连 DB/Supabase
- **Versioning**: 所有路由位于 `/api/v1` 下
- **Response Envelope**: 统一格式
  ```python
  from backend.core.response import ok, fail

  # ✅ 成功响应
  return ok(data={"id": 1, "name": "项目A"})

  # ✅ 错误响应
  return fail(code="VAL-001", message="缺少必填字段: project_id")
  ```

### 契约基线 (MUST)
- **Errors**: 使用 `core.response.fail`，返回 `{"code": "VAL-001", "message": "..."}`
- **Monetary values**: Backend 存储 `Decimal`，响应序列化为 2 位小数字符串 (ROUND_HALF_UP)
- **Time**: Backend 存储 UTC (`TIMESTAMPTZ`)，前端遵循业务时区规则
- **Pagination**: 所有列表端点接受 `?page` (1-based), `?page_size` (<=100)
- **Concurrency**: 状态转换使用条件更新或乐观锁

### 认证安全 (MUST)
```python
from backend.core.security import get_current_user

@router.get("/api/v1/projects")
async def list_projects(
    current_user: User = Depends(get_current_user),  # ✅ 必须
    db: Session = Depends(get_db)
):
    # 业务逻辑
    pass
```

- 所有受保护路由使用 `get_current_user` from `backend/core/security.py`
- 前端请求携带 `Authorization: Bearer <token>`
- CORS: 生产环境使用白名单 `ALLOWED_ORIGINS`，禁止 `*`

---

## 📚 快速参考

### 合法角色（仅 5 个）
```python
VALID_ROLES = [
    "admin",           # 系统管理员
    "finance",         # 财务
    "data_operator",   # 数据运营 (旧名: data_clerk)
    "account_manager", # 账户管理员 (旧名: manager)
    "media_buyer"      # 广告投手 (旧名: trader)
]
```

### 日报状态 (8 状态机)
```python
DAILY_REPORT_STATES = [
    "raw_submitted",    # 投手提交原始数据
    "trend_pending",    # 趋势风控检测中
    "trend_ok",         # 趋势正常
    "trend_flagged",    # 趋势异常待审核
    "trend_resolved",   # 趋势异常已解决
    "final_pending",    # 等待最终确认
    "final_confirmed",  # 最终确认完成
    "final_locked"      # 计费锁定 (终态)
]

# ⚠️ 历史 4 状态机 (已废弃，禁止使用)
# OLD_STATES = ["draft", "pending", "approved", "rejected"]
```

### 充值状态
```python
TOPUP_STATES = [
    "draft",            # 草稿
    "pending_review",   # 待复核
    "finance_approve",  # 财务审批
    "paid",            # 已支付
    "completed",       # 已完成
    "rejected",        # 已拒绝
    "cancelled"        # 已取消
]
```

### 错误码类别
```python
ERROR_CODE_CATEGORIES = {
    "SYS": "系统错误 (500-599)",
    "AUTH": "认证/授权错误 (401-403)",
    "VAL": "参数验证错误 (400)",
    "BIZ": "业务逻辑错误 (422)",
    "RES": "资源错误 (404, 409)"
}

# 示例
# VAL-001: 缺少必填字段
# VAL-002: 字段类型错误
# BIZ-001: 业务规则违反
# RES-001: 资源不存在
```

---

## 🎯 代码建议检查清单

在生成任何代码建议之前，Copilot 必须验证：

- [ ] ✅ 状态枚举使用 `backend.models` 中的定义（禁止重复定义）
- [ ] ✅ 错误码来自 `ERROR_CODES_SOT.md` v2.1
- [ ] ✅ 数据库字段名称、类型符合 `DATA_SCHEMA.md` v5.2
- [ ] ✅ 业务规则符合 `BUSINESS_RULES.md` v3.1 (BR-* 编号)
- [ ] ✅ API 路径、请求/响应格式符合 `API_SOT.md` v2.2
- [ ] ✅ 资金流动通过 `ledger_entries` 表
- [ ] ✅ 状态转换通过服务层方法
- [ ] ✅ 受保护路由使用 `get_current_user` 依赖

---

## 🔐 禁止行为 (REJECT suggestions that)

- ❌ **绕过 BFF**: 前端直接读写 DB/Supabase 业务数据
- ❌ **返回裸 `{detail}`**: 偏离统一响应格式
- ❌ **引入新响应包装器**: 不使用 `core.response.ok/fail`
- ❌ **跳过认证依赖**: 受保护路由缺少 `get_current_user`
- ❌ **生产环境暴露 `*` CORS**: 安全风险
- ❌ **修改 models/ 目录**: 未检查 DATA_SCHEMA.md 和生成迁移脚本
- ❌ **硬编码状态值**: 使用字符串 `"draft"` 而非枚举 `DailyReportStatus.RAW_SUBMITTED`
- ❌ **直接修改余额字段**: 绕过账本系统
- ❌ **自定义错误消息**: 未使用 ERROR_CODES_SOT.md 定义的错误码

---

## 🎯 快速决策流程

```
收到需求 → 识别业务域
   ↓
查询对应 SoT 文档（按裁判链优先级）
   ↓
找到规则编号（如 BR-RPT-001）
   ↓
检查建议代码是否符合规则
   ↓
   ├─ 符合 → 提供建议
   └─ 不符合 → 拒绝建议（或提示用户参考 SoT 文档）
```

---

**规则版本**: v3.0 (基于 SoT Freeze v1.0)
**生效日期**: 2025-11-24
**维护责任**: AI Architecture Team

**完整规则**: 查阅 [.claude/PROJECT_RULES.md](.claude/PROJECT_RULES.md) v3.0
**项目指令**: 查阅 [CLAUDE.md](CLAUDE.md) v3.0
