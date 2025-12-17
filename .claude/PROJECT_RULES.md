---
# Cursor Rules 格式 - YAML Frontmatter
alwaysApply: true
description: "AI 广告代投系统 - 项目规则总纲 (Project Constitution)"
version: "3.5"
author: "AI Architecture Team"
lastUpdated: "2025-12-17"

# 六大规则分类 (参考 Cursor Rules & Prompts)
categories:
  - id: "constitution"
    name: "系统宪法"
    description: "SoT 裁判链、不可侵犯原则"
    sections: ["§一", "§二"]

  - id: "code-style"
    name: "代码风格"
    description: "技术栈约束、响应格式、类型检查"
    sections: ["§三", "§七"]

  - id: "organization"
    name: "项目组织"
    description: "ASDD 4层架构、文档路径、模块结构"
    sections: ["§十三"]

  - id: "constraints"
    name: "约束规则"
    description: "角色权限、数据库设计、状态机约束"
    sections: ["§四", "§五", "§六"]

  - id: "workflow"
    name: "工作流程"
    description: "API开发流程、OpenSpec变更流程、回归测试"
    sections: ["§七", "§十四", "§后端回归测试"]

  - id: "ai-behavior"
    name: "AI 行为"
    description: "AI禁止清单、自检清单、冲突处理"
    sections: ["§八", "§九", "§十", "§十二"]

# 基准文档
baseline:
  overview_freeze: "FREEZE_MANIFEST_v1.0.md"
  sot_freeze: "SOT_FREEZE_MANIFEST_v2.6.md"
  dev_guides_freeze: "DEV_GUIDES_FREEZE_MANIFEST_v2.1.md"
  architecture_freeze: "ARCHITECTURE_FREEZE_MANIFEST_v1.0.md"

# 技术栈 (快速参考)
techStack:
  backend:
    framework: "FastAPI"
    orm: "SQLAlchemy 2.x"
    validation: "Pydantic v2"
    database: "PostgreSQL (Supabase)"
    auth: "Supabase Auth + JWT"
  frontend:
    framework: "Next.js 14 (App Router)"
    language: "TypeScript (strict)"
    ui: "shadcn/ui + Tailwind CSS"
    http: "apiFetch (lib/api.ts)"

# SoT 裁判链 (快速参考)
sotChain:
  - name: "MASTER.md"
    version: "v3.4"
    role: "系统宪法"
  - name: "STATE_MACHINE.md"
    version: "v2.6"
    role: "状态定义"
  - name: "DATA_SCHEMA.md"
    version: "v5.2"
    role: "数据结构"
  - name: "BUSINESS_RULES.md"
    version: "v3.1"
    role: "业务规则"
  - name: "API_SOT.md"
    version: "v9.0"
    role: "API契约"
  - name: "ERROR_CODES_SOT.md"
    version: "v2.1"
    role: "错误码"
  - name: "AUTH_SPEC.md"
    version: "v2.0"
    role: "认证授权"
  - name: "LEDGER_SOT.md"
    version: "v1.1"
    role: "账本规则"
---

# AI 广告代投系统 - 项目规则总纲 (Project Constitution)

> **文档版本**: v3.5 (基于 ASDD Freeze v1.0 + SoT Freeze v2.6 + Dev-Guides Freeze v2.1 + Architecture Freeze v1.0 + OpenSpec v1.0 + Cursor Rules Format)
> **文档类型**: Claude/SuperClaude 的"世界观" - SoT 体系的裁判规则
> **适用范围**: 所有开发/重构/代码生成工作
> **规范级别**: 🔴 强制执行 (CI/CD 验证)
> **生效日期**: 2025-12-02
> **维护责任**: AI Architecture Team
> **Freeze 基准**:
>   - FREEZE_MANIFEST_v1.0.md (Overview Layer Freeze v1.0)
>   - SOT_FREEZE_MANIFEST_v2.6.md (SoT Layer Freeze v2.6)
>   - DEV_GUIDES_FREEZE_MANIFEST_v2.1.md (Dev-Guides Layer Freeze v2.1)
>   - ARCHITECTURE_FREEZE_MANIFEST_v1.0.md (Architecture Layer Freeze v1.0)
>   - MASTER.md v3.4 (系统宪法 - ASDD Freeze v1.0)
>   - STATE_MACHINE.md v2.6 (8状态机)
>   - DATA_SCHEMA.md v5.2
>   - API_SOT.md v9.0
>   - BUSINESS_RULES.md v3.1
>   - ERROR_CODES_SOT.md v2.1
>   - AUTH_SPEC.md v2.0
>   - LEDGER_SOT.md v1.1

