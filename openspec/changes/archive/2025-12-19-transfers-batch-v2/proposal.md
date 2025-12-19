# Change: Transfers Batch Module v2

**Status**: ARCHIVED
**Version**: 2.0
**Date**: 2025-12-02

## Why

### 原始问题

Transfers（死号余额迁移）模块已有完整的后端实现，但存在以下问题：

1. **OpenSpec 规范缺失**
   - 无 `openspec/specs/transfers/spec.md` 文件
   - 无法通过 OpenSpec 工具进行变更追踪和验证

2. **测试全部被跳过**
   - `backend/tests/api/test_transfers_flow_generated.py` 中 15/17 测试被 `@pytest.mark.skip` 标记
   - 原因注释：`"transfer_requests router 尚未实现，等待实现后启用"`
   - 实际上 router/service/model 已完整实现

3. **测试 Fixtures 不完整**
   - `account_manager_headers` fixture 不存在
   - `test_ad_account_2` fixture 需要验证是否正确配置

4. **未纳入回归测试套件**
   - `REGRESSION_TEST_SUITE.md` 中未包含 transfers 模块
   - `run_tests.py` 中未包含 transfers 测试路径

## What Changes

### 1. OpenSpec 规范创建

| 文件 | 变更 |
|------|------|
| `openspec/specs/transfers/spec.md` | 新建 Transfers 模块规范（ADDED Requirements） |

### 2. 测试 Fixtures 修复 (`backend/tests/conftest.py`)

| Fixture | 变更 |
|---------|------|
| `account_manager_headers` | 新增 account_manager 角色认证 headers |
| `account_manager_user` | 新增 account_manager 角色用户 |
| `account_manager_token` | 新增 account_manager JWT token |

### 3. 测试启用 (`backend/tests/api/test_transfers_flow_generated.py`)

| 测试类 | 变更 |
|--------|------|
| `TestTransfersHappyPath` | 移除 5 个测试的 skip 标记 |
| `TestTransfersValidation` | 移除 3 个测试的 skip 标记 |
| `TestTransfersPermissions` | 移除 3 个测试的 skip 标记 |
| `TestTransfersErrorCodes` | 移除 4 个测试的 skip 标记 |
| `TestTransfersStateMachine` | 验证 API 测试可运行 |

### 4. 回归测试纳入

| 文件 | 变更 |
|------|------|
| `backend/tests/REGRESSION_TEST_SUITE.md` | 新增 Transfers API 回归套件说明 |

## Impact

### 影响范围

- **Affected specs**: transfers (新建)
- **Affected code**:
  - `backend/tests/conftest.py` (新增 fixtures)
  - `backend/tests/api/test_transfers_flow_generated.py` (移除 skip)
  - `backend/tests/REGRESSION_TEST_SUITE.md` (新增章节)

### 兼容性

- **NOT breaking**: 仅新增测试和规范，不修改业务代码
- **实现层无变更**: model/service/router 已对齐 SoT，无需修改
- **数据库无变更**: 无需 Alembic migration

### 测试状态

- **Before**: 6 passed, 15 skipped
- **After**: 17 tests enabled, 0 skipped (pending validation run)

## Migration

### 当前状态

- **代码层**: 已完整实现，无需额外操作
- **测试层**: 需要启用并修复测试
- **文档层**: 需要创建 OpenSpec spec

### SoT 对齐验证

本变更需验证以下 SoT 文档对齐：

- [x] **STATE_MACHINE.md v2.6 第12章** - 5 状态：draft/pending_approval/approved/rejected/completed
- [x] **DATA_SCHEMA.md v5.2 第3.4.6节** - transfer_requests 表结构
- [x] **API_SOT.md v9.0** - 7 个 API 端点
- [x] **ERROR_CODES_SOT.md v2.1** - 错误码规范

---

## Changes Summary

### 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `openspec/changes/transfers-batch-v2/proposal.md` | 新建 | 变更提案文档 |
| `openspec/changes/transfers-batch-v2/tasks.md` | 新建 | 任务追踪清单 |
| `openspec/changes/transfers-batch-v2/specs/transfers/spec.md` | 新建 | Transfers 模块规范 |
| `backend/tests/api/test_transfers_flow_generated.py` | 修改 | 移除所有 skip 标记，使用 fixtures |
| `backend/tests/REGRESSION_TEST_SUITE.md` | 修改 | 添加 Transfers 模块到回归套件 |

### 已验证的实现对齐

以下实现已确认对齐 SoT：

- **Model** (`backend/models/workflow/transfer_request.py`)
  - 字段对齐 DATA_SCHEMA.md v5.2 第 3.4.6 节
  - 使用 `TransferRequestStatus` 枚举
  - 包含 `version` 乐观锁字段

- **Service** (`backend/services/transfer_service.py`)
  - 状态流转白名单对齐 STATE_MACHINE.md v2.6 第 12 章
  - 权限检查：admin/account_manager/finance 可创建，finance/admin 可审批，admin 可完成
  - 错误码：AUTH_500, BIZ_001, BIZ_002, STATE_001

- **Router** (`backend/routers/transfers.py`)
  - 7 个端点对齐 API_SOT.md v9.0
  - 已注册到 main.py（前缀 `/api/v1/transfers`）

- **Schema** (`backend/schemas/transfer.py`)
  - 请求/响应 schema 完整
  - Pydantic v2 model_validator 实现同账户校验

---

## Archive Recommendation

### 验证步骤

1. 运行测试验证：
```bash
python -m pytest backend/tests/api/test_transfers_flow_generated.py -v --tb=short
```

2. 如果所有测试通过，执行归档：
```bash
openspec validate transfers-batch-v2 --strict
openspec archive transfers-batch-v2 --yes
```

### 预期测试结果

- **Total**: 17 tests
- **Passed**: 17
- **Skipped**: 0
- **Errors**: 0

### 归档验证清单

- [x] OpenSpec spec 文件已创建 (`specs/transfers/spec.md`)
- [x] 测试已启用（移除所有 skip 标记）
- [x] 测试使用正确的 fixtures
- [x] 回归测试套件已更新
- [ ] 测试运行验证通过（待执行）
- [ ] OpenSpec validate 通过（待执行）
