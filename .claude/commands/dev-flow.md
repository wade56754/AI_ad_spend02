---
description: "统一开发流程: 结合 SuperClaude 分析能力 + AI 代码工厂生成能力"
argument-hint: "<flow-type> <task-description>"
---

# Dev-Flow: SuperClaude + AI 代码工厂 统一开发流程

执行完整的开发周期，自动组合 SuperClaude 分析能力与 AI 代码工厂代码生成能力。

> **SoT 基准**: DEV_FLOW_SOT_v1.1 (docs/sot/DEV_FLOW_SOT_v1.0.md)

## 可用流程 (7 大 Flow)

| 命令 | Flow ID | 说明 | SuperClaude | AI 代码工厂 (v2.4) |
|------|---------|------|-------------|-------------------|
| `be` | BE_DEV_FLOW | 后端功能开发 | /sc:pm 分析 | /gen be + /gen test + /review |
| `fe` | FE_DEV_FLOW | 前端功能开发 | /sc:pm 分析 | /gen fe + /gen test + /review |
| `fix` | API_FIX_FLOW | 接口 Bug 修复 | /sc:troubleshoot 诊断 | /gen be 修复 + /gen test |
| `test` | TEST_HARDEN_FLOW | 测试加固 | /sc:analyze 分析 | /gen test + /review |
| `doc` | DOC_FREEZE_FLOW | 文档审计/冻结 | /sc:document 生成 | /doc 审计 |
| `full` | FULL_FLOW | 完整功能开发 | /sc:pm 全流程 | BE + FE + TEST + DOC |
| `refactor` | REFACTOR_FLOW | 代码重构 | /sc:analyze + /sc:improve | /review + /sot-check |

> **历史命名对照** (已废弃):
> - `feature` → 使用 `be` 或 `full`
> - `bugfix` → 使用 `fix`
> - `docs` → 使用 `doc`

## 执行步骤

用户输入: `$ARGUMENTS`

### 1. 解析参数

```
第一个词 = flow-type (be/fe/fix/test/doc/full/refactor)
剩余内容 = task-description
```

### 2. 流程执行

#### be (BE_DEV_FLOW - 后端功能开发)

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: 需求分析 [SuperClaude]                                 │
│  /sc:pm "分析需求并制定实施计划"                                  │
│  输出: 任务分解清单 + 技术方案                                    │
├─────────────────────────────────────────────────────────────────┤
│  Phase 2: SoT 合规检查 [AI代码工厂]                              │
│  /sot-check docs/sot/                                         │
│  检查: STATE_MACHINE.md, BUSINESS_RULES.md, ERROR_CODES_SOT.md  │
│  输出: SoT 覆盖报告 (blocking_gaps / can_proceed)               │
├─────────────────────────────────────────────────────────────────┤
│  Phase 3: 代码生成 [AI代码工厂 v2.4]                             │
│  /gen be "生成 Schema 层"                                       │
│  /gen be "生成 Service 层"                                      │
│  /gen be "生成 Router 层"                                       │
│  输出: backend/schemas/, backend/services/, backend/routers/    │
├─────────────────────────────────────────────────────────────────┤
│  Phase 4: 测试生成 [AI代码工厂]                                  │
│  /gen test "生成状态机测试 + API 测试"                          │
│  输出: backend/tests/                                           │
├─────────────────────────────────────────────────────────────────┤
│  Phase 5: 代码审查 [混合]                                        │
│  /sc:analyze (代码质量/安全/性能)                                │
│  /sot-check (SoT 合规)                                          │
│  输出: 综合审查报告                                              │
├─────────────────────────────────────────────────────────────────┤
│  Phase 6: 提交 [SuperClaude]                                    │
│  /sc:git commit                                                  │
│  输出: 语义化提交                                                │
└─────────────────────────────────────────────────────────────────┘
```

#### fe (FE_DEV_FLOW - 前端功能开发)

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: SoT 对齐 [AI代码工厂]                                  │
│  /sot-check docs/sot/API_SOT.md                               │
│  输出: API 端点清单 + 数据结构                                   │
├─────────────────────────────────────────────────────────────────┤
│  Phase 2: API Client 生成 [AI代码工厂]                           │
│  /gen fe "生成 API Client"                                       │
│  输出: frontend/src/lib/api/                                     │
├─────────────────────────────────────────────────────────────────┤
│  Phase 3: 组件/页面生成 [AI代码工厂]                             │
│  /gen fe "创建页面/组件"                                         │
│  输出: frontend/src/modules/                                     │
├─────────────────────────────────────────────────────────────────┤
│  Phase 4: 测试生成 [AI代码工厂]                                  │
│  /gen test "生成前端测试"                                        │
│  输出: frontend/tests/                                           │
├─────────────────────────────────────────────────────────────────┤
│  Phase 5: 代码审查 [混合]                                        │
│  /review frontend/src/modules/                                   │
│  输出: 审查报告                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### fix (API_FIX_FLOW - 接口 Bug 修复)

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: 问题诊断 [SuperClaude]                                 │
│  /sc:troubleshoot "问题描述"                                     │
│  输出: 根因分析 + 修复建议                                       │
├─────────────────────────────────────────────────────────────────┤
│  Phase 2: SoT 对比 [AI代码工厂]                                  │
│  /sot-check backend/routers/{file}.py                           │
│  输出: 问题清单 + SoT 规则引用                                   │
├─────────────────────────────────────────────────────────────────┤
│  Phase 3: 代码修复 [AI代码工厂 v2.4]                             │
│  /gen be "修复描述"                                              │
│  输出: 修复后的代码                                              │
├─────────────────────────────────────────────────────────────────┤
│  Phase 4: 测试验证 [混合]                                        │
│  /gen test "生成回归测试"                                        │
│  /review backend/routers/{file}.py                              │
│  输出: 测试报告 + 审查报告                                       │
└─────────────────────────────────────────────────────────────────┘
```

