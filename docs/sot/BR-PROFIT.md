# BR-PROFIT - 利润统计规则

> **文档版本**: v1.0
> **status**: active
> **owner**: wade
> **last_reviewed**: 2025-12-27
> **父文档**: BUSINESS_RULES.md v4.6
> **关联 SoT**: DATA_SCHEMA.md v5.6 §3.6, API_SOT.md v9.0

---

## 互锁 SoT 引用

| SoT 文档 | 版本 | 引用章节 | 引用内容 |
|----------|------|----------|----------|
| BUSINESS_RULES.md | v4.6 | §4.9 | 规则索引定义 |
| DATA_SCHEMA.md | v5.6 | §3.6 | profit_aggregates 表结构 |
| API_SOT.md | v9.0 | §2.3.3 | 账本公式定义 |
| ERROR_CODES.md | v2.3 | §4.8 | PROFIT_ 错误码 |
| STATE_MACHINE.md | v2.7 | §5 | 日报 final_locked 状态 |

---

## 规则总览

| 规则ID | 规则名称 | 优先级 | 测试状态 |
|--------|----------|--------|----------|
| BR-PROFIT-001 | 收入公式（per_lead） | P0 | ✅ |
| BR-PROFIT-002 | 收入公式（fee_rate） | P0 | 🟡 |
| BR-PROFIT-003 | 成本公式 | P0 | ✅ |
| BR-PROFIT-004 | 毛利公式 | P0 | ✅ |
| BR-PROFIT-005 | CPL 公式 | P1 | 🟡 |
| BR-PROFIT-006 | 低量标记 | P2 | 🟡 |

---

## 核心公式定义

> **引用**: DATA_SCHEMA.md v5.6 §3.6, API_SOT.md v9.0 §2.3.3

### 利润计算公式链

```
┌─────────────────────────────────────────────────────────────────┐
│                      利润计算公式链                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [收入 Revenue]                                                 │
│  ├── per_lead 模式: conversions_final × unit_price             │
│  └── fee_rate 模式: ad_spend × service_fee_rate                │
│                                                                 │
│  [成本 Cost]                                                    │
│  └── real_spend + fee（手续费）                                 │
│                                                                 │
│  [毛利 Gross Profit]                                            │
│  └── revenue - cost                                             │
│                                                                 │
│  [毛利率 Gross Margin %]                                        │
│  └── (gross_profit / revenue) × 100                            │
│                                                                 │
│  [CPL (Cost Per Lead)]                                          │
│  └── ad_spend / conversions_final                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 规则详细定义

### BR-PROFIT-001: 收入公式（per_lead）

#### 业务场景
per_lead（按粉计费）是系统主要的结算模式，客户按照实际获取的线索数量付费。收入计算基于运营确认的最终粉数（conversions_final）乘以项目约定的单粉价格（unit_price）。

#### 详细约束
- 📌 **强制**: 收入公式 = `conversions_final × unit_price`
- 📌 **强制**: conversions_final 必须来自 final_locked 状态的日报
- 📌 **强制**: unit_price 从项目配置继承，精度 DECIMAL(15,2)
- ❌ **禁止**: 使用未确认的粉数（raw_conversions）计算收入
- ❌ **禁止**: 手动修改已锁定日报的 conversions_final
- ✅ **允许**: unit_price 为 0（测试项目）

#### 公式详解
```
revenue = conversions_final × unit_price

其中：
- conversions_final: 运营确认的最终粉数（T+1 14:00 前确认）
- unit_price: 项目单粉价格，单位：元/粉
```

#### 前置条件
- 数据状态: 日报状态为 `final_locked`
- 引用: DATA_SCHEMA.md v5.6 §3.2.8（daily_reports.conversions_final）

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 日报未锁定 | `PROFIT_001` | 404 | 指定期间无已锁定日报数据 |
| unit_price 未配置 | `VALIDATION_001` | 400 | 项目单粉价格未配置 |
| 计算失败 | `PROFIT_006` | 500 | 收入计算失败 |

#### 代码引用
- Service: `backend/services/profit_service.py`
- 方法: `calculate_revenue_per_lead()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 正常计算 | conversions=100, price=50 | revenue=5000.00 |
| T2 | 日报未锁定 | status=final_pending | `PROFIT_001` |
| T3 | unit_price=0 | 测试项目 | revenue=0.00 |
| T4 | 小数精度 | conversions=3, price=33.33 | revenue=99.99 |

---

### BR-PROFIT-002: 收入公式（fee_rate）

#### 业务场景
fee_rate（服务费率）模式适用于代运营服务，收入按广告消耗的固定比例收取。这种模式下，系统收入与广告投放规模挂钩，而非转化效果。

