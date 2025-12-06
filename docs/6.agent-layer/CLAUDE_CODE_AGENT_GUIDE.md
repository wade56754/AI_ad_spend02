# Claude Code Agent 使用指南

> **文档版本**: v1.0
> **创建日期**: 2025-12-06
> **适用范围**: Claude Code CLI 用户

---

## 概述

本指南介绍如何在 Claude Code 命令行中直接调用 AI Agent 系统，实现代码生成、测试、文档审计等自动化任务。

## 快速开始

```bash
# 在项目目录中启动 Claude Code
cd /path/to/AI_Ads
claude

# 调用 Agent
/agent be 实现充值API
```

---

## 可用命令一览

| 命令 | 用途 | 示例 |
|------|------|------|
| `/agent` | 调用单个 Agent | `/agent be 实现充值API` |
| `/orch` | 执行多 Agent 工作流 | `/orch be_then_test 实现日报功能` |
| `/sot-check` | SoT 合规检查 | `/sot-check backend/routers/` |
| `/doc-agent` | 文档审计 | `/doc-agent docs/2.sot/` |

---

## 1. `/agent` - 单 Agent 调用

### 语法

```bash
/agent <agent_type> <action> [--files <files>]
```

### 可用 Agent 类型

| Agent | Key | 用途 | SoT 依赖 |
|-------|-----|------|----------|
| Backend Agent | `be` | 生成 FastAPI 路由、服务、Schema | DATA_SCHEMA, API_SOT, STATE_MACHINE |
| Frontend Agent | `fe` | 生成 Next.js/React 组件 | FRONTEND_RULES, UI_DESIGN_SYSTEM |
| Test Agent | `test` | 生成 pytest 测试用例 | TESTING_STRATEGY, STATE_MACHINE |
| Doc Agent | `doc` | 文档生成与审查 | 全部 SoT 文档 |
| Review Agent | `review` | SoT 合规检查 | 全部 SoT 文档 |

### 使用示例

#### 后端代码生成

```bash
# 生成 CRUD API
/agent be 实现 projects CRUD API

# 指定目标文件
/agent be 实现充值服务 --files backend/services/topup_service.py

# 生成完整模块
/agent be 实现对账模块 (router + service + schema)
```

#### 前端代码生成

```bash
# 生成页面组件
/agent fe 实现项目列表页面

# 生成表单组件
/agent fe 实现充值申请表单

# 指定目标文件
/agent fe 实现日报详情抽屉 --files frontend/components/DailyReportDrawer.tsx
```

#### 测试用例生成

```bash
# 生成模块测试
/agent test 生成日报模块测试

# 生成状态机测试
/agent test 生成充值状态转换测试

# 指定测试文件
/agent test 生成对账API测试 --files backend/tests/test_reconciliation_api.py
```

#### 代码审查

```bash
# 审查单个文件
/agent review backend/routers/daily_reports.py

# 审查目录
/agent review backend/services/

# SoT 合规检查
/agent review --action sot_check backend/models/
```

#### 文档操作

```bash
# 生成文档
/agent doc 生成 API 端点文档

# 审查文档
/agent doc 审查 API_SOT.md

# 同步文档版本
/agent doc 同步 SoT 版本引用
```

---

## 2. `/orch` - 编排器工作流

### 语法

```bash
/orch <flow> <task> [--auto-write]
```

### 可用工作流

| Flow | 说明 | 步骤 |
|------|------|------|
| `be_then_test` | 后端 → 测试 | BE Agent → Test Agent |
| `full` | 完整流程 | BE → FE → Test |
| `be_only` | 仅后端 | BE Agent |
| `fe_only` | 仅前端 | FE Agent |

### 工作流详解

#### be_then_test (推荐)

```
┌─────────────┐    ┌─────────────┐
│  BE Agent   │ -> │ Test Agent  │
│ 生成后端代码  │    │ 生成测试用例  │
└─────────────┘    └─────────────┘
```

```bash
# 基本用法
/orch be_then_test 实现充值API并生成测试

# 自动写入
/orch be_then_test 实现日报导出功能 --auto-write
```

#### full (完整流程)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  BE Agent   │ -> │  FE Agent   │ -> │ Test Agent  │
│   后端代码   │    │   前端组件   │    │   测试用例   │
└─────────────┘    └─────────────┘    └─────────────┘
```

```bash
# 实现完整功能
/orch full 实现项目管理功能

# 包含前后端和测试
/orch full 实现死号余额迁移功能
```

### 使用示例

```bash
# 后端 + 测试
/orch be_then_test 实现充值申请API

# 完整流程
/orch full 实现对账管理功能

# 仅后端
/orch be_only 实现账本查询服务

# 仅前端
/orch fe_only 重构日报列表页面

# 自动写入模式 (跳过确认)
/orch be_then_test 实现转账API --auto-write
```

---

## 3. `/sot-check` - SoT 合规检查

### 语法

```bash
/sot-check [file_or_directory]
```

### 检查项

| 检查项 | 说明 | SoT 依据 |
|--------|------|----------|
| 状态枚举 | 禁止自定义，必须使用 8 状态机 | STATE_MACHINE.md v2.6 |
| 错误码 | 必须使用标准格式 `{"code": "XXX-NNN"}` | ERROR_CODES_SOT.md v2.1 |
| 账本操作 | 禁止直接修改 balance | LEDGER_SOT.md v1.1 |
| 数据模型 | 字段类型必须与 Schema 一致 | DATA_SCHEMA.md v5.2 |

### 使用示例

```bash
# 检查整个后端
/sot-check backend/

