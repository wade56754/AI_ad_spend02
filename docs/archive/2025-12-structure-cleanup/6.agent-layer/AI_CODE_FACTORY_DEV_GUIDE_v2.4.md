# AI 代码工厂开发指南

> **版本**: v2.4
> **状态**: active
> **层级**: Tier-3 平台规范
> **Owner**: wade
> **创建日期**: 2025-12-06
> **更新日期**: 2025-12-07
> **Baseline**: MASTER.md v4.4, Agent Layer Freeze v1.0, SoT Freeze v2.6

---

## 变更摘要 (v2.4 vs v2.3)

| 变更项 | 说明 |
|-------|------|
| **架构迁移** | 从 "Python Agent + SuperClaude 双轨" 迁移到 "纯 SuperClaude Skill" 架构 |
| **§9.6 更新** | 移除 Python Agent CLI 模式，统一为 Claude Code 对话模式 |
| **Skills 目录** | Skills 统一位于 `.claude/skills/`，移除 `agents/` 目录 |
| **命令更新** | 新增 `/gen`、`/review` 命令，移除 `/agent`、`/orch` 命令 |
| **弃用标记** | ai-ad-agents-test-orchestrator/runner 标记为 deprecated |

### 历史变更 (v2.3)

| 变更项 | 说明 |
|-------|------|
| **§9.7 精简** | SuperClaude 增强层收敛为概览+模式表，详细内容引用 `SUPERCLAUDE_INTEGRATION_GUIDE_v2.0.md` |
| **技术限制声明** | 明确 SuperClaude 无可编程 SDK，集成方式为 Prompt 级模式迁移 |
| **边界约束统一** | 明确 SuperClaude 命令必须遵守与 AI 代码工厂相同的目录边界 |

---

## 目录

