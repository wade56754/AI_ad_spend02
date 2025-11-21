# AI广告代投系统 - 项目规则总纲（SoT Master）

> **文档版本**: v2.0
> **文档类型**: 项目强制规范（Claude 项目记忆）
> **适用范围**: 所有开发/重构/生成代码工作
> **规范级别**: 🔴 强制执行
> **生效日期**: 2025-11-18
> **维护责任**: 规则总监 + 系统架构团队

---

## 📚 一、SoT 文档体系（唯一真相源）

本项目采用**分层 SoT 架构**，所有开发必须严格遵循以下文档优先级：

### 1. SoT-Data: 数据库定义
**文档**: `docs/core/DATA_SCHEMA.md` (v5.0)

- **作用**: 数据库字段、表结构、类型定义的唯一来源
- **核心规则**:
  - 所有表名、字段名必须与此文档完全一致
  - 主键规则：UUID（用户/渠道）、BIGSERIAL（业务表）
  - 金额字段：必须 `DECIMAL(15,2)`
  - 时间字段：必须 `TIMESTAMPTZ`
  - 状态字段：枚举值必须引用 `STATE_MACHINE.md`

### 2. SoT-State: 状态机定义
**文档**: `docs/core/STATE_MACHINE.md` (v2.3)

- **作用**: 业务状态枚举和合法流转的唯一来源
- **核心状态**:
  - 充值: `draft → pending_review → finance_approve → paid → completed`
  - 日报: `draft → pending → approved/rejected`
  - 项目: `draft → active → suspended → archived`
  - 账户: `new → testing → active → suspended → dead/archived`
- **铁律**: 禁止自创状态值，所有流转必须记录审计日志

### 3. SoT-Implementation: 实现规范
**文档**: `docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md` (v3.x)

- **作用**: 实现规范、角色权限、架构约束
- **核心约束**:
  - 合法角色**仅 5 个**: `admin` | `finance` | `data_operator` | `account_manager` | `media_buyer`
  - 技术栈: FastAPI + Pydantic v2 + SQLAlchemy (同步) + Supabase Auth + Redis
  - 前端: Next.js 16.0.2 + TypeScript + Tailwind + shadcn/ui
  - **当前未启用 RLS**，权限通过 Service 层 RBAC 实现

### 4. SoT-API: API 开发流程
**文档**: `docs/core/API_DEVELOPMENT_FLOW.md` (v7.0)

- **作用**: API 开发流程、响应格式、错误处理规范
- **强制流程**: Schema → Service → Router → Test → Exception Handler
- **响应格式**: 必须使用 `success_response`/`error_response` Envelope
- **前端调用**: 必须使用 `apiFetch`（来自 `lib/api.ts`）

---

## 🔴 二、五大不可违背铁律

### 1. 字段禁止自创
**规则**: 所有表名、字段名必须在 `DATA_SCHEMA.md` 中定义

```markdown
❌ 错误: 使用了不存在的字段 `topup_amount`
✅ 正确: 查找 DATA_SCHEMA.md § 3.4.1，使用 `amount`
```

### 2. 角色限定为 5 个
**规则**: 仅允许使用 5 个标准角色，禁止旧角色名

```python
# ✅ 正确
VALID_ROLES = ["admin", "finance", "data_operator", "account_manager", "media_buyer"]

# ❌ 错误（历史兼容，禁止在新代码中使用）
OLD_ROLES = ["manager", "data_clerk", "trader"]
```

**历史映射**（仅用于理解旧代码）:
- `data_clerk` → `data_operator`
- `manager` → `account_manager`
- `recharge_requests` → `topup_requests`

### 3. 状态值禁止自创
**规则**: 所有状态必须符合 `STATE_MACHINE.md` 定义

```markdown
❌ 错误: 使用了自创状态 `processing`
✅ 正确: 查找 STATE_MACHINE.md § 充值申请状态机，使用 `pending_review`
```

### 4. 前端禁止绕过 BFF
**规则**: 前端必须通过 `apiFetch` 调用 FastAPI，禁止直连数据库

