# Agent Platform 迁移日志

> **迁移文档**: [AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md](./AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md)
> **状态**: Phase 0 + Phase 1 + Phase 2 + Phase 3 + Phase 4 完成 | Phase 5 观察期进行中

---

## 迁移进度总览

| Phase | 描述 | 状态 | 完成日期 |
|-------|------|------|----------|
| Phase 0 | Freeze & 影子模式准备 | ✅ 完成 | 2025-12-04 |
| Phase 1 | 配置层迁移 | ✅ 完成 | 2025-12-04 |
| Phase 2 | Agent 层迁移 | ✅ 完成 | 2025-12-04 |
| Phase 3 | 技能层迁移 | ✅ 完成 | 2025-12-05 |
| Phase 4 | MCP 工具重构 | ✅ 完成 | 2025-12-05 |
| Phase 5 | 观察期 + 最终清理 | 🔄 观察期进行中 | 2025-12-05 ~ 2025-12-12 |

---

## Phase 0: Freeze & 影子模式准备

**完成日期**: 2025-12-04

### 0.3 影子模式兼容壳

**文件**: `agents/__init__.py`

- ✅ 改为影子模式转调壳
- ✅ 使用纯 `os.environ` 检查 `AGENT_PLATFORM_LEGACY`，避免循环依赖
- ✅ Legacy 模式：保留原有导入逻辑
- ✅ 新模式：延迟导入转发到 `agent_platform`

**文件**: `agents/cli.py`

- ✅ 改为转调壳
- ✅ 支持 `AGENT_PLATFORM_LEGACY=1` 回退

**文件**: `agents/cli_legacy.py`

- ✅ 原 CLI 逻辑备份

### 0.5 废弃说明

**文件**: `agents/_DEPRECATED.md`

- ✅ 包含紧急回退说明
- ✅ 包含删除条件清单
- ✅ 包含路径映射表
- ✅ 包含观察期时间线 (2025-12-04 ~ 2025-12-11)

### Phase 0 验收 Checklist

- [x] `agents/__init__.py` 改为转调壳（纯 os.environ 检查）
- [x] `agents/cli.py` 改为转调壳
- [x] `agents/cli_legacy.py` 已创建（原 CLI 备份）
- [x] `agents/_DEPRECATED.md` 已创建

---

## Phase 1: 配置层迁移

**完成日期**: 2025-12-04

### 1.1 创建配置目录

**目录**: `agent_platform/config/`

- ✅ `__init__.py` - 导出所有配置
- ✅ `paths.py` - BASE_PATH（带 fallback 和验证）
- ✅ `sot_files.py` - SOT_FILES 映射（对齐 SoT Freeze v2.6）
- ✅ `constants.py` - `is_legacy_mode()`, `is_mcp_mode()` 等

### 1.2 paths.py 详情

**功能**:
- `_get_base_path()`: 推断项目根路径
  - 优先级 1: `AGENT_PLATFORM_REPO_ROOT` 环境变量
  - 优先级 2: 从文件位置推断
  - 优先级 3: 当前工作目录（fallback）
- `_validate_base_path()`: 验证 `backend/`, `docs/` 是否存在

**导出**:
- `BASE_PATH`, `PROJECT_ROOT`, `BACKEND_DIR`, `FRONTEND_DIR`, `DOCS_DIR`, `TESTS_DIR`

### 1.3 sot_files.py 详情

**SOT_FILES 映射** (对齐 SoT Freeze v2.6 + Dev-Guides Freeze vFinal):

| 层级 | 文件数 |
|------|--------|
| Layer 1: Overview | 7 |
| Layer 2: SoT | 12 |
| Layer 3: Dev-Guides | 7 |
| Test artifacts | 2 |
| **总计** | **28** |

**CRITICAL_SOT_FILES**: `STATE_MACHINE`, `DATA_SCHEMA`, `BUSINESS_RULES`, `API_SOT`, `ERROR_CODES`, `LEDGER_SOT`, `AUTH_SPEC`

### 1.4 constants.py 详情

