# Claude Code 项目配置说明

## 📚 项目规则文档

本项目的所有开发规范已整理在以下文档中：

### 核心规则文档（必读）
- **[PROJECT_RULES.md](PROJECT_RULES.md)** v3.0 - 项目规则总纲（Meta-SoT）
  - SoT 裁判链完整版
  - 5 大不可侵犯原则
  - 8 状态机定义
  - 反模式识别库
  - Claude/SuperClaude 使用指南

### SoT 真相源文档（开发时必须参考 - 已 Freeze v1.0）
1. **[DATA_SCHEMA.md](../docs/2.sot/DATA_SCHEMA.md)** v5.2 - 数据库结构唯一真相
2. **[STATE_MACHINE.md](../docs/2.sot/STATE_MACHINE.md)** v2.6 - 状态机定义唯一真相 (§8: 8状态机)
3. **[BUSINESS_RULES.md](../docs/2.sot/BUSINESS_RULES.md)** v3.1 - 业务规则唯一真相 (BR-*)
4. **[API_SOT.md](../docs/2.sot/API_SOT.md)** v2.2 - API 契约唯一真相
5. **[ERROR_CODES_SOT.md](../docs/2.sot/ERROR_CODES_SOT.md)** v2.1 - 错误码唯一真相
6. **[AUTH_SPEC.md](../docs/2.sot/AUTH_SPEC.md)** v2.0 - 认证授权唯一真相
7. **[LEDGER_SOT.md](../docs/2.sot/LEDGER_SOT.md)** v1.1 - 账本规则唯一真相
8. **[DAILY_REPORT_SOT.md](../docs/2.sot/DAILY_REPORT_SOT.md)** v1.0 - 日报流程唯一真相
9. **[RECONCILIATION_SOT.md](../docs/2.sot/RECONCILIATION_SOT.md)** v1.0 - 对账流程唯一真相
10. **[TRANSFER_SOT.md](../docs/2.sot/TRANSFER_SOT.md)** v1.0 - 调拨规则唯一真相

## 🤖 如何让 Claude 使用这些规则

### 方法1：在对话开始时引用（推荐）
```
请严格遵循 .claude/PROJECT_RULES.md 中定义的所有规则进行开发。
```

### 方法2：在每次任务中明确引用
```
基于以下规范实现 XXX 功能：
1. 数据结构：参考 docs/core/DATA_SCHEMA.md
2. 状态流转：参考 docs/core/STATE_MACHINE.md
3. API规范：参考 docs/core/API_DEVELOPMENT_FLOW.md
```

### 方法3：使用项目记忆功能
在 Claude 对话中使用 `/project` 命令，将 PROJECT_RULES.md 的内容添加到项目记忆中。

## ⚠️ 重要提醒

所有代码生成和修改都必须：
1. ✅ 符合 PROJECT_RULES.md 中的 5 大不可侵犯原则
2. ✅ 遵循 SoT 裁判链优先级
3. ✅ 通过反模式识别检查
4. ✅ 以 `docs/2.sot/` 下的 SoT 文档为唯一依据

如果发现任何代码与规则冲突，**必须以规则为准进行修正**。

## 🎯 快速决策流程

```
收到需求 → 识别业务域 → 查询对应 SoT 文档（按裁判链优先级）
→ 找到规则编号（如 BR-RPT-001）→ 检查代码是否符合
→ 符合 → 继续开发 | 不符合 → 先修复或提 RFC
```

## 📦 文档体系版本

**当前基准**: SoT Freeze v1.0 (2025-11-24)
- **规则总纲**: PROJECT_RULES.md v3.0
- **项目指令**: CLAUDE.md v3.0
- **SoT 文档**: 10 个核心文档已冻结（详见上方列表）

---

**最后更新**: 2025-11-24 | **基准**: SoT Freeze v1.0
