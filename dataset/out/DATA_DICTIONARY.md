# 数据字典 (Data Dictionary)

> 生成时间: 2025-12-22 15:14:13
> 数据范围: 2025年

## 概览

| 表名 | 域 | 粒度 | 行数 | 说明 |
|------|-----|------|------|------|
| ad_spend_daily | 数据域 | 每日每账户消耗记录 | 1977 | 平台广告消耗明细表（日+账户粒度） |
| daily_report | 人域 | 每日每投手每地区汇报 | 2893 | 投手日报事实表（投手自报） |
| media_buyer_dim | 人域 | 一投手一行 | 31 | 投手维度表 |
| project_pnl | 钱域 | 每月每项目收支 | 59 | 项目收支明细表 |

---

## ad_spend_daily

**平台广告消耗明细表（日+账户粒度）**

- 域: 数据域
- 粒度: 每日每账户消耗记录
- 行数: 1977

### 字段说明

| 字段 | 类型 | 非空率 | 示例值 |
|------|------|--------|--------|
| date | object | 100.0% | 2025-07-01, 2025-07-01 |
| region | object | 100.0% | DE, IN |
| media_buyer | object | 100.0% | HW, SG |
| platform_id | object | 100.0% | 1815567322519393, 549740840492004 |
| account_name | object | 100.0% | FV92-zs-tthd-1642, Momentus_client3-140425-5 |
| account_type | object | 100.0% | 美金户, 印度户 |
| agent | object | 100.0% | 开户美国三不限户, 深圳芳林子 |
| platform | object | 100.0% | nan, 65000.0 |
| spend_today_cumulative | float64 | 77.6% | 0.04, 63251.55775 |
| spend_yesterday_cumulative | float64 | 5.5% | 50.0, 16.4472 |
| fee | float64 | 94.7% | 1748.44225, 1268.202143 |
| actual_spend | float64 | 94.7% | 2083.793474, 1485.825631 |
| spend_with_fee | float64 | 8.7% | 14.900028, 2.2898 |
| notes | object | 87.5% | 335.3512236, 217.6234877 |

---

## daily_report

**投手日报事实表（投手自报）**

- 域: 人域
- 粒度: 每日每投手每地区汇报
- 行数: 2893

### 字段说明

| 字段 | 类型 | 非空率 | 示例值 |
|------|------|--------|--------|
| date | object | 100.0% | 2025-01-31, 2025-01-30 |
| media_buyer | object | 100.0% | 老郭, 紫光 |
| region | object | 100.0% | IN, IN |
| team | object | 100.0% | SZ, SZ |
| ad_spend_usd | float64 | 100.0% | 242.24, 270.35 |
| result_count | float64 | 100.0% | 28.0, 33.0 |
| lead_count | float64 | 100.0% | 5.0, 16.0 |
| platform | object | 26.3% | FB, FB |
| cost_per_lead | float64 | 71.8% | 48.448, 16.896875 |
| cost_per_result | float64 | 71.8% | 48.448, 16.896875 |

---

## media_buyer_dim

**投手维度表**

- 域: 人域
- 粒度: 一投手一行
- 行数: 31

### 字段说明

| 字段 | 类型 | 非空率 | 示例值 |
|------|------|--------|--------|
| media_buyer | object | 100.0% | SG, WD |
| team | object | 100.0% | ZZ, ZZ |

---

## project_pnl

**项目收支明细表**

- 域: 钱域
- 粒度: 每月每项目收支
- 行数: 59

### 字段说明

| 字段 | 类型 | 非空率 | 示例值 |
|------|------|--------|--------|
| month | object | 100.0% | 11月, 11月 |
| team | object | 100.0% | SZ, SZ |
| business_type | object | 100.0% | 自投项目, 外部代投 |
| region | object | 100.0% | DE, JP |
| project_name | object | 100.0% | 德国Summer, 岳总 |
| lead_count | float64 | 66.1% | 227.0, 205.0 |
| total_spend | float64 | 66.1% | 22713.24, 30750.0 |
| actual_revenue | float64 | 66.1% | 40860.0, 36900.0 |
| gross_profit | float64 | 69.5% | 18146.76, 6150.0 |
| prepaid_balance | object | 66.1% | -, 0 |
| notes | object | 20.3% | -, - |

---
