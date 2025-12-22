# AI 数据上下文 (AI Data Context)

本文档为 AI 助手提供数据理解的关键信息。

## 业务背景

这是一个 **广告代投管理系统** 的核心数据集，管理视角的四个维度：
- **人**: 投手(media_buyer)、团队(team)、绩效
- **事**: 项目(project)、地区(region)、进度
- **钱**: 消耗(spend)、收入(revenue)、利润(profit)、充值(topup)
- **数据**: 平台消耗对账、手续费计算、成效统计

## 团队编码

| 代码 | 名称 | 说明 |
|------|------|------|
| SZ | 深圳团队 | 主力团队 |
| ZZ | 郑州团队 | 含原金边团队 |
| EXT | 外包 | 单独核算 |

## 地区编码 (ISO 3166-1)

| 代码 | 名称 |
|------|------|
| IN | 印度 |
| DE | 德国 |
| SG | 新加坡 |
| US | 美国 |
| MY | 马来西亚 |
| TR | 土耳其 |
| ID | 印尼 |

## 核心表关系

```
ad_spend_daily (平台真实消耗)
    ├── media_buyer → media_buyer_dim.media_buyer
    └── 对账 → daily_report (按 date + media_buyer + region)

daily_report (投手自报)
    └── team → media_buyer_dim.team

project_pnl (项目收支)
    └── team, region → 可聚合验证
```

## 金额口径说明

| 字段 | 口径 | 计算逻辑 |
|------|------|----------|
| actual_spend | 实际消耗 | 当日平台扣费金额 |
| fee | 手续费 | actual_spend × 代理商费率 |
| spend_with_fee | 含手续费消耗 | actual_spend + fee |
| ad_spend_usd | 投手自报消耗 | 投手填报金额，需与 actual_spend 对账 |
| gross_profit | 项目毛利 | actual_revenue - total_spend |

## 唯一键定义

| 表 | 唯一键 |
|-----|--------|
| ad_spend_daily | (date, platform_id) |
| daily_report | (date, media_buyer, region) |
| media_buyer_dim | media_buyer |
| project_pnl | (month, team, project_name) |

## 数据质量注意

1. `platform_id` 为 Facebook 广告账户 ID (15-16位数字)
2. `#DIV/0!` 等 Excel 错误值已清洗为 null
3. 2024年数据已归档，当前仅含2025年
4. 代理商费率需从独立费率表获取

## 样本数据

### ad_spend_daily

```json
[
  {
    "date": "2025-07-01",
    "region": "DE",
    "media_buyer": "HW",
    "platform_id": "1815567322519393",
    "account_name": "FV92-zs-tthd-1642",
    "account_type": "美金户",
    "agent": "开户美国三不限户",
    "platform": "nan",
    "spend_today_cumulative": 0.04,
    "spend_yesterday_cumulative": NaN,
    "fee": NaN,
    "actual_spend": NaN,
    "spend_with_fee": NaN,
    "notes": null
  },
  {
    "date": "2025-07-01",
    "region": "IN",
    "media_buyer": "SG",
    "platform_id": "549740840492004",
    "account_name": "Momentus_client3-140425-5",
    "account_type": "印度户",
    "agent": "深圳芳林子",
    "platform": "65000.0",
    "spend_today_cumulative": 63251.55775,
    "spend_yesterday_cumulative": NaN,
    "fee": 1748.44225,
    "actual_spend": 2083.793474,
    "spend_with_fee": NaN,
    "notes": "335.3512236"
  },
  {
    "date": "2025-07-01",
    "region": "IN",
    "media_buyer": "HW",
    "platform_id": "768369575850195",
    "account_name": "VH_HK_9_ZYA-004",
    "account_type": "印度户",
    "agent": "深圳芳林子",
    "platform": "1268.202143",
    "spend_today_cumulative": NaN,
    "spend_yesterday_cumulative": NaN,
    "fee": 1268.202143,
    "actual_spend": 1485.825631,
    "spend_with_fee": NaN,
    "notes": "217.6234877"
  }
]
```

### daily_report

```json
[
  {
    "date": "2025-01-31",
    "media_buyer": "老郭",
    "region": "IN",
    "team": "SZ",
    "ad_spend_usd": 242.24,
    "result_count": 28.0,
    "lead_count": 5.0,
    "platform": null,
    "cost_per_lead": 48.448,
    "cost_per_result": 48.448
  },
  {
    "date": "2025-01-30",
    "media_buyer": "紫光",
    "region": "IN",
    "team": "SZ",
    "ad_spend_usd": 270.35,
    "result_count": 33.0,
    "lead_count": 16.0,
    "platform": null,
    "cost_per_lead": 16.896875,
    "cost_per_result": 16.896875
  },
  {
    "date": "2025-01-01",
    "media_buyer": "WD",
    "region": "IN",
    "team": "ZZ",
    "ad_spend_usd": 0.0,
    "result_count": 0.0,
    "lead_count": 0.0,
    "platform": null,
    "cost_per_lead": NaN,
    "cost_per_result": NaN
  }
]
```

### media_buyer_dim

```json
[
  {
    "media_buyer": "SG",
    "team": "ZZ"
  },
  {
    "media_buyer": "WD",
    "team": "ZZ"
  },
  {
    "media_buyer": "YJ",
    "team": "ZZ"
  }
]
```

### project_pnl

```json
[
  {
    "month": "11月",
    "team": "SZ",
    "business_type": "自投项目",
    "region": "DE",
    "project_name": "德国Summer",
    "lead_count": 227.0,
    "total_spend": 22713.24,
    "actual_revenue": 40860.0,
    "gross_profit": 18146.76,
    "prepaid_balance": "-",
    "notes": "-"
  },
  {
    "month": "11月",
    "team": "SZ",
    "business_type": "外部代投",
    "region": "JP",
    "project_name": "岳总",
    "lead_count": 205.0,
    "total_spend": 30750.0,
    "actual_revenue": 36900.0,
    "gross_profit": 6150.0,
    "prepaid_balance": "0",
    "notes": "-"
  },
  {
    "month": "11月",
    "team": "SZ",
    "business_type": "自投项目",
    "region": "SG",
    "project_name": "海总-新加坡、加拿大、美国",
    "lead_count": 1.0,
    "total_spend": 244.28,
    "actual_revenue": 100.0,
    "gross_profit": -144.28,
    "prepaid_balance": "5055",
    "notes": "海总-新加坡、加拿大、美国的预付款是一起的，11月结余合计5055"
  }
]
```