**函数**:
- `is_legacy_mode()`: 检查 `AGENT_PLATFORM_LEGACY` 环境变量
- `is_mcp_mode()`: 检查 `AGENT_PLATFORM_MODE` 环境变量
- `get_platform_mode()`: 返回当前模式字符串

### 1.6 MCP server.py 更新

**文件**: `agent_platform/mcp/server.py`

- ✅ `read_sot_file()`: 已使用 `from agent_platform.config.sot_files import SOT_FILES`
- ✅ `list_sot_files()`: 已更新为 `from agent_platform.config.sot_files import SOT_FILES`
- ⏳ `list_agents()`, `run_agent()`: 保留原导入 `from agents.agents_config`（等 Phase 2）

### Phase 1 验收 Checklist

- [x] `agent_platform/config/` 目录已创建
- [x] `paths.py` 包含 BASE_PATH（带 fallback 和验证）
- [x] `sot_files.py` 包含完整 SOT_FILES 映射
- [x] `constants.py` 包含 `is_legacy_mode()`, `is_mcp_mode()`
- [x] `mcp/server.py` 的 SOT_FILES 导入已更新

---

## Phase 2: Agent 层迁移

**完成日期**: 2025-12-04

### 2.1 Agent 清单与分类

| Agent | 类名 | mcp_safe | 说明 |
|-------|------|----------|------|
| test | TestAgentPure | ✅ True | 生成测试提示词（不执行） |
| review | CodeReviewAgentPure | ✅ True | SoT 一致性检查 |
| doc | DocAgentPure | ✅ True | 文档生成/审核 |
| fe | FEAgent | ❌ False | 调用 fe_dev_skill → LLM |
| be | BEAgent | ❌ False | 调用 be_dev_skill → LLM |
| orch | OrchestratorAgent | ❌ False | 协调其他 Agent |

### 2.2 Registry 扩展

**文件**: `agent_platform/core/registry.py`

- ✅ `AgentMeta` 新增 `mcp_safe: bool` 字段
- ✅ `register()` 支持 `mcp_safe` 参数
- ✅ `list_agents(mcp_safe_only=True)` 过滤 MCP 安全 Agent
- ✅ `list_mcp_safe_agents()` 便捷函数
- ✅ `is_mcp_safe(name)` 检查函数

### 2.3 Agent 子系统目录结构

```
agent_platform/agents/
├── __init__.py           # 统一导出，触发注册
├── pure_logic/           # MCP 安全 Agent (mcp_safe=True)
│   ├── __init__.py
│   ├── test_agent.py     # TestAgentPure
│   ├── code_review_agent.py  # CodeReviewAgentPure
│   └── doc_agent.py      # DocAgentPure
└── llm_dependent/        # LLM 依赖 Agent (mcp_safe=False)
    └── __init__.py       # 注册 fe, be, orch（委托给 agents/agent_core）
```

### 2.4 MCP 安全 Agent 迁移

**TestAgentPure** (`agent_platform/agents/pure_logic/test_agent.py`)
- 从 `agents/agent_core/test_agent.py` 迁移
- 支持 `mode="db"` 和 `mode="backend"`
- 返回 `executed=False`（只生成提示词）
- 注册为 `mcp_safe=True`

**CodeReviewAgentPure** (`agent_platform/agents/pure_logic/code_review_agent.py`)
- 从 `agents/agent_core/code_review_agent.py` 迁移
- 支持 `action="review"` 和 `action="quick_check"`
- 集成 `sot_guard_skill` 进行规则检查
- 注册为 `mcp_safe=True`

**DocAgentPure** (`agent_platform/agents/pure_logic/doc_agent.py`)
- 从 `agents/agent_core/doc_agent.py` 迁移
- 支持 `action="generate"`, `"review"`, `"sync"`
- 使用模板生成文档
- 注册为 `mcp_safe=True`

### 2.5 LLM 依赖 Agent 注册

**文件**: `agent_platform/agents/llm_dependent/__init__.py`

