# Change: Finance Profit Module v1

**Status**: ARCHIVED
**Version**: 1.0
**Date**: 2025-12-02
**Archived**: 2025-12-19

## Why

### 原始问题

当前项目缺少受控的"财务利润表自动化模块"变更线：

1. **利润聚合功能缺失**
   - 现有 `ledger_entries` 和 `daily_reports` 已记录收入/成本原始数据
   - 但缺少自动化的利润汇总、聚合、报表生成能力
   - 财务团队需要手工计算毛利和毛利率

2. **PROFIT_SOT 已创建但未纳入 OpenSpec**
   - `docs/2.sot/PROFIT_SOT.md` v1.1 已完成规范设计
   - 定义了数据模型、API、业务规则、错误码
   - 但尚未通过 OpenSpec change 正式挂到 SoT 网络

3. **数据库扩展未执行**
   - `profit_aggregates` 表（L2 汇总层）待创建
   - `profit_report_snapshots` 表（报表快照）待创建
   - Alembic migration 未编写

4. **API 端点未实现**
   - 6 个 Finance Profit API 端点仅在 PROFIT_SOT 中设计
   - 后端 router/service/schema 均未实现

## What Changes

### 1. OpenSpec Change 登记

| 文件 | 变更 |
|------|------|
| `openspec/changes/finance-profit-v1/proposal.md` | 新建变更提案（本文件） |
| `openspec/changes/finance-profit-v1/tasks.md` | 新建任务追踪清单 |
| `openspec/changes/finance-profit-v1/specs/profit/spec.md` | 新建 Profit 模块规范 |

### 2. 数据库扩展 (Alembic Migration)

| 表名 | 操作 | 说明 |
|------|------|------|
| `profit_aggregates` | 新建 | L2 汇总层核心表，19 个字段 |
| `profit_report_snapshots` | 新建 | 报表快照表，11 个字段 |

### 3. 后端实现

| 组件 | 操作 | 说明 |
|------|------|------|
| `backend/models/profit.py` | 新建 | ProfitAggregate / ProfitReportSnapshot 模型 |
| `backend/schemas/profit.py` | 新建 | 请求/响应 Pydantic schemas |
| `backend/services/profit_service.py` | 新建 | FinanceProfitService 聚合逻辑 |
| `backend/routers/finance_profit.py` | 新建 | 6 个 API 端点 |

### 4. 文档更新

| 文档 | 变更 |
|------|------|
| `docs/2.sot/DATA_SCHEMA.md` | 新增 §3.6 利润表模块（两个表） |
| `docs/2.sot/API_SOT.md` | 新增 §13 Finance Profit API |
| `docs/2.sot/ERROR_CODES_SOT.md` | 新增 PROFIT_001~008 错误码 |

## Impact

### 影响范围

- **Affected specs**: DATA_SCHEMA, API_SOT, ERROR_CODES_SOT (扩展)
- **Affected code**:
  - `backend/models/` (新增 profit.py)
  - `backend/schemas/` (新增 profit.py)
  - `backend/services/` (新增 profit_service.py)
  - `backend/routers/` (新增 finance_profit.py)
  - `alembic/versions/` (新增 migration)
- **Affected tests**:
  - `backend/tests/api/` (新增 test_finance_profit_api.py)
  - `backend/tests/services/` (新增 test_profit_service.py)
  - `REGRESSION_TEST_SUITE.md` (新增 Finance Profit 条目)

### 兼容性

- **NOT breaking**: 纯新增功能，不修改现有模块
- **向后兼容**: 不影响 daily_reports / ledger_entries / transfers 等现有模块
- **数据库**: 仅新增两张表，不修改现有表结构

### 依赖关系

本 change 依赖以下 SoT 文档：