---

## 📜 一、系统宪法 (Core Principles) - SoT 裁判链

**所有技术决策必须遵循以下优先级 (仲裁链)**:

```
MASTER.md v3.4 (系统宪法 - ASDD Freeze v1.0)
    ↓ 引用
STATE_MACHINE.md v2.6 (状态定义) ←─── 🚫 禁止在其他文档重复定义状态
    ↓ 引用
DATA_SCHEMA.md v5.2 (数据结构)   ←─── 📌 所有表结构、字段类型以此为准
    ↓ 引用
BUSINESS_RULES.md v3.1 (业务规则) ←─── ⚖️ BR-* 规则编号具有法律效力
    ↓ 引用
API_SOT.md v9.0 (API 契约)       ←─── 🌐 所有路径、请求/响应格式以此为准
    ↓ 引用
ERROR_CODES_SOT.md v2.1 (错误码) ←─── 🚨 禁止自定义错误码
    ↓ 引用
AUTH_SPEC.md v2.0 (认证授权)     ←─── 🔐 RLS 策略以此为准
    ↓ 引用
LEDGER_SOT.md v1.1 (账本规则)    ←─── 💰 财务逻辑禁止绕过账本
    ↓ 引用
DAILY_REPORT_SOT.md v1.0 (日报流程)
RECONCILIATION_SOT.md v1.0 (对账流程)
TRANSFER_SOT.md v1.0 (调拨流程)
```

### 🔒 不可侵犯原则 (Inviolable Rules)

1. **禁止重复定义状态枚举**
   - ❌ 错误: 在 `models/base.py` 定义 `DailyReportStatus = Enum("DRAFT", "PENDING", "APPROVED", "REJECTED")`
   - ✅ 正确: 使用 STATE_MACHINE.md v2.6 第8章定义的 **8 状态机**
   - **强制**: 所有状态必须从 STATE_MACHINE.md 继承

2. **禁止自定义错误码**
   - ❌ 错误: `raise HTTPException(400, "Invalid request")`
   - ✅ 正确: `raise HTTPException(400, detail={"code": "VAL-001", "message": "..."})`
   - **强制**: 所有错误码必须来自 ERROR_CODES_SOT.md v2.1

3. **禁止直接修改数据库 (必须通过 Alembic)**
   - ❌ 错误: 手动执行 `ALTER TABLE` SQL
   - ✅ 正确: 先更新 DATA_SCHEMA.md v5.2 → 生成 Alembic 迁移 → DBA 审核执行
   - **强制**: 所有 schema 变更必须有对应迁移文件

4. **禁止绕过账本系统**
   - ❌ 错误: 直接修改 `ad_accounts.balance` 字段
   - ✅ 正确: 通过 `ledger_entries` 表记录交易 → 触发余额计算
   - **强制**: 所有资金流动必须在 LEDGER_SOT.md v1.1 定义的双账本体系中

5. **禁止跳过状态机流转**
   - ❌ 错误: `UPDATE daily_reports SET status = 'final_locked' WHERE id = 123`
   - ✅ 正确: 调用 `DailyReportService.transition_to(status)` 触发状态验证
   - **强制**: 所有状态变更必须通过 STATE_MACHINE.md v2.6 定义的合法路径

### 📍 文档路径索引 (ASDD 4层架构)

**完整导航**: 查阅 **[docs/README.md](../docs/README.md)** - 文档导航中心

#### Layer 1: Overview (系统全局视图)
| 文档 | 版本 | 路径 | 核心章节 |
|------|------|------|---------|
| MASTER | v3.4 | `docs/1.overview/MASTER.md` | 系统宪法 (ASDD Freeze) |
| PROJECT | v1.2 | `docs/1.overview/PROJECT.md` | 业务定义与边界 |
| ARCHITECTURE | v1.0 | `docs/1.overview/ARCHITECTURE.md` | 系统架构总览 |
| DOMAIN | v1.0 | `docs/1.overview/DOMAIN.md` | 领域模型与业务逻辑 |

