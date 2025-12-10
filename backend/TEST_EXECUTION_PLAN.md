# 后端全面测试执行计划
> **生成时间**: 2025-12-10
> **测试框架**: pytest 6.0+
> **覆盖率目标**: ≥60%

---

## 📋 测试清单

### 已发现的测试模块 (45个)

#### 🏥 健康检查 & 基础测试
- [x] `test_api_health.py` - API健康检查
- [x] `test_app_smoke.py` - 应用冒烟测试
- [x] `test_api_endpoints.py` - API端点测试

#### 🔐 认证 & 权限测试
- [x] `test_authentication_api.py` - 认证API测试
- [x] `test_auth_service.py` - 认证服务测试
- [x] `test_permissions.py` - 权限测试
- [x] `test_rbac_permissions.py` - RBAC权限测试
- [x] `test_project_permissions.py` - 项目权限测试
- [x] `test_daily_report_permissions.py` - 日报权限测试
- [x] `test_topup_permissions.py` - 充值权限测试
- [x] `test_reconciliation_permissions.py` - 对账权限测试

#### 📊 项目管理测试
- [x] `test_api_projects.py` - 项目API测试
- [x] `test_project_api.py` - 项目API详细测试
- [x] `test_project_service.py` - 项目服务测试

#### 💰 财务模块测试
- [x] `test_topup_api.py` - 充值API测试
- [x] `test_topup_service.py` - 充值服务测试
- [x] `test_finance_profit_api.py` - 财务利润API测试
- [x] `test_ledger_service.py` - 总账服务测试
- [x] `test_ledger_invariants.py` - 总账不变量测试

#### 📅 日报管理测试
- [x] `test_daily_report_api.py` - 日报API测试
- [x] `test_daily_report_service.py` - 日报服务测试
- [x] `test_daily_report_state_machine.py` - 日报状态机测试
- [x] `test_daily_report_performance.py` - 日报性能测试

#### 🔄 对账 & 结算测试
- [x] `test_reconciliation_api.py` - 对账API测试
- [x] `test_reconciliation_service.py` - 对账服务测试
- [x] `test_settlement_api.py` - 结算API测试
- [x] `test_settlement_service.py` - 结算服务测试

#### 📈 广告 & 账户测试
- [x] `test_ad_spend_api.py` - 广告消耗API测试
- [x] `test_ad_account_api.py` - 广告账户API测试
- [x] `test_ad_account_service.py` - 广告账户服务测试

#### 🏢 供应商测试
- [x] `test_supplier_api.py` - 供应商API测试
- [x] `test_supplier_service.py` - 供应商服务测试

#### 🤖 AI 分析测试
- [x] `test_ai_analytics_api.py` - AI分析API测试
- [x] `test_ai_analytics_service.py` - AI分析服务测试

#### 📥 数据导入测试
- [x] `test_import_job_service.py` - 导入任务服务测试
- [x] `test_excel_import_export.py` - Excel导入导出测试

#### 🔧 核心功能测试
- [x] `test_models_crud.py` - 模型CRUD测试
- [x] `test_state_machine_transitions.py` - 状态机转换测试
- [x] `test_state_machine_p2.py` - 状态机P2测试
- [x] `test_error_codes_coverage.py` - 错误码覆盖测试
- [x] `test_new_modules_integration.py` - 新模块集成测试

#### 🔄 业务流程测试 (Generated)
- [x] `test_daily_report_flow_generated.py` - 日报流程测试
- [x] `test_finance_profit_flow_generated.py` - 财务利润流程测试
- [x] `test_transfers_flow_generated.py` - 转账流程测试
- [x] `test_trend_risk_flow_generated.py` - 趋势风险流程测试

---

## 🎯 测试执行策略

### Phase 1: 快速验证（预估 2-3 分钟）
运行单元测试和快速集成测试
```bash
cd d:\git\1108\backend
pytest -m "unit or (integration and not slow)" --tb=short -v
```

### Phase 2: 完整单元测试（预估 5 分钟）
```bash
pytest -m "unit" --cov=backend --cov-report=term-missing
```

