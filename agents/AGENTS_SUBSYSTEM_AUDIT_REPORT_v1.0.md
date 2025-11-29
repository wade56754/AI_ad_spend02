# Agents 子系统完整审计报告

> **版本**: v1.0
> **审计日期**: 2025-11-29
> **审计员**: Claude Code Agent
> **基准**: Agent Layer Freeze v1.0, MASTER.md v3.5, SoT Freeze v2.6

---

## Executive Summary

| 维度 | 健康分数 | P0 | P1 | P2 | P3 |
|------|----------|-----|-----|-----|-----|
| A. 目录结构 | 95/100 | 0 | 1 | 1 | 0 |
| B. 依赖关系 | 90/100 | 0 | 2 | 2 | 0 |
| C. 配置/SoT一致性 | 95/100 | 0 | 1 | 2 | 0 |
| D. 代码质量 | 85/100 | 0 | 3 | 4 | 0 |
| E. API/CLI接口 | 95/100 | 0 | 1 | 1 | 0 |
| F. 测试与调试 | 80/100 | 0 | 2 | 3 | 0 |
| **总计** | **90/100** | **0** | **10** | **13** | **0** |

**结论**: 子系统处于良好状态，无 P0 阻塞问题，可进入下一迭代。

---

## A. 目录结构审计 (95/100)

### 当前结构

```
agents/
├── agents_config.py          # 核心配置：Agent 注册、SoT 路径、工厂函数
├── cli.py                    # CLI 入口
├── server.py                 # FastAPI HTTP 服务
├── agent_core/               # Agent 实现层
│   ├── __init__.py          # (空)
│   ├── fe_agent.py          # FrontendAgent
│   ├── be_agent.py          # BackendAgent
│   ├── test_agent.py        # TestAgent
│   ├── orchestrator_agent.py # OrchestratorAgent
│   ├── doc_agent.py         # DocAgent
│   └── code_review_agent.py # CodeReviewAgent
├── skills/                   # Skill 实现层
│   ├── __init__.py          # 导出 fe/be/db_test skill
│   ├── fe_dev_skill.py      # 前端代码生成
│   ├── be_dev_skill.py      # 后端代码生成
│   ├── db_test_skill.py     # DB 测试 prompt 生成
│   ├── sot_guard_skill.py   # SoT 合规检查
│   ├── doc_skill.py         # (空桩)
│   ├── review_skill.py      # (空桩)
│   └── refactor_skill.py    # (空桩)
└── tools/                    # 工具层
    ├── __init__.py          # 导出 fs/supabase 工具
    ├── types.py             # AgentResponse/SkillResult 类型
    ├── validation.py        # 参数校验
    ├── fs_tool.py           # 文件读写（带路径安全检查）
    ├── supabase_tool.py     # Supabase MCP 占位
    └── claude_code_adapter.py # Claude CLI 适配器
```

### 发现的问题

| 问题ID | 级别 | 描述 | 位置 |
|--------|------|------|------|
| A-P1-01 | P1 | 空桩文件未清理 | `skills/doc_skill.py`, `review_skill.py`, `refactor_skill.py` |
| A-P2-01 | P2 | `agent_core/__init__.py` 为空，未导出 Agent 类 | `agent_core/__init__.py` |

### 修复建议

1. **A-P1-01**: 删除或实现空桩文件
   - 如果不使用：删除 `doc_skill.py`, `review_skill.py`, `refactor_skill.py`
   - 如果保留：添加 `raise NotImplementedError("Stub")` 明确标记

2. **A-P2-01**: 更新 `agent_core/__init__.py` 导出 Agent 类便于外部导入

---

## B. 依赖关系审计 (90/100)

### 架构层级

```
┌─────────────────────────────────────────────────────────┐
│  CLI / HTTP Server (cli.py, server.py)                  │
├─────────────────────────────────────────────────────────┤
│  Agent Layer (agent_core/)                              │
│  - FEAgent, BEAgent, TestAgent, OrchestratorAgent       │
│  - DocAgent, CodeReviewAgent                            │
├─────────────────────────────────────────────────────────┤
│  Skill Layer (skills/)                                  │
│  - fe_dev_skill, be_dev_skill, db_test_skill            │
│  - sot_guard_skill                                      │
├─────────────────────────────────────────────────────────┤
│  Tool Layer (tools/)                                    │
│  - fs_tool, supabase_tool, claude_code_adapter          │
│  - types, validation                                    │
├─────────────────────────────────────────────────────────┤
│  Config (agents_config.py)                              │
└─────────────────────────────────────────────────────────┘
```