#### Layer 2: SoT (单一真相来源)
| 文档 | 版本 | 路径 | 核心章节 |
|------|------|------|---------|
| STATE_MACHINE | v2.6 | `docs/2.sot/STATE_MACHINE.md` | §8 粉数确认 8 状态机 |
| DATA_SCHEMA | v5.2 | `docs/2.sot/DATA_SCHEMA.md` | §3.3 核心表结构 |
| BUSINESS_RULES | v3.1 | `docs/2.sot/BUSINESS_RULES.md` | BR-RPT-*, BR-LED-* |
| API_SOT | v9.0 | `docs/2.sot/API_SOT.md` | §9 Daily Reports API |
| ERROR_CODES_SOT | v2.1 | `docs/2.sot/ERROR_CODES_SOT.md` | SYS/AUTH/VAL/BIZ/RES |
| AUTH_SPEC | v2.0 | `docs/2.sot/AUTH_SPEC.md` | §3 RBAC + RLS 策略 |
| LEDGER_SOT | v1.1 | `docs/2.sot/LEDGER_SOT.md` | §2 双账本体系 |
| DAILY_REPORT_SOT | v1.0 | `docs/2.sot/DAILY_REPORT_SOT.md` | §3 日报全生命周期 |
| RECONCILIATION_SOT | v1.0 | `docs/2.sot/RECONCILIATION_SOT.md` | §3 对账流程 |
| TRANSFER_SOT | v1.0 | `docs/2.sot/TRANSFER_SOT.md` | §2 调拨规则 |

#### Layer 3: Dev-Guides (开发指南)
| 文档 | 路径 | 核心内容 |
|------|------|---------|
| API_DEVELOPMENT_FLOW | `docs/3.dev-guides/API_DEVELOPMENT_FLOW.md` | Router → Service → Repository |
| FRONTEND_DEVELOPMENT_RULES | `docs/3.dev-guides/FRONTEND_DEVELOPMENT_RULES.md` | 前端开发规范 |
| DDD_API_ARCHITECTURE | `docs/3.dev-guides/DDD_API_ARCHITECTURE.md` | DDD 架构设计 |

#### Layer 4: Architecture (架构视图)
| 文档 | 版本 | 路径 | 核心内容 |
|------|------|------|---------|
| SYSTEM_CONTEXT_VIEW | v1.0 | `docs/4.architecture/SYSTEM_CONTEXT_VIEW.md` | C4 Level 1 系统上下文 |
| BOUNDED_CONTEXT_MAP | v1.0 | `docs/4.architecture/BOUNDED_CONTEXT_MAP.md` | DDD 限界上下文映射 |
| SERVICE_COMPONENT_VIEW | v1.0 | `docs/4.architecture/SERVICE_COMPONENT_VIEW.md` | C4 Level 2/3 组件视图 |
| DATA_FLOW_VIEW | v1.0 | `docs/4.architecture/DATA_FLOW_VIEW.md` | 状态机/账本/API 数据流 |

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

**粉数确认 8 状态机** (`daily_reports.status`) - 来源: STATE_MACHINE.md v2.6 §8:

```
[raw_submitted]       投手提交原始数据 (conversions_raw, raw_spend)
     ↓ 自动触发趋势检测
[trend_pending]       等待趋势风控校验
     ↓ 分支
     ├─ [trend_ok]        未触发风控规则 → 自动流转
     └─ [trend_flagged]   触发风控 (TF-001: 粉数骤降 >50%) → 需运营复核
              ↓ 运营审核
         [trend_resolved]  运营确认"正常波动" → 继续流转
     ↓ 合并
[final_pending]       等待运营录入真实消耗 (real_spend)
     ↓ 运营确认
[final_confirmed]     运营确认最终粉数 (conversions_final)
     ↓ 财务锁定
[final_locked]        计费锁定 → 触发账本记录创建
```

**关键业务规则**:
- **BR-RPT-001**: `conversions_raw != conversions_final` 时，差异 >20% 必须标记 `trend_flagged`
- **BR-RPT-002**: 只有 `final_locked` 状态的日报才能参与账本计算
- **BR-RPT-003**: `final_locked` 后禁止修改 (除非走调整流程 ADJUSTMENT_SOT.md)

**充值申请** (`topup_requests.status`):
```
draft → pending_review → finance_approve → paid → completed
   ↓                           ↓
cancelled                   rejected
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

### 日报状态 (8 状态机 - STATE_MACHINE.md v2.6 §8)
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

---

## 🎯 十二、Claude/SuperClaude 使用指南

### 快速决策流程图

```
收到需求 → 识别涉及的业务域
   ↓
