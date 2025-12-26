# Claude CLI 任务指令：CEO 仪表盘重构 (修订版 v3)

> **任务类型**: 前端页面重构 + 后端 API 修复/新增
> **预计工作量**: 10-12 小时
> **优先级**: P0 (存在数据计算错误)
> **基准文档**: MASTER.md v4.4, LEDGER_SOT.md v1.1, 收支表_明细表.csv
> **修订版本**: v3.0 (对齐原始收支表业务逻辑)
> **修订日期**: 2025-12-25

---

> ⚠️ **核心公式声明** (对齐原始收支表)
>
> 本规格书的所有计算公式已与原始收支表验证对齐：
>
> ```
> 毛利 = 收款 - 消耗  （不含手续费）
> 收款 = 进粉 × 单粉价格
> CPL = 消耗 / 进粉
> ```
>
> **手续费处理**: 仅作为参考信息展示，不计入成本计算。

---

> ⚠️ **Phase 依赖声明** (LEDGER_SOT.md v1.1 对齐)
>
> 本规格书设计支持 **Phase 1 和 Phase 2** 双模式。
>
> **Phase 1 简化规则**:
> - 仅使用单账本视角，`ledger_type` 默认为 `PROJECT`
> - 供应商独立余额计算禁用
> - 核心目标：记录资金流水，不做强约束
>
> **Phase 2 启用条件**: Phase 1 稳定运行 2 个月后

---

## 一、v3 修订说明

### 1.1 与 v2 的主要差异

| # | v2 定义 | v3 修正 | 原因 |
|---|---------|---------|------|
| 1 | `cost = real_spend × (1 + fee_rate)` | `cost = real_spend` | 原始数据不含手续费 |
| 2 | 应收 = REVENUE累计, 已收 = TOPUP累计 | 收款 = 进粉 × 单价 (即应收) | 原始数据假设及时付款 |
| 3 | 利润率偏低 (含手续费) | 利润率对齐原始数据 | 验证通过 |

### 1.2 原始数据验证

以下计算结果与收支表_明细表.csv完全一致：

| 项目 | 进粉 | 消耗 | 收款 | 毛利 | 毛利率 | 验证 |
|------|------|------|------|------|--------|------|
| 印度K4 | 4,226 | $86,791 | $131,006 | $44,215 | 33.8% | ✅ |
| 印度新K1 | 5,274 | $108,315 | $163,494 | $55,179 | 33.7% | ✅ |
| 德国Summer | 227 | $22,713 | $40,860 | $18,147 | 44.4% | ✅ |
| 岳总(日本) | 369 | $55,350 | $66,600 | $11,250 | 16.9% | ✅ |
| B哥马来 | 313 | $20,793 | $29,735 | $8,942 | 30.1% | ✅ |

---

## 二、核心公式定义

### 2.1 利润计算公式

```python
# ============================================
# 核心公式（对齐原始收支表）
# ============================================

# 收款（收入）
revenue = conversions × unit_price
# 或使用阶梯定价
revenue = calculate_tiered_revenue(conversions, price_rules)
# 或使用加价模式（华侨粉）
revenue = real_spend × markup_rate

# 成本（消耗）
cost = real_spend  # ⚠️ 不含手续费！

# 毛利
profit = revenue - cost

# 毛利率
profit_rate = profit / revenue

# CPL（单粉成本）
cpl = real_spend / conversions

# ============================================
# 手续费（仅供参考，不计入成本）
# ============================================
fee_reference = real_spend × fee_rate  # 约 8%
# 用途：财务对账时参考，不影响利润计算
```

### 2.2 项目余额公式

```python
# 项目余额（预付款剩余）
project_balance = cumulative_revenue - cumulative_cost
# 或
project_balance = cumulative_topup - cumulative_spend

# 如果 balance > 0：客户有预付款
# 如果 balance < 0：需要客户补款（实际业务中很少见）
```

### 2.3 公司现金公式

```python
# 公司现金余额
cash_balance = opening_balance + total_income - total_expense

# 收入 = 甲方打款（假设与收款一致）
total_income = SUM(client_topup)

# 支出 = 渠道充值 + 后勤支出
total_expense = supplier_topup + operation_cost + infrastructure_cost
```

