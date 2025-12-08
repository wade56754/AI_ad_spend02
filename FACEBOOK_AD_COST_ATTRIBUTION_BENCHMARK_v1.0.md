# Facebook 广告成本归因系统业界最佳实践对标分析

> **研究日期**: 2025-12-07  
> **研究主题**: Facebook 广告成本归因系统的业界最佳实践  
> **对标项目**: AI_ad_spend02 的 ledger / reconciliation 设计  
> **研究范围**: 账本双录、对账批次设计、多币种（USDT/CNY）、项目/投手维度利润表

---

## 📋 执行摘要

本次研究对标了业界在 Facebook 广告成本归因系统中的最佳实践，重点关注财务账本、对账批次、多币种处理和利润报表设计。研究发现，AI_ad_spend02 项目的双账本设计符合业界标准，但在多币种支持、对账自动化程度和利润表维度方面存在改进空间。

**关键发现**:
- ✅ **双账本设计**: 符合业界标准（收入/成本分离）
- ⚠️ **多币种支持**: 当前仅支持 CNY，业界普遍支持多币种
- ⚠️ **对账自动化**: 当前为半自动化，业界趋势为全自动化
- ⚠️ **利润表维度**: 当前支持项目维度，缺少投手维度细分

---

## 🔍 研究范围与方法

### 研究维度

| 维度 | 说明 | 业界实践来源 |
|------|------|------------|
| **账本双录** | 收入与成本的双账本设计 | 广告代理行业标准、财务会计准则 |
| **对账批次设计** | 对账批次的周期、状态、差异处理 | 广告代理管理系统、ERP 系统 |
| **多币种处理** | USDT/CNY 等多币种支持 | 跨境广告代理、国际财务系统 |
| **利润表维度** | 项目/投手维度的利润分析 | 广告代理业务分析、BI 系统 |

### 研究方法

1. **业界标准研究**: 搜索广告代理行业财务系统设计
2. **系统架构对标**: 对比现有 SoT 设计与业界实践
3. **差距分析**: 识别设计差异和改进机会
4. **改进建议**: 提出 3 条可采纳的改进建议

---

## 📊 对标分析：业界做法 vs 现有 SoT

### 1. 账本双录设计

#### 业界最佳实践

**标准做法**:
- **收入账本**: 记录客户充值、按效果计费收入（如按粉数计费）
- **成本账本**: 记录供应商消耗、平台费用、运营成本
- **完全隔离**: 收入与成本账本严格分离，禁止混记
- **余额双写**: 实时余额字段 + 账本流水记录（双重保障）

**典型架构**:
```
业界标准架构:
├── Revenue Ledger (收入账本)
│   ├── Client Deposits (客户充值)
│   ├── Performance Revenue (效果计费)
│   └── Reversals (红冲)
└── Cost Ledger (成本账本)
    ├── Supplier Costs (供应商成本)
    ├── Platform Fees (平台费用)
    └── Operational Costs (运营成本)
```

**关键特性**:
- ✅ 双账本完全独立，禁止混记
- ✅ 余额字段（实时查询）+ 账本流水（审计追溯）
- ✅ 事务保证：余额更新与账本记录在同一事务内
- ✅ 乐观锁/悲观锁：防止并发修改

#### AI_ad_spend02 现有设计

**当前实现** (LEDGER_SOT.md v1.1):

```sql
-- PROJECT 账本（收入侧）
ledger_type = 'PROJECT'
entry_type IN ('REVENUE', 'TOPUP', 'REVERSAL')
project_id IS NOT NULL, supplier_id IS NULL

-- SUPPLIER 账本（成本侧）
ledger_type = 'SUPPLIER'
entry_type IN ('COST', 'TOPUP', 'TRANSFER_OUT', 'TRANSFER_IN', 'REVERSAL')
supplier_id IS NOT NULL, project_id IS NULL
```

**余额管理**:
- ✅ 实时余额: `projects.balance` / `suppliers.balance`
- ✅ 账本流水: `ledger_entries` 表（审计追溯）
- ✅ 双写保证: 余额更新与账本记录在同一事务内
- ✅ 并发控制: `SELECT FOR UPDATE` 行锁

