---
description: "编排器: 执行多Agent工作流 (后端→测试, 完整流程等)"
argument-hint: "<flow> <task> [--auto-write]"
---

# Orchestrator 编排器

执行多 Agent 协作工作流。

## 可用工作流

| Flow | 说明 | 示例 |
|------|------|------|
| `be_then_test` | 后端 → 测试 | `/orch be_then_test 实现充值API` |
| `full` | 后端 → 前端 → 测试 | `/orch full 实现项目管理功能` |
| `fe_only` | 仅前端 | `/orch fe_only 重构日报页面` |
| `be_only` | 仅后端 | `/orch be_only 实现对账服务` |

## 执行步骤

1. 解析用户参数: `$ARGUMENTS`
2. 识别工作流类型
3. 按顺序执行各阶段 Agent
4. 汇总结果报告
5. 等待用户确认后写入 (除非 `--auto-write`)

## 工作流详情

### be_then_test (Phase 3.0B)

```
┌─────────────┐    ┌─────────────┐
│  BE Agent   │ -> │ Test Agent  │
│ 生成后端代码  │    │ 生成测试用例  │
└─────────────┘    └─────────────┘
```

步骤:
1. 读取 SoT 文档
2. BE Agent 生成 router/service/schema
3. Test Agent 生成对应测试
4. 输出完整代码包

### full (完整流程)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  BE Agent   │ -> │  FE Agent   │ -> │ Test Agent  │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 参数解析

用户输入: `$ARGUMENTS`

- 第一个词 = flow 类型
- 剩余内容 = task 描述
- `--auto-write` = 自动写入文件

## SoT 加载

每个阶段自动加载:
- BE: DATA_SCHEMA, API_SOT, STATE_MACHINE, BUSINESS_RULES
- FE: FRONTEND_RULES, UI_DESIGN_SYSTEM
- Test: TESTING_STRATEGY, STATE_MACHINE

## 输出格式

```
## Orchestrator: <flow>
## Task: <task>

### Phase 1: Backend
状态: ✅ 完成
生成文件:
- backend/routers/xxx.py
- backend/services/xxx_service.py

### Phase 2: Test
状态: ✅ 完成
生成文件:
- backend/tests/test_xxx.py

### 汇总
- 总文件数: N
- 代码行数: M
- 测试用例: K

### 下一步
输入 "确认写入" 或 "取消"
```