#### test (TEST_HARDEN_FLOW - 测试加固)

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: 覆盖分析 [AI代码工厂]                                  │
│  /sot-check backend/tests/                                       │
│  输出: 测试缺口清单                                              │
├─────────────────────────────────────────────────────────────────┤
│  Phase 2: 状态机测试 [AI代码工厂]                                │
│  /gen test "补齐状态机测试"                                      │
│  输出: 状态机测试用例                                            │
├─────────────────────────────────────────────────────────────────┤
│  Phase 3: 边界测试 [AI代码工厂]                                  │
│  /gen test "补齐边界条件测试"                                    │
│  输出: 边界测试用例                                              │
├─────────────────────────────────────────────────────────────────┤
│  Phase 4: 覆盖验证 [混合]                                        │
│  /review backend/tests/                                          │
│  输出: 测试审查报告                                              │
└─────────────────────────────────────────────────────────────────┘
```

#### doc (DOC_FREEZE_FLOW - 文档审计/冻结)

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: 文档审计 [AI代码工厂 v2.4]                             │
│  /doc docs/                                                      │
│  输出: DOC_AUDIT_REPORT (P0/P1/P2 问题清单)                     │
├─────────────────────────────────────────────────────────────────┤
│  Phase 2: SoT 一致性检查 [AI代码工厂]                            │
│  /sot-check docs/sot/                                         │
│  输出: SoT 一致性报告                                            │
├─────────────────────────────────────────────────────────────────┤
│  Phase 3: Freeze 报告生成 [AI代码工厂]                           │
│  /doc --freeze {module}                                          │
│  输出: docs/reports/{module}_FREEZE_REPORT.md                   │
└─────────────────────────────────────────────────────────────────┘
```

