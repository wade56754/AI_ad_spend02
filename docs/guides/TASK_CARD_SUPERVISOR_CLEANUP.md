# 任务卡: 清理废弃角色 supervisor

> **任务ID**: TASK-MAINT-001
> **优先级**: P0
> **预估范围**: 97 处引用，24 个文件
> **基准文档**: MASTER.md v4.9 §2.4, PRD v5.1
> **创建日期**: 2026-01-01

---

## 背景

根据 PRD v5.1 和 MASTER.md v4.9，`supervisor` 角色已被废弃，其职责合并到 `project_owner`。

### 废弃角色映射规则

| 废弃角色 | 替代方案 | 说明 |
|---------|---------|------|
| `supervisor` | `project_owner` | PRD v5.1 合并 |
| `data_operator` | `project_owner` 或删除 | 已废弃 |
| `media_buyer` | `pitcher` | 技术层使用业务层角色 |

---

## 影响范围统计

### 按文件分类

| 分类 | 文件数 | 引用数 | 处理方式 |
|------|--------|--------|---------|
| **路由层** | 8 | 34 | 替换 `require_role` 中的角色 |
| **服务层** | 4 | 15 | 替换角色检查 |
| **核心模块** | 4 | 30 | 保留兼容映射，删除业务使用 |
| **Schema** | 1 | 3 | 更新枚举注释 |
| **Model** | 2 | 3 | 更新枚举/注释 |
| **测试** | 4 | 10 | 更新测试用例 |
| **迁移** | 1 | 2 | 保留历史记录 |

---

## 详细文件清单

### 1. 路由层 (优先处理)

#### TASK-MAINT-001-01: `backend/routers/finance_profit.py` (13 处)

```bash
# 定位
grep -n "supervisor" backend/routers/finance_profit.py
```

**处理方式**: 替换 `require_role(["supervisor", ...])` → `require_role(["project_owner", ...])`

**验收标准**:
- □ 无 supervisor 引用
- □ project_owner 拥有相同权限
- □ 单元测试通过

---

#### TASK-MAINT-001-02: `backend/routers/weekly_briefs.py` (5 处)

**处理方式**: 替换 supervisor → project_owner

**验收标准**:
- □ 无 supervisor 引用
- □ 周报权限保持不变

---

#### TASK-MAINT-001-03: `backend/routers/daily_reports.py` (5 处)

**处理方式**: 替换 supervisor → project_owner

**验收标准**:
- □ 无 supervisor 引用
- □ 日报审核权限保持不变

---

#### TASK-MAINT-001-04: `backend/routers/fund.py` (4 处)

**处理方式**: 替换 supervisor → project_owner

**验收标准**:
- □ 无 supervisor 引用
- □ 资金查看权限保持不变

---

#### TASK-MAINT-001-05: `backend/routers/users.py` (3 处)

**处理方式**: 替换 supervisor → project_owner

**验收标准**:
- □ 无 supervisor 引用

---

#### TASK-MAINT-001-06: `backend/routers/ad_spend.py` (2 处)

**处理方式**: 替换 supervisor → project_owner

**验收标准**:
- □ 无 supervisor 引用

---

#### TASK-MAINT-001-07: `backend/routers/topups.py` (1 处)

**状态**: ✅ 已完成 (2026-01-01)

---

#### TASK-MAINT-001-08: `backend/routers/topup.py` (1 处)

**处理方式**: 替换 supervisor → project_owner

**验收标准**:
- □ 无 supervisor 引用

---

### 2. 服务层

#### TASK-MAINT-001-09: `backend/services/fund_service.py` (6 处)

**处理方式**: 替换角色检查

**验收标准**:
- □ 无 supervisor 引用
- □ 资金服务功能正常

---

#### TASK-MAINT-001-10: `backend/services/weekly_brief_service.py` (5 处)

**处理方式**: 替换角色检查

**验收标准**:
- □ 无 supervisor 引用

---

#### TASK-MAINT-001-11: `backend/services/user_service.py` (3 处)

**处理方式**: 替换角色检查

**验收标准**:
- □ 无 supervisor 引用

---

#### TASK-MAINT-001-12: `backend/services/ad_spend_service.py` (1 处)

**处理方式**: 替换角色检查

**验收标准**:
- □ 无 supervisor 引用

---

### 3. 核心模块 (需谨慎处理)

#### TASK-MAINT-001-13: `backend/core/permissions.py` (7 处)

**处理方式**:
- 删除 `supervisor` 作为有效角色的引用
- 保留兼容映射（如 `ROLE_HIERARCHY` 中的映射）

**验收标准**:
- □ supervisor 不再作为有效角色
- □ 向后兼容映射保留
- □ 权限测试通过

---

#### TASK-MAINT-001-14: `backend/core/roles.py` (7 处)

**状态**: ⚠️ 部分完成

**说明**:
- `FORBIDDEN_ROLES` 中的 supervisor 需保留（用于阻止使用）
- `migrate_role()` 中的映射需保留（用于数据迁移）
- 其他业务逻辑中的引用需删除