**对比结果**: ✅ **完全符合业界标准**

| 特性 | 业界标准 | AI_ad_spend02 | 状态 |
|------|---------|--------------|------|
| 双账本隔离 | ✅ 必须 | ✅ PROJECT/SUPPLIER 完全隔离 | ✅ 符合 |
| 余额双写 | ✅ 必须 | ✅ balance 字段 + ledger_entries | ✅ 符合 |
| 事务保证 | ✅ 必须 | ✅ 同一事务内完成 | ✅ 符合 |
| 并发控制 | ✅ 必须 | ✅ SELECT FOR UPDATE | ✅ 符合 |

---

### 2. 对账批次设计

#### 业界最佳实践

**标准做法**:
- **批次周期**: 通常按月或按周进行对账
- **自动化程度**: 业界趋势为全自动化对账（API 对接供应商系统）
- **差异阈值**: 设置差异容忍度（如 <1% 自动核销）
- **状态流转**: draft → processing → reviewed → approved → completed
- **明细粒度**: 支持账户级、日期级、广告系列级明细对账

**典型流程**:
```
业界标准对账流程:
1. 自动拉取供应商对账单（API/文件导入）
2. 自动匹配我方消耗数据（按账户/日期/系列）
3. 自动计算差异（difference = our_spend - supplier_spend）
4. 差异分析（阈值判断、异常检测）
5. 自动/半自动调整（小差异自动核销，大差异人工审核）
6. 生成对账报告（PDF/Excel）
```

**关键特性**:
- ✅ 全自动化对账（API 对接）
- ✅ 智能差异分析（阈值判断、异常检测）
- ✅ 多维度明细对账（账户/日期/系列）
- ✅ 自动调整建议（increase/decrease/writeoff）

#### AI_ad_spend02 现有设计

**当前实现** (RECONCILIATION_SOT.md v1.0):

```sql
-- 对账批次表
reconciliation_batches (
    batch_no, supplier_id, channel_id,
    period_start, period_end,
    our_total_spend, supplier_total_spend,
    difference, difference_rate,
    status: draft/pending_review/approved/needs_adjustment/completed
)

-- 对账明细表
reconciliation_details (
    batch_id, ad_account_id, report_date,
    system_spend, external_spend, difference_amount,
    status: pending/confirmed/adjusted
)

-- 对账调整表
reconciliation_adjustments (
    detail_id, adjustment_type: increase/decrease/writeoff,
    amount, reason
)
```

**对账流程**:
1. 手动创建批次（data_operator/finance）
2. 自动计算 `our_total_spend`（从 daily_reports.real_spend 汇总）
3. 手动输入 `supplier_total_spend`（来自供应商对账单）
4. 自动计算差异
5. 手动创建明细和调整
6. 审批流程（finance/admin）

**对比结果**: ⚠️ **部分符合，自动化程度有待提升**

| 特性 | 业界标准 | AI_ad_spend02 | 差距 |
|------|---------|--------------|------|
| 批次周期设计 | ✅ 支持 | ✅ 支持（period_start/period_end） | ✅ 符合 |
| 自动化程度 | ✅ 全自动化（API 对接） | ⚠️ 半自动化（手动输入 supplier_spend） | ⚠️ 需改进 |
| 差异阈值 | ✅ 自动核销小差异 | ⚠️ 需手动判断 | ⚠️ 需改进 |
| 明细粒度 | ✅ 账户/日期级 | ✅ 支持（ad_account_id, report_date） | ✅ 符合 |
| 状态流转 | ✅ 完整状态机 | ✅ 完整状态机 | ✅ 符合 |
| 调整建议 | ✅ 自动生成 | ⚠️ 需手动创建 | ⚠️ 需改进 |

---

### 3. 多币种支持（USDT/CNY）

#### 业界最佳实践

**标准做法**:
- **多币种账本**: 每个账本支持多币种（USD, CNY, EUR, USDT 等）
- **汇率管理**: 维护汇率表，支持历史汇率和实时汇率
- **本位币转换**: 所有交易记录原币种，报表时转换为本位币
- **汇率差异处理**: 汇率波动产生的差异单独记录