查询对应 SoT 文档 (优先级按第1章裁判链)
   ↓
找到相关规则编号 (如 BR-RPT-001)
   ↓
检查当前代码是否符合规则
   ↓
   ├─ 符合 → 继续开发
   └─ 不符合 → 先修复代码 (或提出 RFC 修改 SoT)
```

### 高频参考场景

| 场景 | 查询路径 | 关键检查点 |
|------|---------|-----------|
| **添加日报字段** | DATA_SCHEMA.md §3.3.1 | 是否与现有字段冲突？是否需要索引？ |
| **修改状态流转** | STATE_MACHINE.md §8 | 是否违反单向流转原则？ |
| **新增 API 端点** | API_SOT.md §9 | 路径是否平面化？响应格式是否统一？ |
| **计算账户余额** | LEDGER_SOT.md §2.3 | 是否通过账本分录计算？是否绕过双账本？ |
| **用户权限验证** | AUTH_SPEC.md §3.2 | 是否符合 RBAC 矩阵？是否触发 RLS？ |

### 常见反模式识别

**当看到以下代码立即拦截**:

```python
# ❌ 反模式 1: 硬编码旧状态 (4 状态机)
class DailyReportStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
# 违反: STATE_MACHINE.md v2.6 定义的是 8 状态机

# ❌ 反模式 2: 直接修改余额
ad_account.balance -= 100
db.commit()
# 违反: LEDGER_SOT.md 要求通过 ledger_entries 记录

# ❌ 反模式 3: 自定义错误码
raise HTTPException(400, "Invalid data")
# 违反: ERROR_CODES_SOT.md 要求使用 VAL-001

# ❌ 反模式 4: 跳过状态流转
report.status = "final_locked"
# 违反: STATE_MACHINE.md 要求按顺序流转

# ❌ 反模式 5: 缺少可追溯性
ledger_entry = LedgerEntry(amount=100, entry_type="SPEND")
# 违反: LEDGER_SOT.md 要求 related_entity_type + related_entity_id
```

### 职责声明

**Claude/SuperClaude**:
- 每次处理需求前，请先查阅本文档第一章"SoT 裁判链"
- 确保所有决策符合仲裁链优先级
- 如有疑问，优先查询对应 SoT 文档的具体章节，而非自行推测
- **记住**: 你的职责是**执行裁判规则**，而非创造规则
- 当遇到 SoT 未覆盖的场景，应提出 RFC 请求，而非自行扩展

---

## 🏛️ 十三、ASDD 4层架构合规性 (v3.2 新增)

### ASDD 4层架构概述

**ASDD (AI-Spec-Driven Development)** 是本项目的文档治理框架，所有代码生成与文档变更必须遵循以下 4 层架构：

```
docs/1.overview/  (系统全局视图 - Freeze v1.0)
    ↓ 引用
docs/2.sot/       (单一真相来源 - Freeze v2.6)
    ↓ 引用
docs/3.dev-guides/ (开发指南 - Freeze v2.1)
    ↓ 引用
