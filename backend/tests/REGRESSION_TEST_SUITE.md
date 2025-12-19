# 回归测试套件（Regression Test Suite）

**版本**: v1.0  
**最后更新**: 2025-01-22  
**状态**: ✅ Active

## 📋 概述

本回归测试套件包含核心业务模块的 API 流程测试，用于快速验证关键功能是否正常工作。

## 🎯 回归五连拍（Regression Test Suite）

以下测试套件按顺序执行，确保核心业务功能正常：

```bash
# 1. Daily Reports API 测试
python -m pytest backend/tests/api/test_daily_report_flow_generated.py -q

# 2. Trend Risk API 测试（趋势风控）
python -m pytest backend/tests/api/test_trend_risk_flow_generated.py -q

# 3. Ledger 测试（账本模块）
python -m pytest backend/tests/ledger -q

# 4. Ad Accounts 测试（广告账户）
python -m pytest backend/tests/ad_accounts -q

# 5. Topup API 测试（充值模块）
python -m pytest backend/tests/test_topup_api.py -q -k "not skip"

# 6. Transfers API 测试（死号余额迁移）
python -m pytest backend/tests/api/test_transfers_flow_generated.py -q

# 7. Finance Profit API 测试（财务利润统计）
python -m pytest backend/tests/api/test_finance_profit_flow_generated.py -q
```

## 🚀 快速执行

### Windows (PowerShell)

```powershell
# 执行全部回归测试
python -m pytest backend/tests/api/test_daily_report_flow_generated.py -q
python -m pytest backend/tests/api/test_trend_risk_flow_generated.py -q
python -m pytest backend/tests/ledger -q
python -m pytest backend/tests/ad_accounts -q
python -m pytest backend/tests/test_topup_api.py -q -k "not skip"
python -m pytest backend/tests/api/test_transfers_flow_generated.py -q
python -m pytest backend/tests/api/test_finance_profit_flow_generated.py -q
```

### Linux/macOS (Bash)

```bash
# 执行全部回归测试
python -m pytest backend/tests/api/test_daily_report_flow_generated.py -q && \
python -m pytest backend/tests/api/test_trend_risk_flow_generated.py -q && \
python -m pytest backend/tests/ledger -q && \
python -m pytest backend/tests/ad_accounts -q && \
python -m pytest backend/tests/test_topup_api.py -q -k "not skip" && \
python -m pytest backend/tests/api/test_transfers_flow_generated.py -q && \
python -m pytest backend/tests/api/test_finance_profit_flow_generated.py -q
```

## 📊 测试覆盖模块

| 模块 | 测试文件 | 测试用例数 | 状态 |
|------|---------|-----------|------|
| Daily Reports | `test_daily_report_flow_generated.py` | 33+ | ✅ |
| Trend Risk | `test_trend_risk_flow_generated.py` | 17 | ✅ |
| Ledger | `backend/tests/ledger/` | 37+ | ✅ |
| Ad Accounts | `backend/tests/ad_accounts/` | - | ✅ |
| Topup | `test_topup_api.py` | 22+ | ✅ |
| Transfers | `test_transfers_flow_generated.py` | 17 | ✅ |
| Finance Profit | `test_finance_profit_flow_generated.py` | 15 | ✅ |

## 🔍 测试内容

### 1. Daily Reports API
- Happy Path: 创建、查询、列表、状态流转
- Validation: 参数校验、必填字段
- Permissions: 角色权限验证
- Error Codes: 错误码返回验证
- State Machine: 8 状态机流转测试

### 2. Trend Risk API
- Happy Path: 标记异常、解决异常、完整流程
- Validation: 参数校验（audit_notes 可选性）
- Permissions: data_operator/admin 权限验证
- Error Codes: TREND_001/002/010 错误码验证
- State Machine: trend_pending → trend_flagged → trend_resolved

### 3. Ledger
- Service 层测试: CRUD 操作、余额计算
- Invariants 测试: 账本不变量验证（LEDGER_SOT.md）

### 4. Ad Accounts
- API 端点测试: CRUD、状态更新、权限控制

### 5. Topup
- API 流程测试: 创建、提交、审批、完成
- 权限和状态机验证

### 6. Transfers (死号余额迁移)
- Happy Path: 创建、提交、审批、完成（draft → pending_approval → approved → completed）
- Validation: 金额校验、源目标账户不能相同
- Permissions: media_buyer 无创建权限、account_manager 无审批权限、finance 无完成权限
- Error Codes: BIZ_002、STATE_001 错误码验证
- State Machine: 5 状态机流转测试（对齐 STATE_MACHINE.md v2.6 第 12 章）

### 7. Finance Profit (财务利润统计)
- Happy Path: 生成聚合、月度查询、日度查询、项目明细、账户明细、汇总查询
- Validation: 周期参数校验（start_date ≤ end_date，不可为未来日期，范围 ≤ 366 天）
- Permissions: admin/finance 全权限、account_manager 部分权限、media_buyer 仅账户明细
- Error Codes: PROFIT_001~008 错误码验证
- 利润公式: gross_profit = total_revenue - total_cost（对齐 PROFIT_SOT.md v1.1）

## 📝 使用说明

### 前置条件

1. 确保 `.venv` 已激活
2. 确保测试数据库配置正确（SQLite in-memory）
3. 确保所有依赖已安装：`pip install -r requirements-test.txt`

### 执行选项

- `-q`: 安静模式，只显示测试结果摘要
- `-v`: 详细模式，显示每个测试用例的详细信息
- `--tb=short`: 简短的错误追踪信息
- `-k "not skip"`: 排除标记为 skip 的测试

### 完整命令示例

```bash
# 详细模式 + 简短错误追踪
python -m pytest backend/tests/api/test_trend_risk_flow_generated.py -v --tb=short

# 安静模式（推荐用于 CI/CD）
python -m pytest backend/tests/api/test_trend_risk_flow_generated.py -q
```

## 🔗 相关文档

- **SoT 文档**: `docs/2.sot/STATE_MACHINE.md v2.6`, `API_SOT.md v9.0`
- **测试规范**: `docs/3.dev-guides/TESTING_STRATEGY.md`
- **自动化测试**: `.claude/skills/ai-ad-api-automation-test/SKILL.md`

## 📌 注意事项

1. **测试顺序**: 建议按顺序执行，某些测试可能依赖前置状态
2. **数据库隔离**: 每个测试用例使用独立的数据库会话，互不干扰
3. **跳过测试**: Topup 测试使用 `-k "not skip"` 排除已标记为 skip 的测试
4. **CI/CD 集成**: 这些测试已集成到 GitHub Actions CI 流程中

## 🎯 后续计划

- [ ] 创建自动化脚本 `run_regression_tests.sh` / `run_regression_tests.bat`
- [ ] 集成到 `run_tests.py` 的 `--type regression` 选项
- [ ] 添加测试覆盖率报告
- [ ] 添加性能基准测试

---

**维护者**: AI_ad_spend02 团队  
**最后审查**: 2025-01-22