**典型设计**:
```sql
-- 业界标准多币种账本设计
ledger_entries (
    amount DECIMAL(15,2),        -- 原币种金额
    currency VARCHAR(10),       -- 原币种（USD/CNY/USDT）
    base_amount DECIMAL(15,2),  -- 本位币金额（CNY）
    exchange_rate DECIMAL(12,6), -- 汇率
    exchange_rate_date DATE     -- 汇率日期
)

-- 汇率表
exchange_rates (
    from_currency VARCHAR(10),
    to_currency VARCHAR(10),
    rate DECIMAL(12,6),
    effective_date DATE,
    source VARCHAR(50)  -- 'manual' / 'api' / 'bank'
)
```

**关键特性**:
- ✅ 原币种记录 + 本位币转换
- ✅ 历史汇率追溯（支持不同时点汇率）
- ✅ 汇率差异单独核算
- ✅ 多币种余额查询（按币种汇总）

#### AI_ad_spend02 现有设计

**当前实现**:

```sql
-- 当前 ledger_entries 表
ledger_entries (
    amount DECIMAL(15,2),
    currency VARCHAR(10) DEFAULT 'CNY'  -- 固定 CNY
)
```

**现状**:
- ❌ 仅支持单一币种（CNY）
- ❌ 无汇率表设计
- ❌ 无本位币转换逻辑
- ⚠️ 部分表有 `currency` 字段但都默认 CNY

**对比结果**: ❌ **不符合业界标准，需要重大改进**

| 特性 | 业界标准 | AI_ad_spend02 | 差距 |
|------|---------|--------------|------|
| 多币种支持 | ✅ 必须 | ❌ 仅 CNY | ❌ 需重大改进 |
| 汇率管理 | ✅ 必须 | ❌ 无 | ❌ 需重大改进 |
| 本位币转换 | ✅ 必须 | ❌ 无 | ❌ 需重大改进 |
| 汇率差异处理 | ✅ 必须 | ❌ 无 | ❌ 需重大改进 |

---

### 4. 项目/投手维度利润表

#### 业界最佳实践

**标准做法**:
- **多维度利润分析**: 项目维度、投手维度、客户维度、渠道维度
- **实时利润计算**: 支持实时查询和历史追溯
- **利润分解**: 收入、成本、毛利、毛利率、净利
- **对比分析**: 支持同比、环比、预算对比

**典型利润表结构**:
```
业界标准利润表:
├── 项目维度利润表
│   ├── 项目收入（按粉数计费）
│   ├── 项目成本（供应商消耗）
│   ├── 项目毛利
│   └── 项目毛利率
├── 投手维度利润表
│   ├── 投手负责项目收入
│   ├── 投手负责项目成本
│   ├── 投手贡献毛利
│   └── 投手贡献毛利率
└── 客户维度利润表
    ├── 客户总充值
    ├── 客户总消耗
    ├── 客户余额
    └── 客户 ROI
```

**关键特性**:
- ✅ 多维度利润分析（项目/投手/客户/渠道）
- ✅ 实时计算和历史追溯
- ✅ 利润分解（收入/成本/毛利/毛利率）
- ✅ 对比分析（同比/环比/预算）

#### AI_ad_spend02 现有设计

**当前实现** (API_SOT.md §11A):

```sql
-- 利润计算逻辑
profit = revenue - cost
profit_margin = profit / revenue × 100

-- API 端点
GET /api/v1/finance/profit/summary?project_id=1
```

**支持维度**:
- ✅ 项目维度利润表（通过 project_id 查询）
- ❌ 投手维度利润表（未实现）
- ⚠️ 客户维度（可通过项目间接查询）
- ⚠️ 渠道维度（可通过项目间接查询）

**对比结果**: ⚠️ **部分符合，缺少投手维度**

