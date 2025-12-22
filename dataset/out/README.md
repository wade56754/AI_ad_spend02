# 广告代投数据集 - AI 使用指南

> 生成时间: 2025-12-22
> 数据范围: 2025年7月 - 2025年12月

## 快速开始

### 让 AI 理解数据的 3 步

**Step 1: 加载上下文**
```
请阅读 @dataset/out/AI_CONTEXT.md 了解数据结构
```

**Step 2: 查看数据**
```
核心数据在 @dataset/out/clean/ 目录下
```

**Step 3: 开始提问**
```
示例：请分析12月各投手的消耗情况
```

## 目录结构

```
dataset/out/
├── clean/                    # 清洗后的核心表（AI主要使用）
│   ├── ad_spend_daily.csv    # 平台消耗明细 (1977行)
│   ├── daily_report.csv      # 投手日报 (2893行)
│   ├── media_buyer_dim.csv   # 投手维度表 (31行)
│   └── project_pnl.csv       # 项目收支 (59行)
│
├── schema/                   # JSON Schema 定义
│   ├── ad_spend_daily.schema.json
│   ├── daily_report.schema.json
│   └── ...
│
├── csv/                      # 原始导出CSV（123个，已归档）
│
├── AI_CONTEXT.md             # ★ AI 专用上下文文档
├── DATA_DICTIONARY.md        # 数据字典
├── AGENT_FEE_RATES.csv       # 代理商费率表（待填写）
└── datapackage.json          # Frictionless 包描述
```

## 核心表说明

| 表名 | 行数 | 用途 | 主键 |
|------|------|------|------|
| ad_spend_daily | 1,977 | 平台真实消耗（以此为准） | (date, platform_id) |
| daily_report | 2,893 | 投手自报数据 | (date, media_buyer, region) |
| media_buyer_dim | 31 | 投手-团队映射 | media_buyer |
| project_pnl | 59 | 项目收支利润 | (month, team, project_name) |

## 业务规则

### 团队编码
- `SZ` = 深圳团队
- `ZZ` = 郑州团队（含原金边）
- `EXT` = 外包（单独核算）

### 地区编码 (ISO)
- `IN` = 印度, `DE` = 德国, `SG` = 新加坡
- `US` = 美国, `MY` = 马来西亚, `TR` = 土耳其

### 金额口径
- `actual_spend` = 平台实际消耗（以此为准）
- `fee` = 手续费 = actual_spend × 代理商费率
- `ad_spend_usd` = 投手自报消耗（需对账）
- `gross_profit` = 项目毛利 = revenue - spend

## AI 提问示例

```
1. 请统计12月各投手的总消耗和账户数
2. 对比 ad_spend_daily 和 daily_report 的消耗差异
3. 计算各代理商的消耗占比
4. 分析项目毛利率排名
5. 找出消耗最高的前10个账户
```

## 待完善事项

- [ ] 填写 `AGENT_FEE_RATES.csv` 中的代理商费率
- [ ] 补充2025年1-6月的消耗数据
- [ ] 建立项目规范命名表

---

**使用问题请联系数据团队**

