---
description: "调用 AI Agent 系统生成代码/测试/文档"
argument-hint: "<agent> <action> [--files <files>]"
---

# AI Agent 调用器

根据用户参数调用对应的 Agent 执行任务。

## 可用 Agent

| Agent | 说明 | 示例 |
|-------|------|------|
| `be` | 后端代码生成 (FastAPI/Pydantic) | `/agent be 实现充值API` |
| `fe` | 前端代码生成 (Next.js/React) | `/agent fe 实现项目列表页` |
| `test` | 测试用例生成 (pytest) | `/agent test 生成日报测试` |
| `doc` | 文档生成/审查 | `/agent doc 审查API文档` |
| `review` | 代码审查 (SoT合规) | `/agent review backend/routers/` |

## 执行步骤

1. 解析用户参数: `$ARGUMENTS`
2. 识别 Agent 类型和 action
3. 加载对应 SoT 文档作为上下文
4. 执行代码生成/审查任务
5. 输出结果 (不自动写入，除非用户确认)

## SoT 裁判链

所有生成必须遵循:
```
STATE_MACHINE.md v2.6 → DATA_SCHEMA.md v5.2 → BUSINESS_RULES.md v3.1
→ API_SOT.md v9.0 → ERROR_CODES_SOT.md v2.1 → LEDGER_SOT.md v1.1
```

## 参数解析

用户输入: `$ARGUMENTS`

请按以下格式解析:
- 第一个词 = Agent 类型 (be/fe/test/doc/review)
- 剩余内容 = action 描述
- `--files` 后的内容 = 目标文件列表

## 执行规则

### BE Agent (后端)
- 读取 `docs/2.sot/DATA_SCHEMA.md`, `API_SOT.md`, `STATE_MACHINE.md`
- 生成符合规范的 FastAPI router/service/schema
- 使用 `backend/models/` 中的现有模型
- 错误码必须来自 `ERROR_CODES_SOT.md`

### FE Agent (前端)
- 读取 `docs/3.dev-guides/FRONTEND_DEVELOPMENT_RULES.md`
- 生成 Next.js App Router 组件
- 使用 shadcn/ui 组件库
- 遵循 TanStack Query 数据获取模式

### Test Agent (测试)
- 读取 `docs/3.dev-guides/TESTING_STRATEGY.md`
- 生成 pytest 测试用例
- 覆盖状态机转换、边界条件、错误处理

### Doc Agent (文档)
- 审查文档与 SoT 一致性
- 检查版本引用是否最新
- 识别 P0/P1/P2 问题

### Review Agent (审查)
- 检查代码是否符合 SoT 规范
- 验证状态枚举、错误码、业务规则
- 输出合规报告

## 输出格式

```
## Agent: <agent_type>
## Action: <action>
## Target: <files>

### 分析结果
...

### 生成代码 (如适用)
...

### 下一步
- [ ] 确认后写入文件
- [ ] 运行测试验证
```