| 特性 | 业界标准 | AI_ad_spend02 | 差距 |
|------|---------|--------------|------|
| 项目维度 | ✅ 必须 | ✅ 已实现 | ✅ 符合 |
| 投手维度 | ✅ 必须 | ❌ 未实现 | ❌ 需改进 |
| 客户维度 | ✅ 建议 | ⚠️ 间接支持 | ⚠️ 可优化 |
| 渠道维度 | ✅ 建议 | ⚠️ 间接支持 | ⚠️ 可优化 |
| 实时计算 | ✅ 必须 | ✅ 已实现 | ✅ 符合 |
| 利润分解 | ✅ 必须 | ✅ 已实现 | ✅ 符合 |

---

## 🎯 改进建议（3 条可采纳）

### 建议 1: 增加多币种支持（USDT/CNY）

**优先级**: P0（高优先级）

**现状问题**:
- 当前系统仅支持 CNY，无法处理 USDT 充值和多币种交易
- 跨境广告代理业务需要多币种支持

**业界做法**:
- 账本记录原币种金额和本位币金额
- 维护汇率表，支持历史汇率和实时汇率
- 报表时统一转换为本位币（CNY）

**改进方案**:

#### 1.1 扩展 ledger_entries 表结构

```sql
-- 修改 ledger_entries 表
ALTER TABLE ledger_entries
    ADD COLUMN base_amount DECIMAL(15,2),      -- 本位币金额（CNY）
    ADD COLUMN exchange_rate DECIMAL(12,6),   -- 汇率
    ADD COLUMN exchange_rate_date DATE,       -- 汇率日期
    ALTER COLUMN currency DROP DEFAULT;       -- 移除默认值，支持多币种

-- 新增汇率表
CREATE TABLE exchange_rates (
    id BIGSERIAL PRIMARY KEY,
    from_currency VARCHAR(10) NOT NULL,      -- 源币种
    to_currency VARCHAR(10) NOT NULL,          -- 目标币种（通常为 CNY）
    rate DECIMAL(12,6) NOT NULL,              -- 汇率
    effective_date DATE NOT NULL,              -- 生效日期
    source VARCHAR(50) DEFAULT 'manual',      -- 来源：'manual' / 'api' / 'bank'
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(from_currency, to_currency, effective_date)
);
```

#### 1.2 扩展余额字段

```sql
-- 项目余额表（多币种）
ALTER TABLE projects
    ADD COLUMN balance_usdt DECIMAL(15,2) DEFAULT 0.00,
    ADD COLUMN balance_cny DECIMAL(15,2) DEFAULT 0.00;

-- 供应商余额表（多币种）
ALTER TABLE suppliers
    ADD COLUMN balance_usdt DECIMAL(15,2) DEFAULT 0.00,
    ADD COLUMN balance_cny DECIMAL(15,2) DEFAULT 0.00;
```

#### 1.3 汇率服务设计

```python
# backend/services/exchange_rate_service.py
class ExchangeRateService:
    """汇率服务"""
    
    @staticmethod
    def get_rate(
        db: Session,
        from_currency: str,
        to_currency: str,
        date: date = None
    ) -> Decimal:
        """
        获取汇率
        - 如果 date 为 None，使用最新汇率
        - 如果 date 指定，使用该日期的历史汇率
        """
        if date is None:
            date = date.today()
        
        rate = db.query(ExchangeRate).filter(
            ExchangeRate.from_currency == from_currency,
            ExchangeRate.to_currency == to_currency,
            ExchangeRate.effective_date <= date
        ).order_by(ExchangeRate.effective_date.desc()).first()
        
        if not rate:
            raise BusinessError(code="EXCHANGE_001", message="汇率不存在")
        
        return rate.rate
    
    @staticmethod
    def convert_amount(
        db: Session,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        date: date = None
    ) -> Decimal:
        """金额转换"""
        if from_currency == to_currency:
            return amount
        
        rate = ExchangeRateService.get_rate(db, from_currency, to_currency, date)
        return amount * rate
```

#### 1.4 账本记录扩展