#### 详细约束
- 📌 **强制**: 收入公式 = `ad_spend × service_fee_rate`
- 📌 **强制**: service_fee_rate 必须在 0-100% 范围内
- 📌 **强制**: ad_spend 使用 real_spend（运营确认消耗）
- ❌ **禁止**: fee_rate 模式使用粉数计算收入
- ❌ **禁止**: 项目创建后修改结算模式
- ✅ **允许**: service_fee_rate = 0%（纯代投不收费）

#### 公式详解
```
revenue = real_spend × service_fee_rate

其中：
- real_spend: 运营确认的真实消耗（T+1 12:00 前录入）
- service_fee_rate: 服务费率，范围 0.00-1.00（0%-100%）
```

#### 前置条件
- 项目配置: settlement_mode = 'fee_rate'
- 引用: DATA_SCHEMA.md v5.6 §3.2.5（projects.settlement_mode）

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 费率超范围 | `VALIDATION_001` | 400 | 服务费率必须在 0-100% 之间 |
| 模式不匹配 | `BIZ_001` | 400 | 项目结算模式不支持此计算 |
| 计算失败 | `PROFIT_006` | 500 | 收入计算失败 |

#### 代码引用
- Service: `backend/services/profit_service.py`
- 方法: `calculate_revenue_fee_rate()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 正常计算 | spend=10000, rate=0.15 | revenue=1500.00 |
| T2 | 费率=0 | rate=0 | revenue=0.00 |
| T3 | 费率超范围 | rate=1.5 | `VALIDATION_001` |
| T4 | 模式错误 | mode=per_lead | `BIZ_001` |

---

### BR-PROFIT-003: 成本公式

#### 业务场景
成本由两部分组成：广告消耗（real_spend）和平台手续费（fee）。手续费是支付给广告平台的服务费用，与广告消耗分开核算，确保成本计算的准确性。

#### 详细约束
- 📌 **强制**: 成本公式 = `real_spend + fee`
- 📌 **强制**: real_spend 和 fee 必须 >= 0
- 📌 **强制**: 手续费独立核算，不计入广告消耗
- ❌ **禁止**: 成本为负数
- ❌ **禁止**: 将手续费合并到广告消耗字段
- ✅ **允许**: fee = 0（无手续费场景）

#### 公式详解
```
cost = real_spend + fee

其中：
- real_spend: 运营确认的真实消耗（广告费）
- fee: 平台手续费（如返点扣除、服务费等）
```

#### 前置条件
- 数据状态: 日报已提交消耗数据
- 引用: DATA_SCHEMA.md v5.6 §3.2.8（daily_reports.real_spend, fee）

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 消耗为负 | `BIZ_101` | 400 | 消耗金额不能为负数 |
| 手续费为负 | `BIZ_101` | 400 | 手续费不能为负数 |
| 计算失败 | `PROFIT_006` | 500 | 成本计算失败 |

#### 代码引用
- Service: `backend/services/profit_service.py`
- 方法: `calculate_cost()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 正常计算 | spend=1000, fee=50 | cost=1050.00 |
| T2 | 无手续费 | spend=1000, fee=0 | cost=1000.00 |
| T3 | 消耗为负 | spend=-100 | `BIZ_101` |
| T4 | 手续费为负 | fee=-50 | `BIZ_101` |

---

### BR-PROFIT-004: 毛利公式

#### 业务场景
毛利是衡量项目盈利能力的核心指标，反映收入覆盖成本后的剩余利润。毛利率则用于评估项目的盈利效率，便于跨项目对比。

#### 详细约束
- 📌 **强制**: 毛利公式 = `revenue - cost`
- 📌 **强制**: 毛利率公式 = `(gross_profit / revenue) × 100`
- 📌 **强制**: revenue = 0 时，毛利率为 NULL（避免除零）
- ✅ **允许**: 毛利为负数（亏损项目）
- ✅ **允许**: 毛利率 > 100%（低成本高收入）
- 📌 **强制**: Phase 1 毛利为负仅告警，不阻断

#### 公式详解
```
gross_profit = revenue - cost
gross_margin_pct = (gross_profit / revenue) × 100

其中：
- revenue: 项目收入（per_lead 或 fee_rate 计算）
- cost: 项目成本（real_spend + fee）
- 毛利率保留两位小数，HALF_UP 四舍五入
```

#### 前置条件
- 数据状态: 收入和成本已计算
- 引用: DATA_SCHEMA.md v5.6 §3.6.1（profit_aggregates.gross_profit）

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 收入数据缺失 | `PROFIT_001` | 404 | 指定期间无收入数据 |
| 成本数据缺失 | `PROFIT_001` | 404 | 指定期间无成本数据 |
| 计算失败 | `PROFIT_006` | 500 | 毛利计算失败 |

