# BR-RECON：对账管理业务规则

**版本**: v2.0
**最后更新**: 2025-01-20
**负责模块**: 对账批次管理 (reconciliation_batches)、对账明细 (reconciliation_details)、调账记录 (reconciliation_adjustments)

---

## 规则总览

| 规则编号 | 规则名称 | 优先级 | 涉及角色 |
|---------|---------|--------|---------|
| BR-RECON-001 | 对账批次创建约束 | P0 | finance |
| BR-RECON-003 | 差异处理与调账 | P0 | finance |

---

## BR-RECON-001：对账批次创建约束

### 业务场景

财务人员定期（通常每月）发起对账批次，系统自动比对"账户余额"与"充值流水"是否一致。

### 详细约束

#### 1.1 权限约束

- **Rule**: 仅 `finance` 角色可以创建对账批次
- **Error Code**: `AUTH_500` (PERMISSION_DENIED)
- **Schema Reference**: `DATA_SCHEMA.md → reconciliation_batches.created_by → users.id`

```python
# backend/routers/reconciliation.py
@router.post("/batches", response_model=ReconciliationBatchResponse)
async def create_batch(
    payload: CreateReconciliationBatchRequest,
    user=Depends(get_current_user),
    service: ReconciliationService = Depends()
):
    # 角色验证
    user_role = user.get("role")
    if user_role != "finance":
        raise AuthorizationException(
            code=AuthErrorCodes.PERMISSION_DENIED.code,  # AUTH_500
            message="仅财务人员可以创建对账批次"
        )

    batch = service.create_batch(payload, user_id=user.get("user", {}).id)
    return envelope_response(data=batch)
```

#### 1.2 必填字段约束

- **period_start**: 对账起始日期（UTC日期）
- **period_end**: 对账结束日期（UTC日期）
- **Constraint**: `period_end >= period_start`
- **Error Code**: `BIZ_200` (INVALID_INPUT)

```python
# backend/services/reconciliation_service.py
def create_batch(self, payload: CreateReconciliationBatchRequest, user_id: UUID):
    # 日期范围验证
    if payload.period_end < payload.period_start:
        raise ValidationException(
            code=BusinessErrorCodes.INVALID_INPUT.code,  # BIZ_200
            message="对账结束日期不能早于起始日期"
        )

    # 检查是否已有重叠的对账批次
    overlapping = self.db.query(ReconciliationBatch).filter(
        ReconciliationBatch.period_start <= payload.period_end,
        ReconciliationBatch.period_end >= payload.period_start,
        ReconciliationBatch.status != "cancelled"
    ).first()

    if overlapping:
        raise BusinessRuleException(
            code=BusinessErrorCodes.DUPLICATE_ENTRY.code,  # BIZ_203
            message=f"该时间段已存在对账批次: {overlapping.batch_code}"
        )

    # 创建批次
    batch = ReconciliationBatch(
        batch_code=generate_batch_code(),
        period_start=payload.period_start,
        period_end=payload.period_end,
        status="pending",  # 初始状态
        created_by=user_id
    )

    self.db.add(batch)
    self.db.flush()

    # 审计日志
    audit_log(
        operation="CREATE_RECONCILIATION_BATCH",
        resource_type="reconciliation_batch",
        resource_id=batch.id,
        user_id=user_id,
        details={"batch_code": batch.batch_code, "period": f"{payload.period_start} ~ {payload.period_end}"}
    )

    return batch
```

#### 1.3 状态初始化

- **初始状态**: `pending`（待处理）
- **状态机**: `pending → processing → review → completed / cancelled`
- **State Machine Reference**: `STATE_MACHINE.md → reconciliation_batch`

### 错误码映射

| 场景 | 错误码 | HTTP状态码 |
|-----|--------|-----------|
| 非财务人员创建 | AUTH_500 | 403 |
| 日期范围无效 | BIZ_200 | 400 |
| 时间段重叠 | BIZ_203 | 409 |

### Test Intent

```gherkin
Given 用户角色为 "finance"
When 创建对账批次，period_start="2025-01-01", period_end="2025-01-31"
Then 批次创建成功，batch_code="RECON-202501-0001"，状态为 "pending"

Given 用户角色为 "media_buyer"
When 尝试创建对账批次
Then 返回 403，错误码 AUTH_500

Given 已存在批次 period_start="2025-01-15", period_end="2025-01-31"
When 创建新批次 period_start="2025-01-20", period_end="2025-02-10"
Then 返回 409，错误码 BIZ_203（时间段重叠）
```

---

## BR-RECON-003：差异处理与调账

### 业务场景

对账批次完成后，若发现"系统余额"与"渠道余额"不一致，财务人员必须创建**调账记录**（reconciliation_adjustments），说明差异原因并调整账目，才能关闭批次。

### 详细约束

#### 3.1 差异检测

- **Rule**: 系统自动计算 `total_difference = system_balance - channel_balance`
- **Schema**: `DATA_SCHEMA.md → reconciliation_details.total_difference`

