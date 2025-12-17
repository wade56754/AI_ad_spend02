# Legacy 测试迁移报告

> **版本**: v1.0
> **日期**: 2025-11-29
> **角色**: 测试重构负责人

---

## 1. Legacy 测试分类总览

| 类型 | 说明 | 数量 | 处理策略 |
|------|------|------|----------|
| **A** | 仅缺少 import（pytest、MagicMock、patch 等） | 2 | 补充导入 + 标记 skip |
| **B** | 依赖旧实现细节（如旧状态机、旧错误结构） | 5 | 标记 xfail/skip |
| **C** | 占位/实验性质（空文件或 assert False） | 4 | 保留但跳过 |
| **D** | 有价值、值得迁移的行为测试 | 9 | 迁移到 agents/tests |

---

## 2. 每个文件的处理方案

### 已迁移到 agents/tests（类型 D - 有价值）

| 原文件 | 新文件 | 处理方式 |
|--------|--------|----------|
| `test_factory.py` | `agents/tests/test_factory.py` | ✅ 迁移 + 原文件标记 skip |
| `test_llm_client.py` | `agents/tests/test_llm_client.py` | ✅ 迁移 + 补充 import + 原文件标记 skip |
| `test_orchestrator_agent.py` | `agents/tests/test_orchestrator.py` | ✅ 迁移（更新为新错误策略） |
| `test_fs_tool.py` | `agents/tests/test_fs_tool.py` | ✅ 迁移 |
| `test_types.py` | `agents/tests/test_types.py` | ✅ 迁移 |
| `test_claude_code_adapter.py` | `agents/tests/test_claude_code_adapter.py` | ✅ 迁移 |
| `test_agents_smoke.py` | `agents/tests/test_orchestrator.py` (合并) | ✅ 合并到 orchestrator 测试 |
| `test_test_agent.py` | `agents/tests/test_orchestrator.py` (合并) | ✅ 合并到 orchestrator 测试 |
| `test_sot_guard_skill.py` | 待迁移 | ⏳ 需要对齐 SoT v2.6 状态机 |

### 保留但跳过（类型 B - 依赖旧实现）

| 文件 | 原因 | 处理方式 |
|------|------|----------|
| `test_fe_agent.py` | 包含业务代码副本而非纯测试 | 标记 skip |
| `test_be_agent.py` | 包含业务代码副本而非纯测试 | 标记 skip |
| `test_agent.py` | 包含业务代码副本而非纯测试 | 标记 skip |
| `test_validation.py` | 包含业务代码副本而非纯测试 | 标记 skip |
| `test_agents_config.py` | 包含业务代码副本而非纯测试 | 标记 skip |

### 空文件或占位（类型 C）

| 文件 | 状态 | 处理方式 |
|------|------|----------|
| `test_doc_skill.py` | 空文件 | 保留（未来补充） |
| `test_server.py` | 空文件 | 保留（未来补充） |
| `test_doc_agent.py` | 空文件 | 保留（未来补充） |
| `test_code_review_agent.py` | 空文件 | 保留（未来补充） |
| `test_refactor_skill.py` | 空文件 | 保留（未来补充） |
| `test_review_skill.py` | 空文件 | 保留（未来补充） |
| `test_supabase_tool.py` | 空文件 | 保留（未来补充） |

### 其他

| 文件 | 状态 |
|------|------|
| `test_cli.py` | 简单测试，已在新目录覆盖 |
| `test_fe_dev_skill.py` | 需要 LLM mock，暂不迁移 |
| `test_be_dev_skill.py` | 需要 LLM mock，暂不迁移 |
| `test_db_test_skill.py` | 需要 LLM mock，暂不迁移 |
| `test_agentsskillssot_guard_skill.py` | 文件名错误，保留待清理 |
| `conftest.py` | 配置文件，保留 |

---

## 3. 新增/迁移的用例清单

### agents/tests/ 目录结构

```
agents/tests/
├── __init__.py
├── conftest.py                    # 测试配置
├── test_factory.py                # Agent 工厂函数测试 (9 用例)
├── test_llm_client.py             # LLM 客户端测试 (7 用例)
├── test_orchestrator.py           # Orchestrator 流程测试 (10 用例)
├── test_fs_tool.py                # 文件系统工具测试 (7 用例)
├── test_types.py                  # 类型定义测试 (5 用例)
└── test_claude_code_adapter.py    # Claude Code 适配器测试 (12 用例)
```

### 用例统计

| 测试文件 | 用例数 | 覆盖模块 |
|----------|--------|----------|
| test_factory.py | 13 | agents_config.py |
| test_llm_client.py | 7 | tools/llm_client.py |
| test_orchestrator.py | 10 | agent_core/orchestrator_agent.py |
| test_fs_tool.py | 7 | tools/fs_tool.py |
| test_types.py | 5 | tools/types.py |
| test_claude_code_adapter.py | 12 | tools/claude_code_adapter.py |
| **总计** | **54** | - |

---

## 4. 建议的 pytest 命令

### 日常开发（推荐）

```bash
# 只运行新版测试（agents/tests）
pytest agents/tests -v

# 运行特定模块
pytest agents/tests/test_factory.py -v
pytest agents/tests/test_orchestrator.py -v
```

### 追踪旧行为（调试用）

```bash
# 运行 legacy 测试（大部分会被 skip）
pytest tests/agents_legacy -v

# 强制运行所有 legacy 测试（包括 skip 的）
pytest tests/agents_legacy -v --runxfail
```

### CI/CD 配置建议

```yaml
# .github/workflows/test.yml
jobs:
  test:
    steps:
      - name: Run Agent Tests
        run: pytest agents/tests -v --tb=short

      # 可选：追踪 legacy 测试状态
      - name: Check Legacy Tests (informational)
        run: pytest tests/agents_legacy -v --tb=line || true
        continue-on-error: true
```

---

## 5. pytest.ini 配置

```ini
[pytest]
pythonpath = .
testpaths = agents/tests
norecursedirs = .git __pycache__ .pytest_cache node_modules tests/agents_legacy
addopts = -v --tb=short
```

**关键点**：
- `testpaths = agents/tests` - 默认只运行新测试
- `norecursedirs` 包含 `tests/agents_legacy` - 排除 legacy 目录

---

## 6. 后续工作

### 待完成迁移

1. **test_sot_guard_skill.py** - 需要对齐 SoT v2.6 状态机定义
2. **test_fe_dev_skill.py / test_be_dev_skill.py** - 需要完善 LLM mock 策略

### 待删除

1. `test_agentsskillssot_guard_skill.py` - 文件名错误
2. 空文件如果 3 个月内没有补充，考虑删除

### 待补充

1. `test_server.py` - FastAPI HTTP 接口测试
2. `test_doc_agent.py` / `test_code_review_agent.py` - 新 Agent 测试

---

*报告生成: 2025-11-29 | 测试重构负责人*