**Part I: 基础规范**
1. [设计哲学](#1-设计哲学)
2. [代码边界定义](#2-代码边界定义) ⭐ 核心
3. [质量标准与上线门禁](#3-质量标准与上线门禁)

**Part II: 开发流程** ⭐ 核心
4. [后端开发流程](#4-后端开发流程业务模块)
5. [前端开发流程](#5-前端开发流程模块视角)
6. [API 开发流程](#6-api-开发流程接口契约视角)
7. [测试流程](#7-测试流程从单元到集成)
8. [文档编写流程](#8-文档编写流程sot--实现文档)

**Part III: 系统实现**
9. [系统架构](#9-系统架构)
   - [9.1 六层架构模型](#91-六层架构模型)
   - [9.2 层级职责矩阵](#92-层级职责矩阵)
   - [9.3 数据流图](#93-数据流图)
   - [9.4 现状与目标对比](#94-现状与目标对比)
   - [9.5 推荐目录结构](#95-推荐目录结构)
   - [9.6 两种运行模式](#96-两种运行模式)
   - [9.7 SuperClaude 增强层](#97-superclaude-增强层)
10. [Skill 与 Command 规范](#10-skill-与-command-规范)
11. [推荐工作流组合](#11-推荐工作流组合)
12. [场景示例：充值审批功能](#12-场景示例充值审批功能)
13. [失败处理与报告](#13-失败处理与报告)
14. [路线图](#14-路线图)

---

# Part I: 基础规范

## 1. 设计哲学

### 1.1 核心理念

**AI 代码工厂** 是一套 **受控的** 自动化代码生成系统：

| 原则 | 说明 |
|------|------|
| **SoT 驱动** | 所有代码必须严格遵循 SoT 文档，AI 只能读不能改 |
| **边界清晰** | 明确可写/只读/禁区，AI 不能越界 |
| **人机协作** | 代码生成自动化，最终提交人工确认 |
| **可审计** | 每次生成都有 Plan + Report，可追溯 |

### 1.2 核心原则

```
┌─────────────────────────────────────────────────────────────┐
│                    AI 代码工厂核心原则                        │
├─────────────────────────────────────────────────────────────┤
│  1. SoT 是法律 → AI 只能读，不能改                           │
│  2. 实现层可写 → schemas/services/routers/tests             │
│  3. 模型层禁区 → models/migrations/密钥 绝不碰              │
│  4. 自动修复有限 → 最多 2 轮，失败就报告                     │
│  5. 提交需人工 → 代码生成自动，commit 人工确认               │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 流程关系总览

```
┌─────────────────────────────────────────────────────────────┐
│                    开发流程关系图                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  后端模块 = 后端开发流程 + API 开发流程 + 测试流程            │
│                                                              │
│  前端模块 = 前端开发流程 + API 契约 + 联调测试               │
│                                                              │
│  全局治理 = 文档编写流程 + Freeze 机制                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 代码边界定义 ⭐

### 2.1 可写区域 (AI 可自动修改)

#### 后端

| 目录 / 文件 | 说明 |
|-------------|------|
| `backend/schemas/**` | Pydantic 请求/响应模型 |
| `backend/services/**` | 业务服务层逻辑 |
| `backend/routers/**` | FastAPI 路由层 |
| `backend/tests/**` | pytest 测试 (API/service/状态机) |
| `backend/core/error_codes.py` | ⚠️ 需走专门 flow，不能随意改 |

#### 前端

| 目录 / 文件 | 说明 |
|-------------|------|
| `frontend/src/modules/**` | 模块化页面 (Shell + hooks + components) |
| `frontend/src/lib/api/**` | API client 封装 |
| `frontend/tests/**` | 前端测试 |

#### 文档 & 工具

| 目录 / 文件 | 说明 |
|-------------|------|
| `docs/3.impl/**` | 实现报告 |
| `docs/reports/**` | Freeze 报告、测试报告 |
| `openspec/changes/**` | 变更记录 |
| `.claude/skills/**` | Skill 描述文档 (非 SoT) |

### 2.2 只读区域 (AI 只能读，不能写)

**这是"法律条文"，AI 只能背书，不能改字：**

| 目录 / 文件 | 说明 |
|-------------|------|
| `docs/sot/MASTER_SPEC.md` | 主规范 |
| `docs/sot/STATE_MACHINE.md` | 状态机定义 |
| `docs/sot/DATA_SCHEMA.md` | 数据模型定义 |
| `docs/sot/LEDGER_SOT.md` | 账本规则 |
| `docs/sot/AUTH_SPEC.md` | 认证授权规范 |
| `docs/sot/BUSINESS_RULES.md` | 业务规则 |
| `docs/sot/ERROR_CODES_SOT.md` | 错误码定义本体 |
| `docs/sot/API_SOT.md` | API 规范 |
| `docs/sot/*_SOT.md` | 所有 SoT 文档 |

> **如果要改 SoT**：只能人工改，或开专门的 `doc-architect` 流程由人盯着改。

### 2.3 禁区 (AI 绝对不能碰)

| 类别 | 文件/目录 | 原因 |
|------|----------|------|
| **配置 & 密钥** | `.env`, `.env.*`, `supabase.json` | 安全敏感 |
| **底层模型** | `backend/models/**` | 对应 DATA_SCHEMA，需 DBA 审核 |
| **数据库迁移** | `migrations/**`, `alembic/**` | 需 DBA 审核 |
| **RLS 策略** | policy 脚本 | 安全敏感 |
| **CI/CD** | `.github/workflows/**` | 基础设施 |
| **部署脚本** | `deploy/**`, `infra/**` | 基础设施 |
| **依赖锁文件** | `package-lock.json`, `pnpm-lock.yaml` | 可读不可写 |
| **虚拟环境** | `.venv/**`, `node_modules/**` | 系统生成 |

### 2.4 边界总结图

```
┌─────────────────────────────────────────────────────────────┐
│                      代码边界分层                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ╔═══════════════════════════════════════════════════════╗  │
│  ║  禁区 (FORBIDDEN)                                      ║  │
│  ║  models/ | migrations/ | .env | .github/workflows/    ║  │
│  ╚═══════════════════════════════════════════════════════╝  │
│                           │                                  │
│                           ▼                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  只读区 (READ-ONLY)                                    │  │
│  │  docs/sot/** - 所有 SoT 文档                         │  │
│  │  AI 读取作为生成依据，但不能修改                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ▼                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  可写区 (WRITABLE)                                     │  │
│  │  schemas/ | services/ | routers/ | tests/             │  │
│  │  AI 可以自动生成和修改                                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.5 边界约束对 SuperClaude 同样适用

> ⚠️ **重要**: SuperClaude 命令 (`/sc:*`) 在本项目中执行时，必须遵守与 AI 代码工厂相同的目录边界约束：
> - 可写区：仅限 `schemas/services/routers/tests/` 等
> - 只读区：所有 `docs/sot/**` 文档
> - 禁区：`models/migrations/.env` 等
>
> SuperClaude 的通用能力不能越过本项目的 SoT 边界。

---

## 3. 质量标准与上线门禁

### 3.1 质量等级定义

| 等级 | 说明 | 处理 |
|------|------|------|
| **P0** | 阻塞级 | 必须修复，不能提交 |
| **P1** | 严重级 | 必须修复，或写明原因+计划 |
| **P2** | 建议级 | 可暂时保留，列表备查 |

### 3.2 上线门禁 (Release Gate)

#### 目标标准

| 检查项 | 要求 |
|--------|------|
| **本模块测试** | 100% 通过，不得有 xfail 伪装 |
| **全项目 pytest** | 不得新增失败/error |
| **SoT 合规 - P0** | 必须为 0 |
| **SoT 合规 - P1** | 默认为 0，保留需写明原因 |
| **mypy** | 改动模块必须通过 |
| **ruff/black** | 不允许新增 lint error |
| **tsc (前端)** | 必须通过编译 |
| **ESLint (前端)** | 不允许新增 error |
| **目录边界校验** | 禁区写入检测必须通过 |

#### 目录边界校验

**检测命令**:
```bash
python tools/guard_paths.py --mode ci
```

**目录白名单** (允许写入):
| 目录 | 说明 |
|------|------|
| `backend/schemas/**` | Pydantic 模型 |
| `backend/services/**` | 业务逻辑 |
| `backend/routers/**` | API 路由 |
| `backend/tests/**` | 测试用例 |
| `frontend/src/modules/**` | 前端模块 |
| `docs/reports/**` | 报告输出 |

**目录黑名单** (禁止写入，触碰立即 fail):
| 目录 | 原因 |
|------|------|
| `backend/models/**` | 需 DBA 审核 |
| `migrations/**` | 需 DBA 审核 |
| `.env*` | 安全敏感 |
| `.github/workflows/**` | CI 基础设施 |
| `docs/sot/**` | SoT 只读 |

**CI 阻断规则**:
- 任何对黑名单目录的写入尝试 → 立即 fail，阻断流水线
- 形成"先校验后修复"流程

#### 分阶段执行策略

| Phase | 强制要求 | 建议但不强制 |
|-------|---------|-------------|
| **Phase 1 (现在)** | 相关 pytest 100%<br>全局不新增失败<br>P0=0, P1=0 | mypy/ruff 对改动文件 |
| **Phase 2** | + mypy/ruff 改动模块强制<br>+ tsc/ESLint 改动模块强制 | 全项目静态检查 |
| **Phase 3** | CI 全项目: pytest + mypy + lint 全绿 | - |

### 3.3 P0 问题清单

| 问题类型 | 说明 | 检测方法 |
|---------|------|---------|
| 状态枚举不一致 | 使用了 SoT 未定义的状态 | /sot-check |
| 直接修改 balance | 绕过 ledger_entries | Grep 检查 |
| 错误码格式错误 | 未使用 ERROR_CODES_SOT 定义 | /sot-check |
| 缺少状态验证 | 状态转换未验证前置状态 | 代码审查 |
| 权限检查缺失 | 未按 AUTH_SPEC 校验 | 代码审查 |
| 账本分录错误 | 不符合 LEDGER_SOT | 代码审查 |

---

# Part II: 开发流程 ⭐

## 4. 后端开发流程（业务模块）

> **目标**: 在 SoT 约束下，实现一个完整的后端模块（三层结构 + 测试 + Freeze）

### 4.1 流程总览

```
┌─────────────────────────────────────────────────────────────┐
│                    后端开发流程 (8 步)                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ① 需求 → SoT 映射 ────────────────────────────── [人工]    │
│     明确模块/状态机/账本规则归属                              │
│              │                                               │
│              ▼                                               │
│  ② 生成实现计划 (Plan) ────────────────────────── [自动]    │
│     PLAN_{module}_vX.Y.md                                   │
│              │                                               │
│              ▼                                               │
│  ③ Schema 层实现 ──────────────────────────────── [自动]    │
│     backend/schemas/{module}.py                             │
│              │                                               │
│              ▼                                               │
│  ④ Service 层实现 ─────────────────────────────── [自动]    │
│     backend/services/{module}_service.py                    │
│              │                                               │
│              ▼                                               │
│  ⑤ Router 层实现 ──────────────────────────────── [自动]    │
│     backend/routers/{module}.py                             │
│              │                                               │
│              ▼                                               │
│  ⑥ 测试实现 ───────────────────────────────────── [自动]    │
│     backend/tests/services/ + backend/tests/api/            │
│              │                                               │
│              ▼                                               │
│  ⑦ 测试执行 & 自动修复 Loop ───────────────────── [自动]    │
│     最多 2 轮自动修复                                        │
│              │                                               │
│              ▼                                               │
│  ⑧ Freeze 报告 ────────────────────────────────── [自动]    │
│     {MODULE}_TEST_FREEZE_REPORT_vX.Y.md                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Step 0: 目录边界校验

**在任何代码生成前，先运行目录守卫脚本**:

```bash
python tools/guard_paths.py --mode ci
```

**Checklist**:
- [ ] 目标文件均在白名单目录内
- [ ] 无黑名单目录触碰
- [ ] 校验通过后方可进入 Step 1

### 4.3 Step 1: SoT 完整性扫描

**必读 SoT (只读)**：

| SoT 文档 | 关注内容 |
|---------|---------|
| `STATE_MACHINE.md` | 该模块涉及的状态机 |
| `LEDGER_SOT.md` | 账本分录规则 |
| `DATA_SCHEMA.md` | 表结构、字段约束 |
| `AUTH_SPEC.md` | 权限矩阵 |
| `BUSINESS_RULES.md` | 业务规则 |
| `ERROR_CODES_SOT.md` | 错误码定义 |

#### SoT 完整性检查器

在生成 Plan **之前**，必须运行 SoT 完整性扫描：

```bash
python tools/sot_scanner.py --module <module_name>
```

**输出示例**:
```json
{
  "module": "topup_approval",
  "sot_coverage": {
    "STATE_MACHINE.md#topup": "found",
    "LEDGER_SOT.md#topup": "found",
    "AUTH_SPEC.md#topup": "missing",
    "ERROR_CODES_SOT.md#TOPUP_*": "partial"
  },
  "blocking_gaps": ["AUTH_SPEC.md#topup"],
  "can_proceed": false
}
```

**阻断规则**:
- 若 `can_proceed: false` → 阻断代码生成，要求先补 SoT
- 若 `blocking_gaps` 非空 → 列出缺失段落，人工补充后重试
- 实现"先补 SoT 再编码"强制流程

**关键判断**: 若 SoT 不完整 → 先人工补 SoT，再允许写代码

### 4.4 Step 2: 生成实现计划

**产出**: `PLAN_{module}_vX.Y.md`

```markdown
# PLAN_TOPUP_APPROVAL_v1.0.md

## 1. 变更文件清单
- backend/schemas/topup.py (新增审批相关 schema)
- backend/services/topup_service.py (新增 approve/reject 方法)
- backend/routers/topups.py (新增审批路由)
- backend/tests/services/test_topup_service.py
- backend/tests/api/test_topups_api.py

## 2. SoT 依赖
- STATE_MACHINE.md#topup: pending → approved/rejected
- LEDGER_SOT.md#topup: 审批后写入分录规则
- AUTH_SPEC.md: admin/finance 可审批

## 3. 关键业务规则
- BR-TP-001: 只有 pending 状态可审批
- BR-TP-002: 审批后不可撤回

## 4. 风险点
- 账本分录需要事务保证
```

### 4.5 Step 3: Schema 层实现

**位置**: `backend/schemas/{module}.py`

**内容**:
- 枚举定义 (必须引用 STATE_MACHINE.md)
- 请求参数模型
- 响应模型
- 分页结构

```python
# backend/schemas/topup.py
from enum import Enum

class TopupStatus(str, Enum):
    """状态枚举 - 对齐 STATE_MACHINE.md#topup"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"

class TopupApproveRequest(BaseModel):
    comment: Optional[str] = None

class TopupApproveResponse(BaseModel):
    id: UUID
    status: TopupStatus
    approved_by: UUID
    approved_at: datetime
```

### 4.6 Step 4: Service 层实现

**位置**: `backend/services/{module}_service.py`

**核心职责**:
- 实现业务函数
- 严格按 SoT 执行:
  - ledger 来源 & 口径
  - 状态机允许的状态组合
  - 权限过滤
- 使用正确的错误码

```python
# backend/services/topup_service.py
async def approve_topup(
    db: AsyncSession,
    topup_id: UUID,
    current_user: User,
    request: TopupApproveRequest
) -> Topup:
    """
    审批充值申请
    - SoT: STATE_MACHINE.md#topup (pending → approved)
    - SoT: LEDGER_SOT.md#topup (审批后写分录)
    - SoT: AUTH_SPEC.md (admin/finance 可审批)
    """
    # 1. 获取充值记录
    topup = await get_topup_by_id(db, topup_id)
    if not topup:
        raise BusinessError(code="TOPUP_001", message="充值记录不存在")

    # 2. 验证状态 (STATE_MACHINE)
    if topup.status != TopupStatus.PENDING:
        raise BusinessError(code="TOPUP_002", message="当前状态不允许审批")

    # 3. 验证权限 (AUTH_SPEC)
    if current_user.role not in ["admin", "finance"]:
        raise AuthError(code="AUTH_500", message="无审批权限")

    # 4. 更新状态
    topup.status = TopupStatus.APPROVED
    topup.approved_by = current_user.id
    topup.approved_at = datetime.utcnow()

    # 5. 写入账本 (LEDGER_SOT)
    await create_ledger_entry(db, ...)

    await db.commit()
    return topup
```

### 4.7 Step 5: Router 层实现

**位置**: `backend/routers/{module}.py`

**内容**:
- 定义 API 端点路径、HTTP method
- 注入依赖 (DB session / current_user)
- 捕获异常 → 映射到正确 HTTP status + 错误码

```python
# backend/routers/topups.py
@router.post("/{topup_id}/approve", response_model=TopupApproveResponse)
async def approve_topup_endpoint(
    topup_id: UUID,
    request: TopupApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    审批充值申请
    - API: POST /api/v1/topups/{id}/approve
    - 权限: admin, finance
    """
    try:
        result = await topup_service.approve_topup(
            db, topup_id, current_user, request
        )
        return TopupApproveResponse.from_orm(result)
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
    except AuthError as e:
        raise HTTPException(status_code=403, detail=e.to_dict())
```

**注册路由** (在 `backend/main.py`):
```python
app.include_router(topups_router, prefix="/api/v1/topups", tags=["topups"])
```

### 4.8 Step 6: 测试实现

#### Service 层测试

**位置**: `backend/tests/services/test_{module}_service.py`

```python
# backend/tests/services/test_topup_service.py

class TestApproveTopup:
    """测试充值审批 Service"""

    async def test_approve_success(self, db, admin_user):
        """正向路径: 成功审批"""
        topup = await create_test_topup(db, status="pending")
        result = await approve_topup(db, topup.id, admin_user, {})
        assert result.status == TopupStatus.APPROVED
        assert result.approved_by == admin_user.id

    async def test_approve_wrong_status(self, db, admin_user):
        """边界: 状态不允许审批"""
        topup = await create_test_topup(db, status="approved")
        with pytest.raises(BusinessError) as exc:
            await approve_topup(db, topup.id, admin_user, {})
        assert exc.value.code == "TOPUP_002"

    async def test_approve_no_permission(self, db, media_buyer_user):
        """边界: 权限不足"""
        topup = await create_test_topup(db, status="pending")
        with pytest.raises(AuthError) as exc:
            await approve_topup(db, topup.id, media_buyer_user, {})
        assert exc.value.code == "AUTH_500"
```

#### API 层测试

**位置**: `backend/tests/api/test_{module}_api.py`

```python
# backend/tests/api/test_topups_api.py

class TestTopupApproveAPI:
    """测试充值审批 API"""

    async def test_approve_api_success(self, client, admin_token):
        """API: 成功审批"""
        topup_id = await create_test_topup_id()
        response = await client.post(
            f"/api/v1/topups/{topup_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"

    async def test_approve_api_forbidden(self, client, media_buyer_token):
        """API: 无权限返回 403"""
        topup_id = await create_test_topup_id()
        response = await client.post(
            f"/api/v1/topups/{topup_id}/approve",
            headers={"Authorization": f"Bearer {media_buyer_token}"}
        )
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "AUTH_500"
```

#### 状态机 / 账本测试

```python
# backend/tests/test_state_machine_transitions.py
async def test_topup_state_transitions():
    """验证 topup 状态机转换"""
    # pending → approved ✓
    # pending → rejected ✓
    # approved → pending ✗ (禁止)
    ...

# backend/tests/test_ledger_invariants.py
async def test_topup_ledger_balance():
    """验证审批后账本余额不变量"""
    ...
```

### 4.9 Step 7: 测试执行 & 自动修复

```bash
# 执行相关测试
pytest backend/tests/services/test_topup_service.py -v
pytest backend/tests/api/test_topups_api.py -v
pytest backend/tests/test_state_machine_transitions.py -k "topup" -v
```

**自动修复 Loop**:
- 最多 2 轮自动修复
- 第 3 次失败 → 生成 `FAILURE_REPORT`

### 4.10 Step 8: Freeze 报告

**产出**: `{MODULE}_TEST_FREEZE_REPORT_vX.Y.md`

```markdown
# TOPUP_APPROVAL_TEST_FREEZE_REPORT_v1.0.md

## 1. SoT 对齐性
| SoT 条款 | 对齐状态 |
|---------|---------|
| STATE_MACHINE.md#topup | ✅ 对齐 |
| LEDGER_SOT.md#topup | ✅ 对齐 |
| AUTH_SPEC.md | ✅ 对齐 |

## 2. 测试覆盖
| 测试文件 | 用例数 | 通过 | 失败 |
|---------|-------|------|------|
| test_topup_service.py | 15 | 15 | 0 |
| test_topups_api.py | 12 | 12 | 0 |

## 3. P0/P1/P2 问题
- P0: 0
- P1: 0
- P2: 1 (建议添加更多边界测试)

## 4. Freeze 评级
✅ **READY FOR MERGE**

## 5. 回滚策略
若出现问题，回滚 topup_service.py 到 commit abc123
```

---

## 5. 前端开发流程（模块视角）

> **目标**: 基于稳定的 API 契约 & SoT，实现一个可维护的前端模块

### 5.1 流程总览

```
┌─────────────────────────────────────────────────────────────┐
│                    前端开发流程 (5 步)                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ① 输入与澄清 ─────────────────────────────────── [人工]    │
│     业务需求 + 已有后端 API                                  │
│              │                                               │
│              ▼                                               │
│  ② 搭前端模块骨架 ─────────────────────────────── [自动]    │
│     frontend/src/modules/{module}/                          │
│              │                                               │
│              ▼                                               │
│  ③ Mock 驱动开发 ──────────────────────────────── [自动]    │
│     data/mock-data.ts → 调顺布局/交互                        │
│              │                                               │
│              ▼                                               │
│  ④ 接入真实 API ───────────────────────────────── [自动]    │
│     替换 mock → 真实请求                                     │
│              │                                               │
│              ▼                                               │
│  ⑤ 联调与验收 ─────────────────────────────────── [人工]    │
│     本地联调 + 验收报告 + Freeze                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Step 1: 输入与澄清

**必读文档**:

| 文档 | 内容 |
|------|------|
| `{MODULE}_API_CONTRACT_vX.Y.md` | API 契约 |
| 相关 SoT (只读) | 业务口径 / 权限模型 / 状态枚举 |

### 5.3 Step 2: 搭前端模块骨架

**目录结构**:

```
frontend/src/modules/{module}/
├── {Module}PageShell.tsx       # 页面整体布局
│   └── 面包屑 / 过滤条 / 表格容器
├── hooks/
│   ├── use{Module}Filters.ts   # 本地筛选、分页、排序状态
│   └── use{Module}Data.ts      # 数据拉取 & 合并
├── components/
│   ├── {Module}Table.tsx       # 表格组件
│   ├── {Module}Chart.tsx       # 图表组件
│   └── {Module}Card.tsx        # 卡片组件
└── data/
    └── mock-data.ts            # Mock 数据
```

### 5.4 Step 3: Mock 驱动开发

```typescript
// data/mock-data.ts
export const mockTopupList: TopupListResponse = {
  items: [
    {
      id: "uuid-1",
      amount: 10000.00,
      status: "pending",
      created_at: "2025-12-06T10:00:00Z",
      // ... 根据 API 契约填充
    }
  ],
  total: 1,
  page: 1,
  page_size: 20
};
```

**开发顺序**:
1. PageShell + 组件先用 mock 渲染
2. 把布局、交互、筛选逻辑调顺
3. 确认 UI 符合设计稿

### 5.5 Step 4: 接入真实 API

```typescript
// hooks/useTopupData.ts
export function useTopupData(filters: TopupFilters) {
  const { data, error, isLoading } = useSWR(
    `/api/v1/topups?${queryString.stringify(filters)}`,
    fetcher
  );

  return {
    topups: data?.items ?? [],
    total: data?.total ?? 0,
    isLoading,
    error
  };
}
```

**处理要点**:
- 加载态 (loading)
- 错误态 (权限不足 / 业务错误 / 空数据)
- 按 API 契约更新 TS 类型定义

### 5.6 Step 5: 联调与验收

**联调步骤**:
1. 起后端 FastAPI + 前端 Next.js
2. 本地联调
3. 用 DevTools / MCP 抓包验证:
   - 请求参数是否符合 API 契约
   - 响应字段是否用全 / 用对

**验收报告**:

```markdown
# TOPUP_FRONTEND_INTEGRATION_REPORT_v1.0.md

## 1. 功能覆盖
- [x] 充值列表展示
- [x] 充值详情查看
- [x] 审批操作
- [x] 状态筛选
- [x] 分页

## 2. API 对接状态
| API | 对接状态 |
|-----|---------|
| GET /api/v1/topups | ✅ |
| POST /api/v1/topups/{id}/approve | ✅ |
| POST /api/v1/topups/{id}/reject | ✅ |

## 3. 已知问题
- 无

## 4. Freeze 状态
✅ Topup Frontend Module: Ready for integration
```

---

## 6. API 开发流程（接口契约视角）

> **目标**: 让前后端通过清晰、版本化的 API 契约对齐

### 6.1 流程总览

```
┌─────────────────────────────────────────────────────────────┐
│                    API 开发流程 (6 步)                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ⓪ SoT 完整性扫描 ─────────────────────────────── [自动]    │
│     确认 STATE_MACHINE/AUTH 段落完整后方可继续              │
│              │                                               │
│              ▼                                               │
│  ① 确定 API 边界 & 资源 ───────────────────────── [人工]    │
│     "这是对哪个资源/视图的操作？"                            │
│              │                                               │
│              ▼                                               │
│  ② 定义 API 契约 ──────────────────────────────── [人工]    │
│     {MODULE}_API_CONTRACT_vX.Y.md                           │
│              │                                               │
│              ▼                                               │
│  ③ 翻译为后端 Router + Schema ─────────────────── [自动]    │
│     backend/routers/ + backend/schemas/                     │
│              │                                               │
│              ▼                                               │
│  ④ 版本管理 & 兼容性 ──────────────────────────── [人工]    │
│     Breaking changes → 版本号 +1                            │
│              │                                               │
│              ▼                                               │
│  ⑤ API 契约 → 前端联调 ────────────────────────── [自动]    │
│     前端严格按契约实现                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6.1.1 Step 0: SoT 完整性扫描

在定义 API 契约前，先确认相关 SoT 段落完整：

```bash
python tools/sot_scanner.py --module <module_name> --scope api
```

**检查范围**:
- `STATE_MACHINE.md#<entity>` - 确认状态转换规则
- `AUTH_SPEC.md#<entity>` - 确认权限矩阵
- `ERROR_CODES_SOT.md#<PREFIX>_*` - 确认错误码前缀

**阻断规则**: 若缺失关键 SoT 段落 → 阻断流程，人工补充后重试

### 6.2 API 契约文档格式

**文件**: `{MODULE}_API_CONTRACT_vX.Y.md`

```markdown
# TOPUP_API_CONTRACT_v1.0.md

## 1. 审批充值申请

### 请求
- **URL**: `POST /api/v1/topups/{id}/approve`
- **Method**: POST

### Path 参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | UUID | 是 | 充值记录 ID |

### Body 参数
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|-------|------|
| comment | string | 否 | null | 审批意见 |

### 响应 (200 OK)
```json
{
  "id": "uuid",
  "status": "approved",
  "approved_by": "uuid",
  "approved_at": "2025-12-06T10:00:00Z"
}
```

### 错误码
| HTTP Status | Code | Message |
|-------------|------|---------|
| 400 | TOPUP_001 | 充值记录不存在 |
| 400 | TOPUP_002 | 当前状态不允许审批 |
| 403 | AUTH_500 | 无审批权限 |

### 示例

**请求**:
```bash
curl -X POST /api/v1/topups/123e4567-e89b/approve \
  -H "Authorization: Bearer xxx" \
  -H "Content-Type: application/json" \
  -d '{"comment": "审批通过"}'
```

**响应**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "approved",
  "approved_by": "user-uuid",
  "approved_at": "2025-12-06T10:30:00Z"
}
```
```

### 6.3 版本管理规则

| 变更类型 | 版本策略 |
|---------|---------|
| 新增字段 (向后兼容) | 小版本 +0.1 |
| 字段改名/删除 (Breaking) | 大版本 +1.0 |
| 新增端点 | 小版本 +0.1 |
| 删除端点 | 大版本 +1.0 |

**Breaking Changes 处理**:
1. API 契约版本 +1 (v1 → v2)
2. 文档中写清废弃旧接口的时间计划
3. 前端按新契约适配

### 6.4 联调不一致处理

```
发现前后端不一致:
  ↓
判断:
  A) 后端没按契约实现 → 后端修复
  B) 契约本身有问题 → 先更新契约，再改代码

原则: 任何改动都必须先更新契约文档
```

---

## 7. 测试流程（从单元到集成）

> **目标**: 保证改动不把现有系统搞崩，对关键模块建立可回溯的质量基线

### 7.1 流程总览

```
┌─────────────────────────────────────────────────────────────┐
│                    测试流程 (5 步)                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ① 测试范围识别 ───────────────────────────────── [自动]    │
│     这次改动影响哪些模块？                                   │
│              │                                               │
│              ▼                                               │
│  ② 测试用例设计 & 实现 ────────────────────────── [自动]    │
│     Service / API / 状态机 / 账本                           │
│              │                                               │
│              ▼                                               │
│  ③ 执行测试 ───────────────────────────────────── [自动]    │
│     pytest (精确 + 可选全量)                                │
│              │                                               │
│              ▼                                               │
│  ④ 自动修复循环 ───────────────────────────────── [自动]    │
│     最多 2 轮                                               │
│              │                                               │
│              ▼                                               │
│  ⑤ 测试总结 & Freeze ──────────────────────────── [自动]    │
│     生成 Freeze 报告                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 测试范围识别

**影响分析**:

| 改动类型 | 需要覆盖的测试 |
|---------|--------------|
| Service 函数修改 | 单元测试 + API 测试 |
| Router 修改 | API 测试 |
| Schema 修改 | 单元测试 + API 测试 |
| 状态机逻辑 | 状态机转换测试 |
| 账本逻辑 | 账本不变量测试 |

### 7.3 测试用例设计

#### Service 层测试设计

| 测试类型 | 说明 | 示例 |
|---------|------|------|
| Happy Path | 正向路径 | 成功审批 |
| 边界条件 | 极值/空数据 | 金额为 0 |
| 错误状态 | 非法状态 | 已审批的再审批 |
| 权限检查 | 不同角色 | 无权限用户审批 |

#### API 层测试设计

| 测试类型 | 说明 | 验证点 |
|---------|------|-------|
| 成功响应 | 正向路径 | HTTP 200 + 响应体 |
| 错误响应 | 业务错误 | HTTP 4xx + 错误码 |
| 权限测试 | 不同角色 | HTTP 403 |

#### 特殊模块测试

```python
# 状态机测试
async def test_topup_state_transitions():
    """验证状态机转换规则"""
    # 允许的转换
    assert can_transition("pending", "approved") == True
    assert can_transition("pending", "rejected") == True

    # 禁止的转换
    assert can_transition("approved", "pending") == False
    assert can_transition("rejected", "approved") == False

# 账本不变量测试
async def test_ledger_balance_invariant():
    """验证账本余额不变量"""
    before_balance = await get_total_balance(db)
    await approve_topup(db, topup_id, user, {})
    after_balance = await get_total_balance(db)

    # 总余额应该增加充值金额
    assert after_balance == before_balance + topup.amount
```

### 7.4 测试执行

```bash
# 精确执行本次相关测试
pytest backend/tests/services/test_topup_service.py -v
pytest backend/tests/api/test_topups_api.py -v

# 可选: 全量回归
pytest backend/tests -v
```

### 7.5 quick-check 可观测性规范

**执行命令**:
```bash
python super_review_agent.py quick-check \
  --doc <doc_path> \
  --codex-prompt <prompt_path>
```

**退出码规范**:
| 退出码 | 含义 |
|--------|------|
| 0 | 成功，无 P0/P1 缺陷 |
| 1 | 发现 P0/P1 缺陷 |
| 2+ | 执行错误 |

**日志输出规范**:
```
📊 Quick Check 结果: P0=<count>, P1=<count>
✓ 文档质量良好，无 P0/P1 缺陷
# 或
⚠️  发现 <p0> 个 P0 缺陷和 <p1> 个 P1 缺陷，需要修复
```

**JSON 日志片段** (用于 CI 解析):
```json
{
  "mode": "quick-check",
  "p0_count": 3,
  "p1_count": 6,
  "passed": false,
  "failures": ["P0-LEDGER-001", "P0-STATE-002"],
  "exit_code": 1
}
```

**上线门禁集成**:
```bash
# CI 中使用退出码阻断
python super_review_agent.py quick-check ... || exit 1
```

### 7.6 自动修复循环

```
┌─────────────────────────────────────────────────────────────┐
│                    自动修复 Loop                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Round 1: 分析失败 → 生成补丁 → 重跑测试                     │
│           (修明显 bug / 漏测)                                │
│                    │                                         │
│                    ▼ 还失败?                                 │
│  Round 2: 分析失败 → 生成补丁 → 重跑测试                     │
│           (补细节或小逻辑错误)                               │
│                    │                                         │
│                    ▼ 还失败?                                 │
│  停止! 生成 FAILURE_REPORT_xxx.md                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**自动修复日志输出规范**:
```json
{
  "mode": "auto-fix",
  "rounds_executed": 2,
  "max_rounds": 2,
  "final_passed": false,
  "rounds": [
    {
      "round": 1,
      "files_changed": ["backend/services/topup.py"],
      "lines_changed": 15,
      "risk_tags": ["other"],
      "test_result": "failed"
    },
    {
      "round": 2,
      "files_changed": ["backend/services/topup.py"],
      "lines_changed": 8,
      "risk_tags": ["state_machine"],
      "test_result": "failed"
    }
  ],
  "failure_report": "FAILURE_REPORT_topup_20251206.md",
  "exit_code": 1
}
```

### 7.7 质量门槛判断

| 检查项 | 要求 |
|--------|------|
| 本次改动测试 | 100% 通过 |
| 全局 pytest | 不得新增失败 |
| SoT 审计 | P0=0, P1=0 |
| quick-check 退出码 | 必须为 0 |

### 7.8 测试 Freeze 报告

**产出**: `{MODULE}_TEST_FREEZE_REPORT_vX.Y.md`

在 MASTER / Orchestration SoT 中登记:
> "该模块测试体系已达上线标准，后续改动必须对齐这份报告"

---

## 8. 文档编写流程（SoT & 实现文档）

> **目标**: 保证"规范 → 实现 → 测试 → Freeze"链路有文字证据

### 8.1 文档分类

| 类别 | 主导者 | AI 权限 | 示例 |
|------|-------|--------|------|
| **SoT 文档** | 人工 | 只读 | STATE_MACHINE.md |
| **实现文档** | AI 可生成 | 可写 | IMPLEMENTATION_REPORT |
| **报告文档** | AI 可生成 | 可写 | TEST_FREEZE_REPORT |

### 8.2 SoT 文档流程（人工主导）

```
┌─────────────────────────────────────────────────────────────┐
│                    SoT 文档编写流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ① 提出变更需求 ───────────────────────────────── [人工]    │
│     "要增加一个充值审批流程"                                 │
│              │                                               │
│              ▼                                               │
│  ② 修改相关 SoT 文件 ──────────────────────────── [人工]    │
│     STATE_MACHINE.md / DATA_SCHEMA.md / ...                 │
│              │                                               │
│              ▼                                               │
│  ③ 评审 & 定版 ────────────────────────────────── [人工]    │
│     标记版本号 (vX.Y)                                       │
│     在 MASTER_SPEC 里记录                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**SoT 变更清单**:

| SoT 文档 | 变更内容 |
|---------|---------|
| `STATE_MACHINE.md` | 新增/修改状态 & 转移规则 |
| `DATA_SCHEMA.md` | 新增字段、表、索引 |
| `LEDGER_SOT.md` | 调整记账口径 |
| `AUTH_SPEC.md` | 权限矩阵变化 |
| `ERROR_CODES_SOT.md` | 新增错误码定义 |

### 8.3 实现文档流程（AI 可生成）

#### 设计/实现 Plan 文档

**文件**: `PLAN_{MODULE}_vX.Y.md`

**内容**:
- 要改哪些文件
- 落地哪些 SoT 条款
- 预期风险点

#### 实现完成报告

**文件**: `{MODULE}_IMPLEMENTATION_REPORT_vX.Y.md`

**内容**:
- 变更摘要
- 新增/修改文件清单
- 核心业务逻辑说明
- 对 SoT 条款的落地情况

#### 测试 & Freeze 报告

**文件**: `{MODULE}_TEST_FREEZE_REPORT_vX.Y.md`

**内容**:
- SoT 对齐性
- 测试覆盖表
- P0/P1/P2 问题与 Freeze 评级
- 回滚策略
- **证据清单**

#### Freeze 报告证据清单

发布前必须填写以下证据字段，确保上线审计闭环：

```markdown
## 6. 证据清单 (必填)

### 6.1 测试命令
```bash
pytest backend/tests/services/test_topup_service.py -v
pytest backend/tests/api/test_topups_api.py -v
```

### 6.2 日志路径
- 测试日志: `logs/test_topup_20251206.log`
- CI 日志: `https://github.com/.../actions/runs/xxxxx`

### 6.3 关联 Commit
- 主提交: `abc123def` - feat: implement topup approval
- 测试修复: `456789ghi` - fix: topup state validation

### 6.4 Plan 文件
- `docs/reports/PLAN_TOPUP_APPROVAL_v1.0.md`

### 6.5 自动修复轮次摘要
| 轮次 | 改动文件 | 改动行数 | 结果 |
|------|---------|---------|------|
| 1 | topup_service.py | 12 | 失败 |
| 2 | topup_service.py | 5 | 成功 |

### 6.6 quick-check 结果
```json
{"p0_count": 0, "p1_count": 0, "passed": true, "exit_code": 0}
```
```

**必填检查**: 若证据清单字段缺失 → 禁止发布

### 8.4 变更记录 (OpenSpec)

**位置**: `openspec/changes/{module}-vX/`

```
openspec/changes/topup-approval-v1/
├── tasks.md           # 任务清单
├── decisions.md       # 决策记录
└── known_issues.md    # 已知问题
```

---

# Part III: 系统实现

## 9. 系统架构

### 9.1 六层架构模型

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AI 代码工厂架构                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Layer 1: 入口层 (Entry)                                      │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  │   │
│  │  │ Claude 对话模式 │  │  CLI 命令模式   │  │  MCP 协议模式  │  │   │
│  │  │ /agent be xxx  │  │ python -m cli  │  │ (future)       │  │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                    │                                 │
│                                    ▼                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Layer 2: 命令路由层 (Command Router)                         │   │
│  │  .claude/commands/                                            │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │   │
│  │  │ agent.md │ │ orch.md  │ │sot-check │ │doc-agent │        │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                    │                                 │
│                                    ▼                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Layer 3: 编排层 (Orchestrator)                               │   │
│  │  agents/agent_core/orchestrator_agent.py                      │   │
│  │  ┌────────────────────────────────────────────────────────┐  │   │
│  │  │  Flow 定义: be_only | test_only | be_then_test | full  │  │   │
│  │  └────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                    │                                 │
│                                    ▼                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Layer 4: Agent 执行层 (Agent Executor)                       │   │
│  │  agents/agent_core/                                           │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐│   │
│  │  │be_agent │ │fe_agent │ │test_agt │ │doc_agt  │ │review_a ││   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘│   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                    │                                 │
│                                    ▼                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Layer 5: Skill 层 (Prompt Factory)                           │   │
│  │  .claude/skills/                                              │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ │   │
│  │  │ be-gen     │ │ fe-gen     │ │ test-gen   │ │ doc-gen    │ │   │
│  │  │ schema-gen │ │ api-gen    │ │ sot-check  │ │ review     │ │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘ │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                    │                                 │
│                            读取 │ 只读                              │
│                                    ▼                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Layer 6: SoT 文档层 (Single Source of Truth)                 │   │
│  │  docs/sot/                                                  │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ │   │
│  │  │STATE_MACH │ │DATA_SCHEMA │ │ LEDGER_SOT │ │ AUTH_SPEC  │ │   │
│  │  │ API_SOT   │ │ERROR_CODES │ │BUSINESS_R  │ │ MASTER_SP  │ │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘ │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                    │                                 │
│                            生成 │ 写入                              │
│                                    ▼                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Output: 产出层                                               │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐     │   │
│  │  │ backend/      │  │ frontend/     │  │ docs/reports/ │     │   │
│  │  │ schemas/      │  │ src/modules/  │  │ FREEZE_REPORT │     │   │
│  │  │ services/     │  │ lib/api/      │  │ IMPL_REPORT   │     │   │
│  │  │ routers/      │  │               │  │               │     │   │
│  │  │ tests/        │  │               │  │               │     │   │
│  │  └───────────────┘  └───────────────┘  └───────────────┘     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 层级职责矩阵

| 层级 | 职责 | 输入 | 输出 | 可修改 |
|------|------|------|------|--------|
| **入口层** | 接收用户指令，路由到正确的命令 | 用户输入 | 命令参数 | ❌ |
| **命令路由层** | 解析命令，分发到 Agent 或 Orchestrator | 命令字符串 | 结构化任务 | ⚠️ 谨慎 |
| **编排层** | 按 Flow 定义调度多个 Agent | 任务描述 | Agent 调用序列 | ⚠️ 谨慎 |
| **Agent 执行层** | 执行具体的代码生成/测试/文档任务 | 任务 + SoT 上下文 | 代码/测试/报告 | ✅ |
| **Skill 层** | 提供可复用的 Prompt 模板 | Agent 调用 | 结构化 Prompt | ✅ |
| **SoT 文档层** | 提供业务规则、数据模型、状态机等约束 | N/A | 约束条件 | ❌ 只读 |
| **产出层** | 生成的代码、测试、报告 | Agent 输出 | 文件 | ✅ (边界内) |

### 9.3 数据流图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        数据流 (Data Flow)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  用户输入                                                            │
│     │                                                                │
│     │ "/agent be 实现充值审批"                                       │
│     ▼                                                                │
│  ┌─────────────┐    解析命令    ┌─────────────┐                     │
│  │ Command     │ ────────────→ │ Orchestrator│                     │
│  │ Router      │               │             │                     │
│  └─────────────┘               └─────────────┘                     │
│                                      │                              │
│                                      │ 调度 Agent                   │
│                                      ▼                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      Agent 执行                              │   │
│  │                                                              │   │
│  │   ┌─────────┐    加载 Skill    ┌─────────┐                  │   │
│  │   │be_agent │ ──────────────→ │ Skill   │                  │   │
│  │   └─────────┘                  │ Prompt  │                  │   │
│  │        │                       └─────────┘                  │   │
│  │        │ 读取 SoT                   │                        │   │
│  │        ▼                            │                        │   │
│  │   ┌─────────────────┐               │                        │   │
│  │   │  SoT 文档层      │               │                        │   │
│  │   │  STATE_MACHINE  │ ◄─────────────┘                        │   │
│  │   │  DATA_SCHEMA    │   约束条件                              │   │
│  │   │  LEDGER_SOT     │                                        │   │
│  │   └─────────────────┘                                        │   │
│  │        │                                                     │   │
│  │        │ 生成代码                                             │   │
│  │        ▼                                                     │   │
│  │   ┌─────────────────────────────────────────────────────┐   │   │
│  │   │  产出文件                                            │   │   │
│  │   │  ├── backend/schemas/topup.py                       │   │   │
│  │   │  ├── backend/services/topup_service.py              │   │   │
│  │   │  ├── backend/routers/topups.py                      │   │   │
│  │   │  └── backend/tests/...                              │   │   │
│  │   └─────────────────────────────────────────────────────┘   │   │
│  │                                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                      │                              │
│                                      │ 执行测试                     │
│                                      ▼                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  自动修复 Loop (最多 2 轮)                                    │   │
│  │                                                              │   │
│  │   pytest → 失败? → 分析 → 修复 → pytest → 还失败?            │   │
│  │                                      │                       │   │
│  │                                      ▼                       │   │
│  │                          第3次失败 → FAILURE_REPORT           │   │
│  │                                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                      │                              │
│                                      │ 成功                        │
│                                      ▼                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  生成报告                                                    │   │
│  │  ├── IMPLEMENTATION_REPORT_vX.Y.md                          │   │
│  │  └── TEST_FREEZE_REPORT_vX.Y.md                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                      │                              │
│                                      │ 人工确认                    │
│                                      ▼                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  git add → git commit → git push                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.4 现状与目标对比

#### 当前状态 (As-Is)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        当前状态 (部分实现)                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  入口层         ✅ Claude 对话模式可用                               │
│                 ⚠️ CLI 模式基础框架存在，需完善                      │
│                                                                      │
│  命令路由层     ✅ /agent, /orch, /sot-check, /doc-agent 已定义     │
│                 ⚠️ 命令解析逻辑需优化                                │
│                                                                      │
│  编排层         ⚠️ orchestrator_agent.py 存在，Flow 定义不完整      │
│                 ❌ be_then_test 流程需完善                           │
│                                                                      │
│  Agent 执行层   ⚠️ be_agent, fe_agent 等存在，功能不完整            │
│                 ❌ 缺乏统一的 SoT Loader                             │
│                                                                      │
│  Skill 层       ⚠️ 12 个 Skill 目录存在，多为文档/测试相关          │
│                 ❌ 缺乏核心 be-gen, test-gen Skill                   │
│                                                                      │
│  SoT 文档层     ✅ 完整，已 Freeze                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### 目标状态 (To-Be)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        目标状态 (Phase 3 完成)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  入口层         ✅ Claude 对话模式                                  │
│                 ✅ CLI 批处理模式                                    │
│                 ✅ MCP 协议集成                                      │
│                                                                      │
│  命令路由层     ✅ 智能命令解析                                     │
│                 ✅ 参数验证                                          │
│                                                                      │
│  编排层         ✅ 完整 Flow 定义                                   │
│                 ✅ 多 Agent 并行支持                                 │
│                 ✅ 自动回滚机制                                      │
│                                                                      │
│  Agent 执行层   ✅ 完整 Agent 矩阵 (be/fe/test/doc/review)         │
│                 ✅ 统一 SoT Loader                                   │
│                 ✅ 自动修复 Loop                                     │
│                                                                      │
│  Skill 层       ✅ be-gen (后端三层生成)                            │
│                 ✅ fe-gen (前端模块生成)                             │
│                 ✅ test-gen (测试用例生成)                           │
│                 ✅ sot-check (SoT 合规检查)                         │
│                                                                      │
│  SoT 文档层     ✅ 完整，版本化，自动校验                           │
│                                                                      │
│  CI/CD 集成     ✅ GitHub Actions (pytest + ruff + mypy)           │
│                 ✅ pre-commit hooks                                  │
│                 ✅ 自动 commit 到 feature branch                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.5 推荐目录结构

```
AI_ad_spend02/
├── .claude/                          # Claude Code 配置层
│   ├── commands/                     # Slash 命令入口
│   │   ├── agent.md                  # /agent - 单 Agent 调用
│   │   ├── orch.md                   # /orch - 多 Agent 工作流
│   │   ├── sot-check.md              # /sot-check - SoT 合规检查
│   │   └── doc-agent.md              # /doc-agent - 文档审计
│   │
│   ├── skills/                       # Skill 定义 (Prompt 工厂)
│   │   └── ai-ad-{domain}-{func}/    # 按领域-功能命名
│   │
│   └── agents/                       # Sub-Agent 定义
│       ├── codex-loop.md             # 代码审查修复循环
│       ├── doc-architect.md          # 文档架构
│       └── doc-fixer.md              # 文档修复
│
├── agent_platform/                   # 核心框架层 (CLI/MCP 模式)
│   ├── core/                         # 协议定义
│   ├── llm/                          # LLM 客户端
│   └── cli.py                        # CLI 入口
│
├── agents/                           # 业务实现层
│   ├── agent_core/                   # Agent 实现
│   │   ├── be_agent.py               # 后端 Agent
│   │   ├── fe_agent.py               # 前端 Agent
│   │   ├── test_agent.py             # 测试 Agent
│   │   └── orchestrator_agent.py     # 编排 Agent
│   └── skills/                       # Skill 函数
│
├── docs/sot/                       # SoT 文档层 (只读!)
│   ├── STATE_MACHINE.md
│   ├── DATA_SCHEMA.md
│   ├── LEDGER_SOT.md
│   └── ...
│
├── backend/                          # 后端代码 (可写区)
│   ├── schemas/                      # ✅ 可写
│   ├── services/                     # ✅ 可写
│   ├── routers/                      # ✅ 可写
│   ├── tests/                        # ✅ 可写
│   └── models/                       # ❌ 禁区
│
└── frontend/                         # 前端代码 (可写区)
    └── src/modules/                  # ✅ 可写
```

### 9.6 运行模式 (v2.4 统一架构)

> ⚠️ **架构变更**: v2.4 已完成从 "Python Agent + SuperClaude 双轨" 到 "纯 SuperClaude Skill" 的迁移。
> Python Agent CLI 模式已弃用，统一使用 Claude Code 对话模式。

```
┌─────────────────────────────────────────────────────────────────┐
│              Claude Code 对话模式 (唯一模式)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  用户命令                       Skill 调用                        │
│  ─────────                     ──────────                        │
│  /gen be <task>       →        ai-ad-be-gen                      │
│  /gen fe <task>       →        ai-ad-fe-gen                      │
│  /gen test <task>     →        ai-ad-test-gen                    │
│  /doc [dir]           →        ai-doc-system-auditor             │
│  /review <file>       →        ai-master-architect               │
│  /sot-check <file>    →        ai-ad-spec-governor               │
│                                                                  │
│  Skills 位置: .claude/skills/                                    │
│  Commands 位置: .claude/commands/                                │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  优势:                                                           │
│  - 无需 LLM API Key (使用 Claude Code 内置能力)                  │
│  - 无 Python 运行时依赖                                          │
│  - Skill 纯 Prompt 定义，易于维护                                │
│  - 统一的命令入口                                                │
└─────────────────────────────────────────────────────────────────┘
```

#### 已弃用组件 (Deprecated)

| 组件 | 状态 | 归档位置 |
|------|------|----------|
| `agents/` 目录 | deprecated | `docs/archive/2025-12-cleanup/agents/` |
| `agent_platform/` 目录 | deprecated | `docs/archive/2025-12-cleanup/agent_platform/` |
| `/agent` 命令 | removed | - |
| `/orch` 命令 | removed | - |
| ai-ad-agents-test-orchestrator | deprecated | `.claude/skills/` (标记为 deprecated) |
| ai-ad-agents-test-runner | deprecated | `.claude/skills/` (标记为 deprecated) |

### 9.7 SuperClaude 增强层

> **详细规范**: 参见 `docs/6.agent-layer/SUPERCLAUDE_INTEGRATION_GUIDE_v2.0.md`

#### 9.7.1 技术限制声明

> ⚠️ **重要：SuperClaude 目前没有可编程 SDK**

| 限制 | 说明 |
|------|------|
| **无 API 调用** | `/sc:xxx` 命令只能由用户在 Claude Code 交互界面手动触发 |
| **Skill 无法直接调用** | `.claude/skills/` 中的 Skill 无法在运行时调用 SuperClaude 命令 |
| **Agent 无法直接调用** | `agent_platform/` 中的 Agent 无法在代码中调用 SuperClaude 命令 |

**当前集成方式**: 通过 **Prompt 级模式迁移**，将 SuperClaude 的工作流思维嵌入到 Skill 和 Agent 的 System Prompt 中。

#### 9.7.2 增强模式概览

| 模式 | 说明 | 触发方式 | 实现状态 |
|------|------|---------|---------|
| `pre_analysis` | 前置分析 - 代码生成前的上下文分析 | Prompt 模板嵌入 | ✅ 文档级配置 |
| `post_review` | 后置审查 - 代码生成后的质量检查 | Prompt 模板嵌入 | ✅ 文档级配置 |
| `smart_suggest` | 智能建议 - 按需调用的优化建议 | 用户手动触发 `/sc:improve` | ✅ 用户级 |
| `troubleshoot` | 问题诊断 - Bug 修复时的根因分析 | 用户手动触发 `/sc:troubleshoot` | ✅ 用户级 |

#### 9.7.3 已增强的 Skills

| Skill | 版本 | 增强模式 | 说明 |
|-------|------|---------|------|
| ai-ad-be-gen | v2.1 | pre_analysis, post_review | 后端代码生成 |
| ai-ad-test-gen | v2.2 | pre_analysis, post_review | 测试用例生成 |
| ai-ad-fe-gen | v2.1 | pre_analysis, post_review | 前端代码生成 |
| ai-doc-system-auditor | v2.0 | post_review, smart_suggest | 文档审计 |

#### 9.7.4 Skill Enhancement 配置示例

在 Skill 的 YAML front matter 中配置增强：

```yaml
---
name: ai-ad-be-gen
version: "2.1"
status: production

# SuperClaude Enhancement Configuration
enhancement:
  enabled: true
  superclaude_patterns:
    - design_first        # 吸收 /sc:design 设计优先
    - step_implementation # 吸收 /sc:implement 步骤化执行
    - task_breakdown      # 吸收 /sc:pm 任务分解
  internal_workflow: true  # 在 System Prompt 中嵌入工作流
  sot_priority: true       # SoT 检查结果优先级最高

baseline: AI_CODE_FACTORY_DEV_GUIDE_v2.3, SoT Freeze v2.6
---
```

#### 9.7.5 Enhancement Hooks API (Phase 2 设计目标)

> ⏳ **状态**: Phase 2 设计目标，当前未实现

未来计划支持的可编程 Enhancement Hooks：

```typescript
// Phase 2 设计目标 - 尚未实现
interface EnhancementHooks {
  enhance_before(context: TaskContext): PreAnalysisResult;
  enhance_after(output: SkillOutput): PostReviewResult;
  suggest(code: string): ImprovementSuggestions;
  diagnose(error: Error): RootCauseAnalysis;
}
```

当前替代方案：通过 System Prompt 模板嵌入工作流模式。

---

## 10. Skill 与 Command 规范

### 10.1 SKILL.md 格式

```markdown
---
name: ai-ad-be-gen-skill
version: "2.1"
status: production
layer: Skill

sot_dependencies:
  required:
    - docs/sot/DATA_SCHEMA.md
    - docs/sot/STATE_MACHINE.md
    - docs/sot/API_SOT.md
  optional:
    - docs/sot/LEDGER_SOT.md
    - docs/sot/ERROR_CODES_SOT.md

output_boundaries:
  writable:
    - backend/schemas/**
    - backend/services/**
    - backend/routers/**
  forbidden:
    - backend/models/**
    - migrations/**

# SuperClaude Enhancement (Prompt 级集成)
enhancement:
  enabled: true
  superclaude_patterns:
    - design_first
    - step_implementation
    - task_breakdown
  internal_workflow: true
  sot_priority: true

baseline: AI_CODE_FACTORY_DEV_GUIDE_v2.3, SoT Freeze v2.6
---

# Skill 名称

## 1. Purpose
## 2. Input Contract
## 3. Output Contract
## 4. Constraints (必须遵守的边界)
## 5. Prompt Template
## 6. Self-Check Checklist
## 7. Version History
```

### 10.2 Skill 行数标准

| 状态 | 行数 | 说明 |
|------|------|------|
| ✅ 健康 | < 500 | 保持 |
| ⚠️ 警告 | 500-1000 | 建议拆分 |
| ❌ 必须拆分 | > 1000 | 立即拆分 |

### 10.3 Command 清单

> ⚠️ **v2.4 架构更新**: `/agent` 和 `/orch` 命令已移除，统一使用 `/gen`、`/review`、`/doc`、`/sot-check`

| Command | 用途 | 示例 |
|---------|------|------|
| `/gen be <task>` | 后端代码生成 | `/gen be 实现充值审批` |
| `/gen fe <task>` | 前端代码生成 | `/gen fe 实现充值页面` |
| `/gen test <task>` | 测试代码生成 | `/gen test 为充值模块生成测试` |
| `/review <file>` | 代码/架构审查 | `/review backend/services/topup_service.py` |
| `/sot-check [path]` | SoT 合规检查 | `/sot-check backend/` |
| `/doc [dir]` | 文档审计 | `/doc docs/` |

<details>
<summary>📜 历史命令参考 (deprecated)</summary>

| 旧命令 | 替代命令 | 说明 |
|--------|---------|------|
| `/agent be <task>` | `/gen be <task>` | 后端代码生成 |
| `/agent fe <task>` | `/gen fe <task>` | 前端代码生成 |
| `/agent test <task>` | `/gen test <task>` | 测试代码生成 |
| `/orch be_then_test <task>` | `/gen be` + `/gen test` | 后端→测试流程 |
| `/orch full <task>` | `/gen be` + `/gen fe` + `/gen test` | 完整流程 |
| `/doc-agent [dir]` | `/doc [dir]` | 文档审计 |

</details>

### 10.4 Agent Types

| Type | Key | SoT 依赖 |
|------|-----|---------|
| Backend | `be` | STATE_MACHINE, DATA_SCHEMA, API_SOT, LEDGER_SOT, AUTH_SPEC |
| Frontend | `fe` | FRONTEND_RULES, UI_DESIGN_SYSTEM |
| Test | `test` | TESTING_STRATEGY, STATE_MACHINE |
| Doc | `doc` | 全部 SoT |
| Review | `review` | 全部 SoT |

### 10.5 预定义 Flows

| Flow ID | 步骤 | 产出 |
|---------|------|------|
| `be_only` | be-gen | Router + Service + Schema |
| `test_only` | test-gen | test_xxx.py |
| `be_then_test` | be-gen → test-gen | 后端代码 + 测试 |
| `full` | be-gen → fe-gen → test-gen | 全栈代码 |

---

## 11. 推荐工作流组合

> **详细说明**: 参见 `docs/6.agent-layer/SUPERCLAUDE_INTEGRATION_GUIDE_v2.0.md` 第三章

### 11.1 命令分类

#### AI 代码工厂专属工具 (SoT 驱动)

> ⚠️ **v2.4 架构更新**: 使用纯 Skill 架构，命令统一为 `/gen`、`/review`、`/doc`、`/sot-check`

| 工具 | 用途 | 场景 | 触发的 Skill |
|------|------|------|-------------|
| `/gen be <task>` | 后端代码生成 | Router/Service/Schema | ai-ad-be-gen |
| `/gen fe <task>` | 前端代码生成 | 组件/页面 | ai-ad-fe-gen |
| `/gen test <task>` | 测试代码生成 | 状态机/账本测试 | ai-ad-test-gen |
| `/review <file>` | 代码审查 | 架构/SoT 合规 | ai-master-architect |
| `/doc [dir]` | 文档审计 | P0/P1/P2 检查 | ai-doc-system-auditor |
| `/sot-check <path>` | SoT 合规检查 | 版本/引用验证 | ai-ad-spec-governor |

#### SuperClaude 通用工具 (手动触发)

| 工具 | 用途 | 场景 |
|------|------|------|
| `/sc:pm` | 项目管理/任务分解 | 需求分析、规划 |
| `/sc:analyze` | 代码分析 | 质量、安全、性能 |
| `/sc:troubleshoot` | 问题诊断 | Bug 定位 |
| `/sc:improve` | 代码改进 | 重构、优化 |
| `/sc:research` | 深度研究 | 技术调研 |
| `/sc:design` | 架构设计 | API、组件设计 |
| `/sc:document` | 文档生成 | 文档编写 |
| `/sc:git` | Git 操作 | 提交、分支 |
| `/sc:test` | 测试执行 | 运行测试 |

### 11.2 黄金工作流组合

#### 完整功能开发 (BE_DEV_FLOW)

```bash
# Step 1: 需求分析 (SuperClaude)
/sc:pm "分析 XXX 功能需求，制定实施计划"

# Step 2: SoT 合规检查 (AI 代码工厂)
/sot-check docs/sot/

# Step 3: 代码生成 (AI 代码工厂)
/gen be "生成 XXX 模块的 Schema 层"
/gen be "实现 XXX 模块的 Service 层"
/gen be "实现 XXX 模块的 Router 层"

# Step 4: 测试生成 (AI 代码工厂)
/gen test "为 XXX 模块生成单元测试"

# Step 5: 代码审查 (混合)
/review backend/services/xxx_service.py
/sot-check backend/services/xxx_service.py

# Step 6: 提交 (SuperClaude)
/sc:git commit
```

#### Bug 修复 (API_FIX_FLOW)

```bash
# Step 1: 问题诊断 (SuperClaude)
/sc:troubleshoot "描述问题现象"

# Step 2: SoT 检查 (AI 代码工厂)
/sot-check backend/services/xxx_service.py

# Step 3: 代码审查定位问题 (AI 代码工厂)
/review backend/services/xxx_service.py

# Step 4: 修复 (AI 代码工厂)
/gen be "修复 XXX 问题"

# Step 5: 测试 (AI 代码工厂)
/gen test "为修复生成回归测试"

# Step 6: 提交 (SuperClaude)
/sc:git commit
```

#### 文档治理 (DOC_FREEZE_FLOW)

```bash
# Step 1: 审计 (AI 代码工厂)
/doc docs/

# Step 2: 验证 (AI 代码工厂)
/sot-check docs/

# Step 3: 审查 (AI 代码工厂)
/review docs/changed_file.md

# Step 4: 提交 (SuperClaude)
/sc:git commit
```

### 11.3 决策矩阵

| 任务类型 | 涉及 SoT | 推荐工具组合 (v2.4) |
|---------|---------|---------------------|
| 新功能开发 | 是 | `/sc:pm` → `/sot-check` → `/gen be` → `/gen test` → `/review` → `/sc:git` |
| Bug 修复 | 可能 | `/sc:troubleshoot` → `/sot-check` → `/gen be` → `/gen test` → `/sc:git` |
| 代码重构 | 是 | `/sc:analyze` → `/sot-check` → `/sc:improve` → `/review` → `/sc:test` |
| 文档更新 | 是 | `/doc` → `/sot-check` → `/review` → `/sc:git` |
| 简单修改 | 否 | `/sc:implement` |
| 研究调查 | 否 | `/sc:research` |
| Git 操作 | 否 | `/sc:git` |

### 11.4 /dev-flow 统一入口 (Phase 2 设计目标)

> ⏳ **状态**: Phase 2 设计目标，当前推荐使用上述命令组合

未来计划实现的 `/dev-flow` 命令将提供统一工作流入口：

```bash
# Phase 2 设计目标 - 尚未实现
/dev-flow feature "实现充值审批功能"
/dev-flow bugfix "修复状态转换问题"
/dev-flow refactor "重构 topup_service"
/dev-flow docs "更新 API 文档"
```

当前替代方案：使用 §11.2 中的黄金工作流组合。

---

## 12. 场景示例：充值审批功能

### 12.1 触发命令

```bash
# v2.4 新命令
/gen be "实现充值审批功能的 Schema 层"
/gen be "实现充值审批功能的 Service 层"
/gen be "实现充值审批功能的 Router 层"
```

### 12.2 完整流程执行

```
Step 1: 读取 SoT
├── STATE_MACHINE.md#topup
├── LEDGER_SOT.md#topup
├── DATA_SCHEMA.md#topups
├── AUTH_SPEC.md
├── BUSINESS_RULES.md
└── ERROR_CODES_SOT.md

Step 2: 生成 Plan
└── PLAN_TOPUP_APPROVAL_v1.0.md

Step 3: 生成代码
├── backend/schemas/topup.py
├── backend/services/topup_service.py
└── backend/routers/topups.py

Step 4: 生成测试
├── backend/tests/services/test_topup_service.py
├── backend/tests/api/test_topups_api.py
└── backend/tests/test_state_machine_transitions.py

Step 5: 执行测试 & 自动修复
└── 最多 2 轮

Step 6: 生成报告
├── TOPUP_APPROVAL_IMPLEMENTATION_REPORT_v1.0.md
└── TOPUP_APPROVAL_TEST_FREEZE_REPORT_v1.0.md

Step 7: 人工确认
└── git diff → git commit → git push
```

### 12.3 自动运行的检查

```bash
# 1. SoT 对齐检查
/sot-check backend/services/topup_service.py
/sot-check backend/routers/topups.py

# 2. pytest 模块相关
pytest backend/tests/services/test_topup_service.py -v
pytest backend/tests/api/test_topups_api.py -v
pytest backend/tests/test_state_machine_transitions.py -k "topup" -v

# 3. 静态检查 (仅改动文件)
ruff check backend/services/topup_service.py
mypy backend/services/topup_service.py
```

### 12.4 成功后的人工步骤

```bash
# 1. Review diff
git diff

# 2. 看报告
cat TOPUP_APPROVAL_IMPLEMENTATION_REPORT_v1.0.md
cat TOPUP_APPROVAL_TEST_FREEZE_REPORT_v1.0.md

# 3. 确认无误后提交
git add .
git commit -m "feat: implement topup approval flow"
git push origin feature/topup-approval
```

---

## 13. 失败处理与报告

### 13.1 失败报告格式

```markdown
# TOPUP_APPROVAL_FAILURE_REPORT_v1.0.md

## 1. 当前代码状态
- 已生成文件列表
- 部分完成的功能

## 2. 失败日志摘要
- pytest 失败用例
- SoT 违规项
- 静态检查错误

## 3. 推测根因
- 可能的原因分析

## 4. 建议人工介入点
- 具体文件
- 具体用例
- 建议修复方向
```

### 13.2 自动修复安全阈值

为防止自动修复引入不可控风险，规定以下阈值：

#### 每轮记录字段

每轮自动修复必须记录：
| 字段 | 说明 |
|------|------|
| `files_changed` | 本轮改动文件列表 |
| `lines_changed` | 本轮改动行数 |
| `risk_tags` | 风险标签 (见下表) |

#### 风险标签定义

| 风险标签 | 含义 | 阈值 |
|---------|------|------|
| `state_machine` | 涉及状态转换 | 立即停止 |
| `ledger` | 涉及账本分录 | 立即停止 |
| `auth` | 涉及权限逻辑 | 立即停止 |
| `other` | 其他业务逻辑 | 允许继续 |

#### 停止阈值

| 条件 | 动作 |
|------|------|
| 单轮改动 > 30 行 | 立即停止，生成 FAILURE_REPORT |
| 触及 `state_machine` / `ledger` / `auth` 标签 | 立即停止，生成 FAILURE_REPORT |
| 累计改动 > 50 行 | 立即停止，生成 FAILURE_REPORT |

**FAILURE_REPORT 新增字段**:
```markdown
## 5. 自动修复风险评估

| 轮次 | 改动文件 | 改动行数 | 风险标签 | 停止原因 |
|------|---------|---------|---------|---------|
| 1 | topup_service.py | 15 | other | 继续 |
| 2 | topup_service.py | 22 | state_machine | **触及状态机，强制停止** |

**总改动行数**: 37
**触发阈值**: state_machine 风险标签
```

### 13.3 失败后的处理流程

```
失败报告生成后:
  ↓
人工查看 FAILURE_REPORT
  ↓
检查风险评估章节
  ↓
选择:
  A) 手动修复 → 重新运行 /gen test "补充测试"
  B) 调整需求 → 重新运行 /gen be "修复问题"
  C) 升级 SoT → 人工修改 SoT 后重试
```

---

## 14. 路线图

### 14.1 Phase 1 (当前)

- [x] 边界定义文档化
- [x] 开发流程规范化 (后端/前端/API/测试/文档)
- [x] 质量标准明确
- [x] SuperClaude Prompt 级集成
- [ ] 基础 Skill 实现 (be-gen, test-gen)
- [ ] 自动修复 Loop (2 轮)

### 14.2 Phase 2

- [ ] CI 集成 (GitHub Actions: pytest + ruff)
- [ ] pre-commit hooks (black/ruff)
- [ ] mypy 强制通过
- [ ] 前端 Agent (fe-gen)
- [ ] /dev-flow 统一入口命令
- [ ] Enhancement Hooks API 实现

### 14.3 Phase 3

- [ ] 全项目 CI 绿灯门禁
- [ ] 自动 commit 到 feature branch
- [ ] MCP 协议集成
- [ ] 多 Agent 并行

---

## 附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| **SoT** | Single Source of Truth，真相源文档，AI 只读 |
| **可写区** | AI 可以自动修改的代码目录 |
| **禁区** | AI 绝对不能碰的文件 |
| **自动修复 Loop** | 失败后自动重试，最多 2 轮 |
| **上线门禁** | 代码提交前必须满足的质量标准 |
| **API 契约** | 前后端对齐的接口规范文档 |
| **Freeze 报告** | 模块质量基线文档 |
| **SuperClaude** | 高级 Claude 工具套件，提供 /sc:* 命令 |
| **Prompt 级模式迁移** | 将 SuperClaude 工作流思维嵌入 Skill/Agent 的 System Prompt |
| **pre_analysis** | 前置分析模式，代码生成前执行 (Prompt 嵌入) |
| **post_review** | 后置审查模式，代码生成后执行 (Prompt 嵌入) |

### B. SoT 文档清单

| 文档 | 版本 | 用途 |
|------|------|------|
| STATE_MACHINE.md | v2.7 | 状态机定义 |
| DATA_SCHEMA.md | v5.3 | 数据模型 |
| API_SOT.md | v9.3 | API 规范 |
| ERROR_CODES_SOT.md | v2.1 | 错误码 |
| LEDGER_SOT.md | v1.2 | 账本规则 |
| AUTH_SPEC.md | v2.0 | 认证授权 |
| BUSINESS_RULES.md | v4.1 | 业务规则 |

### C. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.3 | 2025-12-07 | **SuperClaude 集成收敛**: <br>- §9.7 精简为概览+模式表，详细内容引用 INTEGRATION_GUIDE <br>- 明确技术限制：SuperClaude 无可编程 SDK <br>- §2.5 新增 SuperClaude 边界约束声明 <br>- §11 重命名为"推荐工作流组合"，移除未实现的 /dev-flow 细节 <br>- Enhancement Hooks API 标记为 Phase 2 设计目标 <br>- 更新术语表，移除未实现术语 |
| v2.2 | 2025-12-07 | SuperClaude 集成 (含 Enhancement Layer 详细架构) |
| v2.1 | 2025-12-06 | 可观测性与安全增强 |
| v2.0 | 2025-12-06 | 完整重构：边界定义 + 五大开发流程 + 六层架构模型 |
| v1.0 | 2025-12-01 | 初始版本 |

---

**文档控制**: Owner: wade | Baseline: MASTER.md v4.4, Agent Layer Freeze v1.0, SoT Freeze v2.6