```typescript
// ❌ 错误
const data = await fetch('/api/...')

// ❌ 错误
const { data } = await supabase.from('projects').select('*')

// ✅ 正确
const data = await apiFetch('/api/v1/projects')
```

### 5. API 响应禁止裸数据
**规则**: 必须使用 Envelope 格式

```python
# ❌ 错误
return {"id": 1, "name": "..."}

# ✅ 正确
return success_response(
    data={"id": 1, "name": "..."},
    message="操作成功"
)
```

---

## 🏗️ 三、技术栈约束（不可变更）

### 后端技术栈
- **框架**: FastAPI
- **验证**: Pydantic v2（`ConfigDict(from_attributes=True)`）
- **ORM**: SQLAlchemy（同步版本）
- **认证**: Supabase Auth（**禁止自建 JWT/bcrypt**）
- **缓存**: Redis（仅速率限制/会话缓存，**无队列/RQ**）

### 前端技术栈
- **框架**: Next.js 16.0.2（App Router）
- **语言**: TypeScript（严格模式）
- **UI**: shadcn/ui + Tailwind CSS
- **HTTP**: 必须使用 `apiFetch`（`lib/api.ts`）

### 数据库
- **类型**: PostgreSQL 15（Supabase 托管）
- **权限**: **当前未启用 RLS**，通过 Service 层 RBAC 实现
- **迁移**: Alembic

---

## 👥 四、角色与权限规则

### 五角色体系
| 角色 | 职责 | 关键权限 |
|------|------|----------|
| `admin` | 系统管理员 | 全部权限 |
| `finance` | 财务 | 充值终审、对账、报表 |
| `data_operator` | 数据运营 | 日报审核、数据管理 |
| `account_manager` | 账户管理员 | 项目管理、账户分配 |
| `media_buyer` | 广告投手 | 日报提交、充值申请 |

### 核心权限分工
**日报流程**:
- 提交: `media_buyer`
- 审核: `data_operator`（`admin` 兜底）

**充值流程**:
- 发起: `media_buyer` / `account_manager`
- 复核: `data_operator`
- 终审: `finance`
- 入账: `finance` / `system`（自动）

**项目管理**:
- 维护: `account_manager`
- 干预: `admin`

---

## 💾 五、数据库设计铁律

### 主键规则
```sql
-- 跨系统实体（用户/渠道）: UUID
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid()
);

-- 业务表（项目/账户/日报/充值）: BIGSERIAL
CREATE TABLE projects (
    id BIGSERIAL PRIMARY KEY
);
```

### 数据类型约束
| 用途 | PostgreSQL | SQLAlchemy | Python | TypeScript |
|------|-----------|-----------|--------|------------|
| 金额 | `DECIMAL(15,2)` | `Numeric(15,2)` | `Decimal` | `string`（传输）/`number`（展示） |
| 时间 | `TIMESTAMPTZ` | `DateTime(timezone=True)` | `datetime` | `string` (ISO 8601) |
| 主键 | `BIGSERIAL/UUID` | `BigInteger/UUID` | `int/uuid.UUID` | `number/string` |

### 外键一致性
```python
# ✅ 正确：外键类型与被引用主键一致
class Project(Base):
    id = Column(BigInteger, primary_key=True)  # BIGSERIAL
    account_manager_id = Column(UUID(as_uuid=True), ForeignKey('user_profiles.id'))  # UUID

# ❌ 错误：外键类型不匹配
class Project(Base):
    account_manager_id = Column(BigInteger, ForeignKey('user_profiles.id'))  # 错误！user_profiles.id 是 UUID
```

---

## 🔄 六、状态机约束

### 核心状态流转

**充值申请** (`topup_requests.status`):
```
draft → pending_review → finance_approve → paid → completed
   ↓                           ↓
cancelled                   rejected
```

**日报** (`daily_reports.status`):
```
draft → pending → approved
                    ↓
                 rejected
```

**项目** (`projects.status`):
```
draft → active → suspended → archived
```

**广告账户** (`ad_accounts.status`):
```
new → testing → active → suspended → dead
                                      ↓
                                  archived
```