```python
# 修改 ledger_entry 创建逻辑
ledger_entry = LedgerEntry(
    ledger_type="PROJECT",
    entry_type="TOPUP",
    amount=Decimal("1000.00"),           # 原币种金额（USDT）
    currency="USDT",                     # 原币种
    base_amount=Decimal("7200.00"),      # 本位币金额（CNY，按汇率转换）
    exchange_rate=Decimal("7.2"),         # 汇率（USDT/CNY）
    exchange_rate_date=date.today(),     # 汇率日期
    project_id=project_id,
    ...
)
```

**影响范围**:
- `LEDGER_SOT.md`: 需要更新双账本规则，支持多币种
- `DATA_SCHEMA.md`: 需要新增 `exchange_rates` 表定义
- `RECONCILIATION_SOT.md`: 需要支持多币种对账
- `backend/services/ledger_service.py`: 需要支持多币种转换

**预期收益**:
- ✅ 支持 USDT/CNY 等多币种交易
- ✅ 支持跨境广告代理业务
- ✅ 符合业界标准

---

### 建议 2: 提升对账自动化程度

**优先级**: P1（中优先级）

**现状问题**:
- 当前对账流程为半自动化：需要手动输入 `supplier_total_spend`
- 业界趋势为全自动化对账（API 对接供应商系统）

**业界做法**:
- API 对接供应商系统，自动拉取对账单
- 自动匹配我方消耗数据
- 智能差异分析（阈值判断、异常检测）
- 自动调整建议（小差异自动核销）

**改进方案**:

#### 2.1 新增供应商 API 对接模块

```python
# backend/services/supplier_api_service.py
class SupplierAPIService:
    """供应商 API 对接服务"""
    
    @staticmethod
    async def fetch_reconciliation_statement(
        supplier_id: UUID,
        channel_id: UUID,
        period_start: date,
        period_end: date
    ) -> Dict:
        """
        从供应商 API 拉取对账单
        - 支持 Meta Ads API
        - 支持 Google Ads API
        - 支持自定义 API 格式
        """
        supplier = get_supplier(supplier_id)
        
        if supplier.api_type == "meta_ads":
            return await fetch_meta_ads_statement(
                supplier.api_config,
                channel_id,
                period_start,
                period_end
            )
        elif supplier.api_type == "google_ads":
            return await fetch_google_ads_statement(
                supplier.api_config,
                channel_id,
                period_start,
                period_end
            )
        else:
            raise BusinessError(code="SUPPLIER_001", message="不支持的 API 类型")
```

#### 2.2 自动对账批次创建

```python
# backend/services/reconciliation_service.py
class ReconciliationService:
    """对账服务（增强版）"""
    
    @staticmethod
    async def create_reconciliation_batch_auto(
        db: Session,
        supplier_id: UUID,
        channel_id: UUID,
        period_start: date,
        period_end: date,
        user_id: UUID
    ) -> ReconciliationBatch:
        """
        自动创建对账批次（全自动化）
        """
        # 1. 自动计算我方消耗
        our_total_spend = calculate_our_spend(
            db, supplier_id, channel_id, period_start, period_end
        )
        
        # 2. 自动拉取供应商对账单
        supplier_statement = await SupplierAPIService.fetch_reconciliation_statement(
            supplier_id, channel_id, period_start, period_end
        )
        supplier_total_spend = supplier_statement['total_spend']
        
        # 3. 自动计算差异
        difference = our_total_spend - supplier_total_spend
        difference_rate = (difference / supplier_total_spend * 100) if supplier_total_spend > 0 else 0
        
        # 4. 自动创建批次
        batch = ReconciliationBatch(
            supplier_id=supplier_id,
            channel_id=channel_id,
            period_start=period_start,
            period_end=period_end,
            our_total_spend=our_total_spend,
            supplier_total_spend=supplier_total_spend,
            difference=difference,
            difference_rate=difference_rate,
            source='api_import',  # 标记为 API 导入
            status='draft',
            created_by=user_id
        )
        db.add(batch)
        
        # 5. 自动创建明细（按账户/日期）
        await create_reconciliation_details_auto(db, batch.id, supplier_statement)
        
        # 6. 智能差异分析
        if abs(difference_rate) < 1.0:  # 差异率 < 1%，自动核销
            batch.status = 'approved'
            create_adjustment_auto(db, batch.id, 'writeoff', difference)
        elif abs(difference) < 10.00:  # 差异金额 < 10元，自动核销
            batch.status = 'approved'
            create_adjustment_auto(db, batch.id, 'writeoff', difference)
        else:
            batch.status = 'pending_review'  # 大差异需人工审核
        
        db.commit()
        return batch
```