- ✅ `fe` 注册为 `mcp_safe=False`（委托给 `agents.agent_core.fe_agent`）
- ✅ `be` 注册为 `mcp_safe=False`（委托给 `agents.agent_core.be_agent`）
- ✅ `orch` 注册为 `mcp_safe=False`（委托给 `agents.agent_core.orchestrator_agent`）

### 2.6 测试文件

**文件**: `agent_platform/tests/test_agents_registry.py`

- ✅ `TestAgentRegistration`: 注册与发现测试
- ✅ `TestAgentCreation`: Agent 创建测试
- ✅ `TestMcpSafeAgentInvocation`: MCP 安全 Agent 调用测试
- ✅ `TestAgentMetadata`: 元数据测试

### Phase 2 验收 Checklist

- [x] `agent_platform/core/registry.py` 新增 `mcp_safe` 支持
- [x] `agent_platform/agents/` 目录结构创建
- [x] `pure_logic/` 包含 3 个 MCP 安全 Agent
- [x] `llm_dependent/` 注册 3 个 LLM 依赖 Agent
- [x] 测试文件 `test_agents_registry.py` 创建
- [x] 迁移日志更新

### Phase 2 已知限制

1. **旧 agents/ 实现仍存在**：Phase 2 不删除旧代码，保持兼容
2. **LLM Agent 未完全迁移**：fe, be, orch 仍委托给旧实现
3. **Skills 层未迁移**：db_test_skill, sot_guard_skill 等仍在 agents/skills/

---

## Phase 3: 技能层迁移

**完成日期**: 2025-12-05

### 3.1 Skill 清单与分类

| Skill | 类型 | mcp_safe | 说明 |
|-------|------|----------|------|
| db_test_skill | 纯逻辑 | ✅ True | 生成数据库测试提示词 |
| backend_test_skill | 纯逻辑 | ✅ True | 生成 pytest 测试提示词 |
| sot_guard_skill | 纯逻辑 | ✅ True | SoT 规则校验 (~500 行) |
| fe_dev_skill | LLM 依赖 | ❌ False | 前端代码生成（调用 LLM） |
| be_dev_skill | LLM 依赖 | ❌ False | 后端代码生成（调用 LLM） |
| doc_skill | 占位 | ❌ False | NotImplementedError |
| review_skill | 占位 | ❌ False | NotImplementedError |
| refactor_skill | 占位 | ❌ False | NotImplementedError |

### 3.2 目录结构

```
agent_platform/skills/
├── __init__.py           # 统一导出，触发注册
├── registry.py           # SkillMeta 和 SkillRegistry
├── pure_logic/           # MCP 安全 Skill (mcp_safe=True)
│   ├── __init__.py       # 注册 db_test, backend_test, sot_guard
│   ├── db_test_skill.py
│   ├── backend_test_skill.py
│   └── sot_guard_skill.py
└── llm_dependent/        # LLM 依赖 Skill (mcp_safe=False)
    └── __init__.py       # 注册 fe_dev, be_dev, doc, review, refactor
```

### 3.3 Registry 设计

**文件**: `agent_platform/skills/registry.py`

- ✅ `SkillMeta` 数据类（name, func, description, version, tags, mcp_safe）
- ✅ `SkillRegistry` 单例（register, get, list_skills, invoke, is_mcp_safe）
- ✅ 便捷函数：`list_skills()`, `list_mcp_safe_skills()`, `invoke_skill()`, `is_skill_mcp_safe()`

### 3.4 纯逻辑 Skill 迁移

**db_test_skill** (`agent_platform/skills/pure_logic/db_test_skill.py`)
- 从 `agents/skills/db_test_skill.py` 迁移
- 更新导入：使用 `agent_platform.config.sot_files`
- 注册为 `mcp_safe=True`

**backend_test_skill** (`agent_platform/skills/pure_logic/backend_test_skill.py`)
- 从 `agents/skills/backend_test_skill.py` 迁移
- 支持 scope/level/timeout 参数
- 注册为 `mcp_safe=True`

