# Spec Delta: Reconciliation Capability

**Change-ID**: `add-reconciliation-control-center`
**Capability**: `reconciliation`
**Affected SoT**: DATA_SCHEMA.md, STATE_MACHINE.md, BUSINESS_RULES.md, ERROR_CODES_SOT.md

---

## ADDED Requirements

### Requirement: Balance Snapshot Management

系统 SHALL 支持广告账户余额/押款的每日快照记录。

#### Scenario: Create single snapshot
- **GIVEN** 用户角色为 finance 或 account_manager
- **WHEN** 用户为某账户创建指定日期的余额快照
- **AND** 该账户该日期不存在快照
- **THEN** 系统创建快照记录，包含 balance、deposit、remaining_balance
- **AND** 记录 source='manual', created_by=当前用户

#### Scenario: Batch import snapshots
- **GIVEN** 用户角色为 finance 或 account_manager
- **WHEN** 用户上传包含多个账户多个日期的快照数据
- **THEN** 系统批量创建快照记录
- **AND** 对于已存在的 (account_id, date) 组合，返回冲突错误
- **AND** 返回导入成功数量和失败列表

#### Scenario: Duplicate snapshot rejected
- **GIVEN** 某账户某日期已存在快照
- **WHEN** 用户尝试创建相同 (account_id, date) 的快照
- **THEN** 系统返回 HTTP 409 Conflict
- **AND** 错误码 REC-002

#### Scenario: Query snapshot history
- **GIVEN** 某账户存在多个日期的快照
- **WHEN** 用户查询该账户的快照历史
- **THEN** 系统返回按日期排序的快照列表
- **AND** 支持日期范围过滤

---

### Requirement: Conservation Formula Validation

系统 SHALL 按照守恒公式校验对账数据一致性。

#### Scenario: Conservation check pass
- **GIVEN** 对账期间 [T1, T2] 内所有账户数据完整
- **AND** 守恒公式差异 ≤ ¥1.00
- **WHEN** 系统执行对账校验
- **THEN** 对账批次状态标记为 approved
- **AND** 不生成差异单

#### Scenario: Conservation check fail - yellow alert
- **GIVEN** 对账期间某账户守恒公式差异 > ¥1.00 且 ≤ ¥100.00
- **WHEN** 系统执行对账校验
- **THEN** 生成 issue_type='conservation_failed' 的黄灯差异单
- **AND** sla_deadline = created_at + 5 工作日

#### Scenario: Conservation check fail - red alert
- **GIVEN** 对账期间某账户守恒公式差异 > ¥100.00
- **WHEN** 系统执行对账校验
- **THEN** 生成 issue_type='conservation_failed' 的红灯差异单
- **AND** sla_deadline = created_at + 2 工作日
- **AND** 记录 expected_amount, actual_amount, difference_amount

#### Scenario: Snapshot missing during reconciliation
- **GIVEN** 对账期间某账户缺少余额快照
- **WHEN** 系统执行对账校验
- **THEN** 生成 issue_type='snapshot_missing' 的差异单
- **AND** 自动分配给户管 (account_manager)

---

### Requirement: Reconciliation Issue Lifecycle

系统 SHALL 按照状态机管理差异单生命周期。

#### Scenario: Issue auto-created
- **GIVEN** 对账校验发现差异
- **WHEN** 差异超过阈值
- **THEN** 系统自动创建差异单，status='open'
- **AND** 记录 issue_date, issue_type, 差异金额

#### Scenario: Issue assigned
- **GIVEN** 差异单状态为 open
- **AND** 用户角色为 finance 或 admin
- **WHEN** 用户分配责任人
- **THEN** 差异单状态变为 assigned
- **AND** 记录 assigned_to, assigned_at
- **AND** 记录审计日志

#### Scenario: Issue investigation started
- **GIVEN** 差异单状态为 assigned
- **AND** 当前用户为 assigned_to
- **WHEN** 用户开始调查
- **THEN** 差异单状态变为 investigating

#### Scenario: Issue resolved
- **GIVEN** 差异单状态为 investigating
- **AND** 当前用户为 assigned_to
- **WHEN** 用户提交处理结论
- **AND** 填写 resolution_type 和 resolution_note
- **THEN** 差异单状态变为 resolved
- **AND** 记录 resolved_at, resolved_by

#### Scenario: Issue closed
- **GIVEN** 差异单状态为 resolved
- **AND** 用户角色为 finance 或 admin
- **WHEN** 用户确认关闭
- **THEN** 差异单状态变为 closed（终态）
- **AND** 记录审计日志

#### Scenario: Invalid state transition rejected
- **GIVEN** 差异单状态为 open
- **WHEN** 用户尝试直接关闭
- **THEN** 系统返回 HTTP 400
- **AND** 错误码 REC-003

#### Scenario: Unauthorized operation rejected
- **GIVEN** 差异单已分配给用户 A
- **AND** 当前用户为用户 B（非 assigned_to）
- **WHEN** 用户 B 尝试处理差异单
- **THEN** 系统返回 HTTP 403
- **AND** 错误码 REC-004

---

### Requirement: SLA Monitoring

系统 SHALL 监控差异单处理时效。

#### Scenario: SLA deadline calculation
- **GIVEN** 差异单创建时间为 T
- **AND** 差异等级为红灯
- **WHEN** 系统计算 SLA 截止时间
- **THEN** sla_deadline = T + 2 个工作日（排除周末和法定节假日）

#### Scenario: SLA breach detection
- **GIVEN** 差异单 sla_deadline 已过
- **AND** 差异单状态不在 ['resolved', 'closed']
- **WHEN** 系统执行 SLA 检查（每小时）
- **THEN** 标记 sla_breached = true
- **AND** 触发上报通知（CEO 角色可见）

#### Scenario: Query SLA status
- **GIVEN** 用户查询差异单列表
- **WHEN** 筛选条件包含 sla_status
- **THEN** 支持筛选：正常(within)、临近(warning)、超时(breached)

---

## MODIFIED Requirements

### Requirement: Ad Account Extended Fields

修改现有 ad_accounts 表，新增押款相关字段。

#### Scenario: Deposit field access
- **GIVEN** ad_accounts 表包含 deposit 字段
- **WHEN** 查询账户信息
- **THEN** 返回 deposit 金额（默认 0.00）

#### Scenario: Deposit update with audit
- **GIVEN** 用户角色为 finance 或 account_manager
- **WHEN** 用户更新账户押款金额
- **AND** 押款变化 ≥ ¥1000.00
- **THEN** 需要财务审批
- **AND** 记录押款变化到 ledger_entries（entry_type='DEPOSIT_CHANGE'）

---

## Error Codes Reference

| 错误码 | HTTP | 场景 |
|--------|------|------|
| REC-001 | 400 | 守恒校验失败 |
| REC-002 | 409 | 快照重复 |
| REC-003 | 400 | 状态流转非法 |
| REC-004 | 403 | 操作权限不足 |
| REC-005 | 400 | SLA 已超时 |
| REC-006 | 400 | 差异单未分配 |

---

**END OF SPEC**
