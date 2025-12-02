# Change: Align Reconciliation Batch Module with SoT (v2)

**Status**: READY FOR ARCHIVE
**Version**: 2.0-final
**Date**: 2025-12-02

## Why

### 原始问题

Reconciliation 模块存在多个严重问题导致 7/13 测试被标记为 SKIP：

1. **模型重复定义**
   - `backend/models/reconciliation.py` 和 `backend/models/finance/reconciliation.py` 均定义了 `ReconciliationBatch`、`ReconciliationDetail`
   - SQLAlchemy 表重复注册导致运行时错误风险
   - `ReconciliationAdjustment` 在旧模块中定义，但 finance 模块中才是 SoT 实现

2. **字段命名不一致**
   - Service 使用 `reconciliation_date`，Model 使用 `period_start/period_end`
   - Service 使用 `batch_no`，Model 使用 `batch_code`
   - Service 使用 `adjustment_amount`，新 Model 使用 `amount`
   - Service 使用 `auto_match`, `total_accounts`, `matched_accounts` 等不存在的字段

3. **测试 Mock 逻辑错误**
   - `test_get_batches_with_filters` 中 `limit()` 直接返回列表，而非查询对象
   - 导致测试无法正确验证 `.all()` 调用链

4. **测试覆盖率风险**
   - 7/13 测试被 `pytest.skip()` 标记
   - 无法纳入回归测试套件

## What Changes

### 1. 模型层统一 (`backend/models/`)

| 文件 | 变更 |
|------|------|
| `finance/reconciliation.py` | 添加 `ReconciliationAdjustment` 模型（SoT DATA_SCHEMA.md v5.2），添加属性别名 `batch_no`, `approved_by`, `reconciliation_date` |
| `reconciliation.py` | 从 finance 模块导入正式模型，旧类标记为 `__abstract__ = True` 避免表重复注册 |
| `enums.py` | 新增 `ReconciliationAdjustmentType` 枚举 (`increase`, `decrease`, `writeoff`) |
| `__init__.py` | 导出 `ReconciliationAdjustment`, `ReconciliationAdjustmentType` |
| `base.py` | 重新导出 `ReconciliationAdjustmentType` |

### 2. 服务层修复 (`backend/services/reconciliation_service.py`)

| 方法 | 修复内容 |
|------|----------|
| `create_batch()` | 使用 `batch_code`, `period_start/period_end` 代替旧字段名 |
| `get_batches()` | 使用 `period_end` 进行日期过滤 |
| `run_reconciliation()` | 移除对 `auto_match`, `total_accounts` 等不存在字段的依赖 |
| `get_batch_details()` | 使用 `status` 代替 `match_status` |
| `create_adjustment()` | 使用 `amount` 代替 `adjustment_amount` |
| `get_statistics()` | 使用 `period_end` 进行日期过滤；使用 `ReconciliationAdjustment.amount` |
| `export_reconciliation_data()` | 使用 `period_end`；通过 `ad_account` 关系访问 `project`/`channel` |
| `_update_batch_statistics()` | 仅更新存在的字段 (`total_system_spend`, `total_actual_spend`, `discrepancy`) |

### 3. Schema 层修复 (`backend/schemas/reconciliation.py`)

- `AdjustmentType` 枚举更新为 SoT 值：`increase`, `decrease`, `writeoff`
- `ReconciliationAdjustmentCreateRequest` 字段对齐模型

### 4. 测试层修复 (`backend/tests/test_reconciliation_service.py`)

| 测试 | 修复内容 |
|------|----------|
| `test_create_batch_success` | 移除 skip，使用正确字段名 |
| `test_create_batch_duplicate_date` | 移除 skip，期望 `BusinessLogicError` |
| `test_run_reconciliation_success` | 移除 skip，使用 draft 状态 |
| `test_run_reconciliation_invalid_status` | 移除 skip，期望 `BusinessLogicError` |
| `test_create_adjustment_success` | 移除 skip，使用 SoT 调整类型 |
| `test_export_reconciliation_data` | 移除 skip，使用属性别名 |
| `test_get_batches_with_filters` | 修复 mock：`limit()` 返回查询对象，再调用 `.all()` |
| `test_update_batch_statistics` | 更新断言，仅验证存在的字段 |

## Impact

### 影响范围