**验收标准**:
- □ FORBIDDEN_ROLES 保留 supervisor
- □ migrate_role 保留映射
- □ 无业务代码使用 supervisor

---

#### TASK-MAINT-001-15: `backend/core/role_mapping.py` (12 处)

**状态**: ✅ 已完成 (2026-01-01)

**说明**: 向后兼容映射已正确配置

---

#### TASK-MAINT-001-16: `backend/core/state_machine.py` (4 处)

**处理方式**: 替换状态机中的角色引用

**验收标准**:
- □ 状态转换规则使用 project_owner
- □ 状态机测试通过

---

### 4. Schema/Model

#### TASK-MAINT-001-17: `backend/schemas/user.py` (3 处)

**处理方式**: 更新角色枚举注释/文档

**验收标准**:
- □ 枚举值无 supervisor
- □ 文档说明清晰

---

#### TASK-MAINT-001-18: `backend/models/enums.py` (2 处)

**处理方式**:
- 检查 UserRole 枚举
- 删除或注释废弃值

**验收标准**:
- □ UserRole 无 supervisor 值
- □ 数据库兼容

---

#### TASK-MAINT-001-19: `backend/models/core/user.py` (1 处)

**处理方式**: 更新模型注释

**验收标准**:
- □ 模型文档正确

---

### 5. 测试文件

#### TASK-MAINT-001-20: `backend/tests/integration/api/test_b1_topup_api.py` (4 处)

**处理方式**: 更新测试用例中的角色

**验收标准**:
- □ 测试使用 project_owner
- □ 测试通过

---

#### TASK-MAINT-001-21: `backend/tests/integration/api/test_b2_daily_report_api.py` (3 处)

**处理方式**: 更新测试用例中的角色

**验收标准**:
- □ 测试使用 project_owner
- □ 测试通过

---

#### TASK-MAINT-001-22: `backend/tests/integration/api/test_d1_settlement_api.py` (2 处)

**处理方式**: 更新测试用例中的角色

**验收标准**:
- □ 测试使用 project_owner
- □ 测试通过

---

#### TASK-MAINT-001-23: `backend/tests/core/test_permissions_p0.py` (1 处)

**处理方式**: 更新权限测试

**验收标准**:
- □ 测试 project_owner 权限
- □ 测试通过

---

### 6. 数据库迁移 (保留不改)

#### TASK-MAINT-001-24: `backend/alembic/versions/20251224_add_ceo_role.py` (2 处)

**处理方式**: ⏭️ 跳过 - 历史迁移记录保留

**说明**: 迁移文件记录历史变更，不应修改

---

## 执行计划

### Phase 1: 路由层清理 (8 个文件)

```bash
# 批量检查
grep -rn "supervisor" backend/routers/

# 逐文件处理
# 1. finance_profit.py (最多)
# 2. weekly_briefs.py
# 3. daily_reports.py
# 4. fund.py
# 5. users.py
# 6. ad_spend.py
# 7. topup.py
# 8. topups.py ✅
```

### Phase 2: 服务层清理 (4 个文件)

```bash
grep -rn "supervisor" backend/services/
```

### Phase 3: 核心模块清理 (4 个文件)

```bash
grep -rn "supervisor" backend/core/
```

### Phase 4: Schema/Model 清理 (3 个文件)

```bash
grep -rn "supervisor" backend/schemas/ backend/models/
```

### Phase 5: 测试更新 (4 个文件)

```bash
grep -rn "supervisor" backend/tests/
```

### Phase 6: 验证

```bash
# 1. 运行所有测试
pytest backend/tests/ -v

# 2. 检查残留
grep -rn "supervisor" backend/ --include="*.py" | grep -v "role_mapping\|roles.py\|alembic"

# 3. 类型检查
mypy backend/
```

---

## 验收标准 (总体)

- □ `grep -rn "supervisor" backend/routers/` 返回 0 结果
- □ `grep -rn "supervisor" backend/services/` 返回 0 结果
- □ 核心模块仅在兼容映射中保留 supervisor
- □ 所有单元测试通过
- □ 所有集成测试通过
- □ API 功能正常

---

## 注意事项

1. **向后兼容**: `backend/core/role_mapping.py` 和 `backend/core/roles.py` 中的映射逻辑需保留，用于处理旧数据
2. **数据库**: 如果数据库中存在 `supervisor` 角色的用户，需要先运行数据迁移
3. **前端**: 前端代码中的 supervisor 引用需同步清理
4. **测试顺序**: 先修改代码，再修改测试，确保测试反映新行为

---

## 相关任务卡

- TASK-AUTH-004: 权限校验中间件 (已包含角色白名单)
- TASK-USER-001: 用户列表 API (角色筛选)

---

## 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|---------|
| 2026-01-01 | v1.0 | 初始版本 |
| 2026-01-01 | v1.1 | 完成 topups.py, role_mapping.py |