#### 代码引用
- Service: `backend/services/profit_service.py`
- 方法: `calculate_gross_profit()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 正常盈利 | revenue=5000, cost=3000 | profit=2000, margin=40% |
| T2 | 亏损项目 | revenue=1000, cost=1500 | profit=-500, margin=-50% |
| T3 | 零收入 | revenue=0, cost=100 | profit=-100, margin=NULL |
| T4 | 零成本 | revenue=1000, cost=0 | profit=1000, margin=100% |

---

### BR-PROFIT-005: CPL 公式

#### 业务场景
CPL（Cost Per Lead，单粉成本）是投放效率的核心指标，反映获取每个线索的平均成本。投手的绩效考核和账户优化决策都依赖 CPL 数据。

#### 详细约束
- 📌 **强制**: CPL 公式 = `ad_spend / conversions_final`
- 📌 **强制**: conversions_final = 0 时，CPL 为 NULL（避免除零）
- 📌 **强制**: CPL 保留两位小数，HALF_UP 四舍五入
- ✅ **允许**: CPL 值无上限（低效投放）
- ❌ **禁止**: CPL 为负数
- 📌 **强制**: 参考 BR-PROFIT-006 低量标记规则

#### 公式详解
```
cpl = ad_spend / conversions_final

其中：
- ad_spend: 广告消耗（real_spend 或 raw_spend）
- conversions_final: 运营确认的最终粉数
- 结果保留两位小数
```

#### 前置条件
- 数据状态: 日报包含消耗和粉数数据
- 引用: DATA_SCHEMA.md v5.6 §3.2.8

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 粉数为零 | `BIZ_001` | 400 | 粉数为零，无法计算 CPL |
| 消耗数据缺失 | `PROFIT_001` | 404 | 指定期间无消耗数据 |
| 计算失败 | `PROFIT_006` | 500 | CPL 计算失败 |

#### 代码引用
- Service: `backend/services/profit_service.py`
- 方法: `calculate_cpl()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 正常计算 | spend=1000, leads=20 | cpl=50.00 |
| T2 | 粉数为零 | spend=1000, leads=0 | cpl=NULL |
| T3 | 消耗为零 | spend=0, leads=10 | cpl=0.00 |
| T4 | 小数精度 | spend=100, leads=3 | cpl=33.33 |

---

### BR-PROFIT-006: 低量标记

#### 业务场景
当进粉数较少时，CPL 的统计意义降低，容易受单个异常数据影响。系统对低量数据进行标记，提示用户谨慎参考，避免基于不稳定数据做决策。

#### 详细约束
- 📌 **强制**: 进粉数 < 5 时，CPL 必须标记为「低量不稳定」
- 📌 **强制**: 标记通过 `cpl_flag` 字段实现
- 📌 **强制**: 低量标记不影响 CPL 计算结果
- ✅ **允许**: 前端展示时高亮低量数据
- ✅ **允许**: 报表统计时排除低量数据
- 📌 **强制**: Phase 1 仅标记提示，不阻断展示

#### 低量阈值定义
| 阈值 | 标记 | 说明 |
|------|------|------|
| conversions_final < 5 | `low_volume` | 低量不稳定 |
| conversions_final >= 5 | 无标记 | 正常统计 |

#### 前置条件
- 数据状态: CPL 已计算
- 引用: MASTER.md v4.6 §2.5（Phase 1 软性原则）

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 无 | - | - | 此规则不产生错误，仅标记提示 |

#### 代码引用
- Service: `backend/services/profit_service.py`
- 方法: `apply_low_volume_flag()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 低量标记 | leads=3 | cpl_flag='low_volume' |
| T2 | 正常量级 | leads=10 | cpl_flag=NULL |
| T3 | 边界值 | leads=5 | cpl_flag=NULL |
| T4 | 边界值 | leads=4 | cpl_flag='low_volume' |

---

## 规则依赖关系

```
BR-PROFIT-001/002 (收入公式)
         ↓
BR-PROFIT-003 (成本公式)
         ↓
BR-PROFIT-004 (毛利公式) ←── 依赖收入和成本
         ↓
BR-PROFIT-005 (CPL 公式)
         ↓
BR-PROFIT-006 (低量标记) ←── 依赖 CPL 结果
```

---

## 利润聚合层级

> **引用**: DATA_SCHEMA.md v5.6 §3.6

| 层级 | 聚合粒度 | 数据来源 | 存储表 |
|------|----------|----------|--------|
| L0 | 日报明细 | daily_reports | daily_reports |
| L1 | 账户-日 | L0 聚合 | ledger_entries |
| L2 | 项目-周期 | L1 聚合 | profit_aggregates |
| L3 | 报表快照 | L2 快照 | profit_report_snapshots |

---

## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2025-12-27 | 初始版本，对齐 BUSINESS_RULES.md v4.6；错误码对齐 ERROR_CODES.md v2.3（PROFIT_*系列） |

---

**文档性质**: 业务规则子模块
**执行级别**: 强制执行
**父文档**: BUSINESS_RULES.md v4.6
**关联 SoT**: DATA_SCHEMA.md v5.6 §3.6, API_SOT.md v9.0
**版本**: v1.0