| 依赖文档 | 版本 | 用途 |
|---------|------|------|
| PROFIT_SOT.md | v1.1 | 设计来源（数据模型、API、业务规则） |
| DATA_SCHEMA.md | v5.2 | ledger_entries / daily_reports 表结构 |
| LEDGER_SOT.md | v1.1 | 双账本逻辑、REVENUE/COST 定义 |
| STATE_MACHINE.md | v2.6 | 粉数确认状态机（§8 final_locked） |
| ERROR_CODES_SOT.md | v2.1 | 错误码命名规范 |
| API_SOT.md | v9.0 | API 响应格式规范 |

## Migration

### 当前状态

- **设计层**: PROFIT_SOT.md v1.1 已完成（dev-ready）
- **数据库层**: 待创建 Alembic migration
- **代码层**: 待实现 models/services/routers
- **测试层**: 待生成测试骨架

### 新增表结构

**profit_aggregates** (L2 汇总层)：
- 主键: `id` BIGSERIAL
- 周期: `period_type`, `period_start`, `period_end`
- 维度: `project_id`, `ad_account_id`
- 指标: `total_revenue`, `total_cost`, `gross_profit`, `gross_margin_pct`
- 辅助: `total_conversions`, `total_real_spend`, `total_topup`, `transfer_in`, `transfer_out`
- 锁定: `is_locked`, `locked_at`, `locked_by`
- 审计: `created_at`, `updated_at`

**profit_report_snapshots** (报表快照)：
- 主键: `id` BIGSERIAL
- 报表: `report_type`, `period_month`, `project_id`
- 数据: `report_data` (JSONB)
- 状态: `status` (draft/confirmed/locked)
- 审计: `generated_at`, `generated_by`, `confirmed_at`, `confirmed_by`

### 新增 API 端点

| 端点 | 方法 | 描述 | 角色 |
|-----|------|------|------|
| `/api/v1/finance/profit/generate` | POST | 生成利润聚合 | finance, admin |
| `/api/v1/finance/profit/monthly` | GET | 月度利润表 | finance, admin |
| `/api/v1/finance/profit/daily` | GET | 日度利润数据 | finance, admin |
| `/api/v1/finance/profit/projects/{id}` | GET | 项目利润明细 | account_manager+ |
| `/api/v1/finance/profit/accounts/{id}` | GET | 账户消耗明细 | media_buyer+ |
| `/api/v1/finance/profit/summary` | GET | 整体利润汇总 | finance, admin |

## Risks & Rollback

### 风险评估

| 风险 | 等级 | 缓解措施 |
|------|------|---------|
| 新表 migration 失败 | 中 | 先在开发环境测试，使用 Alembic downgrade |
| 利润计算逻辑错误 | 高 | 单元测试覆盖边界情况，与 ledger 数据抽样对账 |
| 性能问题（大数据量聚合） | 中 | 使用预计算表，避免实时聚合；添加合适索引 |
| 权限控制遗漏 | 低 | 测试覆盖所有角色组合 |

### 回滚策略

1. **数据库回滚**: `alembic downgrade -1` 删除新建表
2. **代码回滚**: 删除 models/services/routers/schemas 相关文件
3. **文档回滚**: 撤销 DATA_SCHEMA / API_SOT / ERROR_CODES_SOT 的扩展内容

### 回归要求

任何实现阶段完成后，必须执行：

```bash
python run_tests.py --type regression
```

确保以下模块回归全绿：
- Daily Reports
- Ledger
- Transfers
- Topup
- Ad Accounts
- **Finance Profit** (新增)

## Scope

### In Scope

- ✅ 数据库 schema: profit_aggregates / profit_report_snapshots
- ✅ 后端 models: ProfitAggregate / ProfitReportSnapshot
- ✅ 后端 schemas: 请求/响应 Pydantic 定义
- ✅ 后端 services: FinanceProfitService 聚合逻辑
- ✅ 后端 routers: 6 个 API 端点
- ✅ 错误码: PROFIT_001 ~ PROFIT_008
- ✅ 测试: API 集成测试 + Service 单元测试
- ✅ 文档: DATA_SCHEMA / API_SOT / ERROR_CODES_SOT 扩展