#### full (FULL_FLOW - 完整功能开发)

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: 后端开发                                               │
│  执行: BE_DEV_FLOW (完整 6 步)                                  │
│  产出: Schema + Service + Router + 后端测试                     │
├─────────────────────────────────────────────────────────────────┤
│  Phase 2: 前端开发                                               │
│  执行: FE_DEV_FLOW (完整 5 步)                                  │
│  产出: API Client + 页面/组件 + 前端测试                        │
├─────────────────────────────────────────────────────────────────┤
│  Phase 3: 测试加固                                               │
│  执行: TEST_HARDEN_FLOW (完整 4 步)                             │
│  产出: 状态机测试 + 边界测试 + 覆盖率报告                       │
├─────────────────────────────────────────────────────────────────┤
│  Phase 4: 文档冻结                                               │
│  执行: DOC_FREEZE_FLOW (完整 3 步)                              │
│  产出: 文档审计报告 + Freeze 报告                               │
└─────────────────────────────────────────────────────────────────┘
```

#### refactor (REFACTOR_FLOW - 代码重构)

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️ 约束: 不得改变业务行为，不得修改 SoT 定义                    │
├─────────────────────────────────────────────────────────────────┤
│  Phase 1: 快照基线                                               │
│  pytest backend/tests/ --tb=short (保存通过用例清单)            │
│  输出: 测试快照 + API 响应样本                                   │
├─────────────────────────────────────────────────────────────────┤
│  Phase 2: 代码分析 [SuperClaude]                                 │
│  /sc:analyze "分析目标代码"                                      │
│  输出: 代码质量报告 + 重构建议                                   │
├─────────────────────────────────────────────────────────────────┤
│  Phase 3: SoT 验证 [AI代码工厂]                                  │
│  /sot-check {target_files}                                       │
│  输出: 合规报告 + 技术债清单                                     │
├─────────────────────────────────────────────────────────────────┤
│  Phase 4: 重构实施 [SuperClaude]                                 │
│  /sc:improve "执行重构"                                          │
│  或 /gen be "重构 {module}"                                      │
│  输出: 重构后的代码                                              │
├─────────────────────────────────────────────────────────────────┤
│  Phase 5: 等价验证 [混合]                                        │
│  /sot-check {target_files} + pytest (对比快照)                  │
│  输出: 测试通过 + SoT 合规 + 行为等价验证                       │
└─────────────────────────────────────────────────────────────────┘
```

## SoT 约束

所有流程自动遵循 SoT 裁判链:
```
STATE_MACHINE.md v2.6 → DATA_SCHEMA.md v5.2 → BUSINESS_RULES.md v3.2
→ API_SOT.md v9.0 → ERROR_CODES_SOT.md v2.1 → AUTH_SPEC.md v2.0
→ DATA_SCHEMA.md v5.11 §3.4.4
```

## 使用示例

```bash
# 后端功能开发
/dev-flow be 实现充值审批功能

# 前端功能开发
/dev-flow fe 实现充值申请页面

# 接口 Bug 修复
/dev-flow fix 日报状态无法从 trend_pending 转换到 trend_ok

# 测试加固
/dev-flow test 补齐对账模块状态机测试

# 文档审计/冻结
/dev-flow doc 季度文档审计

# 完整功能开发 (前后端 + 测试 + 文档)
/dev-flow full 实现对账模块

# 代码重构
/dev-flow refactor 重构 topup_service.py 的审批逻辑
```

## 输出格式

```
## Dev-Flow: <flow-type> (<flow-id>)
## Task: <task-description>
## SoT Baseline: DEV_FLOW_SOT v1.1

### Phase 1: <phase-name>
工具: <tool-used>
状态: [进行中/完成/跳过]
结果摘要: ...

### Phase 2: <phase-name>
...

### 最终结果
- 总阶段数: N
- 成功: X
- 跳过: Y
- 失败: Z

### 生成产物
- 代码文件: [列表]
- 文档文件: [列表]
- 测试文件: [列表]

### 下一步建议
...
```

## 参考文档

- [DEV_FLOW_SOT v1.1](../docs/sot/DEV_FLOW_SOT_v1.0.md) - 开发流程真相源
- [SUPERCLAUDE_INTEGRATION_GUIDE v2.2](../docs/6.agent-layer/SUPERCLAUDE_INTEGRATION_GUIDE_v2.2.md)
- [AI_CODE_FACTORY_DEV_GUIDE v2.4](../docs/6.agent-layer/AI_CODE_FACTORY_DEV_GUIDE_v2.3.md)