docs/4.architecture/ (架构视图 - Freeze v1.0)
```

### 代码生成合规性检查

**所有代码生成前必须执行以下检查**:

1. **SoT/Dev-Guides/Architecture 对齐验证**
   - 查询 SoT Layer 对应文档 (STATE_MACHINE/DATA_SCHEMA/API_SOT 等)
   - 查询 Dev-Guides Layer 对应文档 (API_DEVELOPMENT_FLOW 等)
   - 查询 Architecture Layer 对应文档 (DATA_FLOW_VIEW 等)
   - 确保三层定义一致，无冲突

2. **Freeze 状态验证**
   - 检查文档是否处于 Freeze 状态 (`status: frozen` or `status: ready_for_production`)
   - 禁止修改已冻结文档 (需先提交 RFC 解冻)
   - 禁止引用未冻结文档作为实现依据

3. **版本对齐验证**
   - 确保引用的 SoT 版本号与 Freeze Manifest 一致
   - 例: STATE_MACHINE.md 必须引用 v2.6 (SoT Freeze v2.6)
   - 例: API_SOT.md 必须引用 v9.0 (SoT Freeze v2.6)

### 文档变更合规性检查

**所有文档变更必须通过 ai-ad-spec-governor 管道**:

```
DISCOVER → AUDIT → FIX → VERIFY → FREEZE_CHECK → SUMMARY
```

**变更规则**:
1. **Overview Layer 变更**: 需 Master Architect 批准 + RFC
2. **SoT Layer 变更**: 需 SoT Guardian 批准 + RFC + 影响分析
3. **Dev-Guides Layer 变更**: 需开发团队 Lead 批准
4. **Architecture Layer 变更**: 需 Master Architect 批准

### Agent 文件操作规范

**所有 Agent (AI Agent/人工) 在操作文件前必须**:

1. **Freeze 状态查询**
   ```markdown
   Q: 我要修改 STATE_MACHINE.md，是否允许？
   A: 查询 docs/2.sot/SOT_FREEZE_MANIFEST_v2.6.md
      → STATE_MACHINE.md status: frozen → 禁止直接修改
      → 必须提交 RFC → 解冻 → 修改 → 重新 Freeze
   ```

2. **版本引用检查**
   ```markdown
   Q: 我要引用 DATA_SCHEMA.md，应该用哪个版本？
   A: 查询 docs/2.sot/SOT_FREEZE_MANIFEST_v2.6.md
      → DATA_SCHEMA.md v5.2 (frozen) → 使用 v5.2
   ```

3. **Layer 依赖关系检查**
   ```markdown
   Q: 我要修改 API_DEVELOPMENT_FLOW.md (Dev-Guides)，是否需要检查 SoT？
   A: 是
      → 查询 API_SOT.md v9.0 (SoT Layer 上游)
      → 查询 SERVICE_COMPONENT_VIEW.md v1.0 (Architecture Layer 下游)
      → 确保修改不违反上游 SoT，不破坏下游 Architecture
   ```

### Freeze Manifest 路径

| Layer | Freeze Manifest | 路径 |
|-------|-----------------|------|
| **Overview** | FREEZE_MANIFEST_v1.0.md | `docs/1.overview/FREEZE_MANIFEST_v1.0.md` |
| **SoT** | SOT_FREEZE_MANIFEST_v2.6.md | `docs/2.sot/SOT_FREEZE_MANIFEST_v2.6.md` |
| **Dev-Guides** | DEV_GUIDES_FREEZE_MANIFEST_v2.1.md | `docs/3.dev-guides/DEV_GUIDES_FREEZE_MANIFEST_v2.1.md` |
| **Architecture** | ARCHITECTURE_FREEZE_MANIFEST_v1.0.md | `docs/4.architecture/ARCHITECTURE_FREEZE_MANIFEST_v1.0.md` |

---

## 🧪 十三、后端回归测试门槛 (Backend Regression Gate)

### 强制回归测试规则

**任何修改以下范围的变更，MUST 在合并前通过回归测试套件**：

| 变更范围 | 触发条件 | 验证命令 |
|---------|---------|---------|
| `backend/services/*` | 修改任何 service 文件 | `python run_tests.py --type regression` |
| `backend/routers/*` | 修改任何 router 文件 | `python run_tests.py --type regression` |
| `docs/2.sot/*` | 修改任何 SoT 文档 | `python run_tests.py --type regression` |
| `.claude/skills/ai-ad-api-automation-test/*` | 修改测试自动化 skill | `python run_tests.py --type regression` |

### 回归测试套件定义

**回归测试套件（Regression Test Suite）**：见 `backend/tests/REGRESSION_TEST_SUITE.md`

**五连拍测试套件**：
1. Daily Reports API (`test_daily_report_flow_generated.py`)
2. Trend Risk API (`test_trend_risk_flow_generated.py`)
3. Ledger (`backend/tests/ledger/`)
4. Ad Accounts (`backend/tests/ad_accounts/`)
5. Topup API (`test_topup_api.py`)

### CI/CD 强制规则

**GitHub Actions 规则**：
- `.github/workflows/backend-regression.yml` workflow **MUST** 通过
- 任何 PR 如果修改了上述范围，Backend Regression Tests job **MUST** 显示 ✅ 通过
- 如果回归测试失败，**禁止合并**（block merge）

### 本地验证命令

```bash
# 方式 1: 使用 run_tests.py
python run_tests.py --type regression

# 方式 2: 使用批处理脚本（Windows）
run_regression_tests.bat

# 方式 3: 使用 Shell 脚本（Linux/macOS）
./run_regression_tests.sh

# 方式 4: 手动执行（五连拍）
python -m pytest backend/tests/api/test_daily_report_flow_generated.py -q
python -m pytest backend/tests/api/test_trend_risk_flow_generated.py -q
python -m pytest backend/tests/ledger -q
python -m pytest backend/tests/ad_accounts -q
python -m pytest backend/tests/test_topup_api.py -q -k "not skip"
```

### 违规处理

**如果 PR 修改了上述范围但未通过回归测试**：
1. ❌ **CI 自动阻止合并**（GitHub Actions 失败）
2. 🔴 **Reviewer 必须拒绝 PR**（在 PR 评论中标注 "Regression tests failed"）
3. 📝 **开发者必须修复**（修复代码或测试，重新提交）

**例外情况**（需明确说明）：
- 如果回归测试失败是因为测试本身的问题（而非代码问题），需在 PR 中说明并附上修复测试的计划
- 如果修改是纯文档更新（不涉及业务逻辑），可申请豁免（需 Reviewer 批准）

---

## 🔄 十四、OpenSpec 集成规则

### OpenSpec 唯一变更通道

**从 v3.3 起，所有 SoT 变更必须通过 OpenSpec 流程**：

```
openspec/changes/<change-id>/
├── proposal.md        # 变更提案
├── tasks.md           # 实施清单
├── design.md          # 技术设计（可选）
└── specs/             # Spec deltas
    └── <capability>/
        └── spec.md    # ADDED/MODIFIED/REMOVED
```

### 必须走 OpenSpec 的场景

| 变更类型 | 示例 | 相关 SoT | 必须走 OpenSpec |
|---------|------|----------|-----------------|
| 状态机修改 | 新增 `trend_review` 状态 | STATE_MACHINE.md | ✅ 强制 |
| 错误码变更 | 新增 `BIZ-010` | ERROR_CODES_SOT.md | ✅ 强制 |
| API 契约变更 | 新增 `/api/v1/transfers` | API_SOT.md | ✅ 强制 |
| 数据库结构变更 | 新增 `audit_logs` 表 | DATA_SCHEMA.md | ✅ 强制 |
| 业务规则变更 | 新增 BR-LED-005 | BUSINESS_RULES.md | ✅ 强制 |
| Bug 修复 | 恢复既有行为 | - | ❌ 可跳过 |
| 文档 typo | 拼写修正 | - | ❌ 可跳过 |

### Claude/SuperClaude OpenSpec 检查清单

**每次涉及 SoT 变更前**：

```markdown
□ 是否已创建 OpenSpec change？
  change-id: ____________ → openspec/changes/<id>/ 存在: ✅/❌

□ 是否已编写 spec deltas？
  检查: openspec/changes/<id>/specs/*/spec.md 存在: ✅/❌

