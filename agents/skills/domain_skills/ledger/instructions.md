# 账本管理技能 - 核心指令

> **SoT 引用**: DATA_SCHEMA.md v5.7 §3.4.4, MASTER.md v4.7

## 核心原则

**F-003 禁止**: 禁止直接修改 balance，必须通过 ledger_entries 记录

```python
# ❌ 错误做法
ad_account.balance -= 100

# ✅ 正确做法
ledger_entry = LedgerEntry(
    account_id=ad_account.id,
    amount=-100,
    entry_type="debit",
    description="广告消耗"
)
db.add(ledger_entry)
# balance 通过触发器或计算字段更新
```

## 账本结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `account_id` | UUID | 关联账户 |
| `entry_type` | String | debit/credit |
| `amount` | Decimal | 金额 (正数) |
| `balance_after` | Decimal | 操作后余额 |
| `description` | String | 描述 |
| `created_at` | DateTime | 创建时间 |

## 余额计算公式

```python
# SoT: DATA_SCHEMA.md#3.4.4
balance = Σ充值 - Σ消耗
        = Σ(credit entries) - Σ(debit entries)
```

## 押款定义 (PRD v5.1)

```python
# SoT: PRD v5.1
押款 = 代理商未消耗余额 = Σ历史充值 - Σ历史消耗
```

## 代码模板

### 账本条目模型 (Python)

```python
# SoT: DATA_SCHEMA.md#ledger_entries
class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    
    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("ad_accounts.id"))
    entry_type: Mapped[str]  # 'debit' | 'credit'
    amount: Mapped[Decimal]
    balance_after: Mapped[Decimal]
    description: Mapped[str]
    created_at: Mapped[datetime]
```

### 记账服务

```python
# SoT: BUSINESS_RULES.md#BR-FIN
class LedgerService:
    def record_entry(
        self,
        account_id: UUID,
        amount: Decimal,
        entry_type: Literal["debit", "credit"],
        description: str
    ) -> LedgerEntry:
        """记录一笔账本条目"""
        # 获取当前余额
        current_balance = self._get_current_balance(account_id)
        
        # 计算新余额
        if entry_type == "credit":
            new_balance = current_balance + amount
        else:
            new_balance = current_balance - amount
        
        # 创建条目
        entry = LedgerEntry(
            account_id=account_id,
            entry_type=entry_type,
            amount=amount,
            balance_after=new_balance,
            description=description
        )
        
        return entry
```