**sot_guard_skill** (`agent_platform/skills/pure_logic/sot_guard_skill.py`)
- 从 `agents/skills/sot_guard_skill.py` 迁移
- 包含 SotParser、check_*_compliance 函数
- 注册为 `mcp_safe=True`

### 3.5 LLM 依赖 Skill 注册

**文件**: `agent_platform/skills/llm_dependent/__init__.py`

- ✅ `fe_dev` 注册为 `mcp_safe=False`（委托给 `agents.skills.fe_dev_skill`）
- ✅ `be_dev` 注册为 `mcp_safe=False`（委托给 `agents.skills.be_dev_skill`）
- ✅ `doc`, `review`, `refactor` 注册为占位（返回 NotImplementedError）

### 3.6 配置层增强

**文件**: `agent_platform/config/paths.py`

- ✅ 新增 `read_optional()` 函数（读取可选文件）

**文件**: `agent_platform/core/exceptions.py`

- ✅ 新增 `SkillNotFoundError` 异常
- ✅ 新增 `SkillExecutionError` 异常

### 3.7 测试文件

**文件**: `agent_platform/tests/test_skills_registry.py`

- ✅ `TestSkillRegistration`: 注册与发现测试
- ✅ `TestSkillInvocation`: Skill 调用测试
- ✅ `TestSkillMetadata`: 元数据测试
- ✅ `TestPureLogicSkills`: 纯逻辑 Skill 功能测试

### Phase 3 验收 Checklist

- [x] `agent_platform/skills/registry.py` 创建
- [x] `agent_platform/skills/` 目录结构创建
- [x] `pure_logic/` 包含 3 个 MCP 安全 Skill
- [x] `llm_dependent/` 注册 5 个 LLM 依赖/占位 Skill
- [x] `agent_platform/config/paths.py` 新增 `read_optional()`
- [x] `agent_platform/core/exceptions.py` 新增 Skill 异常
- [x] 测试文件 `test_skills_registry.py` 创建
- [x] 迁移日志更新

### Phase 3 已知限制

1. **旧 agents/skills/ 实现仍存在**：Phase 3 不删除旧代码，保持兼容
2. **LLM Skill 未完全迁移**：fe_dev, be_dev 仍委托给旧实现
3. **占位 Skill 未实现**：doc, review, refactor 返回 NotImplementedError

---

## Phase 4: MCP 工具重构

**完成日期**: 2025-12-05

### 4.1 重构目标

将 MCP Server 的 Agent/Skill 工具迁移到使用新的 `agent_platform` registry，并强制执行 `mcp_safe` 过滤。

### 4.2 MCP 工具清单

| 工具 | 说明 | mcp_safe 过滤 |
|------|------|---------------|
| `ap_list_agents` | 列出 Agent | ✅ 默认只返回 mcp_safe=True |
| `ap_run_agent` | 执行 Agent | ✅ 强制只允许 mcp_safe=True |
| `ap_list_skills` | 列出 Skill | ✅ 默认只返回 mcp_safe=True |
| `ap_run_skill` | 执行 Skill | ✅ 强制只允许 mcp_safe=True |

### 4.3 重构变更

**文件**: `agent_platform/mcp/server.py`

#### ap_list_agents 重构
- 从 `agents.agents_config._AGENT_REGISTRY` → `agent_platform.agents.list_agents()`
- 新增 `include_all` 参数（默认 False，只返回 MCP-safe Agent）
- 返回增强元数据：version, mcp_safe, tags

#### ap_run_agent 重构
- 从 `agents.agents_config.create_agent()` → `agent_platform.agents.create_agent()`
- 强制 `mcp_safe` 检查：非安全 Agent 返回 `MCP_UNSAFE_AGENT` 错误
- enum 限制为 `["test", "review", "doc"]`

#### 新增 ap_list_skills
- 使用 `agent_platform.skills.list_skills()`
- 支持 `include_all` 参数
- 默认只返回 MCP-safe Skill

#### 新增 ap_run_skill
- 使用 `agent_platform.skills.invoke_skill()`
- 强制 `mcp_safe` 检查
- enum 限制为 `["db_test", "backend_test", "sot_guard"]`