#### 2.3 智能差异分析

```python
# backend/services/reconciliation_analysis_service.py
class ReconciliationAnalysisService:
    """对账差异分析服务"""
    
    @staticmethod
    def analyze_difference(
        difference: Decimal,
        difference_rate: Decimal,
        our_total_spend: Decimal
    ) -> Dict:
        """
        智能差异分析
        - 阈值判断
        - 异常检测
        - 调整建议
        """
        analysis = {
            "severity": "low",  # low / medium / high
            "auto_resolvable": False,
            "suggested_action": None,
            "reason": None
        }
        
        # 小差异自动核销
        if abs(difference_rate) < 1.0 or abs(difference) < 10.00:
            analysis["severity"] = "low"
            analysis["auto_resolvable"] = True
            analysis["suggested_action"] = "writeoff"
            analysis["reason"] = "差异在容忍范围内，建议自动核销"
        
        # 中等差异需人工审核
        elif abs(difference_rate) < 5.0:
            analysis["severity"] = "medium"
            analysis["auto_resolvable"] = False
            analysis["suggested_action"] = "manual_review"
            analysis["reason"] = "差异需人工审核"
        
        # 大差异需立即处理
        else:
            analysis["severity"] = "high"
            analysis["auto_resolvable"] = False
            analysis["suggested_action"] = "urgent_review"
            analysis["reason"] = "差异较大，需立即处理"
        
        return analysis
```

**影响范围**:
- `RECONCILIATION_SOT.md`: 需要更新对账流程，支持自动化
- `DATA_SCHEMA.md`: 需要新增 `supplier_api_configs` 表（存储 API 配置）
- `backend/services/reconciliation_service.py`: 需要实现自动化逻辑
- `backend/services/supplier_api_service.py`: 需要新增供应商 API 对接服务

**预期收益**:
- ✅ 减少人工操作（从手动输入到自动拉取）
- ✅ 提高对账效率（从数小时到数分钟）
- ✅ 降低人为错误（自动匹配和计算）
- ✅ 符合业界趋势（全自动化对账）

---

### 建议 3: 增加投手维度利润表

**优先级**: P1（中优先级）

**现状问题**:
- 当前利润表仅支持项目维度
- 缺少投手（media_buyer）维度的利润分析
- 无法评估投手的贡献和 ROI

**业界做法**:
- 支持多维度利润分析（项目/投手/客户/渠道）
- 投手维度利润 = 投手负责项目的收入 - 成本
- 支持投手绩效排名和贡献分析

**改进方案**:

#### 3.1 扩展利润表 API

```python
# backend/routers/finance_profit.py
@router.get("/profit/summary")
async def get_profit_summary(
    project_id: Optional[int] = None,
    media_buyer_id: Optional[UUID] = None,  # 新增：投手维度
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    dimension: str = "project"  # 'project' / 'media_buyer' / 'client' / 'channel'
):
    """
    获取利润汇总（支持多维度）
    - dimension=project: 项目维度（现有功能）
    - dimension=media_buyer: 投手维度（新增）
    - dimension=client: 客户维度（新增）
    - dimension=channel: 渠道维度（新增）
    """
    if dimension == "media_buyer":
        return await get_media_buyer_profit_summary(
            media_buyer_id, start_date, end_date
        )
    elif dimension == "project":
        return await get_project_profit_summary(
            project_id, start_date, end_date
        )
    # ...
```

#### 3.2 投手维度利润计算逻辑

