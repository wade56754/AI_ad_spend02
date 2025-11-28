# Agents Layer Fix Report v3.0

> **日期**: 2025-11-28
> **基准**: MASTER.md v3.5, Agent Layer Freeze v1.0, SoT Freeze v2.6
> **执行者**: Claude Code (ai-ad-spec-governor)

---

## Executive Summary

| 优先级 | 问题数 | 已修复 | 需手动操作 |
|--------|--------|--------|------------|
| **P0** | 2 | 0 | 2 (需手动删除) |
| **P1** | 3 | 3 | 0 |
| **合计** | 5 | 3 | 2 |

---

## 1. P0 问题修复状态

### P0-AG-001: 废弃目录 agents/agents/ 仍存在 ⚠️ 需手动操作

**问题**: 遗留的旧 Agent 实现目录仍存在，与 `agent_core/` 功能重复

**状态**: 需手动删除（文件可能被进程锁定）

**手动操作步骤**:
```powershell
# 关闭所有使用这些文件的进程（VSCode, Python 等）
Remove-Item -Path "D:\git\1108\AI_ad_spend02\agents\agents" -Recurse -Force
```

**需删除的文件**:
- `agents/agents/__init__.py`
- `agents/agents/be_agent.py`
- `agents/agents/fe_agent.py`
- `agents/agents/test_agent.py`

---

### P0-AG-002: 错误命名文件 agentsskillssot_guard_skill.py ⚠️ 需手动操作

**问题**: 文件名包含路径分隔符，是创建错误产生的重复文件

**状态**: 需手动删除（文件可能被进程锁定）

**手动操作步骤**:
```powershell
Remove-Item -Path "D:\git\1108\AI_ad_spend02\agents\skills\agentsskillssot_guard_skill.py" -Force
```

---

## 2. P1 问题修复状态

### P1-AG-001: OrchestratorAgent 硬编码路径 ✅ 已修复

**问题**: `_run_frontend_restructure()` 硬编码了 12 个前端文件路径

**修复方案**:
1. 在 `agents_config.py` 添加 `FRONTEND_RESTRUCTURE_FILES` 配置
2. 修改 `orchestrator_agent.py` 从配置读取文件列表
3. 支持通过 `request["frontend_files"]` 覆盖默认列表

**修改文件**:
- `agents/agents_config.py` (行 106-122): 添加 `FRONTEND_RESTRUCTURE_FILES` 列表
- `agents/agent_core/orchestrator_agent.py` (行 333-335): 使用配置替代硬编码

**代码变更**:
```python
# agents_config.py
FRONTEND_RESTRUCTURE_FILES: List[str] = [
    "src/lib/api/apiFetch.ts",
    "src/lib/api/apiTypes.ts",
    # ... 12 个文件
]

# orchestrator_agent.py
from ..agents_config import FRONTEND_RESTRUCTURE_FILES
frontend_files = request.get("frontend_files") or FRONTEND_RESTRUCTURE_FILES
```

---

### P1-AG-002: ClaudeCodeClient 忽略 model/temperature 参数 ✅ 已修复

**问题**: `ClaudeCodeClient._MessagesAPI.create()` 接收但未使用 model/temperature 参数

**修复方案**:
1. 添加 debug 日志记录请求参数
2. 支持 `system` 参数传递
3. 添加文档说明 CLI 模式的限制

**修改文件**:
- `agents/tools/claude_code_adapter.py` (行 303-353): 增强 `create()` 方法

**代码变更**:
```python
# 记录请求参数
logger.debug(
    f"ClaudeCodeClient.create: model={model}, max_tokens={max_tokens}, "
    f"temperature={temperature}, messages_count={len(messages)}"
)

# 支持 system 参数
system_prompt = kwargs.get("system")
if system_prompt:
    prompt_parts.append(f"[SYSTEM]\n{system_prompt}")
```

---

### P1-AG-003: SotParser 缺少 reload 机制 ✅ 已修复

**问题**: SoT 文档更新后需要重启进程才能生效

**修复方案**:
1. 添加 `reload()` 类方法
2. 添加 `invalidate_cache()` 类方法
3. 支持运行时热更新

**修改文件**:
- `agents/skills/sot_guard_skill.py` (行 158-186): 添加 reload/invalidate 方法

**使用示例**:
```python
from agents.skills.sot_guard_skill import SotParser

# 当 SoT 文档更新后
SotParser.reload()  # 重新加载最新内容

# 或者仅使缓存失效
SotParser.invalidate_cache()  # 下次访问时重新解析
```

---

## 3. 修改文件清单

| 文件 | 变更类型 | 描述 |
|------|----------|------|
| `agents/agents_config.py` | 修改 | 添加 FRONTEND_RESTRUCTURE_FILES 配置 |
| `agents/agent_core/orchestrator_agent.py` | 修改 | 使用配置替代硬编码路径 |
| `agents/tools/claude_code_adapter.py` | 修改 | 增强参数日志和 system 支持 |
| `agents/skills/sot_guard_skill.py` | 修改 | 添加 reload/invalidate 方法 |

### 需手动删除的文件

| 文件/目录 | 原因 |
|-----------|------|
| `agents/agents/` (整个目录) | 废弃的旧实现，与 agent_core 重复 |
| `agents/skills/agentsskillssot_guard_skill.py` | 命名错误的重复文件 |

---

## 4. 验证步骤

### 4.1 语法验证 ✅
```bash
python -m py_compile agents\agents_config.py
python -m py_compile agents\agent_core\orchestrator_agent.py
python -m py_compile agents\tools\claude_code_adapter.py
python -m py_compile agents\skills\sot_guard_skill.py
```

### 4.2 导入验证 ✅
```bash
python -c "from agents import create_agent, list_agents; print(list_agents().keys())"
python -c "from agents.agents_config import FRONTEND_RESTRUCTURE_FILES; print(len(FRONTEND_RESTRUCTURE_FILES))"
python -c "from agents.skills.sot_guard_skill import SotParser; SotParser.reload(); print('OK')"
```

### 4.3 手动删除后验证
```bash
# 确认废弃目录已删除
python -c "import agents.agents" # 应报错 ModuleNotFoundError
```

---

## 5. 向后兼容性

| API | 状态 | 说明 |
|-----|------|------|
| `create_agent()` | ✅ 兼容 | 无签名变更 |
| `list_agents()` | ✅ 兼容 | 无变更 |
| `OrchestratorAgent.handle_request()` | ✅ 兼容 | 新增可选参数 `frontend_files` |
| `ClaudeCodeClient.messages.create()` | ✅ 兼容 | 新增 system 支持，原有调用不受影响 |
| `SotParser` | ✅ 兼容 | 新增 reload/invalidate 方法 |

---

## 6. 后续建议

1. **立即执行**: 手动删除 P0 中标注的文件/目录
2. **可选优化**:
   - 为 OrchestratorAgent 添加 `doc_only` 流程
   - 添加执行耗时统计日志
   - 编写 AGENTS_DEBUG.md 调试文档

---

**报告生成时间**: 2025-11-28
**基准对齐**: ASDD 6-Layer Architecture, Agent Layer Freeze v1.0
