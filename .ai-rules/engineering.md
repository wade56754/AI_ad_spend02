# 工程规范

> 本文件是 AI 编码的工程约束，所有规则引用 `docs/sot/MASTER.md`，不重复定义口径。

---

## 1. 角色与权限

**引用**: [MASTER.md §2.4 角色定义](../docs/sot/MASTER.md)

### 1.1 合法角色（7个）

```python
VALID_ROLES = [
    "ceo",             # 老板
    "project_owner",   # 项目负责人
    "finance",         # 财务
    "supervisor",      # 主管
    "pitcher",         # 投手
    "account_manager", # 户管
    "admin"            # 管理员
]
```

### 1.2 数据域隔离

| 角色 | 数据域 | 引用 |
|------|-------|------|
| pitcher | 只能看自己账户 | R-PERM-002 |
| project_owner | 只能看自己项目 | R-PERM-001 |
| supervisor | 可跨团队 | R-PERM-003 |
| ceo | 全局 | R-PERM-004 |

---

## 2. 状态机

**引用**: [MASTER.md §B.3 状态机](../docs/sot/MASTER.md)

### 2.1 日报状态机（SM-1）

```
draft → submitted → approved → confirmed → locked
                  ↘ returned ↗
                  ↘ voided
```

- 终态: `locked`, `voided`
- 开发前必查: 状态转换是否符合SM-1

### 2.2 差异单状态机（SM-2）

```
created → pending → resolved → closed
```

- 终态: `closed`

### 2.3 月结状态机（SM-3）

```
open → locked
```

- 终态: `locked`
- locked后数据不可修改

---

## 3. 财务公式

**引用**: [MASTER.md §B.2 规则](../docs/sot/MASTER.md)

### 3.1 成本计算

| 规则ID | 公式 |
|--------|------|
| R-COST-001 | `platform_spend = ad_spend`（不含手续费） |
| R-COST-002 | `total_cost = ad_spend + service_fee` |
| R-COST-003 | `available_funds = opening_balance + Σtopup - Σad_spend` |

### 3.2 对账公式

| 规则ID | 公式 |
|--------|------|
| R-RECON-001 | `prepaid_balance = client_payment - fulfilled_revenue` |
| R-RECON-002 | `opening_balance + Σtopup - Σad_spend = current_balance` |

### 3.3 红冲规则

| 规则ID | 要求 |
|--------|------|
| R-REV-001 | 红冲适用范围：账本流水、进粉确认、平台消耗 |
| R-REV-002 | 原记录不可UPDATE/DELETE |
| R-REV-003 | 红冲记录必须有ref_id |
| R-REV-004 | 红冲记录必须有reason |

---

## 4. 代码规范

### 4.1 后端规范

```python
# Pydantic v2 写法
from pydantic import BaseModel, ConfigDict

class MySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    def to_dict(self):
        return self.model_dump()  # 不用 .dict()
```

```python
# API响应格式
from backend.core.response import success_response, BusinessError

# 成功
return success_response(data={"id": 1}, message="操作成功")

# 错误
raise BusinessError(
    code=BusinessErrorCodes.INVALID_STATE_TRANSITION,
    message="状态转换非法"
)
```

### 4.2 前端规范

```typescript
// TypeScript严格模式，禁止any
// ❌ 错误
const data: any = response.data;

// ✅ 正确
interface UserData { id: number; name: string; }
const data: UserData = response.data;
```

```typescript
// 使用 apiFetch，不直接调用 fetch
import { apiFetch } from '@/lib/api';

const data = await apiFetch('/api/users');
```

---

## 5. 禁止行为

| ID | 禁止行为 | 正确做法 |
|----|---------|---------|
| F-001 | 自定义错误码 | 使用 ERROR_CODES_SOT.md |
| F-002 | 发明新状态 | 使用 STATE_MACHINE.md |
| F-003 | 直接修改 balance | 通过 ledger_entries 记录 |
| F-004 | 绕过 BFF 直连数据库 | 使用 apiFetch |
| F-005 | 使用旧角色名 | 仅用7个标准角色 |
| F-006 | UPDATE/DELETE账本记录 | 只能追加+红冲 |

---

## 6. 开发检查清单

### 6.1 开发前

```markdown
[ ] 查 docs/sot/INDEX.md 找到对应规格章节
[ ] 确认状态机是否符合
[ ] 确认公式是否正确
[ ] 确认权限是否符合数据域
```

### 6.2 开发后

```markdown
[ ] 权限：投手只能操作自己账户
[ ] 权限：项目负责人只能操作自己项目
[ ] 状态机：状态流转符合SM-*
[ ] 金额：可用资金公式含opening_balance
[ ] 金额：平台消耗不含手续费
[ ] 锁定：locked状态数据不可修改
[ ] 红冲：有ref_id和reason
[ ] Phase 1：只提示不阻断
```

---

## 7. 引用文档

| 文档 | 路径 | 用途 |
|------|------|------|
| MASTER.md | docs/sot/MASTER.md | 规格总纲 |
| INDEX.md | docs/sot/INDEX.md | 模块映射 |
| STATE_MACHINE.md | docs/sot/STATE_MACHINE.md | 状态机 |
| DATA_SCHEMA.md | docs/sot/DATA_SCHEMA.md | 数据模型 |
| API_SOT.md | docs/sot/API_SOT.md | API规格 |
| ERROR_CODES_SOT.md | docs/sot/ERROR_CODES_SOT.md | 错误码 |

---

**生效日期**: 2025-12-27
**版本**: v1.0
