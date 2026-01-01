# AI 代码工厂迁移指南

> **迁移版本**: v5.0 → Hooks v1.0
> **迁移日期**: 2026-01-01
> **迁移方案**: 方案 C - 轻量化 + Hook 集成

---

## 迁移概述

根据架构审查报告，AI 代码工厂已迁移到 **Claude Code Hook 集成模式**。

### 核心变化

| 维度 | 迁移前 | 迁移后 |
|------|--------|--------|
| 代码量 | 19K 行 (70 文件) | ~2K 行 (4 文件) |
| 运行方式 | 独立 CLI | Claude Code Hook |
| 启动时间 | 慢 (加载 RAG) | 即时 |
| 学习成本 | 高 | 低 |

---

## 新架构位置

核心验证能力已迁移到 `.claude/hooks/lib/`:

```
.claude/
├── sot-validator.yaml          # SoT 验证配置 (YAML)
├── hooks/
│   ├── pre_tool_use.py         # 工具使用前检查 (入口)
│   └── lib/
│       ├── config.py           # 配置模块 (v2.0)
│       ├── compliance_checker.py # 合规检查器
│       └── sot_validator.py    # SoT 验证器 (新增)
```

---

## 模块状态

### 已迁移 (独特价值保留)

| 原模块 | 新位置 | 说明 |
|--------|--------|------|
| `sot/loader.py` | `.claude/hooks/lib/config.py` | SoT 版本管理 |
| `security.py` | `.claude/hooks/lib/sot_validator.py` | 角色/状态验证 |
| `phase_config.py` | `.claude/hooks/lib/sot_validator.py` | Phase 边界控制 |
| `core/constants.py` | `.claude/hooks/lib/config.py` | 常量定义 |

### 弃用 (与 Claude Code 重叠)

| 模块 | 原因 | Claude Code 替代 |
|------|------|------------------|
| `cli.py` | 交互模式 | Claude Code 原生 CLI |
| `rag/` | 知识库检索 | Grep/Glob 工具 |
| `searcher.py` | 代码搜索 | Explore Agent |
| `repo_map/` | 仓库地图 | 原生文件浏览 |
| `llm_client.py` | LLM 调用 | Claude Code 内置 |
| `prompts/` | 提示词系统 | 直接对话 |
| `assembler.py` | 代码组装 | Claude Code 生成 |
| `selector.py` | 代码选择 | Claude Code 理解 |
| `adapter.py` | 代码适配 | 规则内联到 Hook |

### 保留但不活跃

| 模块 | 状态 | 说明 |
|------|------|------|
| `event_stream/` | 保留 | 未来可扩展 |
| `guardrails/` | 保留 | 防护栏机制 |
| `tests/` | 保留 | 测试用例 |

---

## 验证能力对比

### 角色验证

**迁移前** (`security.py`):
```python
from agents.skills.code_factory.security import SoTComplianceChecker
checker = SoTComplianceChecker()
result = checker.check_role("supervisor")
```

**迁移后** (`.claude/hooks/lib/sot_validator.py`):
```python
from .sot_validator import SoTValidator
validator = SoTValidator()
issues = validator.validate_roles(code_content, filepath)
```

### Phase 边界控制

**迁移前** (`phase_config.py`):
```python
from agents.skills.code_factory.phase_config import PhaseManager
manager = PhaseManager()
allowed = manager.is_action_allowed("auto_reject")
```

**迁移后**:
```python
from .sot_validator import SoTValidator
validator = SoTValidator()
issues = validator.validate_phase_boundary(code_content, filepath)
```

### 高风险模块检测

**迁移前**: 无独立功能

**迁移后**:
```python
from .sot_validator import SoTValidator
validator = SoTValidator()
issues = validator.detect_high_risk(code_content, filepath)
```

---

## 配置迁移

### 角色定义

**迁移前** (`core/constants.py`):
```python
BUSINESS_ROLES = {"ceo", "project_owner", ...}
```

**迁移后** (`.claude/sot-validator.yaml`):
```yaml
validation_rules:
  roles:
    whitelist:
      - ceo
      - project_owner
      - finance
      - pitcher
      - account_manager
      - admin
```

### SoT 版本

**迁移前** (`core/constants.py`):
```python
SOT_EXPECTED_VERSIONS = {"MASTER.md": "v4.8", ...}
```

**迁移后** (`.claude/hooks/lib/config.py`):
```python
SOT_VERSIONS = {
    "MASTER.md": "v4.8",
    "BUSINESS_RULES.md": "v4.8",
    "DATA_SCHEMA.md": "v5.7",
    "STATE_MACHINE.md": "v2.8",
}
```

---

## 如何使用新系统

### 1. 自动验证 (推荐)

编辑代码时，Claude Code 会自动通过 `pre_tool_use.py` Hook 进行验证。

### 2. 手动验证

```python
# 在 Python 中调用
import sys
sys.path.insert(0, ".claude/hooks")
from lib.sot_validator import validate_code, get_validation_report

result = validate_code(code_content, "backend/services/xxx.py")
print(result.format_report())
```

### 3. 配置调整

编辑 `.claude/sot-validator.yaml` 可以:
- 添加/移除角色白名单
- 调整 Phase 边界规则
- 定义高风险模块

---

## 清理旧代码

如果确认迁移完成，可以删除以下目录/文件:

```bash
# 弃用模块 (可安全删除)
rm agents/skills/code_factory/cli.py
rm -rf agents/skills/code_factory/rag/
rm agents/skills/code_factory/searcher.py
rm -rf agents/skills/code_factory/repo_map/
rm agents/skills/code_factory/llm_client.py
rm -rf agents/skills/code_factory/prompts/
rm agents/skills/code_factory/assembler.py
rm agents/skills/code_factory/selector.py
rm agents/skills/code_factory/adapter.py
```

**注意**: 建议保留 1-2 周观察期后再删除。

---

## 开源最佳实践借鉴

本次迁移借鉴了以下开源项目:

| 项目 | 借鉴点 |
|------|--------|
| [OpenHands](https://github.com/OpenHands/OpenHands) | 事件驱动架构 (`ValidationEvent`) |
| [MetaGPT](https://github.com/FoundationAgents/MetaGPT) | SOP 配置化 (YAML) |
| [Cline](https://cline.bot) | Plan Mode 用户确认 |

---

## 问题反馈

如遇到迁移问题，请:
1. 检查 `.claude/logs/pre_tool_use.log`
2. 确认 `.claude/sot-validator.yaml` 配置正确
3. 提交 Issue 到项目仓库