□ 是否通过验证？
  运行: openspec validate <id> --strict → 结果: ✅/❌

□ 是否已获得审批？
  proposal.md 状态: ✅ Approved / ❌ Pending
```

### 禁止操作

1. ❌ **直接编辑 openspec/specs/**
   - 该目录仅由 `openspec archive` 更新
   - 手动编辑将被 revert

2. ❌ **无 change-id 的 SoT 修改**
   - 所有 SoT 变更必须关联 change-id
   - Commit message 必须包含 `[<change-id>]`

3. ❌ **未审批即实施**
   - proposal.md 未获批准前不得开始编码
   - 违规实施将被代码回滚

### 分支命名规范

```bash
# OpenSpec change 实施分支
feature/<change-id>

# 示例
feature/add-transfer-v2
feature/update-state-machine-v3
```

### Commit message 规范

```bash
# 格式
<type>(<scope>): <description> [<change-id>]

# 示例
feat(api): add transfer endpoint [add-transfer-v2]
docs(sot): update STATE_MACHINE for 9-state [update-state-machine-v3]
```

### OpenSpec Change 回归测试要求

**任意 OpenSpec change，只要涉及以下模块，MUST 在合并前附带回归测试结果**：

| 模块 | 相关能力 | 回归测试要求 |
|------|---------|------------|
| DailyReports | `daily_reports` capability | ✅ 必须通过 `test_daily_report_flow_generated.py` |
| TrendRisk | `trend_risk` / `daily_reports.trend_*` | ✅ 必须通过 `test_trend_risk_flow_generated.py` |
| Ledger | `ledger` capability | ✅ 必须通过 `backend/tests/ledger/` |
| AdAccounts | `ad_accounts` capability | ✅ 必须通过 `backend/tests/ad_accounts/` |
| Topups | `topup_requests` capability | ✅ 必须通过 `test_topup_api.py` |

**合并前检查清单**：
- [ ] 回归测试全部通过（本地或 CI）
- [ ] 在 PR 描述中附上回归测试结果截图/日志
- [ ] 在 PR 描述中注明 commit id（用于追溯）
- [ ] 如果回归测试失败，说明原因并附上修复计划

**示例 PR 描述格式**：
```markdown
## Regression Test Results