### 依赖关系矩阵

| 模块 | 依赖 agents_config | 依赖 tools | 依赖 skills | 循环风险 |
|------|-------------------|-----------|-------------|----------|
| cli.py | ✓ | - | - | 低 |
| server.py | ✓ | - | - | 低 |
| FEAgent | - | types, validation | fe_dev_skill | 低 |
| BEAgent | - | types, validation | be_dev_skill | 低 |
| TestAgent | - | types | db_test_skill | 低 |
| DocAgent | ✓ (SOT_FILES) | - | - | **已修复** |
| CodeReviewAgent | - | - | sot_guard_skill | 低 |
| OrchestratorAgent | ✓ (create_agent) | types | - | 低 |
| fe_dev_skill | ✓ (SOT_FILES等) | fs_tool, claude_code_adapter | - | 低 |
| be_dev_skill | ✓ (SOT_FILES等) | fs_tool, claude_code_adapter | - | 低 |
| sot_guard_skill | ✓ (SOT_FILES等) | - | - | 低 |

### 发现的问题

| 问题ID | 级别 | 描述 | 位置 |
|--------|------|------|------|
| B-P1-01 | P1 | fe_dev_skill 和 be_dev_skill 代码重复率高（~80%） | `skills/fe_dev_skill.py:22-81`, `skills/be_dev_skill.py:22-81` |
| B-P1-02 | P1 | `skills/__init__.py` 未导出 `sot_guard_skill` | `skills/__init__.py` |
| B-P2-01 | P2 | `_get_client()` 函数在 fe/be_dev_skill 中重复定义 | 两个 skill 文件 |
| B-P2-02 | P2 | `_extract_response_text()` 函数在 fe/be_dev_skill 中重复定义 | 两个 skill 文件 |

### 修复建议

1. **B-P1-01/B-P2-01/B-P2-02**: 提取共用代码到 `tools/llm_client.py`
   ```python
   # tools/llm_client.py
   def get_llm_client() -> Any: ...
   def extract_response_text(resp: Any) -> str: ...
   ```

2. **B-P1-02**: 更新 `skills/__init__.py`
   ```python
   from .sot_guard_skill import validate_against_sot, guard_check
   ```

---

## C. 配置/SoT 一致性审计 (95/100)

### SOT_FILES 配置检查

| SoT Key | 配置路径 | 是否存在 | 版本对齐 |
|---------|---------|----------|----------|
| MASTER | docs/1.overview/MASTER.md | - | v3.5 |
| STATE_MACHINE | docs/2.sot/STATE_MACHINE.md | - | v2.6 |
| DATA_SCHEMA | docs/2.sot/DATA_SCHEMA.md | - | v5.2 |
| BUSINESS_RULES | docs/2.sot/BUSINESS_RULES.md | - | v3.1 |
| API_SOT | docs/2.sot/API_SOT.md | - | v9.0 |
| ERROR_CODES | docs/2.sot/ERROR_CODES_SOT.md | - | v2.1 |
| LEDGER_SOT | docs/2.sot/LEDGER_SOT.md | - | v1.1 |
| AUTH_SPEC | docs/2.sot/AUTH_SPEC.md | - | v2.0 |

### 发现的问题

| 问题ID | 级别 | 描述 | 位置 |
|--------|------|------|------|
| C-P1-01 | P1 | `sot_guard_skill.py` 硬编码默认值可能与 SoT 不同步 | `sot_guard_skill.py:52-122` |
| C-P2-01 | P2 | `DocAgent._get_sot_versions()` 返回硬编码版本号 | `doc_agent.py:508-520` |
| C-P2-02 | P2 | `CRITICAL_SOT_FILES` 缺少 `AUTH_SPEC` | `agents_config.py:124-127` |

### 修复建议

1. **C-P1-01**: SoT 文档变更后需调用 `SotParser.reload()` 刷新缓存

2. **C-P2-01**: 从 YAML frontmatter 动态读取版本号
   ```python
   def _get_sot_versions(self) -> Dict[str, str]:
       # 从 SoT 文档的 frontmatter 解析版本
       ...
   ```

3. **C-P2-02**: 添加 AUTH_SPEC 到 CRITICAL_SOT_FILES

---

## D. 代码质量审计 (85/100)

### 错误处理检查