---

## 三、页面结构设计

### 3.1 整体布局

```
┌─────────────────────────────────────────────────────────────────┐
│  CEO Dashboard                           2025年12月 ▼  [刷新]  │
│  数据更新于 2025-12-25 10:30                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Section 1: 公司现金] ─────────────────────────────────────── │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────────────┐ │
│  │ 期末余额  │ │ 本月收入  │ │ 本月支出  │ │ 周转天数        │ │
│  │ $40,581   │ │ $301,800  │ │ $261,218  │ │ 18天            │ │
│  │ ↑56.0%    │ │ 甲方打款  │ │ 渠道+后勤 │ │ 仅广告业务      │ │
│  └───────────┘ └───────────┘ └───────────┘ └─────────────────┘ │
│                                                                 │
│  [Section 2: 经营概览] ─────────────────────────────────────── │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────────────┐ │
│  │ 本月收款  │ │ 本月消耗  │ │ 本月毛利  │ │ 毛利率          │ │
│  │ $120,715  │ │ $98,500   │ │ $22,215   │ │ 18.4%           │ │
│  │ 1,861粉   │ │ CPL $52.9 │ │ ↑12.3%    │ │ 目标20% 🟡      │ │
│  └───────────┘ └───────────┘ └───────────┘ └─────────────────┘ │
│                                                                 │
│  [Section 3: 项目余额] ─────────────────────────────────────── │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  项目          │ 累计收款  │ 累计消耗  │ 余额     │ 状态   ││
│  │  ───────────────────────────────────────────────────────── ││
│  │  海总          │ $99,055   │ $89,450   │ $9,605   │ 预付✅ ││
│  │  渠道106       │ $108,000  │ $88,200   │ $19,800  │ 待退🔄 ││
│  │  F2            │ $20,900   │ $20,550   │ $350     │ 预付✅ ││
│  │  印度测试      │ $20,000   │ $7,595    │ 已退     │ 已退↩️ ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  [Section 4: 待办事项] ─────────────────────────────────────── │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ⚠️ 异常项目 (1)                                             ││
│  │ • 华侨粉 毛利率-16.7%，建议暂停          [暂停] [查看]      ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  [Section 5: 项目毛利排行] ────────────────────── [查看全部→] │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ # │ 项目          │ 进粉  │ 收款     │ 消耗    │ 毛利率   ││
│  │───────────────────────────────────────────────────────────  ││
│  │🟢│ 印度新K1      │ 5274  │ $163,494 │$108,315 │ 33.7%    ││
│  │🟢│ 印度K4        │ 4226  │ $131,006 │ $86,791 │ 33.8%    ││
│  │🟢│ 德国Summer    │ 227   │ $40,860  │ $22,713 │ 44.4%    ││
│  │🟡│ 岳总(日本)    │ 369   │ $66,600  │ $55,350 │ 16.9%    ││
│  │🔴│ 华侨粉        │ -     │ $2,011   │ $2,346  │ -16.7%   ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  [Section 6: 趋势图] ──────────────────────── [按日][按周][按月]│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  收款 ── 消耗 ‥‥ 毛利 ─·─                                  ││
│  │  (显示三条线的折线图)                                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、后端 API 设计

### 4.1 API 总览

| # | API | 方法 | 用途 |
|---|-----|------|------|
| 1 | `/api/v1/dashboard/ceo/overview` | GET | 仪表盘全部数据 |
| 2 | `/api/v1/dashboard/ceo/cash-status` | GET | 公司现金状况 |
| 3 | `/api/v1/dashboard/ceo/profit-summary` | GET | 经营概览（毛利） |
| 4 | `/api/v1/dashboard/ceo/project-balance` | GET | 项目余额列表 |
| 5 | `/api/v1/dashboard/ceo/action-items` | GET | 待办事项 |
| 6 | `/api/v1/dashboard/ceo/project-ranking` | GET | 项目毛利排行 |
| 7 | `/api/v1/dashboard/ceo/trend` | GET | 趋势数据 |

### 4.2 API 1: 仪表盘总览

```
GET /api/v1/dashboard/ceo/overview
```

**Response**:
```json
{
  "success": true,
  "data": {
    "period": "2025-12",
    "currency": "USD",
    "generated_at": "2025-12-25T10:30:00Z",
    "formula_version": "v3",
    "formula_note": "毛利=收款-消耗，不含手续费",
    
    "cash_status": {
      "opening_balance": 26016.50,
      "closing_balance": 40581.44,
      "total_income": 301799.63,
      "total_expense": 261218.19,
      "balance_change_pct": 56.0,
      "runway_days": 18
    },
    
    "profit_summary": {
      "total_revenue": 120715.00,
      "total_cost": 98500.00,
      "total_profit": 22215.00,
      "profit_rate": 0.184,
      "total_conversions": 1861,
      "avg_cpl": 52.93,
      "target_profit_rate": 0.20,
      "profit_status": "warning"
    },
    
    "project_balance_summary": {
      "total_projects": 4,
      "prepaid_count": 2,
      "pending_refund_count": 1,
      "refunded_count": 1,
      "total_prepaid_balance": 9955.00
    },
    
    "action_items": {
      "abnormal_projects_count": 1,
      "pending_reports_count": 3
    },
    
    "top_projects": [
      {
        "project_name": "印度新K1",
        "profit": 55179.00,
        "profit_rate": 0.337,
        "status": "healthy"
      }
    ]
  }
}
```

### 4.3 API 2: 公司现金状况

```
GET /api/v1/dashboard/ceo/cash-status
```

**Response**:
```json
{
  "success": true,
  "data": {
    "period": "2025-12",
    "currency": "USD",
    
    "balance": {
      "opening": 26016.50,
      "closing": 40581.44,
      "change": 14564.94,
      "change_pct": 56.0
    },
    
    "income": {
      "total": 301799.63,
      "breakdown": [
        {"type": "client_topup", "label": "甲方打款", "amount": 289394.63},
        {"type": "supplier_refund", "label": "渠道退款", "amount": 12405.00}
      ]
    },
    
    "expense": {
      "total": 261218.19,
      "breakdown": [
        {"type": "supplier_topup", "label": "渠道充值", "amount": 224273.11},
        {"type": "operation", "label": "后勤支出", "amount": 27916.85},
        {"type": "infrastructure", "label": "广告配套", "amount": 9028.23}
      ]
    },
    
    "runway": {
      "days": 18,
      "avg_daily_ad_spend": 2242.73,
      "note": "仅计算广告业务支出，不含后勤"
    }
  }
}
```

### 4.4 API 3: 经营概览（毛利）

```
GET /api/v1/dashboard/ceo/profit-summary
```

> **核心公式**: `毛利 = 收款 - 消耗`（不含手续费）

**Response**:
```json
{
  "success": true,
  "data": {
    "period": "2025-12",
    "currency": "USD",
    "formula": "毛利 = 收款 - 消耗（不含手续费）",
    
    "revenue": {
      "total": 120715.00,
      "label": "收款",
      "conversions": 1861,
      "avg_unit_price": 64.87,
      "note": "收款 = 进粉 × 单粉价格"
    },
    
    "cost": {
      "total": 98500.00,
      "label": "消耗",
      "note": "不含手续费"
    },
    
    "profit": {
      "total": 22215.00,
      "label": "毛利",
      "rate": 0.184,
      "target_rate": 0.20,
      "gap": -0.016,
      "status": "warning",
      "status_label": "低于目标"
    },
    
    "cpl": {
      "overall": 52.93,
      "formula": "CPL = 消耗 / 进粉"
    },
    
    "fee_reference": {
      "estimated_rate": 0.08,
      "estimated_amount": 7880.00,
      "note": "仅供参考，不计入成本"
    },
    
    "comparison": {
      "vs_last_month": {
        "revenue_change_pct": 8.5,
        "profit_change_pct": 12.3
      }
    }
  }
}
```

### 4.5 API 4: 项目余额

```
GET /api/v1/dashboard/ceo/project-balance
```

> **核心公式**: `余额 = 累计收款 - 累计消耗`

**Response**:
```json
{
  "success": true,
  "data": {
    "period": "2025-12",
    "currency": "USD",
    "formula": "余额 = 累计收款 - 累计消耗",
    
    "items": [
      {
        "project_id": 1,
        "project_name": "海总-新加坡、加拿大",
        "client_name": "海总",
        "cumulative_revenue": 99055.00,
        "cumulative_cost": 89450.00,
        "balance": 9605.00,
        "status": "prepaid",
        "status_label": "客户预付",
        "note": "预付款剩余 $9,605"
      },
      {
        "project_id": 6,
        "project_name": "渠道106-日本FB",
        "client_name": "渠道106",
        "cumulative_revenue": 108000.00,
        "cumulative_cost": 88200.00,
        "balance": 19800.00,
        "status": "pending_refund",
        "status_label": "待退款",
        "note": "项目结束，待退 $19,800"
      },
      {
        "project_id": 5,
        "project_name": "印度资金测试",
        "client_name": "印度测试",
        "cumulative_revenue": 20000.00,
        "cumulative_cost": 7595.00,
        "balance": 0,
        "status": "refunded",
        "status_label": "已退款",
        "refund_amount": 12405.00,
        "refund_date": "2025-10-19"
      }
    ],
    
    "totals": {
      "cumulative_revenue": 247955.00,
      "cumulative_cost": 205795.00,
      "total_balance": 42160.00
    },
    
    "summary": {
      "prepaid_count": 2,
      "pending_refund_count": 1,
      "refunded_count": 1
    }
  }
}
```

### 4.6 API 5: 待办事项

```
GET /api/v1/dashboard/ceo/action-items
```

**Response**:
```json
{
  "success": true,
  "data": {
    "abnormal_projects": {
      "count": 1,
      "items": [
        {
          "project_id": 4,
          "project_name": "华侨粉",
          "issue_type": "negative_profit",
          "severity": "high",
          "metrics": {
            "revenue": 2011.00,
            "cost": 2346.00,
            "profit": -335.00,
            "profit_rate": -0.167
          },
          "message": "毛利率-16.7%，本月亏损$335",
          "suggested_action": "pause",
          "actions": [
            {"key": "pause", "label": "暂停项目", "variant": "destructive"},
            {"key": "view", "label": "查看详情", "variant": "outline"}
          ]
        }
      ]
    },
    
    "pending_reports": {
      "count": 3,
      "items": [
        {
          "date": "2025-12-24",
          "count": 3,
          "status": "final_confirmed"
        }
      ]
    },
    
    "pending_refunds": {
      "count": 1,
      "total_amount": 19800.00,
      "items": [
        {
          "project_name": "渠道106-日本FB",
          "amount": 19800.00
        }
      ]
    }
  }
}
```

### 4.7 API 6: 项目毛利排行

```
GET /api/v1/dashboard/ceo/project-ranking
```

> **核心公式**: `毛利 = 收款 - 消耗`

**Response**:
```json
{
  "success": true,
  "data": {
    "period": "2025-12",
    "currency": "USD",
    "formula": "毛利 = 收款 - 消耗（不含手续费）",
    
    "items": [
      {
        "rank": 1,
        "project_id": 101,
        "project_name": "印度新K1",
        "profit_status": "healthy",
        "pricing": {
          "type": "fixed",
          "unit_price": 31.00
        },
        "metrics": {
          "conversions": 5274,
          "revenue": 163494.00,
          "cost": 108315.00,
          "profit": 55179.00,
          "profit_rate": 0.337,
          "cpl": 20.54
        },
        "validation": {
          "formula": "163494 - 108315 = 55179",
          "matches_original": true
        }
      },
      {
        "rank": 2,
        "project_id": 102,
        "project_name": "印度K4",
        "profit_status": "healthy",
        "pricing": {
          "type": "fixed",
          "unit_price": 31.00
        },
        "metrics": {
          "conversions": 4226,
          "revenue": 131006.00,
          "cost": 86791.00,
          "profit": 44215.00,
          "profit_rate": 0.338,
          "cpl": 20.54
        }
      },
      {
        "rank": 3,
        "project_id": 103,
        "project_name": "德国Summer",
        "profit_status": "healthy",
        "pricing": {
          "type": "fixed",
          "unit_price": 180.00
        },
        "metrics": {
          "conversions": 227,
          "revenue": 40860.00,
          "cost": 22713.00,
          "profit": 18147.00,
          "profit_rate": 0.444,
          "cpl": 100.06
        }
      },
      {
        "rank": 4,
        "project_id": 104,
        "project_name": "岳总(日本)",
        "profit_status": "warning",
        "pricing": {
          "type": "fixed",
          "unit_price": 180.00
        },
        "metrics": {
          "conversions": 369,
          "revenue": 66600.00,
          "cost": 55350.00,
          "profit": 11250.00,
          "profit_rate": 0.169,
          "cpl": 150.00
        }
      },
      {
        "rank": 5,
        "project_id": 105,
        "project_name": "B哥马来",
        "profit_status": "healthy",
        "pricing": {
          "type": "fixed",
          "unit_price": 95.00
        },
        "metrics": {
          "conversions": 313,
          "revenue": 29735.00,
          "cost": 20793.00,
          "profit": 8942.00,
          "profit_rate": 0.301,
          "cpl": 66.43
        }
      },
      {
        "rank": 6,
        "project_id": 4,
        "project_name": "华侨粉",
        "profit_status": "danger",
        "pricing": {
          "type": "markup",
          "markup_rate": 1.2,
          "note": "按消耗×1.2结算"
        },
        "metrics": {
          "conversions": null,
          "revenue": 2011.00,
          "cost": 2346.00,
          "profit": -335.00,
          "profit_rate": -0.167,
          "cpl": null
        }
      }
    ],
    
    "summary": {
      "total_projects": 6,
      "healthy_count": 4,
      "warning_count": 1,
      "danger_count": 1,
      "total_profit": 137398.00,
      "avg_profit_rate": 0.279
    }
  }
}
```

---

## 五、后端实现规格

### 5.1 目录结构

```
backend/
├── routers/
│   └── dashboard/
│       ├── __init__.py
│       └── ceo.py
│
├── services/
│   └── dashboard/
│       ├── __init__.py
│       ├── ceo_dashboard_service.py
│       ├── cash_status_service.py
│       ├── profit_service.py          # v3 修正版
│       ├── project_balance_service.py  # 新增
│       └── action_items_service.py
│
├── schemas/
│   └── dashboard/
│       ├── __init__.py
│       └── ceo.py
```

### 5.2 核心 Service: 利润计算（v3 修正版）

```python
# backend/services/dashboard/profit_service.py

