# SoT Spec Compliance Reviewer

> **用途**: SoT 规格合规审查子代理提示词模板
> **调用方式**: Task tool (review)

## 子代理调度模板

```
Task tool (review):
  description: "Review Task N for SoT compliance"
  prompt: |
    你正在审查 Task N 的实现是否符合 SoT 规范。

    ## 审查清单

    ### 1. STATE_MACHINE.md 合规性

    检查项:
    - [ ] 所有状态值在 8-state 白名单内
    - [ ] 状态转换遵循允许的路径
    - [ ] 无发明的状态

    白名单 (daily_report):
    ```python
    VALID_STATES = frozenset([
        'raw_submitted',
        'trend_pending',
        'trend_ok',
        'spend_pending',
        'spend_ok',
        'final_pending',
        'final_confirmed',
        'final_locked'
    ])
    ```

    ### 2. BUSINESS_RULES.md 合规性

    检查项:
    - [ ] 实现了所需的 BR-XXX-YYY 规则
    - [ ] 无发明的业务逻辑
    - [ ] Phase 1 约束被尊重

    Phase 1 约束:
    - ❌ 禁止自动阻断/拒绝/暂停/冻结
    - ❌ 禁止自动惩罚机制
    - ✅ 允许: 记录、提示、高亮、警告

    ### 3. ERROR_CODES_SOT.md 合规性

    检查项:
    - [ ] 所有错误码有有效前缀
    - [ ] 错误消息匹配定义
    - [ ] HTTP 状态码正确

    有效前缀:
    ```
    AUTH-, USER-, PROJ-, ACCT-, FIN-, RPT-, RECON-,
    PROFIT-, TOPUP-, TRANSFER-, LEDGER-, SYS-,
    VAL-, PERM-, STATE-, DATA-
    ```

    ### 4. DATA_SCHEMA.md 合规性

    检查项:
    - [ ] 字段名匹配 schema
    - [ ] 类型匹配定义
    - [ ] 必填字段存在

    ### 5. 角色白名单合规性

    检查项:
    - [ ] 所有角色在 6-role 白名单内

    白名单:
    ```python
    VALID_ROLES = frozenset([
        'ceo',
        'project_owner',
        'finance',
        'pitcher',
        'account_manager',
        'admin'
    ])
    ```

    废弃角色 (禁止使用):
    - ❌ supervisor (已废弃，使用 project_owner)
    - ❌ data_operator (不在宪法中)
    - ❌ media_buyer (非标准，使用 pitcher)

    ## 输出格式

    | 检查项 | 状态 | 详情 |
    |-------|------|------|
    | 状态值 | PASS/FAIL | [具体说明] |
    | 状态转换 | PASS/FAIL | [具体说明] |
    | 业务规则 | PASS/FAIL | [具体说明] |
    | 错误码 | PASS/FAIL | [具体说明] |
    | 字段 schema | PASS/FAIL | [具体说明] |
    | 角色 | PASS/FAIL | [具体说明] |
    | Phase 1 约束 | PASS/FAIL | [具体说明] |

    **总体结果**: PASS / FAIL (附带阻断问题)

    ## 发现问题时

    如果发现违规:
    1. 明确指出违规位置 (文件:行号)
    2. 引用 SoT 文档章节
    3. 提供修复建议
    4. 标记为阻断或警告

    示例:
    ```
    ❌ FAIL: 状态值违规
    位置: backend/services/topup_service.py:45
    问题: 使用了未定义状态 'reviewing'
    SoT 引用: STATE_MACHINE.md#topup_request
    修复: 使用 'pending_review' 替代 'reviewing'
    严重度: 阻断
    ```
```

## 使用示例

```
Task tool (review):
  description: "Review Task 3: TopupService.approve for SoT compliance"
  prompt: |
    你正在审查 Task 3: TopupService.approve 的实现是否符合 SoT 规范。

    ## 变更文件
    - backend/services/topup_service.py
    - backend/tests/services/test_topup_service.py

    ## 相关 SoT 文档
    - STATE_MACHINE.md#topup_request
    - BR-TP-001, BR-TP-002
    - ERROR_CODES_SOT.md (TP-* 前缀)

    ## 审查清单

    ### 1. STATE_MACHINE.md 合规性
    - [ ] 状态: pending_review → finance_approve 路径有效
    - [ ] 无发明状态

    ### 2. BUSINESS_RULES.md 合规性
    - [ ] BR-TP-001: finance 角色权限检查已实现
    - [ ] BR-TP-002: 金额验证已实现

    ### 3. ERROR_CODES_SOT.md 合规性
    - [ ] TP-INVALID-STATUS 使用正确
    - [ ] TP-PERMISSION-DENIED 使用正确

    ### 4. 角色白名单合规性
    - [ ] 使用 'finance' 角色 (白名单内)

    ## 执行审查

    使用 /sot-check 验证变更文件:
    /sot-check backend/services/topup_service.py backend/tests/services/test_topup_service.py

    ## 输出审查结果
```

## 审查原则

1. **严格白名单**: 只允许 SoT 定义的值
2. **可追溯性**: 每个检查项都有 SoT 引用
3. **明确判定**: PASS 或 FAIL，无模糊地带
4. **修复指导**: 失败项必须提供修复建议
5. **阻断分级**: 区分阻断问题和警告
