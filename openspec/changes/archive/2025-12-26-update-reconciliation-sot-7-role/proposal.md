# Change: 升级 RECONCILIATION_SOT.md 到 7 角色体系

> **Change ID**: update-reconciliation-sot-7-role
> **版本升级**: v1.0 → v2.0
> **对齐基准**: MASTER.md v4.4 §2.4

---

## Why

RECONCILIATION_SOT.md v1.0 使用过时的 5 角色体系（admin, finance, data_operator, account_manager, media_buyer），与当前系统标准的 7 角色体系不一致。根据 MASTER.md v4.4 §2.4，系统统一使用 7 角色：

| 新角色 | 中文名 | 原角色映射 |
|--------|--------|-----------|
| ceo | 老板 | 无对应 (新增) |
| project_owner | 项目负责人 | 无对应 (新增) |
| finance | 财务 | finance (保留) |
| supervisor | 主管 | 无对应 (新增) |
| pitcher | 投手 | media_buyer (重命名) |
| account_manager | 户管 | account_manager (保留) |
| admin | 管理员 | admin (保留) |

**被移除角色**: `data_operator`（职责合并到 `finance` 和 `account_manager`）

---

## What Changes

### 1. 角色映射更新

| 文档章节 | 变更内容 |
|---------|---------|
| §1.1 文档职责 | 更新角色引用 |
| §4.2 流程角色权限 | `data_operator` → `finance/account_manager` |
| §12.1 角色权限矩阵 | 完整重写为 7 角色矩阵 |
| §12.2 RLS 策略引用 | 更新角色判断 SQL |

### 2. 权限矩阵变更 **BREAKING**

**旧矩阵** (5 角色):
```
| 操作 | admin | finance | data_operator | account_manager | media_buyer |
```

**新矩阵** (7 角色):
```
| 操作 | ceo | project_owner | finance | supervisor | pitcher | account_manager | admin |
```

### 3. 具体权限调整

| 操作 | 原权限 | 新权限 |
|-----|-------|-------|
| 创建对账批次 | data_operator, finance, admin | finance, account_manager, admin |
| 查看对账批次 | admin, finance, data_operator, account_manager | ceo(全局), project_owner(自己项目), finance(全局), supervisor(团队), account_manager(全局), admin(全局) |
| 提交审核 | data_operator, finance, admin | finance, account_manager, admin |
| 审批/拒绝 | finance, admin | finance, admin |
| 完成对账 | finance, admin | finance, admin |

### 4. 状态机保持不变

5 状态流转规则不变：`draft → pending_review → approved → completed` with `needs_adjustment` branch

---

## Impact

### 受影响的 SoT 文档
- `docs/2.sot/RECONCILIATION_SOT.md` - 主要变更
- `docs/2.sot/AUTH_SPEC.md` v2.0 - 确认 7 角色已定义（无需变更）
- `docs/4.architecture/RECONCILIATION_CONTROL_CENTER_ARCHITECTURE.md` v2.1 - 已对齐

### 受影响的代码
- `backend/core/permissions.py` - 确认权限检查使用新角色
- `backend/routers/reconciliations.py` - 确认路由权限装饰器
- RLS 策略 SQL (若已启用)

### 不受影响
- 数据库表结构
- API 端点定义
- 状态机流转规则
- 差异计算逻辑
- 账本影响规则

---

## Migration

1. 本变更为 **文档规范变更**，不涉及数据迁移
2. 代码层权限检查需验证是否已对齐 7 角色
3. 建议执行回归测试验证权限控制

---

## Approval Checklist

- [ ] 确认 7 角色定义与 MASTER.md v4.4 一致
- [ ] 确认权限矩阵覆盖所有对账操作
- [ ] 确认 RLS 示例 SQL 可执行
- [ ] 确认与 RECONCILIATION_CONTROL_CENTER_ARCHITECTURE.md v2.1 一致
