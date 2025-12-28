# RECONCILIATION_SOT.md Spec Delta

> **变更类型**: MODIFIED
> **目标版本**: v2.0
> **对齐基准**: MASTER.md v4.4 §2.4

---

## MODIFIED Requirements

### Requirement: 角色权限定义

系统 SHALL 使用 MASTER.md v4.4 定义的 7 角色体系进行权限控制，取代原有 5 角色体系。

**7 角色定义**:
| 角色ID | 中文名 | 对账模块职责 |
|--------|-------|-------------|
| ceo | 老板 | 查看对账概览（只读） |
| project_owner | 项目负责人 | 查看自己项目的对账结果 |
| finance | 财务 | 创建/审批/完成对账，处理差异 |
| supervisor | 主管 | 查看团队对账状态 |
| pitcher | 投手 | 无对账模块权限 |
| account_manager | 户管 | 创建对账批次，录入快照 |
| admin | 管理员 | 全部权限 |

#### Scenario: 角色映射验证
- **WHEN** 系统检查对账模块权限
- **THEN** 仅使用以上 7 个角色ID
- **AND** 拒绝使用已废弃角色（data_operator, media_buyer）

---

### Requirement: 对账操作权限矩阵

系统 SHALL 按以下矩阵控制对账模块操作权限。

| 操作 | ceo | project_owner | finance | supervisor | pitcher | account_manager | admin |
|-----|-----|--------------|---------|------------|---------|-----------------|-------|
| 查看对账批次 | ✅全局 | ✅自己项目 | ✅全局 | ✅团队 | ❌ | ✅全局 | ✅全局 |
| 创建对账批次 | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ |
| 编辑草稿 | ❌ | ❌ | ✅ | ❌ | ❌ | ✅自己创建 | ✅ |
| 提交审核 | ❌ | ❌ | ✅ | ❌ | ❌ | ✅自己创建 | ✅ |
| 审批/拒绝 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 创建调整 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 执行调整 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 完成对账 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 删除批次 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅仅draft |

#### Scenario: finance 创建并审批对账
- **WHEN** finance 用户创建对账批次
- **THEN** 批次状态为 draft
- **WHEN** finance 用户提交审核
- **THEN** 批次状态变为 pending_review
- **WHEN** 另一个 finance/admin 用户审批
- **THEN** 批次状态变为 approved
- **AND** approved_by != created_by (SOD 原则)

#### Scenario: account_manager 创建但无法审批
- **WHEN** account_manager 用户创建对账批次
- **THEN** 批次状态为 draft
- **WHEN** account_manager 用户提交审核
- **THEN** 批次状态变为 pending_review
- **WHEN** account_manager 用户尝试审批
- **THEN** 返回 AUTH_500 权限不足错误

#### Scenario: project_owner 仅查看自己项目
- **WHEN** project_owner 用户查询对账批次列表
- **THEN** 仅返回与其负责项目关联的对账批次
- **AND** 无法创建/编辑/审批对账批次

---

### Requirement: RLS 策略角色判断

系统 SHALL 在 RLS 策略中使用 7 角色进行权限判断。

**示例 SQL**:
```sql
-- reconciliation_batches 查询策略 (7 角色版本)
CREATE POLICY policy_reconciliation_batches_select_role
ON reconciliation_batches FOR SELECT
USING (
    -- admin/finance 可查看所有
    fn_current_user_role() IN ('admin', 'finance', 'account_manager')
    OR (
        -- ceo 可查看所有
        fn_current_user_role() = 'ceo'
    )
    OR (
        -- project_owner 仅查看自己项目关联的批次
        fn_current_user_role() = 'project_owner'
        AND EXISTS (
            SELECT 1 FROM projects p
            WHERE p.pm_user_id = fn_current_user_id()
            AND p.supplier_id = reconciliation_batches.supplier_id
        )
    )
    OR (
        -- supervisor 仅查看团队关联的批次
        fn_current_user_role() = 'supervisor'
        AND EXISTS (
            SELECT 1 FROM users u
            WHERE u.supervisor_id = fn_current_user_id()
            AND u.id = reconciliation_batches.created_by
        )
    )
);
```

#### Scenario: RLS 策略生效
- **WHEN** 用户查询对账批次
- **THEN** 根据用户角色自动过滤返回结果
- **AND** pitcher 角色返回空结果

---

## REMOVED Requirements

### Requirement: data_operator 角色权限

**Reason**: `data_operator` 角色已被废弃，其职责已合并到 `finance` 和 `account_manager` 角色。

**Migration**:
- 原 `data_operator` 用户应被重新分配为 `finance` 或 `account_manager` 角色
- 历史审计日志中的 `data_operator` 引用保留不变

### Requirement: media_buyer 角色权限

**Reason**: `media_buyer` 角色已重命名为 `pitcher`，且对账模块中无权限。

**Migration**:
- 原 `media_buyer` 用户应被重新分配为 `pitcher` 角色
- `pitcher` 角色在对账模块中无任何权限