| 模块 | 异常捕获 | 日志记录 | 错误传播 | 评分 |
|------|---------|---------|---------|------|
| fe_dev_skill | ✓ | ✓ | ✓ | A |
| be_dev_skill | ✓ | ✓ | ✓ | A |
| db_test_skill | ✓ | ✓ | ✓ | A |
| sot_guard_skill | ✓ | ✓ | ✓ | A |
| claude_code_adapter | ✓ | ✓ | ✓ | A |
| fs_tool | ✓ | ✓ | ✓ | A |
| supabase_tool | ✓ | 部分 | N/A | B |
| doc_agent | ✓ | ✓ | ✓ | A |
| code_review_agent | ✓ | ✓ | ✓ | A |
| orchestrator_agent | ✓ | ✓ | ✓ | A |

### 发现的问题

| 问题ID | 级别 | 描述 | 位置 |
|--------|------|------|------|
| D-P1-01 | P1 | `supabase_tool.py` 所有方法都抛出 `NotImplementedError` | `supabase_tool.py:35,41,47` |
| D-P1-02 | P1 | `TestAgent` 不实际执行测试，可能误导调用方 | `test_agent.py:67-78` |
| D-P1-03 | P1 | `OrchestratorAgent` 文件写入失败不中断流程 | `orchestrator_agent.py:402-410` |
| D-P2-01 | P2 | LLM 超时默认 300s 可能过长 | `claude_code_adapter.py:26` |
| D-P2-02 | P2 | 缺少 LLM 调用成本/token 统计 | `fe_dev_skill.py`, `be_dev_skill.py` |
| D-P2-03 | P2 | `_looks_like_state()` 函数过于简单，可能误判 | `sot_guard_skill.py:726-734` |
| D-P2-04 | P2 | JSON 解析失败时 `raw` 字段只保留前 500 字符 | `fe_dev_skill.py:246` |

### 修复建议

1. **D-P1-01**: 实现 Supabase MCP 集成或添加清晰的"未配置"提示

2. **D-P1-02**: 在响应中添加更明确的警告
   ```python
   "warning": "TESTS NOT EXECUTED - Manual Supabase MCP execution required"
   ```

3. **D-P1-03**: 添加写入失败计数和阈值检查
   ```python
   if failed_writes > 0:
       notes.append(f"Warning: {failed_writes} file writes failed")
   ```

---

## E. API/CLI 接口审计 (95/100)

### CLI 接口 (`cli.py`)

| 命令 | 参数 | 状态 | 说明 |
|------|------|------|------|
| `status` | - | ✓ | 检查 LLM 服务状态 |
| `run <agent>` | `--action`, `--files`, `--base-path` | ✓ | 运行指定 Agent |
| `run orch` | `--action`, `--task`, `--auto-write` | ✓ | 运行 Orchestrator |

### HTTP 接口 (`server.py`)

| 端点 | 方法 | 状态 | 说明 |
|------|------|------|------|
| `/health` | GET | ✓ | 健康检查 |
| `/agents` | GET | ✓ | 列出所有 Agent |
| `/agents/{key}/handle` | POST | ✓ | 调用 Agent |

### 发现的问题

| 问题ID | 级别 | 描述 | 位置 |
|--------|------|------|------|
| E-P1-01 | P1 | HTTP 接口缺少请求速率限制 | `server.py` |
| E-P2-01 | P2 | CLI 帮助文档未包含 `doc` 和 `review` Agent 示例 | `cli.py:150-166` |

### 修复建议