"""
利润计算服务 (v3 修正版)

核心公式（对齐原始收支表）:
- 收款 = 进粉 × 单粉价格
- 消耗 = SUM(real_spend)
- 毛利 = 收款 - 消耗 （⚠️ 不含手续费！）
- CPL = 消耗 / 进粉

验证基准:
- 印度K4: 毛利率 33.8% (不是 26.6%)
- 德国Summer: 毛利率 44.4% (不是 37.4%)
"""

from decimal import Decimal
from typing import Dict
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models import Project, DailyReport


class ProfitService:
    """利润计算服务"""
    
    # 利润率阈值
    PROFIT_RATE_HEALTHY = Decimal("0.20")  # >= 20% 健康
    PROFIT_RATE_WARNING = Decimal("0.10")  # >= 10% 警告
    # < 10% 危险

    def __init__(self, db: Session):
        self.db = db

    def get_profit_summary(self, period: str = None) -> Dict:
        """
        获取利润概览
        
        公式: 毛利 = 收款 - 消耗（不含手续费）
        """
        start_date, end_date = self._parse_period(period)
        
        projects = self.db.query(Project).filter(
            Project.status.in_(["active", "completed"])
        ).all()
        
        total_revenue = Decimal("0")
        total_cost = Decimal("0")
        total_conversions = 0
        
        for project in projects:
            metrics = self._calculate_project_metrics(project, start_date, end_date)
            total_revenue += metrics["revenue"]
            total_cost += metrics["cost"]
            total_conversions += metrics["conversions"] or 0
        
        # 计算毛利（不含手续费）
        total_profit = total_revenue - total_cost
        profit_rate = total_profit / total_revenue if total_revenue > 0 else Decimal("0")
        avg_cpl = total_cost / total_conversions if total_conversions > 0 else Decimal("0")
        
        return {
            "period": period or self._current_period(),
            "currency": "USD",
            "formula": "毛利 = 收款 - 消耗（不含手续费）",
            "revenue": {
                "total": float(total_revenue),
                "label": "收款",
                "conversions": total_conversions,
                "note": "收款 = 进粉 × 单粉价格"
            },
            "cost": {
                "total": float(total_cost),
                "label": "消耗",
                "note": "不含手续费"
            },
            "profit": {
                "total": float(total_profit),
                "label": "毛利",
                "rate": float(profit_rate),
                "target_rate": 0.20,
                "status": self._get_profit_status(profit_rate)
            },
            "cpl": {
                "overall": float(avg_cpl),
                "formula": "CPL = 消耗 / 进粉"
            },
            "fee_reference": {
                "estimated_rate": 0.08,
                "estimated_amount": float(total_cost * Decimal("0.08")),
                "note": "仅供参考，不计入成本"
            }
        }

    def _calculate_project_metrics(
        self, 
        project: Project, 
        start_date, 
        end_date
    ) -> Dict:
        """
        计算单个项目的指标
        
        ⚠️ v3 核心修正:
        - cost = real_spend（不含手续费）
        - profit = revenue - cost
        """
        # 获取进粉数
        conversions = self.db.query(
            func.coalesce(func.sum(DailyReport.conversions_final), 0)
        ).filter(
            DailyReport.project_id == project.id,
            DailyReport.status == "final_locked",
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date
        ).scalar()
        conversions = int(conversions)
        
        # 获取消耗
        real_spend = self.db.query(
            func.coalesce(func.sum(DailyReport.real_spend), 0)
        ).filter(
            DailyReport.project_id == project.id,
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date
        ).scalar()
        real_spend = Decimal(str(real_spend))
        
        # 计算收款（按进粉计费）
        revenue = self._calculate_revenue(project, conversions, real_spend)
        
        # ⚠️ v3 修正：消耗就是成本，不含手续费
        cost = real_spend
        
        # 计算毛利
        profit = revenue - cost
        profit_rate = profit / revenue if revenue > 0 else Decimal("0")
        
        # CPL
        cpl = real_spend / conversions if conversions > 0 else None
        
        return {
            "conversions": conversions if conversions > 0 else None,
            "revenue": revenue,
            "cost": cost,  # 不含手续费
            "profit": profit,
            "profit_rate": profit_rate,
            "cpl": cpl
        }

    def _calculate_revenue(
        self, 
        project: Project, 
        conversions: int, 
        real_spend: Decimal
    ) -> Decimal:
        """
        计算收款（支持三种定价模式）
        """
        price_rules = project.price_rules or {}
        pricing_type = price_rules.get("type", "fixed")
        
        if pricing_type == "markup":
            # 华侨粉模式：按消耗加价
            markup_rate = Decimal(str(price_rules.get("markup_rate", 1.2)))
            return real_spend * markup_rate
        
        elif pricing_type == "tiered":
            # 阶梯定价
            return self._calculate_tiered_revenue(conversions, price_rules)
        
        else:  # fixed
            # 固定单价
            unit_price = project.unit_price or Decimal("0")
            return Decimal(conversions) * unit_price

    def _calculate_tiered_revenue(
        self, 
        conversions: int, 
        price_rules: dict
    ) -> Decimal:
        """计算阶梯定价收入"""
        tiers = price_rules.get("tiers", [])
        if not tiers:
            return Decimal("0")
        
        total_revenue = Decimal("0")
        remaining = conversions
        
        for tier in sorted(tiers, key=lambda x: x.get("min", 0)):
            tier_min = tier.get("min", 0)
            tier_max = tier.get("max") or float("inf")
            tier_price = Decimal(str(tier.get("price", 0)))
            
            if remaining <= 0:
                break
            
            tier_count = min(remaining, int(tier_max - tier_min + 1))
            total_revenue += tier_count * tier_price
            remaining -= tier_count
        
        return total_revenue

    def _get_profit_status(self, profit_rate: Decimal) -> str:
        if profit_rate >= self.PROFIT_RATE_HEALTHY:
            return "healthy"
        if profit_rate >= self.PROFIT_RATE_WARNING:
            return "warning"
        if profit_rate >= 0:
            return "danger"
        return "loss"

    def _parse_period(self, period: str):
        from datetime import date, timedelta
        if not period:
            today = date.today()
            start = today.replace(day=1)
            end = today
        else:
            year, month = map(int, period.split("-"))
            start = date(year, month, 1)
            if month == 12:
                end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(year, month + 1, 1) - timedelta(days=1)
        return start, end

    def _current_period(self) -> str:
        from datetime import date
        return date.today().strftime("%Y-%m")