- **Affected specs**: reconciliation
- **Affected code**:
  - `backend/models/finance/reconciliation.py`
  - `backend/models/reconciliation.py`
  - `backend/models/enums.py`
  - `backend/models/__init__.py`
  - `backend/models/base.py`
  - `backend/services/reconciliation_service.py`
  - `backend/schemas/reconciliation.py`
  - `backend/tests/test_reconciliation_service.py`

### 兼容性

- **NOT breaking**: 添加属性别名保持向后兼容
- **旧代码兼容**: `batch.batch_no`, `batch.reconciliation_date` 仍可正常访问
- **数据库无变更**: 无需 Alembic migration（仅代码层修复）

### 测试状态

- **Before**: 6 passed, 7 skipped
- **After**: 13 passed, 0 skipped, 0 errors

## Migration

### 当前状态

- **代码层**: 已完成，无需额外操作
- **数据库层**: `reconciliation_adjustments` 表结构已在 finance 模块定义

### 未来 TODO

- [ ] 生成 Alembic migration 脚本（如果数据库中尚未存在 `reconciliation_adjustments` 表）
- [ ] `ReconciliationReport` 模型完整实现（当前为占位符）
- [ ] 导出功能扩展（更多格式支持）

---

## Archive Recommendation

### 是否可以归档 reconciliation-batch-v2

**建议：可以归档**

**验证清单：**
1. [x] 所有 13/13 测试通过，0 skipped，0 errors
2. [x] 模型重复定义问题已解决（旧类标记为 `__abstract__ = True`）
3. [x] 服务层字段名已对齐 SoT
4. [x] Schema 枚举值已对齐 SoT
5. [x] 属性别名保持向后兼容

**归档命令：**
```bash
openspec validate align-reconciliation-batch-v2 --strict
openspec archive align-reconciliation-batch-v2 --yes
```

**注意事项：**
- 归档前建议运行完整回归测试套件确认无副作用
- 如需数据库迁移，应在归档后单独创建新的 OpenSpec change

---

## 变更完成总结

**归档日期**: 2025-12-02

### SoT 文档对齐

本变更已对齐以下 SoT 文档：

- **DATA_SCHEMA.md v5.2** - Reconciliation 模块数据模型（第 3.5 节）
  - `ReconciliationBatch` 字段：`batch_code`, `period_start`, `period_end`, `total_system_spend`, `total_actual_spend`, `discrepancy`
  - `ReconciliationDetail` 字段：`system_spend`, `actual_spend`, `discrepancy`, `status`
  - `ReconciliationAdjustment` 模型完整实现（第 3.5.3 节）：`amount`, `adjustment_type` (increase/decrease/writeoff)

- **STATE_MACHINE.md v2.6** - Reconciliation 状态机
  - `ReconciliationBatchStatus`: DRAFT → PENDING_REVIEW → APPROVED/NEEDS_ADJUSTMENT → COMPLETED
  - `ReconciliationDetailStatus`: PENDING → CONFIRMED/ADJUSTED

- **ERROR_CODES_SOT.md v2.x** - 错误码规范
  - `BIZ_302`: 对账批次日期重复
  - `BIZ_303`: 权限不足
  - `SYS_004`: 资源不存在

### 回归测试

以下测试文件已纳入回归测试套件，**13/13 测试全部通过**：

- `backend/tests/test_reconciliation_service.py`
  - `test_create_batch_success` ✅
  - `test_create_batch_duplicate_date` ✅
  - `test_get_batches_with_filters` ✅
  - `test_get_batch_by_id_not_found` ✅
  - `test_run_reconciliation_success` ✅
  - `test_run_reconciliation_invalid_status` ✅
  - `test_review_detail_success` ✅
  - `test_create_adjustment_success` ✅
  - `test_get_statistics` ✅
  - `test_export_reconciliation_data` ✅
  - `test_update_batch_statistics` ✅
  - `test_permission_check_for_account_manager` ✅
  - `test_auto_match_rate_calculation` ✅

### Future TODO

以下项目不在本次变更范围内，需后续单独处理：

1. **Alembic Migration**
   - 如果生产数据库中尚未存在 `reconciliation_adjustments` 表，需要生成并执行 migration 脚本

2. **ReconciliationReport 模型**
   - 当前为占位符（`ReconciliationReport = None`），需完整实现
   - 参考 DATA_SCHEMA.md v5.2 第 3.5.4 节

3. **导出功能扩展**
   - 当前仅支持基础导出格式
   - 可扩展支持 Excel、CSV、PDF 等更多格式

4. **测试覆盖率提升**
   - 当前服务层测试覆盖主要业务逻辑
   - 可考虑增加边界条件测试和集成测试