```python
# backend/services/reconciliation_service.py
def process_batch(self, batch_id: UUID, user_id: UUID):
    batch = self.get_batch_by_id(batch_id)

    # 状态验证
    ensure_transition_allowed(
        resource_type="reconciliation_batch",
        current_status=batch.status,
        target_status="processing"
    )

    batch.status = "processing"

    # 查询该批次的所有明细
    details = self.db.query(ReconciliationDetail).filter(
        ReconciliationDetail.batch_id == batch_id
    ).all()

    for detail in details:
        # 计算差异
        detail.total_difference = detail.system_balance - detail.channel_balance

        if abs(detail.total_difference) > Decimal("0.01"):
            detail.has_discrepancy = True
        else:
            detail.has_discrepancy = False

    batch.status = "review"
    audit_log(operation="PROCESS_BATCH", resource_id=batch_id, user_id=user_id)
```

#### 3.2 关闭批次前的调账强制约束

- **Rule**: 若存在 `has_discrepancy=True` 的明细，必须为每个差异创建 `reconciliation_adjustments` 记录
- **Error Code**: `BIZ_202` (INVALID_OPERATION)

```python
def close_batch(self, batch_id: UUID, user_id: UUID):
    batch = self.get_batch_by_id(batch_id)

    # 状态验证
    ensure_transition_allowed(
        resource_type="reconciliation_batch",
        current_status=batch.status,
        target_status="completed"
    )

    # 检查是否有未处理的差异
    unresolved_details = self.db.query(ReconciliationDetail).filter(
        ReconciliationDetail.batch_id == batch_id,
        ReconciliationDetail.has_discrepancy == True
    ).all()

    for detail in unresolved_details:
        # 检查是否已创建调账记录
        adjustment_count = self.db.query(ReconciliationAdjustment).filter(
            ReconciliationAdjustment.detail_id == detail.id
        ).count()

        if adjustment_count == 0:
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,  # BIZ_202
                message=f"对账明细 {detail.id} 存在差异（{detail.total_difference}），必须先创建调账记录"
            )

    # 关闭批次
    batch.status = "completed"
    batch.completed_at = datetime.now(timezone.utc)

    audit_log(
        operation="CLOSE_RECONCILIATION_BATCH",
        resource_id=batch_id,
        user_id=user_id,
        details={"total_details": len(unresolved_details)}
    )
```

#### 3.3 调账记录必填字段

- **adjustment_amount**: 调整金额（DECIMAL(15,2)）
- **adjustment_reason**: 调整原因（枚举值）
- **adjustment_type**: 调整类型（`system_error`, `channel_delay`, `manual_correction`）
- **Schema**: `DATA_SCHEMA.md → reconciliation_adjustments`

```python
def create_adjustment(
    self,
    detail_id: UUID,
    payload: CreateAdjustmentRequest,
    user_id: UUID
):
    detail = self.db.query(ReconciliationDetail).filter_by(id=detail_id).first()
    if not detail:
        raise NotFoundException(code="BIZ_404", message="对账明细不存在")

    if not detail.has_discrepancy:
        raise BusinessRuleException(
            code=BusinessErrorCodes.INVALID_OPERATION.code,
            message="该明细无差异，无需调账"
        )

    # 创建调账记录
    adjustment = ReconciliationAdjustment(
        detail_id=detail_id,
        adjustment_amount=payload.adjustment_amount,
        adjustment_type=payload.adjustment_type,
        adjustment_reason=payload.adjustment_reason,
        created_by=user_id
    )

    self.db.add(adjustment)

    # 更新明细的调账状态
    detail.adjustment_status = "adjusted"

    audit_log(
        operation="CREATE_ADJUSTMENT",
        resource_type="reconciliation_adjustment",
        resource_id=adjustment.id,
        user_id=user_id,
        details={
            "detail_id": str(detail_id),
            "amount": str(payload.adjustment_amount),
            "type": payload.adjustment_type
        }
    )

    return adjustment
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 |
|-----|--------|-----------|
| 存在未调账差异 | BIZ_202 | 400 |
| 对账明细不存在 | BIZ_404 | 404 |
| 状态流转非法 | STATE_301 | 400 |

### Test Intent

```gherkin
Given 对账批次 batch_id="xxx"，状态为 "review"
  And 存在明细 detail_id="yyy"，has_discrepancy=True，total_difference=100.50
  And 该明细无调账记录
When 调用 close_batch(batch_id)
Then 返回 400，错误码 BIZ_202，message包含 "必须先创建调账记录"

Given 对账批次 batch_id="xxx"，状态为 "review"
  And 存在明细 detail_id="yyy"，has_discrepancy=True
  And 已创建调账记录 adjustment_amount=100.50, adjustment_type="system_error"
When 调用 close_batch(batch_id)
Then 批次状态更新为 "completed"，completed_at 为当前UTC时间

Given 对账明细 detail_id="yyy"，has_discrepancy=False
When 创建调账记录
Then 返回 400，错误码 BIZ_202，message="该明细无差异，无需调账"
```

---

## 参考文档

- **数据模型**: `DATA_SCHEMA.md → reconciliation_batches, reconciliation_details, reconciliation_adjustments`
- **状态机**: `STATE_MACHINE.md → reconciliation_batch`
- **错误码**: `ERROR_CODES.md → AUTH_500, BIZ_200, BIZ_202, BIZ_203, BIZ_404, STATE_301`
- **核心开发手册**: `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md → 第5章 财务与对账模块`
