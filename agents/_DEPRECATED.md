# agents/ 模块废弃声明

> **状态**: 影子模式（兼容壳）
> **迁移日期**: 2025-12-04
> **观察期**: 2025-12-04 ~ 2025-12-11 (7 天)
> **迁移文档**: [AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md](../docs/dev/AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md)

---

## 废弃声明

`agents/` 目录已迁移至 `agent_platform/`。

当前目录仅作为**影子模式兼容壳**，所有调用将转发至新模块。

---

## 紧急回退

如遇问题，可设置环境变量临时回退到旧逻辑：

```bash
# Windows
set AGENT_PLATFORM_LEGACY=1
python -m agents.cli status

# Linux/macOS
export AGENT_PLATFORM_LEGACY=1
python -m agents.cli status
```

---

## 删除条件

观察期结束后，满足以下全部条件方可删除 `agents/` 目录：

- [ ] 连续 7 天无 `AGENT_PLATFORM_LEGACY=1` 使用记录
- [ ] 无代码直接导入 `agents/` 模块（除影子壳）
- [ ] 所有 `.claude/commands` 已更新为新路径
- [ ] CI/CD 流水线持续绿色
- [ ] 无外部依赖报告

### 检查命令

```bash
# 检查是否还有直接导入
grep -r "from agents" --include="*.py" . | grep -v "agent_platform" | grep -v "_DEPRECATED"
grep -r "import agents" --include="*.py" . | grep -v "agent_platform" | grep -v "_DEPRECATED"

# 检查 .claude/commands 中的旧路径
grep -r "agents.cli" .claude/commands/
```

---

## 路径映射表

| 旧路径 | 新路径 | 迁移状态 |
|--------|--------|----------|
| `agents/agents_config.py` | `agent_platform/config/*.py` | ✅ Phase 1 完成 |
| `agents/agent_core/` | `agent_platform/agents/` | ⏳ Phase 2 待执行 |
| `agents/skills/` | `agent_platform/skills/` | ⏳ Phase 3 待执行 |
| `agents/tools/` | `agent_platform/tools/` | ⏳ Phase 3 待执行 |
| `agents/cli.py` | `agent_platform/__main__.py` | ✅ Phase 0 完成（转调壳） |
| `agents/__init__.py` | 影子模式兼容壳 | ✅ Phase 0 完成 |

---

## 导入路径变更

```python
# 旧（已废弃）
from agents import create_agent, SOT_FILES
from agents.agents_config import BASE_PATH

# 新（推荐）
from agent_platform.config import SOT_FILES, BASE_PATH
from agents import create_agent  # Phase 2 后将变为 from agent_platform.agents import create_agent
```

---

## 时间线

| 日期 | 事件 |
|------|------|
| 2025-12-04 | Phase 0 + Phase 1 完成，进入观察期 |
| 2025-12-11 | 观察期结束，评估删除条件 |
| TBD | Phase 2-4 执行 |
| TBD | 满足删除条件后，删除 agents/ 目录 |

---

## 联系方式

如有问题，请联系项目维护者或查阅迁移文档。
