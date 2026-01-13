# AI 代码工厂约束规则

> 自动生成于 2026-01-14 05:04
> 基于 SoT: MASTER.md v4.8, STATE_MACHINE.md v2.8

---

## 必读上下文

**在每次对话开始时，请先阅读以下文件:**

1. `memory-bank/progress.md` - 当前进度
2. `memory-bank/current-task.md` - 当前任务
3. `memory-bank/decisions.md` - 已做决策

这些文件包含项目的实时状态，帮助你了解当前工作进展。

---

## TDD 强制要求

本项目强制使用测试驱动开发 (TDD)。

### 铁律

**NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST**

### Red-Green-Refactor 循环

1. **RED**: 先写一个失败的测试
2. **验证 RED**: 运行测试，确认失败
3. **GREEN**: 写最小代码使测试通过
4. **验证 GREEN**: 运行测试，确认通过
5. **REFACTOR**: 清理代码，保持测试通过

### 禁止行为

- ❌ 先写实现，后补测试
- ❌ 跳过测试直接实现
- ❌ 实现超出测试要求的功能

---

## SoT 白名单

### 允许的角色 (4 个)

```
account_manager, admin, finance, media_buyer
```

### 允许的日报状态 (8 个)

```
final_confirmed, final_locked, final_pending, raw_submitted, trend_flagged, trend_ok, trend_pending, trend_resolved
```

状态转换图:
```
raw_submitted → trend_pending → trend_ok/trend_flagged
    → trend_resolved → final_pending → final_confirmed → final_locked
```

---

## 禁止清单

**违反以下规则的代码将被 pre-commit hook 阻断！**

### 禁止的角色

```
accountant, data_clerk, data_operator, manager, operator, super_admin, supervisor, trader
```

### 禁止的日报状态

```
approved, draft, pending, rejected
```

### 禁止的操作

| 操作 | 原因 | 正确做法 |
|------|------|----------|
| 直接修改 `balance` 字段 | 违反账本规则 | 通过 `ledger_entries` 记录 |
| 自定义错误码 | 缺乏一致性 | 使用 `ERROR_CODES_SOT.md` |
| 绕过认证 | 安全风险 | 使用 Supabase Auth |
| 硬编码密钥 | 安全风险 | 使用环境变量 |

### 禁止的代码模式

```python
# ❌ 直接修改余额
ad_account.balance -= 100

# ❌ 使用废弃角色
user.role = "supervisor"

# ❌ 使用废弃状态
report.status = "draft"

# ❌ 自定义错误码
raise HTTPException(400, "Invalid")
```

---

## 完成任务后

1. **更新进度**: 修改 `memory-bank/progress.md`
2. **记录决策**: 重要决策写入 `memory-bank/decisions.md`
3. **提交代码**: 运行 `git add . && git commit` 触发验证
4. **验证通过**: pre-commit hook 会自动检查 SoT 合规

---

## 快捷命令

```bash
# 生成/更新规则文件
python -m agents.skills.code_factory.hooks.rules_generator

# 运行 pre-commit 检查
python -m agents.skills.code_factory.hooks.pre_commit

# 快速验证单个文件
python -m agents.skills.code_factory.hooks.fast_verify <file>
```

---

## 文档参考

| 文档 | 路径 | 说明 |
|------|------|------|
| 架构宪法 | `docs/sot/MASTER.md` | 最高优先级 |
| 状态机 | `docs/sot/STATE_MACHINE.md` | 8 状态定义 |
| 数据模型 | `docs/sot/DATA_SCHEMA.md` | 表结构 |
| 错误码 | `docs/sot/ERROR_CODES_SOT.md` | 错误码注册表 |
| API 契约 | `docs/sot/API_SOT.md` | API 定义 |
