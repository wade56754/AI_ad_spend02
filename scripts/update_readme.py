# -*- coding: utf-8 -*-
content = """# Code Blocks - 代码块索引

> **版本**: v2.0
> **更新日期**: 2025-12-24
> **基准**: MASTER.md v4.4, 模块化开发计划

---

## 一、概述

本目录存放所有可复用的代码块文档。每个代码块都有清晰的接口契约、使用示例和组合规则，支持搭积木式开发。

### 文档完成状态

| 类别 | 总数 | 已完成 | 完成率 |
|------|------|--------|--------|
| 前端代码块 | 10 | 3 | 30% |
| 后端代码块 | 8 | 0 | 0% |
| **合计** | **18** | **3** | **17%** |

---

## 二、待完成代码块清单 (优先级排序)

### P0 - 必须完成 (上线阻塞)

| # | 代码块 | 类型 | 复用页面数 | 文档路径 |
|---|--------|------|-----------|---------|
| 1 | DataTable | 前端/核心 | 8+ | frontend/core/data-table.md |
| 2 | StatusBadge | 前端/核心 | 5 | frontend/core/status-badge.md |
| 3 | DataState | 前端/核心 | 10 | frontend/core/data-state.md |
| 4 | pagination | 后端/核心 | 8+ | backend/core/pagination.md |
| 5 | response-envelope | 后端/核心 | 全部 | backend/core/response-envelope.md |
| 6 | error-codes | 后端/核心 | 全部 | backend/core/error-codes.md |

### P1 - 重要 (功能完整性)

| # | 代码块 | 类型 | 复用页面数 | 文档路径 |
|---|--------|------|-----------|---------|
| 7 | ActionButtons | 前端/流程 | 3 | frontend/workflow/action-buttons.md |
| 8 | GlobalFilters | 前端/流程 | 4 | frontend/workflow/global-filters.md |
| 9 | permission-filter | 后端/核心 | 5 | backend/core/permission-filter.md |
| 10 | state-machine | 后端/流程 | 4 | backend/workflow/state-machine.md |

### P2 - 建议完成 (质量提升)

| # | 代码块 | 类型 | 复用页面数 | 文档路径 |
|---|--------|------|-----------|---------|
| 11 | PageHeader | 前端/核心 | 10 | frontend/core/page-header.md |
| 12 | ApprovalTimeline | 前端/流程 | 2 | frontend/workflow/approval-timeline.md |
| 13 | FormDialog | 前端/流程 | 3 | frontend/workflow/form-dialog.md |
| 14 | audit-log | 后端/流程 | 5 | backend/workflow/audit-log.md |
| 15 | ledger-entry | 后端/财务 | 3 | backend/finance/ledger-entry.md |
| 16 | kpi-calculator | 后端/财务 | 3 | backend/finance/kpi-calculator.md |

---

## 三、前端代码块索引

### 3.1 核心代码块 (core/)

| 代码块 | 状态 | 源码位置 | 复用页面 |
|--------|------|---------|---------|
| DataTable | 待编写 | components/ui/data-table/ | 全部列表页 (8+) |
| StatCard | 已完成 | features/dashboard/components/ | 驾驶舱, 资金, 盈亏 |
| StatusBadge | 待编写 | components/ui/StatusBadge.tsx | 日报, 充值, 项目 |
| PageHeader | 待编写 | components/layout/page-header.tsx | 全部页面 |
| DataState | 待编写 | components/ui/data-state/ | 全部页面 |

### 3.2 流程代码块 (workflow/)

| 代码块 | 状态 | 源码位置 | 复用页面 |
|--------|------|---------|---------|
| GlobalFilters | 待编写 | features/dashboard/components/ | 驾驶舱, 列表页 |
| ApprovalTimeline | 待编写 | features/topups/components/ | 充值, 转账 |
| ActionButtons | 待编写 | features/daily-reports/components/ | 日报, 充值 |
| FormDialog | 待编写 | (待抽取) | 项目, 用户, 账户 |

### 3.3 图表代码块 (chart/)

| 代码块 | 状态 | 源码位置 | 复用页面 |
|--------|------|---------|---------|
| TrendChart | 已完成 | features/dashboard/components/ | 驾驶舱, 报表 |
| TopList | 已完成 | features/dashboard/components/ | 驾驶舱, 盈亏 |

---

## 四、后端代码块索引

### 4.1 核心代码块 (core/)

| 代码块 | 状态 | 源码位置 | 复用服务 |
|--------|------|---------|---------|
| pagination | 待编写 | core/dependencies.py | 全部列表 API |
| permission-filter | 待编写 | services/*_service.py | 项目, 日报, 充值 |
| response-envelope | 待编写 | core/response.py | 全部 API |
| error-codes | 待编写 | core/error_codes.py | 全部 API |

### 4.2 流程代码块 (workflow/)

| 代码块 | 状态 | 源码位置 | 复用服务 |
|--------|------|---------|---------|
| state-machine | 待编写 | services/daily_report_service.py | 日报, 充值, 转账 |
| audit-log | 待编写 | services/audit_service.py | 全部写操作 |

### 4.3 财务代码块 (finance/)

| 代码块 | 状态 | 源码位置 | 复用服务 |
|--------|------|---------|---------|
| ledger-entry | 待编写 | services/ledger_service.py | 充值, 结算 |
| kpi-calculator | 待编写 | services/finance/profit_service.py | 盈亏, 驾驶舱 |

---

## 五、目录结构

docs/9.code-blocks/
  README.md                 - 本索引文件
  frontend/
    _template.md            - 前端模板
    core/
      data-table.md         - P0 待编写
      stat-card.md          - 已完成
      status-badge.md       - P0 待编写
      page-header.md        - P2 待编写
      data-state.md         - P0 待编写
    workflow/
      global-filters.md     - P1 待编写
      approval-timeline.md  - P2 待编写
      action-buttons.md     - P1 待编写
      form-dialog.md        - P2 待编写
    chart/
      trend-chart.md        - 已完成
      top-list.md           - 已完成
  backend/
    _template.md            - 后端模板
    core/
      pagination.md         - P0 待编写
      permission-filter.md  - P1 待编写
      response-envelope.md  - P0 待编写
      error-codes.md        - P0 待编写
    workflow/
      state-machine.md      - P1 待编写
      audit-log.md          - P2 待编写
    finance/
      ledger-entry.md       - P2 待编写
      kpi-calculator.md     - P2 待编写

---

## 六、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2025-12-24 | 新增待完成代码块清单、优先级排序、完成状态标记 |
| v1.0 | 2025-12-22 | 初始版本，建立代码块索引体系 |

---

维护者: AI 广告代投系统开发团队
关联文档: MASTER.md v4.4, 模块化开发计划
"""

with open(r'D:\project\AI_ad_spend02\docs\9.code-blocks\README.md', 'w', encoding='utf-8') as f:
    f.write(content)
print('README.md updated successfully')
