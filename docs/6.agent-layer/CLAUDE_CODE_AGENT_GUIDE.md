# Claude Code Agent 使用指南

> **文档版本**: v2.1 (7 Flow 架构)
> **SoT 基准**: DEV_FLOW_SOT_v1.1
> **创建日期**: 2025-12-06
> **更新日期**: 2025-12-07
> **适用范围**: Claude Code CLI 用户

---

## 概述

本指南介绍如何在 Claude Code 命令行中使用 AI 代码工厂命令，实现代码生成、测试、文档审计等自动化任务。

> **v2.4 架构**: 统一使用 `/gen`、`/review`、`/doc`、`/sot-check`
> **7 Flow 架构**: 使用 `/dev-flow` 执行标准开发流程

## 快速开始

```bash
# 在项目目录中启动 Claude Code
cd /path/to/AI_Ads
claude

# 使用开发流程命令 (推荐)
/dev-flow be 实现充值审批功能

# 或单独使用核心命令
/gen be 实现充值API
```

---

## 可用命令一览

### 开发流程命令 (推荐)

| 命令 | Flow ID | 用途 | 示例 |
|------|---------|------|------|
| `/dev-flow be` | BE_DEV_FLOW | 后端功能开发 | `/dev-flow be 实现充值审批` |
| `/dev-flow fe` | FE_DEV_FLOW | 前端功能开发 | `/dev-flow fe 实现充值页面` |
| `/dev-flow fix` | API_FIX_FLOW | 接口 Bug 修复 | `/dev-flow fix 日报导出返回空` |
| `/dev-flow test` | TEST_HARDEN_FLOW | 测试加固 | `/dev-flow test 补齐状态机测试` |
| `/dev-flow doc` | DOC_FREEZE_FLOW | 文档审计/冻结 | `/dev-flow doc docs/2.sot/` |
| `/dev-flow full` | FULL_FLOW | 完整功能开发 | `/dev-flow full 实现对账模块` |
| `/dev-flow refactor` | REFACTOR_FLOW | 代码重构 | `/dev-flow refactor 重构审批逻辑` |

### 核心命令

| 命令 | 用途 | 示例 |
|------|------|------|
| `/gen be` | 后端代码生成 | `/gen be 实现充值API` |
| `/gen fe` | 前端代码生成 | `/gen fe 实现充值页面` |
| `/gen test` | 测试代码生成 | `/gen test 为充值模块生成测试` |
| `/review` | 代码审查 | `/review backend/services/topup_service.py` |
| `/sot-check` | SoT 合规检查 | `/sot-check backend/routers/` |
| `/doc` | 文档审计 | `/doc docs/2.sot/` |

---

## 1. `/gen` - 代码生成

### 语法

```bash
/gen <type> <task> [--files <files>]
```

### 可用类型

| 类型 | 用途 | SoT 依赖 |
|------|------|----------|
| `be` | 后端代码生成 (FastAPI) | DATA_SCHEMA, API_SOT, STATE_MACHINE |
| `fe` | 前端代码生成 (React/Next.js) | FRONTEND_RULES, UI_DESIGN_SYSTEM |
| `test` | 测试代码生成 (pytest) | TESTING_STRATEGY, STATE_MACHINE |

### 使用示例

#### 后端代码生成

```bash
# 生成 CRUD API
/gen be 实现 projects CRUD API

# 指定目标文件
/gen be 实现充值服务 --files backend/services/topup_service.py

# 生成完整模块 (Schema → Service → Router)
/gen be 实现对账模块
```

#### 前端代码生成

```bash
# 生成页面组件
/gen fe 实现项目列表页面

# 生成表单组件
/gen fe 实现充值申请表单

# 指定目标文件
/gen fe 实现日报详情抽屉 --files frontend/components/DailyReportDrawer.tsx
```

#### 测试代码生成

```bash
# 生成模块测试
/gen test 生成日报模块测试

# 生成状态机测试
/gen test 生成充值状态转换测试

# 指定测试文件
/gen test 生成对账API测试 --files backend/tests/test_reconciliation_api.py
```

---

## 2. `/review` - 代码审查

### 语法

```bash
/review <file_or_directory>
```

### 审查内容

- **代码质量**: 可读性、复杂度、错误处理
- **安全检查**: 注入漏洞、权限问题
- **SoT 合规**: 状态机、错误码、数据模型
- **架构一致性**: 分层规范、依赖关系

### 使用示例

```bash
# 审查单个文件
/review backend/routers/daily_reports.py

# 审查目录
/review backend/services/

# 审查前端组件
/review frontend/src/components/TopupForm.tsx
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

# 检查 SoT 文档一致性
/sot-check docs/2.sot/
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

## 4. `/doc` - 文档审计

### 语法

```bash
/doc [directory] [--auto-fix]
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
| BUSINESS_RULES.md | v3.2 |
| API_SOT.md | v9.0 |
| ERROR_CODES_SOT.md | v2.1 |
| AUTH_SPEC.md | v2.0 |
| LEDGER_SOT.md | v1.1 |

### 使用示例

```bash
# 扫描全部文档
/doc

# 扫描指定目录
/doc docs/2.sot/

# 扫描并自动修复
/doc --auto-fix

# 仅扫描开发指南
/doc docs/3.dev-guides/
```

---

## 开发流程推荐 (7 Flow)

### 使用 /dev-flow 命令 (推荐)