### Phase 3: 集成测试（预估 10 分钟）
```bash
pytest -m "integration" --cov=backend --cov-report=html
```

### Phase 4: API 端到端测试（预估 8 分钟）
```bash
pytest -m "api or e2e" -v
```

### Phase 5: 完整测试套件（预估 20-30 分钟）
```bash
pytest --cov=backend --cov-report=html --cov-report=term-missing --html=test-report.html
```

---

## 📊 测试覆盖模块

| 模块路由 | 测试文件数 | 覆盖率目标 | 优先级 |
|---------|-----------|-----------|-------|
| `authentication.py` | 3 | ≥80% | 🔴 高 |
| `projects.py` | 3 | ≥75% | 🔴 高 |
| `topup.py` | 3 | ≥75% | 🔴 高 |
| `daily_reports.py` | 5 | ≥80% | 🔴 高 |
| `reconciliation.py` | 3 | ≥70% | 🟡 中 |
| `settlements.py` | 2 | ≥70% | 🟡 中 |
| `ad_accounts.py` | 2 | ≥70% | 🟡 中 |
| `ad_spend.py` | 1 | ≥65% | 🟡 中 |
| `finance_profit.py` | 2 | ≥70% | 🟡 中 |
| `ledger.py` | 2 | ≥75% | 🔴 高 |
| `suppliers.py` | 2 | ≥65% | 🟢 低 |
| `ai_analytics.py` | 2 | ≥60% | 🟢 低 |
| `import_jobs.py` | 2 | ≥65% | 🟢 低 |
| `transfers.py` | 1 | ≥65% | 🟢 低 |
| `reports.py` | 0 | ≥50% | 🟢 低 |
| `channels.py` | 0 | ≥50% | 🟢 低 |
| `health.py` | 1 | 100% | 🔴 高 |

**未覆盖路由（需生成测试）**:
- ⚠️ `reports.py` - 报表管理
- ⚠️ `channels.py` - 渠道管理
- ⚠️ `project_templates.py` - 项目模板
- ⚠️ `agents.py` - 代理管理

---

## 🔍 测试报告输出

### HTML 报告
- **路径**: `backend/htmlcov/index.html`
- **内容**: 代码覆盖率热力图

### 终端报告
- **缺失行数**: 显示未覆盖代码行
- **覆盖率百分比**: 每个模块的覆盖率

### Pytest HTML 报告
- **路径**: `backend/test-report.html`
- **内容**: 测试用例执行详情

---

## 🚨 已知问题 & 注意事项

1. **数据库依赖**: 集成测试需要数据库连接（当前使用 SQLite）
2. **异步测试**: 需要 `pytest-asyncio` 插件（已在 pytest.ini 中注释）
3. **覆盖率阈值**: 设置为 60%（`--cov-fail-under=60`）
4. **慢速测试**: 标记为 `@pytest.mark.slow` 的测试运行时间 >1秒

---

## 🎯 建议的执行顺序

### 1️⃣ 立即执行（快速验证）
```bash
pytest tests/test_api_health.py tests/test_app_smoke.py -v
```

### 2️⃣ 核心模块测试（优先级高）
```bash
pytest -m "auth or project or daily_report" -v
```

### 3️⃣ 财务模块测试
```bash
pytest -m "topup or reconciliation" -v
```

### 4️⃣ 完整回归测试
```bash
pytest --cov=backend --cov-report=html
```

---

## 📝 测试执行命令速查

| 测试类型 | 命令 |
|---------|------|
| **冒烟测试** | `pytest tests/test_app_smoke.py -v` |
| **单元测试** | `pytest -m unit` |
| **集成测试** | `pytest -m integration` |
| **API测试** | `pytest -m api` |
| **权限测试** | `pytest -m permissions` |
| **特定模块** | `pytest tests/test_topup_*.py` |
| **覆盖率报告** | `pytest --cov=backend --cov-report=html` |
| **失败重试** | `pytest --lf -v` (last-failed) |
| **并行执行** | `pytest -n auto` (需要 pytest-xdist) |

---

**准备就绪！请选择执行策略并开始测试。** 🚀