### 4.4 错误类型

| error_kind | 说明 |
|------------|------|
| `AGENT_NOT_FOUND` | Agent 不存在 |
| `MCP_UNSAFE_AGENT` | Agent 不是 MCP-safe（需要 LLM） |
| `AGENT_CREATION_ERROR` | Agent 创建失败 |
| `AGENT_EXECUTION_ERROR` | Agent 执行失败 |
| `SKILL_NOT_FOUND` | Skill 不存在 |
| `MCP_UNSAFE_SKILL` | Skill 不是 MCP-safe |
| `SKILL_EXECUTION_ERROR` | Skill 执行失败 |

### 4.5 测试文件

**文件**: `agent_platform/tests/test_mcp_server_agents.py`

- ✅ `TestMCPListAgents`: 列表过滤测试
- ✅ `TestMCPRunAgent`: 执行与 mcp_safe 测试
- ✅ `TestMCPListSkills`: Skill 列表测试
- ✅ `TestMCPRunSkill`: Skill 执行测试
- ✅ `TestMCPToolRegistry`: 工具注册测试
- ✅ `TestMCPHandleRequest`: 请求处理测试

### Phase 4 验收 Checklist

- [x] `ap_list_agents` 使用新 registry
- [x] `ap_run_agent` 强制 mcp_safe 过滤
- [x] `ap_list_skills` 新增
- [x] `ap_run_skill` 新增
- [x] 测试文件创建
- [x] 迁移日志更新

### Phase 4 已知限制

1. **旧 agents/ 实现仍存在**：Phase 4 不删除旧代码
2. **MCP 工具数量增加**：从 7 个增加到 9 个
3. **enum 硬编码**：MCP-safe Agent/Skill 列表硬编码在 schema 中

---

## 健康检查

### 检查命令

```bash
# Phase 0 健康检查
python -c "import agents; print('Shadow OK')"
AGENT_PLATFORM_LEGACY=1 python -c "from agents import BASE_PATH; print('Legacy OK:', BASE_PATH)"

# Phase 1 健康检查
python -c "from agent_platform.config import SOT_FILES; print('Config OK:', len(SOT_FILES))"
python -c "from agent_platform.mcp.server import _registry; print('MCP OK:', len(_registry.tools))"

# Phase 2 健康检查
python -c "from agent_platform.agents import list_agents, list_mcp_safe_agents; print('All:', [a.name for a in list_agents()]); print('MCP Safe:', [a.name for a in list_mcp_safe_agents()])"
python -c "from agent_platform.agents import is_agent_mcp_safe; print('test:', is_agent_mcp_safe('test')); print('fe:', is_agent_mcp_safe('fe'))"

# Phase 3 健康检查
python -c "from agent_platform.skills import list_skills, list_mcp_safe_skills; print('All:', [s.name for s in list_skills()]); print('MCP Safe:', [s.name for s in list_mcp_safe_skills()])"
python -c "from agent_platform.skills import is_skill_mcp_safe; print('db_test:', is_skill_mcp_safe('db_test')); print('fe_dev:', is_skill_mcp_safe('fe_dev'))"
python -c "from agent_platform.skills import invoke_skill; r = invoke_skill('sot_guard', changes={}); print('sot_guard:', r['passed'])"

# Phase 4 健康检查
python -c "from agent_platform.mcp.server import list_agents; r = list_agents(); print('MCP Agents:', [a['name'] for a in r['agents']])"
python -c "from agent_platform.mcp.server import list_skills; r = list_skills(); print('MCP Skills:', [s['name'] for s in r['skills']])"
python -c "from agent_platform.mcp.server import run_agent; r = run_agent('review', {'action': 'review', 'changes': {}}); print('run_agent:', r['success'])"
python -c "from agent_platform.mcp.server import run_skill; r = run_skill('sot_guard', {'changes': {}}); print('run_skill:', r['success'])"
python -c "from agent_platform.mcp.server import run_agent; r = run_agent('fe', {}); print('unsafe blocked:', r['error_kind'])"

# 全量测试
pytest agent_platform/tests/ -v --tb=short
```