### 状态变更规则
1. **禁止直接 UPDATE**: 必须通过 Service 层业务方法
2. **必须审计**: 所有流转记录到 `audit_logs`（操作者、时间、旧/新状态、理由）
3. **权限校验**: 不同角色只能执行允许的状态转换
4. **终态保护**: 终态不可回退（除 `admin` 审计）

---

## 🌐 七、API 开发强制流程

### 开发顺序（不可跨越）
```
1. 查阅 SoT 文档 → 2. 数据库模型 + Alembic 迁移 →
3. Service 层 + 单元测试 → 4. Router 层 →
5. 集成/E2E 测试 + 文档
```

### 统一响应格式（Envelope）

**成功响应**:
```json
{
  "success": true,
  "data": {"id": 1, "status": "pending"},
  "message": "操作成功",
  "code": "SUCCESS",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-18T10:00:00Z"
}
```

**错误响应**:
```json
{
  "success": false,
  "error": {
    "code": "BIZ_003",
    "message": "状态转换非法",
    "details": {
      "from": "approved",
      "to": "pending",
      "help": "请查阅 STATE_MACHINE.md 了解合法的状态转换"
    }
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-18T10:00:00Z"
}
```

### 错误码来源
**必须来自**: `docs/ERROR_CODES.md`

```python
# ✅ 正确
from core.error_codes import AuthErrorCodes, BusinessErrorCodes
raise BusinessError(code=BusinessErrorCodes.INVALID_STATE_TRANSITION.code)

# ❌ 错误
raise HTTPException(status_code=400, detail="状态错误")  # 没有使用标准错误码
```

---

## 🚫 八、AI 使用禁止清单

### 严禁行为（违规立即回退）

1. ❌ **发明新的字段/表/状态/角色/错误码**
   - 所有定义必须来自 SoT 文档

2. ❌ **引用历史废弃方案**
   - bolt.new 在线前端
   - 本地 bcrypt/自建 JWT
   - 强制启用 RLS
   - Redis 队列 (RQ/Celery)

3. ❌ **绕过 Service 层**
   - 在 Router 中直接写 SQL
   - 直接操作数据库 Session

4. ❌ **前端绕过 BFF**
   - 使用 `fetch()` 而非 `apiFetch`
   - 直接调用 Supabase API（Auth 除外）

5. ❌ **使用旧命名**
   - 角色: `data_clerk` / `manager` / `trader`
   - 表名: `recharge_requests` / `users`（应用层）

6. ❌ **修改技术栈**
   - 未经批准更改 SoT 定义的框架、库、配置

---

## ✅ 九、AI 自检清单（每次生成代码前必查）

### 1. 数据库一致性检查
```markdown
□ 我使用的表名是否在 DATA_SCHEMA.md § 2 中存在？
  表名: ____________ → 查找结果: ✅/❌

□ 我使用的字段名是否在对应表定义中存在？
  字段名: ____________ → 查找 DATA_SCHEMA.md § 3.x: ✅/❌

□ 数据类型是否正确？
  - 金额用 Decimal？ ✅/❌
  - 时间用 datetime/TIMESTAMPTZ？ ✅/❌
  - 主键类型与外键一致？ ✅/❌
```

### 2. 角色合法性检查
```markdown
□ 我使用的角色是否在以下列表中？
  [admin, finance, data_operator, account_manager, media_buyer]

  我的代码中使用了: ____________
  检查结果: ✅/❌

□ 我是否不小心使用了旧角色名？
  [data_clerk, manager, trader]
  检查结果: ✅ 未使用 / ❌ 使用了
```

### 3. 状态机合规检查
```markdown
□ 我的状态值是否在 STATE_MACHINE.md 中定义？
  模块: ____________ (如 topup_requests)
  状态值: ____________
  查找结果: ✅/❌

□ 我的状态转换是否合法？
  从: ____________ → 到: ____________
  STATE_MACHINE.md 中存在此路径: ✅/❌
```

### 4. API 调用方式检查
```markdown
□ 前端是否使用 apiFetch？
  import { apiFetch } from '@/lib/api': ✅/❌

□ 后端是否有权限验证？
  使用 @require_role 或 get_current_user: ✅/❌

□ 是否绕过 BFF 直接访问数据库？
  检查结果: ✅ 未绕过 / ❌ 绕过了
```