### Out of Scope

- ❌ 前端页面实现
- ❌ PDF/Excel 导出功能
- ❌ 复杂可视化图表
- ❌ 多币种支持（MVP 仅支持 CNY）
- ❌ 报表邮件推送

## Done 条件

### 验收清单

- [ ] Alembic migration 执行成功，两张新表已创建
- [ ] 后端 models/services/routers 实现完成
- [ ] 6 个 API 端点可正常调用（Happy Path 测试通过）
- [ ] 所有 PROFIT_00X 错误码有对应测试用例
- [ ] 所有 BR-PROFIT-00X 业务规则有对应测试用例
- [ ] REGRESSION_TEST_SUITE 新增 Finance Profit 条目
- [ ] 回归测试全绿（含新增 + 现有模块）
- [ ] DATA_SCHEMA.md 新增 §3.6 利润表模块
- [ ] API_SOT.md 新增 §13 Finance Profit API
- [ ] ERROR_CODES_SOT.md 新增 PROFIT_ 前缀和错误码
- [ ] `openspec validate finance-profit-v1 --strict` 通过
- [ ] `openspec archive finance-profit-v1 --yes` 归档完成

---

## Changes Summary

### 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `openspec/changes/finance-profit-v1/proposal.md` | 新建 | 变更提案文档 |
| `openspec/changes/finance-profit-v1/tasks.md` | 新建 | 任务追踪清单 |
| `openspec/changes/finance-profit-v1/specs/profit/spec.md` | 新建 | Profit 模块规范 |
| `alembic/versions/xxx_add_profit_tables.py` | 新建 | 数据库迁移 |
| `backend/models/profit.py` | 新建 | SQLAlchemy 模型 |
| `backend/schemas/profit.py` | 新建 | Pydantic schemas |
| `backend/services/profit_service.py` | 新建 | 业务逻辑服务 |
| `backend/routers/finance_profit.py` | 新建 | API 路由 |
| `backend/tests/api/test_finance_profit_api.py` | 新建 | API 集成测试 |
| `backend/tests/services/test_profit_service.py` | 新建 | Service 单元测试 |
| `docs/2.sot/DATA_SCHEMA.md` | 修改 | 新增 §3.6 |
| `docs/2.sot/API_SOT.md` | 修改 | 新增 §13 |
| `docs/2.sot/ERROR_CODES_SOT.md` | 修改 | 新增 PROFIT_ 类错误码 |

### SoT 对齐引用

本 change 的设计来源：

- **PROFIT_SOT.md v1.1** (`docs/2.sot/PROFIT_SOT.md`)
  - 数据模型定义: §2
  - API 规格: §3
  - 业务规则: §4 (BR-PROFIT-001 ~ BR-PROFIT-008)
  - 错误码: §5 (PROFIT_001 ~ PROFIT_008)
  - 测试矩阵: §6

---

## Archive Recommendation

### 验证步骤

1. 确认所有实现完成：
```bash
# 检查数据库表
python -c "from backend.models.profit import ProfitAggregate; print('Models OK')"

# 运行 API 测试
python -m pytest backend/tests/api/test_finance_profit_api.py -v

# 运行 Service 测试
python -m pytest backend/tests/services/test_profit_service.py -v
```

2. 运行完整回归测试：
```bash
python run_tests.py --type regression
```

3. 执行 OpenSpec 验证和归档：
```bash
openspec validate finance-profit-v1 --strict
openspec archive finance-profit-v1 --yes
```

### 归档验证清单

- [ ] OpenSpec change 文件已创建
- [ ] Alembic migration 已执行
- [ ] 后端实现已完成
- [ ] 测试已编写并通过
- [ ] SoT 文档已更新
- [ ] 回归测试全绿
- [ ] OpenSpec validate 通过