```

### 5.3 新增 Service: 项目余额

```python
# backend/services/dashboard/project_balance_service.py

"""
项目余额服务

核心公式（对齐原始收支表"剩余预付款"）:
- 余额 = 累计收款 - 累计消耗
- 如果 > 0：客户预付款
- 如果 = 0：已结清
- 如果 < 0：需补款（罕见）
"""

from decimal import Decimal
from typing import Dict, List
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models import Project, LedgerEntry


class ProjectBalanceService:
    """项目余额服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_all_balances(self, period: str = None) -> Dict:
        """获取所有项目余额"""
        projects = self.db.query(Project).filter(
            Project.status.in_(["active", "completed", "refunded"])
        ).all()
        
        items = []
        totals = {
            "cumulative_revenue": Decimal("0"),
            "cumulative_cost": Decimal("0"),
            "total_balance": Decimal("0")
        }
        
        for project in projects:
            balance_info = self._get_project_balance(project)
            items.append(balance_info)
            
            totals["cumulative_revenue"] += Decimal(str(balance_info["cumulative_revenue"]))
            totals["cumulative_cost"] += Decimal(str(balance_info["cumulative_cost"]))
            totals["total_balance"] += Decimal(str(balance_info["balance"]))
        
        # 按余额排序
        items.sort(key=lambda x: x["balance"], reverse=True)
        
        return {
            "formula": "余额 = 累计收款 - 累计消耗",
            "items": items,
            "totals": {k: float(v) for k, v in totals.items()},
            "summary": self._get_summary(items)
        }

    def _get_project_balance(self, project: Project) -> Dict:
        """
        计算单个项目余额
        
        余额 = 累计收款(TOPUP) - 累计消耗(COST记录或real_spend)
        """
        # 累计收款（甲方打款）
        cumulative_revenue = self.db.query(
            func.coalesce(func.sum(LedgerEntry.amount), 0)
        ).filter(
            LedgerEntry.project_id == project.id,
            LedgerEntry.entry_type == "TOPUP"
        ).scalar()
        cumulative_revenue = Decimal(str(cumulative_revenue))
        
        # 累计消耗（按进粉计费）
        # 这里使用 REVENUE 记录作为"已计费消耗"
        cumulative_cost = self.db.query(
            func.coalesce(func.sum(LedgerEntry.amount), 0)
        ).filter(
            LedgerEntry.project_id == project.id,
            LedgerEntry.entry_type == "REVENUE"
        ).scalar()
        cumulative_cost = Decimal(str(cumulative_cost))
        
        # 计算余额
        balance = cumulative_revenue - cumulative_cost
        
        # 检查退款
        refund = self._get_refund_info(project.id)
        
        # 确定状态
        status = self._determine_status(balance, refund, project.status)
        
        return {
            "project_id": project.id,
            "project_name": project.name,
            "client_name": project.client_name,
            "cumulative_revenue": float(cumulative_revenue),
            "cumulative_cost": float(cumulative_cost),
            "balance": float(balance) if not refund else 0,
            "status": status["code"],
            "status_label": status["label"],
            "refund_amount": refund.get("amount") if refund else None,
            "refund_date": refund.get("date") if refund else None
        }

    def _get_refund_info(self, project_id: int) -> Dict:
        """获取退款信息"""
        refund = self.db.query(LedgerEntry).filter(
            LedgerEntry.project_id == project_id,
            LedgerEntry.entry_type == "REVERSAL"
        ).first()
        
        if refund:
            return {
                "amount": abs(float(refund.amount)),
                "date": refund.occurred_at.strftime("%Y-%m-%d") if refund.occurred_at else None
            }
        return None

    def _determine_status(self, balance: Decimal, refund: Dict, project_status: str) -> Dict:
        """确定项目余额状态"""
        if refund:
            return {"code": "refunded", "label": "已退款"}
        if project_status == "completed" and balance > 0:
            return {"code": "pending_refund", "label": "待退款"}
        if balance > 0:
            return {"code": "prepaid", "label": "客户预付"}
        if balance == 0:
            return {"code": "settled", "label": "已结清"}
        return {"code": "need_topup", "label": "需补款"}

    def _get_summary(self, items: List[Dict]) -> Dict:
        return {
            "prepaid_count": len([i for i in items if i["status"] == "prepaid"]),
            "pending_refund_count": len([i for i in items if i["status"] == "pending_refund"]),
            "refunded_count": len([i for i in items if i["status"] == "refunded"]),
            "settled_count": len([i for i in items if i["status"] == "settled"])
        }
```

---

## 六、数据验证

### 6.1 与原始收支表对照

| 项目 | 原始毛利率 | v3计算结果 | 验证 |
|------|------------|------------|------|
| 印度新K1 | 33.7% | 33.7% | ✅ |
| 印度K4 | 33.8% | 33.8% | ✅ |
| 印度K26 | 33.5% | 33.5% | ✅ |
| 德国Summer | 44.4% | 44.4% | ✅ |
| 岳总(日本) | 16.9% | 16.9% | ✅ |
| B哥马来 | 30.1% | 30.1% | ✅ |

### 6.2 公式验证

```
印度K4 验证:
- 进粉: 4,226
- 单价: $31
- 收款: 4226 × 31 = $131,006 ✅
- 消耗: $86,791
- 毛利: 131006 - 86791 = $44,215 ✅
- 毛利率: 44215 / 131006 = 33.8% ✅
```

---

## 七、验收标准

### 7.1 公式验收

- [ ] 毛利 = 收款 - 消耗（不含手续费）
- [ ] 毛利率与原始收支表一致（误差 < 0.1%）
- [ ] CPL = 消耗 / 进粉

### 7.2 数据验收

- [ ] 印度K4 毛利率显示 33.8%（不是 26.6%）
- [ ] 德国Summer 毛利率显示 44.4%（不是 37.4%）
- [ ] 所有项目毛利率与原始收支表一致

### 7.3 显示验收

- [ ] 所有金额显示 USD（$）
- [ ] 手续费作为参考信息单独展示
- [ ] 公式说明清晰可见

---

## 八、执行顺序

```
Phase 0: 验证准备 (1h)
├── 0.1 导入原始收支表数据
├── 0.2 创建验证脚本
└── 0.3 确认公式计算正确

Phase 1: 后端 API (4h)
├── 1.1 profit_service.py (v3 修正)
├── 1.2 project_balance_service.py (新增)
├── 1.3 cash_status_service.py
├── 1.4 ceo router
└── 1.5 单元测试 + 数据验证

Phase 2: 前端页面 (4h)
├── 2.1 公司现金区块
├── 2.2 经营概览区块（毛利）
├── 2.3 项目余额表格
├── 2.4 待办事项面板
├── 2.5 项目排行表格
└── 2.6 趋势图

Phase 3: 验收测试 (1h)
├── 3.1 与原始收支表对照验证
├── 3.2 公式正确性检查
└── 3.3 性能测试
```

---

## 九、v2 → v3 差异总结

| 项目 | v2 定义 | v3 定义 | 原因 |
|------|---------|---------|------|
| 成本 | `消耗 × (1 + 费率)` | `消耗` | 原始数据不含手续费 |
| 手续费 | 计入成本 | 仅作参考 | 对齐原始逻辑 |
| 应收 | REVENUE累计 | 收款(进粉×单价) | 简化为及时付款 |
| 未收 | 应收 - 已收 | 移除 | 原始数据无此概念 |
| 毛利率 | 偏低 (含手续费) | 对齐原始 | 验证通过 |

---

## 十、参考文档

| 文档 | 版本 | 引用内容 |
|------|------|----------|
| MASTER.md | v4.4 | §2.3 核心管理目标 |
| LEDGER_SOT.md | v1.1 | §1 Phase 声明 |
| 收支表_明细表.csv | 2025-10/11 | 业务公式验证基准 |

---

**文档版本**: v3.0
**修订日期**: 2025-12-25
**核心修正**: 移除手续费计算，对齐原始收支表业务逻辑