# 检查特定文件
/sot-check backend/routers/topup.py

# 检查服务层
/sot-check backend/services/

# 检查模型层
/sot-check backend/models/
```

### 输出示例

```
## SoT 合规检查报告

### 检查范围
- 目录: backend/routers/
- 文件数: 12

### P0 问题 (阻断级)
| 文件 | 行号 | 问题 | SoT 引用 |
|------|------|------|----------|
| topup.py | 42 | 自定义状态枚举 | STATE_MACHINE.md §8 |

### P1 问题 (警告级)
| 文件 | 行号 | 问题 | SoT 引用 |
|------|------|------|----------|
| ledger.py | 88 | 错误码格式不规范 | ERROR_CODES_SOT.md |

### 统计
- P0: 1 个
- P1: 1 个
- 合规率: 92%
```

---

## 4. `/doc-agent` - 文档审计

### 语法

```bash
/doc-agent [directory] [--auto-fix]
```

### 检查内容

1. **版本引用**: 是否引用最新 SoT 版本
2. **交叉引用**: 链接是否有效
3. **层级结构**: 文档是否在正确目录
4. **格式规范**: Markdown 格式是否正确

### 当前 SoT 版本基线

| 文档 | 版本 |
|------|------|
| STATE_MACHINE.md | v2.6 |
| DATA_SCHEMA.md | v5.2 |
| BUSINESS_RULES.md | v3.1 |
| API_SOT.md | v9.0 |
| ERROR_CODES_SOT.md | v2.1 |
| AUTH_SPEC.md | v2.0 |
| LEDGER_SOT.md | v1.1 |

### 使用示例

```bash
# 扫描全部文档
/doc-agent

# 扫描指定目录
/doc-agent docs/2.sot/

# 扫描并自动修复
/doc-agent --auto-fix

# 仅扫描开发指南
/doc-agent docs/3.dev-guides/
```

### 输出示例

```
## 文档审计报告

### 扫描范围
- 目录: docs/
- 文件数: 42

### 问题汇总
- P0: 0 个
- P1: 2 个
- P2: 5 个

### P1 问题详情
| 文件 | 问题 | 建议修复 |
|------|------|----------|
| TRANSFER_SOT.md | 引用 v2.5 应为 v2.6 | 更新版本号 |
| RECONCILIATION_SOT.md | 引用 v2.5 应为 v2.6 | 更新版本号 |

### 下一步
- 输入 "修复 P1" 修复警告级问题
- 输入 "跳过" 不做修改
```

---

## SoT 裁判链

所有 Agent 生成的代码必须遵循以下优先级:

```
┌─────────────────────────────────────────────────────────────┐
│  STATE_MACHINE.md v2.6  (状态机定义，最高优先级)              │
├─────────────────────────────────────────────────────────────┤
│  DATA_SCHEMA.md v5.2    (数据模型，23 张表)                  │
├─────────────────────────────────────────────────────────────┤
│  BUSINESS_RULES.md v3.1 (业务规则)                          │
├─────────────────────────────────────────────────────────────┤
│  API_SOT.md v9.0        (API 规范，126 端点)                 │
├─────────────────────────────────────────────────────────────┤
│  ERROR_CODES_SOT.md v2.1 (错误码)                           │
├─────────────────────────────────────────────────────────────┤
│  AUTH_SPEC.md v2.0      (认证授权)                          │
├─────────────────────────────────────────────────────────────┤
│  LEDGER_SOT.md v1.1     (账本系统)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 最佳实践

### 1. 先检查后写入

```bash
# 默认预览模式
/orch be_then_test 实现API

# 确认无误后再自动写入
/orch be_then_test 实现API --auto-write
```

### 2. 指定目标文件

```bash
# ✅ 好: 明确指定文件
/agent be 实现充值服务 --files backend/services/topup_service.py

# ⚠️ 避免: 范围过大
/agent be 实现所有后端功能
```

### 3. 分步执行复杂任务

```bash
# 第一步: 后端
/agent be 实现充值 router 和 service

# 第二步: 测试
/agent test 生成充值模块测试

# 第三步: 检查
/sot-check backend/routers/topup.py
```

### 4. 定期文档审计

```bash
# 每周执行一次
/doc-agent --auto-fix
```

---

## 常见问题

### Q: Agent 生成的代码有错误怎么办?

A: 使用 `/sot-check` 检查合规性，然后手动修复或重新生成。

### Q: 如何查看 Agent 加载了哪些 SoT 文档?

A: Agent 会自动加载 `docs/2.sot/` 目录下的所有 SoT 文档。

### Q: 生成的代码不符合项目规范?

A: 检查 SoT 文档是否最新，使用 `/doc-agent` 审计文档一致性。

### Q: 如何自定义 Agent 行为?

A: 修改 `.claude/commands/` 目录下的命令定义文件。

---

## 相关文档

- [Agent 层概览](./AGENT_LAYER_OVERVIEW.md)
- [编排管道规范](./AGENT_ORCHESTRATION_PIPELINE.md)
- [技能注册表](./AGENT_SKILL_REGISTRY.md)
- [Agent 安全规范](./AGENT_SECURITY_SPEC.md)

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-06 | 初始版本，包含 4 个 slash commands |