### 5. 响应格式检查
```markdown
□ API 响应是否使用 Envelope？
  return success_response(...): ✅/❌
  或使用 BusinessError/PermissionError: ✅/❌

□ 是否直接返回 dict？
  检查结果: ✅ 未直接返回 / ❌ 直接返回了
```

### 6. 历史兼容陷阱检查
```markdown
□ 是否使用了历史名称？
  禁止使用:
  - 角色: data_clerk / manager / trader
  - 表名: recharge_requests / users (应用层)
  - 方案: 本地 bcrypt / 自建 JWT / RLS / Redis 队列

  检查结果: ✅ 未使用 / ❌ 使用了
```

### 7. 数据类型检查
```markdown
□ 金额字段是否使用 Decimal？
  from decimal import Decimal: ✅/❌

□ 时间字段是否使用 datetime？
  from datetime import datetime: ✅/❌

□ 是否使用了 float 表示金额？
  检查结果: ✅ 未使用 / ❌ 使用了（错误！）
```

---

## 📌 十、冲突处理流程

### 当 AI 输出与 SoT 冲突时

1. **立即停止**代码生成
2. **重新加载**相关 SoT 文档
3. **向用户说明**冲突点和正确做法
4. **重新生成**符合 SoT 的代码

### SoT 文档优先级
```
DATA_SCHEMA.md > STATE_MACHINE.md >
AI_AD_SYSTEM_MAIN_DOCUMENT.md > API_DEVELOPMENT_FLOW.md >
其他文档
```

### 文档更新触发
- 当 SoT 文档变更时，必须立即同步更新本规则总纲
- 所有 AI 工具配置文件（`.cursorrules` / `.claude/*`）必须同步

---

## 📚 十一、快速参考

### 合法角色（仅 5 个）
```python
VALID_ROLES = [
    "admin",           # 系统管理员
    "finance",         # 财务
    "data_operator",   # 数据运营
    "account_manager", # 账户管理员
    "media_buyer"      # 广告投手
]
```

### 充值状态（完整）
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

### 日报状态
```python
DAILY_REPORT_STATES = [
    "draft",      # 草稿
    "pending",    # 待审核
    "approved",   # 已通过
    "rejected"    # 已驳回
]
```

### 标准响应示例
```python
# 成功
return success_response(
    data=result,
    message="操作成功"
)

# 业务错误
raise BusinessError(
    code=BusinessErrorCodes.INVALID_STATE_TRANSITION,
    message="状态转换非法"
)

# 权限错误
raise PermissionError(
    code=AuthErrorCodes.INSUFFICIENT_PERMISSIONS,
    message="权限不足"
)
```

---

## 📝 附录：文档索引

### SoT 文档路径
- `docs/core/DATA_SCHEMA.md` - 数据库定义（v5.0）
- `docs/core/STATE_MACHINE.md` - 状态机定义（v2.3）
- `docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md` - 实现规范（v3.x）
- `docs/core/API_DEVELOPMENT_FLOW.md` - API 开发流程（v7.0）
- `docs/ERROR_CODES.md` - 错误码定义

### 模块文档
- `docs/modules/topup/` - 充值模块
- `docs/modules/daily_report/` - 日报模块
- `docs/modules/project/` - 项目模块
- `docs/modules/reconciliation/` - 对账模块

### AI 工具配置
- `.claude/PROJECT_RULES.md` - 本文件（项目记忆）
- `.claude/settings.local.json` - Claude Code 配置
- `.cursorrules` - Cursor 配置（如有）

---

**规则总纲版本**: v2.0
**生效日期**: 2025-11-18
**最后更新**: 2025-11-18
**下次审查**: SoT 文档变更时
**维护责任人**: 规则总监 + 系统架构团队

---

## 🔒 执行承诺

- **开发团队**：开始任务前必须确认已阅读并理解本规则总纲
- **Code Review**：按此规则执行，发现冲突需立即纠正
- **AI 工具**：每次生成代码前必须执行完整自检清单
- **架构变更**：必须先更新 SoT 文档及本规则总纲，再进入开发环节

**违规处理**: PR 自动拒绝 / 代码回滚 / 重新生成