### 预期结果

| 检查项 | 预期结果 |
|--------|----------|
| Shadow mode import | `Shadow OK` (带 DeprecationWarning) |
| Legacy mode | `Legacy OK: <path>` |
| Config import | `Config OK: 28` (SOT_FILES 数量) |
| MCP server | `MCP OK: 7` (工具数量) |
| All agents | `['test', 'review', 'doc', 'fe', 'be', 'orch']` |
| MCP safe agents | `['test', 'review', 'doc']` |
| is_agent_mcp_safe('test') | `True` |
| is_agent_mcp_safe('fe') | `False` |
| All skills | `['db_test', 'backend_test', 'sot_guard', 'fe_dev', 'be_dev', 'doc', 'review', 'refactor']` |
| MCP safe skills | `['db_test', 'backend_test', 'sot_guard']` |
| is_skill_mcp_safe('db_test') | `True` |
| is_skill_mcp_safe('fe_dev') | `False` |
| sot_guard invoke | `True` (passed) |
| MCP list_agents | `['test', 'review', 'doc']` (MCP-safe only) |
| MCP list_skills | `['db_test', 'backend_test', 'sot_guard']` |
| MCP run_agent('review') | `True` (success) |
| MCP run_skill('sot_guard') | `True` (success) |
| MCP run_agent('fe') blocked | `MCP_UNSAFE_AGENT` |

---

## Phase 5: 观察期 + 最终清理

**观察期时间窗口**: 2025-12-05 ~ 2025-12-12 (7 天)

**状态**: 🔄 观察期进行中

### 5.1 观察期基线

| 项目 | 值 | 说明 |
|------|-----|------|
| 观察期开始 | 2025-12-05 | Phase 4 完成日 |
| 观察期结束 | 2025-12-12 | 7 天后 |
| MCP 工具数量 | 9 | Phase 4 后稳定 |
| MCP-safe Agent | 3 | test, review, doc |
| MCP-safe Skill | 3 | db_test, backend_test, sot_guard |
| 待删除文件数 | ~40 | agents/ 目录 |

### 5.2 Phase 5 - 健康检查命令清单

以下命令建议每天或每次大改后执行，可直接复制到终端：

```bash
# ============================================================
# Phase 5 健康检查命令 - 每日执行清单
# 项目: AI_ad_spend02
# 执行路径: D:\git\1108\AI_ad_spend02
# ============================================================

# 1. MCP Server 基础检查
python -c "from agent_platform.mcp.server import _registry; print('MCP Tools:', len(_registry.tools), '个')"

# 2. Agent 列表检查 (应返回 test, review, doc)
python -c "from agent_platform.mcp.server import list_agents; r = list_agents(); print('MCP Agents:', [a['name'] for a in r['agents']])"

# 3. Skill 列表检查 (应返回 db_test, backend_test, sot_guard)
python -c "from agent_platform.mcp.server import list_skills; r = list_skills(); print('MCP Skills:', [s['name'] for s in r['skills']])"

# 4. ap_run_agent 验证 - test
python -c "from agent_platform.mcp.server import run_agent; r = run_agent('test', {'mode': 'db'}); print('test Agent:', 'success' if r['success'] else 'FAILED', r.get('agent_result', {}).get('executed', 'N/A'))"

# 5. ap_run_agent 验证 - review
python -c "from agent_platform.mcp.server import run_agent; r = run_agent('review', {'action': 'review', 'changes': {}}); print('review Agent:', 'success' if r['success'] else 'FAILED')"

# 6. ap_run_agent 验证 - doc
python -c "from agent_platform.mcp.server import run_agent; r = run_agent('doc', {'action': 'generate', 'doc_type': 'spec', 'target': 'test.md', 'context': 'test'}); print('doc Agent:', 'success' if r['success'] else 'FAILED')"

# 7. ap_run_skill 验证 - sot_guard
python -c "from agent_platform.mcp.server import run_skill; r = run_skill('sot_guard', {'changes': {}}); print('sot_guard Skill:', 'passed' if r['skill_result']['passed'] else 'FAILED')"

# 8. MCP-unsafe Agent 拦截验证 (应返回 MCP_UNSAFE_AGENT)
python -c "from agent_platform.mcp.server import run_agent; r = run_agent('fe', {}); print('fe Agent blocked:', r.get('error_kind', 'NOT_BLOCKED'))"

# 9. MCP-unsafe Skill 拦截验证 (应返回 MCP_UNSAFE_SKILL)
python -c "from agent_platform.mcp.server import run_skill; r = run_skill('fe_dev', {}); print('fe_dev Skill blocked:', r.get('error_kind', 'NOT_BLOCKED'))"

# 10. 全量测试
pytest agent_platform/tests/ -v --tb=short

# 11. 检查旧路径导入 (应无输出)
findstr /s /i "from agents import" *.py 2>nul | findstr /v "agents\\"
# Linux/Mac:
# grep -r "from agents import" --include="*.py" . | grep -v "^./agents/"

# 12. 检查 Legacy 模式使用 (应无匹配)
findstr /s "AGENT_PLATFORM_LEGACY" *.py *.md 2>nul | findstr /v "MIGRATION"
```

