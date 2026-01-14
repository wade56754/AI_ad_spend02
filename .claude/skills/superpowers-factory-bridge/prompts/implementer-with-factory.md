# Implementer Subagent with AI Code Factory

> **用途**: 实现者子代理提示词模板
> **调用方式**: Task tool (general-purpose)

## 子代理调度模板

```
Task tool (general-purpose):
  description: "Implement Task N: [task name]"
  prompt: |
    你正在实现 Task N: [任务名称]

    ## 任务描述
    [从计划中复制的完整任务文本]

    ## SoT 上下文 (预加载)

    ### STATE_MACHINE.md#<entity>
    [相关状态定义和转换规则]

    ### BUSINESS_RULES.md
    [相关业务规则 BR-XXX-YYY]

    ### ERROR_CODES_SOT.md
    [预期错误码列表]

    ## AI Code Factory 集成

    ### 后端任务
    使用 /gen be 生成代码:
    - 遵循模块边界 (STATE_MACHINE.md v2.9 §2)
    - 包含 SoT 注解
    - 使用 frozenset 白名单值

    ### 前端任务
    使用 /gen fe 生成代码:
    - 使用 COMPONENT_REGISTRY.md 组件
    - 遵循设计系统
    - 包含 SoT 注解

    ## TDD 铁律强制执行

    在写任何实现代码之前:
    1. 写失败测试 (调用 /gen test)
    2. 运行测试，验证 FAIL
    3. 只有当测试失败后才写实现

    ╔════════════════════════════════════════════════════════════╗
    ║ 如果你在测试之前写了代码 → 删除代码 → 重新开始              ║
    ╚════════════════════════════════════════════════════════════╝

    ## 自检清单

    实现完成后，验证:
    - [ ] 所有状态值来自 STATE_MACHINE.md 白名单
    - [ ] 所有角色来自 6-role 白名单 (ceo, project_owner, finance, pitcher, account_manager, admin)
    - [ ] 所有错误码来自 ERROR_CODES_SOT.md
    - [ ] 无 Phase 2+ 功能 (自动阻断、自动拒绝)
    - [ ] SoT 注解存在
    - [ ] 测试先于实现代码

    ## 输出格式

    完成后提供:
    1. 创建/修改的文件列表
    2. 测试运行结果
    3. /sot-check 结果
    4. 提交信息建议
```

## 使用示例

### 后端服务任务

```
Task tool (general-purpose):
  description: "Implement Task 3: Create TopupService.approve method"
  prompt: |
    你正在实现 Task 3: Create TopupService.approve method

    ## 任务描述
    实现充值申请的审批方法，包含:
    - 状态转换: pending_review → finance_approve
    - 权限检查: 仅 finance 角色可操作
    - 金额验证: amount > 0

    ## SoT 上下文 (预加载)

    ### STATE_MACHINE.md#topup_request
    状态: draft → pending_review → finance_approve → paid → completed
    转换规则:
    - pending_review → finance_approve: 需要 finance 角色

    ### BUSINESS_RULES.md
    - BR-TP-001: 只有 finance 角色可以审批充值申请
    - BR-TP-002: 审批金额必须大于 0

    ### ERROR_CODES_SOT.md
    - TP-INVALID-STATUS: 无效的状态转换
    - TP-PERMISSION-DENIED: 权限不足
    - TP-INVALID-AMOUNT: 无效金额

    ## AI Code Factory 集成

    使用 /gen be 生成代码:
    - 遵循模块边界 (STATE_MACHINE.md v2.9 §2)
    - 包含 SoT 注解
    - 使用 frozenset 白名单值

    ## TDD 铁律强制执行

    在写任何实现代码之前:
    1. 写失败测试 (调用 /gen test)
    2. 运行测试，验证 FAIL
    3. 只有当测试失败后才写实现

    ## 自检清单

    实现完成后，验证:
    - [ ] 状态值: pending_review, finance_approve (来自 STATE_MACHINE.md)
    - [ ] 角色: finance (来自 6-role 白名单)
    - [ ] 错误码: TP-* (来自 ERROR_CODES_SOT.md)
    - [ ] 无自动阻断功能
    - [ ] SoT 注解存在
```

### 前端组件任务

```
Task tool (general-purpose):
  description: "Implement Task 5: Create TopupApprovalDialog component"
  prompt: |
    你正在实现 Task 5: Create TopupApprovalDialog component

    ## 任务描述
    创建充值审批弹窗组件，包含:
    - 显示充值申请详情
    - 审批/拒绝按钮
    - 状态反馈

    ## SoT 上下文 (预加载)

    ### STATE_MACHINE.md#topup_request
    用户可见状态: 待审核 → 已审批 → 已打款 → 已完成

    ### COMPONENT_REGISTRY.md
    必须使用:
    - Dialog from shadcn/ui
    - Button from shadcn/ui
    - StatusBadge from components/ui

    ## AI Code Factory 集成

    使用 /gen fe 生成代码:
    - 使用 COMPONENT_REGISTRY.md 组件
    - 遵循设计系统
    - 包含 SoT 注解

    ## TDD 铁律强制执行

    在写任何实现代码之前:
    1. 写失败测试 (调用 /gen test)
    2. 运行测试，验证 FAIL
    3. 只有当测试失败后才写实现

    ## 自检清单

    实现完成后，验证:
    - [ ] 使用 Dialog, Button, StatusBadge 组件
    - [ ] 状态文本来自 STATE_MACHINE.md
    - [ ] 无硬编码字符串
    - [ ] SoT 注解存在
```

## 关键原则

1. **TDD 铁律**: 测试先行，无例外
2. **SoT 约束**: 所有值来自白名单
3. **防幻觉**: 不发明未定义的状态/角色/错误码
4. **最小实现**: 只做任务要求的，不过度设计
5. **可追溯**: 每个决策都有 SoT 引用