1. **E-P1-01**: 添加 FastAPI 中间件限流
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   ```

2. **E-P2-01**: 更新 CLI 帮助文档

---

## F. 测试与调试审计 (80/100)

### 可测试性检查

| 组件 | 单元测试 | 集成测试 | Mock 支持 |
|------|---------|---------|----------|
| FEAgent | 需要 | - | ✓ (可 mock LLM) |
| BEAgent | 需要 | - | ✓ (可 mock LLM) |
| TestAgent | 需要 | - | ✓ |
| OrchestratorAgent | 需要 | - | ✓ (可 mock 子 Agent) |
| DocAgent | 需要 | - | ✓ |
| CodeReviewAgent | 需要 | - | ✓ |
| sot_guard_skill | 需要 | - | ✓ |

### 发现的问题

| 问题ID | 级别 | 描述 | 位置 |
|--------|------|------|------|
| F-P1-01 | P1 | 无单元测试覆盖 | `tests/` 目录 |
| F-P1-02 | P1 | 调试日志级别不一致 | 多个文件 |
| F-P2-01 | P2 | 缺少性能基准测试 | - |
| F-P2-02 | P2 | 无 LLM 调用统计接口 | - |
| F-P2-03 | P2 | `SotParser.reload()` 缺少测试验证 | `sot_guard_skill.py:159-174` |

### 修复建议

1. **F-P1-01**: 创建测试文件
   ```
   tests/
   ├── test_fe_agent.py
   ├── test_be_agent.py
   ├── test_orchestrator_agent.py
   ├── test_sot_guard_skill.py
   └── conftest.py  # pytest fixtures
   ```

2. **F-P1-02**: 统一使用 `logger.debug()` 进行详细日志，`logger.info()` 进行关键步骤日志

---

## 验证步骤

### 语法验证

```bash
cd D:\git\1108\AI_ad_spend02
python -m py_compile agents/agents_config.py
python -m py_compile agents/cli.py
python -m py_compile agents/server.py
python -m py_compile agents/agent_core/orchestrator_agent.py
python -m py_compile agents/skills/sot_guard_skill.py
```

### 导入验证

```bash
python -c "from agents.agents_config import create_agent, list_agents; print(list_agents().keys())"
python -c "from agents.skills.sot_guard_skill import SotParser; p = SotParser.get_instance(); print(p.daily_report_states)"
```

### 功能验证

```bash
# CLI 状态检查
python -m agents.cli status

# Agent 列表
python -c "from agents.agents_config import list_agents; import json; print(json.dumps(list_agents(), indent=2))"
```

---

## 优先级修复计划

### Phase 1: P1 问题修复（建议 1-2 天）

1. [ ] B-P1-01: 提取 fe/be_dev_skill 共用代码
2. [ ] B-P1-02: 更新 skills/__init__.py 导出
3. [ ] D-P1-01: 实现 SupabaseTool 或添加清晰提示
4. [ ] E-P1-01: 添加 HTTP 速率限制
5. [ ] F-P1-01: 创建核心单元测试

### Phase 2: P2 问题修复（建议 2-3 天）

1. [ ] A-P1-01: 清理空桩文件
2. [ ] A-P2-01: 更新 agent_core/__init__.py
3. [ ] C-P2-02: 添加 AUTH_SPEC 到 CRITICAL_SOT_FILES
4. [ ] D-P2-01: 调整 LLM 超时配置
5. [ ] E-P2-01: 更新 CLI 帮助文档

---

## 附录

### A. 文件清单

| 文件路径 | 行数 | 主要职责 |
|---------|------|---------|
| agents_config.py | 467 | 核心配置、Agent 注册 |
| cli.py | 200 | CLI 入口 |
| server.py | 188 | HTTP 服务 |
| agent_core/fe_agent.py | 76 | 前端 Agent |
| agent_core/be_agent.py | 76 | 后端 Agent |
| agent_core/test_agent.py | 84 | 测试 Agent |
| agent_core/orchestrator_agent.py | 439 | 编排 Agent |
| agent_core/doc_agent.py | 692 | 文档 Agent |
| agent_core/code_review_agent.py | 174 | 代码审核 Agent |
| skills/fe_dev_skill.py | 269 | 前端代码生成 |
| skills/be_dev_skill.py | 283 | 后端代码生成 |
| skills/db_test_skill.py | 99 | DB 测试 prompt |
| skills/sot_guard_skill.py | 771 | SoT 合规检查 |
| tools/types.py | 162 | 类型定义 |
| tools/validation.py | 49 | 参数校验 |
| tools/fs_tool.py | 80 | 文件操作 |
| tools/supabase_tool.py | 48 | Supabase 占位 |
| tools/claude_code_adapter.py | 379 | Claude CLI 适配 |

**总计**: 24 个 Python 文件，约 4,500 行代码

### B. 6 个已注册 Agent

| Key | 类名 | 描述 |
|-----|------|------|
| fe | FEAgent | 前端开发 Agent |
| be | BEAgent | 后端开发 Agent |
| test | TestAgent | 数据库测试 Agent |
| orch | OrchestratorAgent | 编排 Agent |
| doc | DocAgent | 文档 Agent |
| review | CodeReviewAgent | 代码审核 Agent |

---

**审计完成**: 2025-11-29
**下次审计建议**: Phase 1 完成后