```python
# backend/services/finance_profit_service.py
class FinanceProfitService:
    """财务利润服务（扩展版）"""
    
    @staticmethod
    def get_media_buyer_profit_summary(
        db: Session,
        media_buyer_id: UUID,
        start_date: date = None,
        end_date: date = None
    ) -> Dict:
        """
        获取投手维度利润汇总
        
        计算逻辑:
        1. 查询投手负责的项目（通过 project_members 表）
        2. 汇总项目收入（PROJECT 账本 REVENUE）
        3. 汇总项目成本（SUPPLIER 账本 COST）
        4. 计算投手贡献毛利 = 收入 - 成本
        """
        # 1. 查询投手负责的项目
        projects = db.query(Project).join(ProjectMember).filter(
            ProjectMember.user_id == media_buyer_id,
            ProjectMember.role == 'media_buyer'
        ).all()
        
        project_ids = [p.id for p in projects]
        
        # 2. 汇总收入（PROJECT 账本）
        revenue_query = db.query(
            func.sum(LedgerEntry.amount)
        ).filter(
            LedgerEntry.ledger_type == 'PROJECT',
            LedgerEntry.entry_type == 'REVENUE',
            LedgerEntry.project_id.in_(project_ids)
        )
        
        if start_date:
            revenue_query = revenue_query.filter(
                LedgerEntry.occurred_at >= start_date
            )
        if end_date:
            revenue_query = revenue_query.filter(
                LedgerEntry.occurred_at <= end_date
            )
        
        total_revenue = revenue_query.scalar() or Decimal("0.00")
        
        # 3. 汇总成本（SUPPLIER 账本）
        # 通过 daily_reports 关联项目，再关联供应商
        cost_query = db.query(
            func.sum(LedgerEntry.amount)
        ).join(
            DailyReport, LedgerEntry.reference_id == DailyReport.id
        ).filter(
            LedgerEntry.ledger_type == 'SUPPLIER',
            LedgerEntry.entry_type == 'COST',
            DailyReport.project_id.in_(project_ids)
        )
        
        if start_date:
            cost_query = cost_query.filter(
                LedgerEntry.occurred_at >= start_date
            )
        if end_date:
            cost_query = cost_query.filter(
                LedgerEntry.occurred_at <= end_date
            )
        
        total_cost = abs(cost_query.scalar() or Decimal("0.00"))  # COST 为负数，取绝对值
        
        # 4. 计算利润
        total_profit = total_revenue - total_cost
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            "media_buyer_id": str(media_buyer_id),
            "media_buyer_name": get_user_name(media_buyer_id),
            "project_count": len(project_ids),
            "total_revenue": str(total_revenue),
            "total_cost": str(total_cost),
            "total_profit": str(total_profit),
            "profit_margin": float(profit_margin),
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }
    
    @staticmethod
    def get_media_buyer_profit_ranking(
        db: Session,
        start_date: date = None,
        end_date: date = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        获取投手利润排名（Top N）
        """
        # 查询所有投手
        media_buyers = db.query(User).filter(
            User.role == 'media_buyer'
        ).all()
        
        rankings = []
        for buyer in media_buyers:
            summary = FinanceProfitService.get_media_buyer_profit_summary(
                db, buyer.id, start_date, end_date
            )
            rankings.append(summary)
        
        # 按利润排序
        rankings.sort(key=lambda x: Decimal(x['total_profit']), reverse=True)
        
        return rankings[:limit]
```

#### 3.3 API 端点扩展

```python
# 新增 API 端点
GET /api/v1/finance/profit/summary?dimension=media_buyer&media_buyer_id={id}
GET /api/v1/finance/profit/ranking?dimension=media_buyer&limit=10
```

**影响范围**:
- `API_SOT.md`: 需要新增投手维度利润 API 端点
- `backend/services/finance_profit_service.py`: 需要实现投手维度计算逻辑
- `backend/routers/finance_profit.py`: 需要新增投手维度端点
- `DATA_SCHEMA.md`: 需要确认 `project_members` 表支持投手角色关联

**预期收益**:
- ✅ 支持投手绩效评估
- ✅ 支持投手贡献分析
- ✅ 支持投手利润排名
- ✅ 符合业界标准（多维度利润分析）

---