```bash
# 后端功能开发 (BE_DEV_FLOW)
/dev-flow be 实现充值审批功能

# 前端功能开发 (FE_DEV_FLOW)
/dev-flow fe 实现充值申请页面

# 接口 Bug 修复 (API_FIX_FLOW)
/dev-flow fix 日报导出接口返回空数据

# 测试加固 (TEST_HARDEN_FLOW)
/dev-flow test 补齐对账模块状态机测试

# 文档审计/冻结 (DOC_FREEZE_FLOW)
/dev-flow doc docs/2.sot/

# 完整功能开发 (FULL_FLOW)
/dev-flow full 实现对账模块

# 代码重构 (REFACTOR_FLOW)
/dev-flow refactor 重构 topup_service.py 的审批逻辑
```

### 手动执行各步骤

#### 后端功能开发 (BE_DEV_FLOW)

```bash
# Step 1: SoT 对齐检查
/sot-check docs/2.sot/

# Step 2: Schema 层
/gen be 生成充值审批的 Pydantic Schema

# Step 3: Service 层
/gen be 实现充值审批的 Service 层

# Step 4: Router 层
/gen be 实现充值审批的 Router 层

# Step 5: 测试
/gen test 为充值审批生成状态机测试 + API 测试

# Step 6: 审查
/review backend/services/topup_approval_service.py
```

#### Bug 修复 (API_FIX_FLOW)

```bash
# Step 1: SoT 检查
/sot-check backend/routers/daily_report.py

# Step 2: 修复
/gen be 修复日报导出接口返回空数据问题

# Step 3: 回归测试
/gen test 为日报导出接口生成回归测试

# Step 4: 审查
/review backend/routers/daily_report.py
```

#### 代码重构 (REFACTOR_FLOW)

```bash
# ⚠️ 约束: 不得改变业务行为，不得修改 SoT 定义

# Step 1: 建立测试基线
pytest backend/tests/ --tb=short > refactor_baseline.txt

# Step 2: SoT 检查
/sot-check backend/services/topup_service.py

# Step 3: 代码分析
/review backend/services/topup_service.py

# Step 4: 重构实施
/gen be 重构 topup_service.py 的审批逻辑

# Step 5: 等价验证
/sot-check backend/services/topup_service.py
pytest backend/tests/ -v > refactor_after.txt
diff refactor_baseline.txt refactor_after.txt
```

---

## SoT 裁判链

所有生成的代码必须遵循以下优先级:

```
┌─────────────────────────────────────────────────────────────┐
│  STATE_MACHINE.md v2.6  (状态机定义，最高优先级)              │
├─────────────────────────────────────────────────────────────┤
│  DATA_SCHEMA.md v5.2    (数据模型，23 张表)                  │
├─────────────────────────────────────────────────────────────┤
│  BUSINESS_RULES.md v4.1 (业务规则)                          │
├─────────────────────────────────────────────────────────────┤
│  API_SOT.md v9.3        (API 规范，126 端点)                 │
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

### 1. 先检查后生成

```bash
# 先检查 SoT 合规性
/sot-check backend/

# 再生成代码
/gen be 实现新功能
```

### 2. 指定目标文件

```bash
# ✅ 好: 明确指定文件
/gen be 实现充值服务 --files backend/services/topup_service.py

# ⚠️ 避免: 范围过大
/gen be 实现所有后端功能
```

### 3. 分步执行复杂任务

```bash
# 第一步: 后端
/gen be 实现充值 router 和 service

# 第二步: 测试
/gen test 生成充值模块测试

# 第三步: 检查
/sot-check backend/routers/topup.py
```

### 4. 定期文档审计

```bash
# 每周执行一次
/doc --auto-fix
```

---

## 常见问题

### Q: 生成的代码有错误怎么办?

A: 使用 `/sot-check` 检查合规性，然后手动修复或重新生成。

### Q: 如何查看加载了哪些 SoT 文档?

A: Skill 会自动加载 `docs/2.sot/` 目录下的所有 SoT 文档。

### Q: 生成的代码不符合项目规范?

A: 检查 SoT 文档是否最新，使用 `/doc` 审计文档一致性。

### Q: 如何自定义命令行为?

A: 修改 `.claude/skills/` 目录下的 Skill 定义文件。

---

## 相关文档

- [AI 代码工厂开发指南](./AI_CODE_FACTORY_DEV_GUIDE_v2.4.md)
- [SuperClaude 集成指南](./SUPERCLAUDE_INTEGRATION_GUIDE_v2.2.md)
- [Skills 索引](../../.claude/skills/README.md)

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.1 | 2025-12-07 | 新增 7 Flow 架构，新增 /dev-flow 命令文档 |
| v2.0 | 2025-12-07 | 升级到 v2.4 命令架构，移除 /agent、/orch、/doc-agent |
| v1.0 | 2025-12-06 | 初始版本 |

---

<details>
<summary>📜 已弃用命令参考 (v2.3 及更早)</summary>

以下命令在 v2.4 架构中已移除：

| 旧命令 | 新命令 | 说明 |
|--------|--------|------|
| `/agent be <task>` | `/gen be <task>` | 后端代码生成 |
| `/agent fe <task>` | `/gen fe <task>` | 前端代码生成 |
| `/agent test <task>` | `/gen test <task>` | 测试代码生成 |
| `/orch be_then_test <task>` | `/gen be` + `/gen test` | 后端→测试流程 |
| `/orch full <task>` | `/gen be` + `/gen fe` + `/gen test` | 完整流程 |
| `/doc-agent [dir]` | `/doc [dir]` | 文档审计 |

</details>