✅ All regression tests passed

- Daily Reports API: 33 passed
- Trend Risk API: 17 passed
- Ledger: 54 passed (3 skipped)
- Ad Accounts: 51 passed
- Topup API: 22 passed

**Commit**: `ac2335c`
**Test Command**: `python run_tests.py --type regression`
**CI Status**: ✅ [Backend Regression Tests](https://github.com/.../actions/runs/...)
```

### OpenSpec 与 ASDD 映射

| OpenSpec 概念 | ASDD 等价物 |
|---------------|------------|
| `openspec/specs/` | `docs/2.sot/` (SoT Layer) |
| `proposal.md` | RFC in `docs/1.overview/` |
| `design.md` | Architecture views in `docs/4.architecture/` |
| `tasks.md` | Dev-Guides 实施清单 |

---

## 🔐 十五、规则总纲生效声明

**本文档自 v3.0 起生效，具有以下法律效力**:

1. **强制性**: 所有代码提交必须符合本规则，CI/CD 流程应集成一致性检查脚本
2. **优先级**: 当本文档与其他文档冲突时，以本文档为准 (本文档是 SoT 的 Meta-SoT)
3. **修订流程**: 修改本文档需经过架构委员会 2/3 多数通过
4. **培训要求**: 所有新加入团队成员必须完成本文档学习并通过测试
5. **Freeze 保护**:
   - 禁止直接修改状态定义 → 必须通过 RFC 流程
   - 禁止重复定义枚举 → 所有下游文档只能引用上游 SoT
   - 强制 PR 审查 → 所有 SoT 文档修改必须经过一致性脚本验证
   - 仲裁链修改 → 需 2 名架构师批准

**签署人**: AI Architecture Team
**生效日期**: 2025-11-24
**基准版本**: SoT Freeze v1.0

---

**规则总纲版本**: v3.4 (基于 ASDD 4层 Freeze: Overview v1.0 + SoT v2.6 + Dev-Guides v2.1 + Architecture v1.0 + OpenSpec v1.0)
**生效日期**: 2025-12-02
**最后更新**: 2025-12-02
**下次审查**: Freeze Manifest 变更时或每季度
**维护责任人**: AI Architecture Team

**版本变更历史**:
- v3.5 (2025-12-17): 整合 Cursor Rules 格式，添加 YAML frontmatter，六大规则分类体系，技术栈/SoT裁判链快速参考
- v3.4 (2025-12-02): 新增第十三章「后端回归测试门槛」，强制回归测试规则，CI/CD 集成要求，OpenSpec change 回归测试要求
- v3.3 (2025-12-01): 新增第十四章「OpenSpec 集成规则」，确立 OpenSpec 为唯一变更通道，添加 Claude/SuperClaude OpenSpec 检查清单
- v3.2 (2025-11-27): 新增 ASDD 4层架构合规性章节，更新 Freeze 基准为 4层 Freeze Manifests，更新文档路径索引为 4层架构
- v3.1 (2025-11-25): 基于 ASDD Freeze v1.0 + SoT Freeze v1.0
- v3.0 (2025-11-24): 初始版本

---

## 🔒 执行承诺

- **开发团队**: 开始任务前必须确认已阅读并理解本规则总纲
- **Code Review**: 按此规则执行，发现冲突需立即纠正
- **AI 工具 (Claude/SuperClaude)**: 每次生成代码前必须执行完整自检清单
- **架构变更**: 必须先更新 SoT 文档及本规则总纲，再进入开发环节
- **违规处理**: PR 自动拒绝 / 代码回滚 / 重新生成

**记住**: SoT 文档体系已达到"裁判级"成熟度 (Freeze v1.0)，本规则总纲是所有 AI Agent 的"世界观"基础。