## 📊 对标总结表

| 维度 | 业界标准 | AI_ad_spend02 现状 | 差距等级 | 改进优先级 |
|------|---------|-------------------|---------|-----------|
| **账本双录** | 收入/成本完全隔离 | ✅ PROJECT/SUPPLIER 完全隔离 | ✅ 符合 | - |
| **余额双写** | balance 字段 + ledger 流水 | ✅ 已实现 | ✅ 符合 | - |
| **对账批次** | 支持周期、状态、明细 | ✅ 已实现 | ✅ 符合 | - |
| **对账自动化** | 全自动化（API 对接） | ⚠️ 半自动化（手动输入） | ⚠️ 中等差距 | P1 |
| **多币种支持** | 必须支持（USD/CNY/USDT） | ❌ 仅支持 CNY | ❌ 重大差距 | P0 |
| **汇率管理** | 必须支持历史汇率 | ❌ 无 | ❌ 重大差距 | P0 |
| **项目维度利润** | 必须支持 | ✅ 已实现 | ✅ 符合 | - |
| **投手维度利润** | 必须支持 | ❌ 未实现 | ❌ 中等差距 | P1 |

---

## 🎯 实施路线图

### Phase 1: 多币种支持（P0，3-4 周）

**Week 1-2**: 数据库设计
- 新增 `exchange_rates` 表
- 扩展 `ledger_entries` 表（base_amount, exchange_rate, exchange_rate_date）
- 扩展 `projects` / `suppliers` 余额字段（balance_usdt, balance_cny）

**Week 3**: 服务层实现
- 实现 `ExchangeRateService`
- 修改 `LedgerService` 支持多币种转换
- 修改余额更新逻辑支持多币种

**Week 4**: API 和测试
- 新增汇率管理 API
- 修改现有 API 支持多币种
- 编写测试用例

### Phase 2: 对账自动化（P1，2-3 周）

**Week 1**: API 对接模块
- 实现 `SupplierAPIService`
- 支持 Meta Ads API / Google Ads API
- 实现自动拉取对账单

**Week 2**: 自动化对账流程
- 实现 `create_reconciliation_batch_auto`
- 实现智能差异分析
- 实现自动调整建议

**Week 3**: 测试和优化
- 编写测试用例
- 性能优化
- 错误处理完善

### Phase 3: 投手维度利润表（P1，1-2 周）

**Week 1**: 服务层实现
- 实现 `get_media_buyer_profit_summary`
- 实现 `get_media_buyer_profit_ranking`

**Week 2**: API 和测试
- 新增投手维度 API 端点
- 编写测试用例
- 更新 API_SOT.md

---

## 📚 参考来源

### 业界标准来源

1. **广告代理行业财务系统**: 
   - 基于广告代理管理系统的通用设计模式
   - 参考 ERP 系统的财务模块设计

2. **多币种会计系统**:
   - 国际财务报告准则（IFRS）多币种处理规范
   - 跨境业务财务系统设计最佳实践

3. **对账自动化**:
   - 广告平台 API 对接实践（Meta Ads API, Google Ads API）
   - 企业级对账系统自动化设计

4. **利润表多维度分析**:
   - BI 系统多维度分析设计
   - 广告代理业务分析最佳实践

---

## 📝 结论

AI_ad_spend02 项目的 ledger / reconciliation 设计在**双账本隔离**和**余额双写**方面完全符合业界标准，但在**多币种支持**、**对账自动化**和**投手维度利润表**方面存在改进空间。

**建议采纳的 3 条改进**:
1. ✅ **增加多币种支持（USDT/CNY）** - P0 优先级，支持跨境业务
2. ✅ **提升对账自动化程度** - P1 优先级，提高效率和准确性
3. ✅ **增加投手维度利润表** - P1 优先级，支持绩效评估

实施这些改进后，系统将更符合业界最佳实践，能够更好地支持跨境广告代理业务和精细化运营管理。

---

**报告生成时间**: 2025-12-07  
**研究工具**: Web Search + SoT 文档分析  
**下一步**: 根据改进建议制定详细实施计划