### 5.3 Phase 5 - 待更新命令列表

扫描结果：**.claude/commands/ 已全部迁移至新 MCP 接口**

| 文件 | 状态 | 迁移说明 |
|------|------|----------|
| `.claude/commands/doc-agent.md` | ✅ 无需更新 | 使用 ai-ad-doc-* Skill |
| `.claude/commands/mcp-orch.md` | ✅ 无需更新 | 使用 ap_* MCP 工具 |
| `.claude/commands/gen-backend-mcp.md` | ✅ 无需更新 | 使用 ap_* MCP 工具 |
| `.claude/commands/gen-frontend-mcp.md` | ✅ 无需更新 | 使用 ap_* MCP 工具 |

**扫描方法**:
```bash
# 检查 .claude/commands/ 中是否有旧 agents/ 路径引用
findstr /s "agents.cli" .claude\commands\*.md
findstr /s "from agents import" .claude\commands\*.md
# 结果: 无匹配
```

### 5.4 健康检查记录

| 日期 | 执行人 | 结果 | 问题 | 备注 |
|------|--------|------|------|------|
| 2025-12-05 | Claude | ✅ 通过 | 10 个测试失败 | 已修复，见 5.6 节 |
| | | | | |
| | | | | |

### 5.5 观察期内发现的问题

| 编号 | 级别 | 描述 | 状态 | 解决日期 |
|------|------|------|------|----------|
| OBS-001 | P1 | test_mcp_server.py 使用旧 mock 路径 | ✅ 已修复 | 2025-12-05 |
| OBS-002 | P1 | 测试使用 MCP-unsafe Agent (be/fe) | ✅ 已修复 | 2025-12-05 |

### 5.6 Test Fix Log (2025-12-05)

**问题背景**: Phase 4 完成后，原有 10 个测试用例失败。分析发现主要原因是：
1. 测试代码使用旧的 `agents.agents_config._AGENT_REGISTRY` mock 路径
2. 测试尝试运行 MCP-unsafe Agent (be, fe)，但 Phase 4 引入的 `mcp_safe` 检查阻止了这些调用

**修复方案**: 更新测试代码以对齐 Phase 4 的新行为，不修改业务逻辑

#### 修复的测试用例 (4 处)

| 文件 | 测试方法 | 问题 | 修复 |
|------|----------|------|------|
| `test_mcp_server.py:186-199` | `test_run_existing_agent_success` | 使用 `be` Agent | 改为使用 MCP-safe 的 `review` Agent |
| `test_mcp_server.py:215-228` | `test_run_agent_handles_llm_guard_error` | 测试 LLM Guard 错误 | 重命名为 `test_run_mcp_unsafe_agent_blocked`，测试 `MCP_UNSAFE_AGENT` 错误 |
| `test_mcp_server.py:230-245` | `test_run_agent_with_context` | 使用 `fe` Agent | 改为使用 MCP-safe 的 `doc` Agent |
| `test_mcp_server.py:247-264` | `test_run_agent_list_available` | 使用旧 registry mock | 移除 mock，直接使用新 registry 并验证 MCP-safe 过滤 |

