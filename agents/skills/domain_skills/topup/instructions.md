# 充值管理技能 - 核心指令

> **SoT 引用**: STATE_MACHINE.md v2.8, DATA_SCHEMA.md v5.7

## 充值 7 状态机

```
draft → pending_review → finance_approve → paid → completed
  ↓           ↓                ↓
cancelled   rejected        rejected
```

## 状态说明

| 状态 | 说明 | 可操作人 |
|------|------|---------|
| `draft` | 草稿，可编辑 | pitcher |
| `pending_review` | 待审核 | account_manager |
| `finance_approve` | 财务审批中 | finance |
| `paid` | 已转账 | finance |
| `completed` | 已完成 | 系统 |
| `rejected` | 已拒绝 | account_manager, finance |
| `cancelled` | 已取消 | pitcher (仅 draft 状态可取消) |

## 审批链 (PRD v2.2)

```
投手申请 → 户管收集 → 财务审批 → 转账
```

**重要**: 日常充值不需要老板逐笔审批

## 关键约束

1. **cancelled 只能从 draft 转换**
2. **rejected 可从 pending_review 或 finance_approve 转换**
3. **禁止 F-009**: 禁止充值流程强制添加老板逐笔审批

## 代码模板

### 状态枚举 (Python)

```python
# SoT: STATE_MACHINE.md#topup
class TopupStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    FINANCE_APPROVE = "finance_approve"
    PAID = "paid"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
```

### 状态转换验证

```python
# SoT: STATE_MACHINE.md#topup
TOPUP_TRANSITIONS = {
    "draft": ["pending_review", "cancelled"],
    "pending_review": ["finance_approve", "rejected"],
    "finance_approve": ["paid", "rejected"],
    "paid": ["completed"],
    "completed": [],
    "rejected": [],
    "cancelled": [],
}

def can_transition(current: str, target: str) -> bool:
    return target in TOPUP_TRANSITIONS.get(current, [])
```