#### 验证的测试文件 (无需修改)

| 文件 | 测试数 | 状态 | 说明 |
|------|--------|------|------|
| `test_mcp_server_agents.py` | 20 | ✅ 通过 | 已正确使用 MCP-safe 行为 |
| `test_skills_registry.py` | 15 | ✅ 通过 | 已正确测试 Skill 注册和调用 |

#### 回归测试结果

```
pytest agent_platform/tests/test_mcp_server.py \
       agent_platform/tests/test_mcp_server_agents.py \
       agent_platform/tests/test_skills_registry.py -v
```

**结果**: 全部通过 (exit code 0)
- `test_mcp_server.py`: 18 tests ✅
- `test_mcp_server_agents.py`: 20 tests ✅
- `test_skills_registry.py`: 15 tests ✅
- **总计**: 53 tests passed

### Phase 5 验收 Checklist

观察期结束后（2025-12-12），需完成以下验收：

**功能验收**
- [ ] 全量 pytest 通过
- [ ] ap_list_agents 返回 ["test", "review", "doc"]
- [ ] ap_run_agent(test/review/doc) 全部成功
- [ ] ap_list_skills 返回 ["db_test", "backend_test", "sot_guard"]
- [ ] ap_run_skill(sot_guard) 成功

**安全验收**
- [ ] mcp_safe 拦截生效 (fe/be/orch 被阻止)
- [ ] 无循环依赖

**生态验收**
- [ ] .claude/commands/ 全部使用新接口
- [ ] 无 Legacy 模式使用记录
- [ ] 健康检查记录 >= 3 次

**删除验收（观察期结束后执行）**
- [ ] 执行 `git rm -r agents/`
- [ ] 删除后全量测试通过
- [ ] MCP Server 正常启动

详见 [AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md](./AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md) Phase 5 章节

---

## Git 建议命令

```bash
# 创建迁移分支（如果尚未创建）
git checkout -b refactor/agent-platform-merge-v1.2

# 提交 Phase 0 + Phase 1 变更
git add agents/__init__.py agents/cli.py agents/cli_legacy.py agents/_DEPRECATED.md
git add agent_platform/config/
git add agent_platform/mcp/server.py
git add docs/dev/AGENT_PLATFORM_MIGRATION_LOG.md
git commit -m "refactor(agents): Phase 0+1 完成 - 影子模式 + 配置层迁移

Phase 0:
- agents/__init__.py 改为影子模式转调壳
- agents/cli.py 改为转调壳
- 创建 agents/_DEPRECATED.md 废弃说明

Phase 1:
- 创建 agent_platform/config/ 配置层
- paths.py: BASE_PATH 带 fallback 和验证
- sot_files.py: SOT_FILES 映射 (28 文件)
- constants.py: is_legacy_mode(), is_mcp_mode()
- 更新 mcp/server.py SOT_FILES 导入

迁移文档: docs/dev/AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md
观察期: 2025-12-04 ~ 2025-12-11

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 修改记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2025-12-04 | v1.0 | 初版：Phase 0 + Phase 1 完成记录 |
| 2025-12-04 | v2.0 | Phase 2 完成：Agent 层迁移，mcp_safe 机制 |
| 2025-12-05 | v3.0 | Phase 3 完成：技能层迁移，SkillRegistry，8 个 Skill 注册 |
| 2025-12-05 | v4.0 | Phase 4 完成：MCP 工具重构，9 个 MCP 工具，mcp_safe 强制过滤 |
| 2025-12-05 | v5.0 | Phase 5 开始：观察期设计、健康检查命令、待更新命令扫描、删除计划 |
| 2025-12-05 | v5.1 | Test Fix：修复 4 个测试用例，回归测试通过 (53 tests) |
