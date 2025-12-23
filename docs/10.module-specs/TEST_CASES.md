# MVP 模块测试用例文档

> **版本**: v2.0
> **创建日期**: 2025-12-23
> **更新日期**: 2025-12-23
> **基准**: docs/10.module-specs/ 模块规格书
> **覆盖模块**: A1-A3, B1-B3, C1-C3, D1

---

## 目录

1. [测试用例规范](#1-测试用例规范)
2. [A1 老板驾驶舱](#2-a1-老板驾驶舱)
3. [A2 资金总览](#3-a2-资金总览)
4. [A3 项目盈亏](#4-a3-项目盈亏)
5. [B1 充值审批](#5-b1-充值审批)
6. [B2 日报审核](#6-b2-日报审核)
7. [B3 周度简报](#7-b3-周度简报)
8. [C1 项目管理](#8-c1-项目管理)
9. [C2 投手管理](#9-c2-投手管理)
10. [C3 消耗明细](#10-c3-消耗明细)
11. [D1 月度结算](#11-d1-月度结算)
12. [跨模块集成测试](#12-跨模块集成测试)
13. [UI 通用测试](#13-ui-通用测试)

---

## 1. 测试用例规范

### 1.1 用例编号规则

```
TC-{模块编号}-{类型}-{序号}

模块编号: A1/A2/A3/B1/B2/B3/C1/C2/C3/D1/INT (集成)
类型:
  - FN: 功能测试 (Functional)
  - BD: 边界测试 (Boundary)
  - PM: 权限测试 (Permission)
  - DI: 数据完整性测试 (Data Integrity)
  - ST: 状态机测试 (State Machine)
  - UI: 界面测试 (UI)
  - NE: 网络异常测试 (Network Error)

示例: TC-A1-FN-001
```

### 1.2 优先级定义

| 优先级 | 说明 | 测试时机 | 用例数量目标 |
|--------|------|----------|--------------|
| P0 | 核心功能，阻塞性 | 每次构建 | ~30 用例 |
| P1 | 重要功能 | 每日测试 | ~70 用例 |
| P2 | 一般功能 | 回归测试 | ~50 用例 |
| P3 | 边缘场景 | 发布前 | ~20 用例 |

### 1.3 测试状态

| 状态 | 说明 |
|------|------|
| :white_check_mark: | 通过 |
| :x: | 失败 |
| :construction: | 待执行 |
| :no_entry: | 阻塞 |

### 1.4 Smoke Test 标记

带有 **[SMOKE]** 标记的用例为冒烟测试子集，用于快速验证系统核心功能。

### 1.5 合法角色清单 (MASTER.md v4.4 §2.4)

| 角色 | 中文名 | 职责 |
|------|--------|------|
| ceo | 老板 | 资金安全、公司盈亏、最终决策 |
| project_owner | 项目负责人 | 项目盈亏、资金使用效率 |
| finance | 财务 | 资金出入准确、数据真实、对账 |
| supervisor | 主管 | 团队产出、投手管理、日常监督 |
| pitcher | 投手 | CPL 达标、日报准确、执行投放 |
| account_manager | 户管 | 账户分配、账户状态监控 |
| admin | 管理员 | 系统配置（不参与业务） |

---

## 2. A1 老板驾驶舱

**模块优先级**: P0
**规格书**: [A1-dashboard.md](./A1-dashboard.md)

### 2.1 功能测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-A1-FN-001 | **[SMOKE]** KPI卡片数据显示 | 系统有本月数据 | 1. 以 ceo 角色登录<br>2. 进入驾驶舱页面<br>3. 验证 4 个 KPI 卡片渲染 | 显示4个KPI卡片：本月消耗、本月进粉、整体CPL、预计毛利；数据与 API 响应一致 | P0 | :construction: |
| TC-A1-FN-002 | KPI变化率计算 | 有上期对比数据 | 1. 进入驾驶舱<br>2. 查看变化百分比<br>3. 验证计算公式 | 变化率=（本期-上期）/上期×100%，正数显示绿色↑，负数显示红色↓，精度保留1位小数 | P1 | :construction: |
| TC-A1-FN-003 | 运营状态卡片 | 有项目数据 | 1. 进入驾驶舱<br>2. 验证运营状态区域 | 显示：活跃项目数、异常项目数（CPL>target×1.3）、待审批充值数 | P0 | :construction: |
| TC-A1-FN-004 | 时间范围切换-7日 | 驾驶舱已加载 | 1. 点击时间筛选器<br>2. 选择"7日"<br>3. 验证数据刷新 | KPI和趋势图数据刷新为近7日数据，API 请求包含正确日期参数 | P1 | :construction: |
| TC-A1-FN-005 | KPI卡片联动趋势图 | 驾驶舱已加载 | 1. 点击"本月消耗"卡片<br>2. 验证趋势图切换 | 趋势图切换到消耗指标，卡片显示选中状态（蓝色边框） | P1 | :construction: |
| TC-A1-FN-006 | Top列表显示 | 有项目数据 | 1. 查看归因列表区域<br>2. 验证两个列表 | 显示"消耗Top5"和"ROAS最差Top5"两个列表，按降序排列 | P1 | :construction: |
| TC-A1-FN-007 | 待处理事项跳转 | 有待审批充值 | 1. 点击"待审批充值(3)"<br>2. 验证跳转 | 跳转到 /topups?status=pending_review，筛选条件自动填充 | P1 | :construction: |
| TC-A1-FN-008 | 手动刷新 | 驾驶舱已加载 | 1. 点击刷新按钮<br>2. 观察加载状态 | 所有数据重新加载，显示加载动画，完成后刷新时间戳更新 | P2 | :construction: |
| TC-A1-FN-009 | Top列表项跳转 | 有项目数据 | 1. 点击Top列表中的项目<br>2. 验证跳转 | 跳转到 /projects/{id} 项目详情页 | P2 | :construction: |

### 2.2 边界测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-A1-BD-001 | **[SMOKE]** 零转化CPL显示 | conversions=0 | 1. 准备 conversions=0 的数据<br>2. 进入驾驶舱<br>3. 验证 CPL 显示 | CPL 显示"--"而非报错，无 console 错误 | P0 | :construction: |
| TC-A1-BD-002 | 低量标记 | conversions<5 | 1. 准备 conversions=3 的数据<br>2. 进入驾驶舱 | CPL 显示"¥XX.XX (低量)"，黄色标识 | P1 | :construction: |
| TC-A1-BD-003 | 空数据状态 | 无任何数据 | 1. 清空测试数据<br>2. 进入驾驶舱 | 显示空状态提示"暂无数据"，不报错，有引导文案 | P1 | :construction: |
| TC-A1-BD-004 | 加载状态 | 网络延迟 | 1. 模拟网络延迟 2s<br>2. 进入驾驶舱 | 显示 Skeleton 加载骨架屏，覆盖所有卡片区域 | P2 | :construction: |
| TC-A1-BD-005 | 错误状态 | API返回 500 | 1. Mock API 返回 500<br>2. 进入驾驶舱 | 显示错误提示"加载失败"，有重试按钮，点击重试后重新请求 | P1 | :construction: |
| TC-A1-BD-006 | 大数字格式化 | 消耗>100万 | 1. 准备消耗=1500000 的数据<br>2. 进入驾驶舱 | 显示"¥150 万"格式，非科学计数法，非"¥150w" | P1 | :construction: |

### 2.3 权限测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-A1-PM-001 | **[SMOKE]** CEO查看全公司数据 | 以 ceo 角色登录 | 1. 登录 ceo 账号<br>2. 进入驾驶舱<br>3. 验证数据范围 | 可见全公司 KPI 数据，无项目筛选限制 | P0 | :construction: |
| TC-A1-PM-002 | 投手只看自己数据 | 以 pitcher 角色登录 | 1. 登录 pitcher 账号<br>2. 进入驾驶舱<br>3. 验证数据范围 | 只能看到自己相关的数据，数据量明显少于 CEO | P0 | :construction: |
| TC-A1-PM-003 | 项目负责人看自己项目 | 以 project_owner 角色登录 | 1. 登录 project_owner 账号<br>2. 进入驾驶舱<br>3. 验证数据范围 | 只能看到自己负责项目的数据，Top 列表只含自己项目 | P0 | :construction: |
| TC-A1-PM-004 | 主管看团队数据 | 以 supervisor 角色登录 | 1. 登录 supervisor 账号<br>2. 进入驾驶舱 | 可见团队汇总数据，包含下属投手数据 | P1 | :construction: |
| TC-A1-PM-005 | 财务看全公司财务指标 | 以 finance 角色登录 | 1. 登录 finance 账号<br>2. 进入驾驶舱 | 可见全公司消耗、充值相关指标，但不显示项目负责人归因信息 | P1 | :construction: |
| TC-A1-PM-006 | 户管看账户维度数据 | 以 account_manager 角色登录 | 1. 登录 account_manager 账号<br>2. 进入驾驶舱 | 可见账户维度汇总，Top 列表显示账户而非项目 | P1 | :construction: |

### 2.4 网络异常测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-A1-NE-001 | 网络断开 | 驾驶舱已加载 | 1. 断开网络<br>2. 点击刷新 | 显示网络错误提示，保留上次数据，有重试按钮 | P1 | :construction: |
| TC-A1-NE-002 | 请求超时 | 网络延迟 >30s | 1. 模拟 30s 延迟<br>2. 进入驾驶舱 | 显示超时提示，有重试按钮 | P2 | :construction: |

### 2.5 UI 测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-A1-UI-001 | 响应式布局-桌面 | 视窗宽度 ≥1200px | 1. 设置浏览器宽度 1440px<br>2. 进入驾驶舱 | 4 个 KPI 卡片一行显示，趋势图与 Top 列表并排 | P2 | :construction: |
| TC-A1-UI-002 | 响应式布局-平板 | 视窗宽度 768-1199px | 1. 设置浏览器宽度 1024px<br>2. 进入驾驶舱 | KPI 卡片 2×2 网格，趋势图单独一行 | P2 | :construction: |
| TC-A1-UI-003 | 暗色模式显示 | 系统开启暗色模式 | 1. 切换暗色模式<br>2. 进入驾驶舱 | 所有组件正确显示暗色主题，文字对比度符合 WCAG AA | P3 | :construction: |

---

## 3. A2 资金总览

**模块优先级**: P0
**规格书**: [A2-fund-overview.md](./A2-fund-overview.md)

### 3.1 功能测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-A2-FN-001 | **[SMOKE]** 资金概览卡片 | 有充值和消耗数据 | 1. 以 ceo 角色登录<br>2. 进入资金总览页<br>3. 验证 5 个卡片 | 显示5个卡片：累计充值、累计消耗、当前余额、应收款、资金占用；数值格式正确 | P0 | :construction: |
| TC-A2-FN-002 | 资金流水表格 | 有资金记录 | 1. 查看流水表格<br>2. 验证列字段 | 显示时间、类型、金额、账户、操作人、备注，按时间倒序排列 | P0 | :construction: |
| TC-A2-FN-003 | **[SMOKE]** 余额计算准确 | 有充值和消耗 | 1. 查看当前余额<br>2. 对比数据库计算 | 余额 = 累计充值 - 累计消耗，与数据库 ledger_entries 汇总一致 | P0 | :construction: |
| TC-A2-FN-004 | 时间范围筛选 | 有历史数据 | 1. 选择日期范围 2024-01-01 至 2024-01-31<br>2. 点击确认 | 显示指定时间范围的数据，API 参数包含 start_date, end_date | P1 | :construction: |
| TC-A2-FN-005 | 账户筛选 | 有多个账户 | 1. 选择特定账户<br>2. 验证数据过滤 | 只显示该账户的资金数据，KPI 卡片数值相应更新 | P1 | :construction: |
| TC-A2-FN-006 | 导出功能 | 以 finance 角色登录，有数据 | 1. 点击导出按钮<br>2. 验证下载 | 下载 Excel 文件，包含当前筛选条件的完整数据 | P2 | :construction: |

### 3.2 数据完整性测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-A2-DI-001 | **[SMOKE]** 充值SoT一致性 | 有 ledger_entries 记录 | 1. 查询数据库 SUM(amount) WHERE type='topup'<br>2. 对比页面累计充值 | 累计充值=SUM(ledger_entries WHERE type='topup')，误差<0.01 | P0 | :construction: |
| TC-A2-DI-002 | 消耗SoT一致性 | 有 ad_spend_daily 记录 | 1. 查询数据库 SUM(spend)<br>2. 对比页面累计消耗 | 累计消耗=SUM(ad_spend_daily.spend)，误差<0.01 | P0 | :construction: |
| TC-A2-DI-003 | 资金占用计算 | 有在途充值 | 1. 查看资金占用<br>2. 对比数据库 | 资金占用=未到账充值(status=paid)+预付款 | P1 | :construction: |

### 3.3 权限测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-A2-PM-001 | **[SMOKE]** CEO 查看全部资金 | 以 ceo 角色登录 | 1. 进入资金总览<br>2. 验证数据范围 | 可见全公司资金数据，无账户筛选限制 | P0 | :construction: |
| TC-A2-PM-002 | 财务查看全部资金 | 以 finance 角色登录 | 1. 进入资金总览<br>2. 验证数据范围和操作权限 | 可见全公司资金数据，可导出，无审批权限 | P0 | :construction: |
| TC-A2-PM-003 | 项目负责人看自己项目 | 以 project_owner 角色登录 | 1. 进入资金总览<br>2. 验证数据范围 | 只能看到自己项目关联账户的资金数据 | P0 | :construction: |
| TC-A2-PM-004 | 投手无权访问 | 以 pitcher 角色登录 | 1. 尝试进入资金总览 | 无菜单入口，直接访问 URL 返回 403 或重定向 | P0 | :construction: |
| TC-A2-PM-005 | 户管看账户资金 | 以 account_manager 角色登录 | 1. 进入资金总览 | 可见所管理账户的资金数据，无导出权限 | P1 | :construction: |

### 3.4 边界测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-A2-BD-001 | 负余额显示 | 余额<0 | 1. 准备消耗>充值的数据<br>2. 进入资金总览 | 余额显示红色负数，如"-¥12,300" | P1 | :construction: |
| TC-A2-BD-002 | 空数据状态 | 无任何资金记录 | 1. 清空测试数据<br>2. 进入资金总览 | 显示空状态，所有卡片显示"¥0"或"--" | P1 | :construction: |

---

## 4. A3 项目盈亏

**模块优先级**: P0
**规格书**: [A3-project-pnl.md](./A3-project-pnl.md)

### 4.1 功能测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-A3-FN-001 | **[SMOKE]** 概览卡片显示 | 有项目数据 | 1. 以 ceo 角色登录<br>2. 进入盈亏看板 | 显示：今日利润、本周利润、本月利润、整体利润率 | P0 | :construction: |
| TC-A3-FN-002 | 项目列表显示 | 有项目数据 | 1. 查看项目盈亏明细<br>2. 验证表格列 | 表格显示：项目名、负责人、消耗、进粉、CPL、利润、利润率、异常标记 | P0 | :construction: |
| TC-A3-FN-003 | **[SMOKE]** 利润计算 | 有消耗和进粉 | 1. 查看某项目利润<br>2. 验证计算公式 | 利润=进粉×unit_price-消耗，与数据库计算一致 | P0 | :construction: |
| TC-A3-FN-004 | 维度切换 | 有数据 | 1. 点击"账户"维度<br>2. 验证表格变化 | 表格切换为按账户汇总视图，列结构相应调整 | P1 | :construction: |
| TC-A3-FN-005 | 排序功能 | 有多项目 | 1. 点击"利润"表头<br>2. 再次点击 | 首次按利润降序排列，再次点击升序排列 | P1 | :construction: |
| TC-A3-FN-006 | 日期筛选 | 有历史数据 | 1. 选择日期范围<br>2. 验证数据刷新 | 显示指定时间段的盈亏数据，KPI 卡片同步更新 | P1 | :construction: |
| TC-A3-FN-007 | 异常标记显示 | 有 CPL 超标项目 | 1. 查看异常列<br>2. 验证标记规则 | CPL>target_cpl×1.3 的项目显示黄色⚠️图标 | P0 | :construction: |
| TC-A3-FN-008 | 负责人显示 | 项目有负责人 | 1. 查看负责人列 | 显示项目负责人姓名，可点击查看详情 | P1 | :construction: |
| TC-A3-FN-009 | 趋势图显示 | 有历史数据 | 1. 查看趋势图区域 | 显示收入/成本/利润趋势折线图，支持悬停查看详情 | P1 | :construction: |

### 4.2 边界测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-A3-BD-001 | 零进粉 CPL | conversions=0 | 1. 准备 conversions=0 的项目<br>2. 查看该项目 CPL | CPL 显示"--"，不显示错误 | P0 | :construction: |
| TC-A3-BD-002 | 低量 CPL 标记 | conversions<5 | 1. 准备 conversions=3 的项目<br>2. 查看 CPL | 显示"¥XX (低量)"，灰色提示 | P1 | :construction: |
| TC-A3-BD-003 | 单价为空 | unit_price=null | 1. 准备 unit_price 为空的项目<br>2. 查看收入列 | 收入显示"待定"，利润不计算 | P1 | :construction: |
| TC-A3-BD-004 | 负利润显示 | profit<0 | 1. 准备亏损项目<br>2. 查看利润列 | 红色显示负数，如"-¥12,300" | P0 | :construction: |
| TC-A3-BD-005 | 目标 CPL 为空 | target_cpl=null | 1. 准备无目标 CPL 的项目<br>2. 查看异常列 | 不显示异常标记，异常列为空 | P2 | :construction: |

### 4.3 权限测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-A3-PM-001 | **[SMOKE]** CEO看全部项目 | 以 ceo 角色登录 | 1. 进入盈亏看板<br>2. 验证项目列表 | 显示全部项目，无筛选限制 | P0 | :construction: |
| TC-A3-PM-002 | 项目负责人看自己项目 | 以 project_owner 角色登录 | 1. 进入盈亏看板<br>2. 验证项目列表 | 只显示自己负责的项目 | P0 | :construction: |
| TC-A3-PM-003 | 投手无权限 | 以 pitcher 角色登录 | 1. 尝试进入盈亏看板 | 无菜单入口，或显示无权限提示 | P1 | :construction: |

---

## 5. B1 充值审批

**模块优先级**: P1
**规格书**: [B1-topup-approval.md](./B1-topup-approval.md)

### 5.1 状态机测试 (7 状态)

**状态机定义 (B1-topup-approval.md §6.1):**
```
draft → pending_review → finance_approve → paid → completed
          ↓                   ↓
       rejected            voided
```

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-B1-ST-001 | **[SMOKE]** draft→pending_review | 充值记录 status=draft | 1. 以 project_owner 登录<br>2. 点击提交审核 | 状态变更为 pending_review，记录审核时间 | P0 | :construction: |
| TC-B1-ST-002 | pending_review→finance_approve | status=pending_review | 1. 以 supervisor 登录<br>2. 点击确认数据 | 状态变更为 finance_approve | P0 | :construction: |
| TC-B1-ST-003 | finance_approve→paid | status=finance_approve | 1. 以 finance 登录<br>2. 点击审批通过 | 状态变更为 paid，记录审批人和时间 | P0 | :construction: |
| TC-B1-ST-004 | paid→completed | status=paid | 1. 确认到账<br>2. 点击完成 | 状态变更为 completed，记录完成时间 | P0 | :construction: |
| TC-B1-ST-005 | pending_review→rejected | status=pending_review | 1. 点击拒绝<br>2. 填写拒绝原因 | 状态变更为 rejected，记录原因 | P0 | :construction: |
| TC-B1-ST-006 | **[SMOKE]** 终态不可操作 | status=completed | 1. 尝试点击任何操作按钮 | 所有操作按钮禁用/隐藏，提示"已完成" | P0 | :construction: |
| TC-B1-ST-007 | pending_review→voided | status=pending_review | 1. 点击作废<br>2. 确认作废 | 状态变更为 voided，记录作废时间 | P1 | :construction: |

### 5.2 非法状态转换测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-B1-ST-008 | draft 不可跳转 paid | status=draft | 1. 尝试直接调用 API 转换到 paid | 返回 400 错误码 ST-001，提示"非法状态转换" | P0 | :construction: |
| TC-B1-ST-009 | completed 不可回退 | status=completed | 1. 尝试调用 API 回退到 paid | 返回 400 错误码 ST-002，提示"终态不可回退" | P0 | :construction: |
| TC-B1-ST-010 | rejected 不可继续 | status=rejected | 1. 尝试调用 API 转换到 finance_approve | 返回 400 错误码 ST-001 | P1 | :construction: |
| TC-B1-ST-011 | voided 不可恢复 | status=voided | 1. 尝试调用 API 转换到 pending_review | 返回 400 错误码 ST-001 | P1 | :construction: |

### 5.3 功能测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-B1-FN-001 | **[SMOKE]** 创建充值申请 | 以 project_owner 登录 | 1. 点击新建<br>2. 填写金额、账户<br>3. 点击提交 | 创建成功，状态为 draft，显示在列表中 | P0 | :construction: |
| TC-B1-FN-002 | 充值列表筛选 | 有多条记录 | 1. 选择状态筛选<br>2. 选择日期范围 | 按条件过滤显示，URL 参数同步更新 | P1 | :construction: |
| TC-B1-FN-003 | 审批时间线 | 有审批历史 | 1. 点击查看详情<br>2. 查看时间线 | 显示完整审批时间线，包含每步操作人和时间 | P1 | :construction: |
| TC-B1-FN-004 | 金额格式化 | 金额=150000 | 1. 查看列表金额列 | 显示"¥15 万"或"¥150,000" | P2 | :construction: |
| TC-B1-FN-005 | 批量审批 | 有多条待审批 | 1. 选择多条记录<br>2. 点击批量通过 | 所选记录状态同时变更 | P2 | :construction: |

### 5.4 权限测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-B1-PM-001 | **[SMOKE]** 项目负责人创建 | 以 project_owner 登录 | 1. 创建充值申请 | 允许创建，只能选择自己项目的账户 | P0 | :construction: |
| TC-B1-PM-002 | 投手无法创建 | 以 pitcher 登录 | 1. 尝试创建 | 无"新建"按钮，或被拒绝 | P0 | :construction: |
| TC-B1-PM-003 | 财务审批权限 | 以 finance 登录 | 1. 审批 finance_approve 状态记录 | 允许审批通过/拒绝 | P0 | :construction: |
| TC-B1-PM-004 | CEO查看全部 | 以 ceo 登录 | 1. 进入充值审批 | 可见全部充值记录，可审批 | P0 | :construction: |

---

## 6. B2 日报审核

**模块优先级**: P1
**规格书**: [B2-daily-report-review.md](./B2-daily-report-review.md)

### 6.1 状态机测试 (8 状态)

**状态机定义 (STATE_MACHINE.md v2.6):**
```
raw_submitted → trend_pending → trend_ok → final_pending → final_confirmed → final_locked
                       ↓
                trend_flagged → trend_resolved
```

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-B2-ST-001 | **[SMOKE]** raw_submitted→trend_pending | 投手已提交日报 | 1. 系统自动触发<br>2. 验证状态 | 状态自动变更为 trend_pending | P0 | :construction: |
| TC-B2-ST-002 | trend_pending→trend_ok | status=trend_pending | 1. 以 supervisor 登录<br>2. 点击趋势通过 | 状态变更为 trend_ok | P0 | :construction: |
| TC-B2-ST-003 | trend_pending→trend_flagged | status=trend_pending | 1. 以 supervisor 登录<br>2. 点击标记异常<br>3. 填写异常原因 | 状态变更为 trend_flagged，原因必填 | P0 | :construction: |
| TC-B2-ST-004 | trend_flagged→trend_resolved | status=trend_flagged | 1. 以 supervisor 登录<br>2. 处理异常<br>3. 填写处理结果 | 状态变更为 trend_resolved | P0 | :construction: |
| TC-B2-ST-005 | trend_ok→final_pending | status=trend_ok | 1. 提交终审 | 状态变更为 final_pending | P0 | :construction: |
| TC-B2-ST-006 | final_pending→final_confirmed | status=final_pending | 1. 以 finance 登录<br>2. 终审确认 | 状态变更为 final_confirmed | P0 | :construction: |
| TC-B2-ST-007 | final_confirmed→final_locked | status=final_confirmed | 1. 系统自动锁定 | 状态变更为 final_locked | P0 | :construction: |
| TC-B2-ST-008 | trend_resolved→final_pending | status=trend_resolved | 1. 提交终审 | 状态变更为 final_pending | P1 | :construction: |

### 6.2 非法状态转换测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-B2-ST-009 | raw_submitted 不可跳转 final | status=raw_submitted | 1. 尝试直接调用 API 转换到 final_confirmed | 返回 400 错误码 ST-001 | P0 | :construction: |
| TC-B2-ST-010 | final_locked 不可回退 | status=final_locked | 1. 尝试调用 API 回退到 final_confirmed | 返回 400 错误码 ST-002 | P0 | :construction: |
| TC-B2-ST-011 | trend_ok 不可回退 trend_pending | status=trend_ok | 1. 尝试回退到 trend_pending | 返回 400 错误码 ST-001 | P1 | :construction: |

### 6.3 趋势风控测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-B2-TF-001 | TF-001 CPL 突增 | 7日历史数据 | 1. 提交 CPL>7日均值×1.5 的日报 | 自动触发 trend_flagged，记录触发规则 TF-001 | P1 | :construction: |
| TC-B2-TF-002 | TF-002 消耗突增 | 7日历史数据 | 1. 提交 spend>7日均值×2.0 的日报 | 自动触发 trend_flagged，记录触发规则 TF-002 | P1 | :construction: |
| TC-B2-TF-003 | TF-003 进粉骤降 | 7日历史数据 | 1. 提交 conversions<7日均值×0.5 的日报 | 自动触发 trend_flagged，记录触发规则 TF-003 | P1 | :construction: |

### 6.4 功能测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-B2-FN-001 | **[SMOKE]** 投手创建日报 | 以 pitcher 登录 | 1. 点击新建<br>2. 填写消耗、进粉<br>3. 点击提交 | 创建成功，状态为 raw_submitted | P0 | :construction: |
| TC-B2-FN-002 | KPI卡片统计 | 有日报数据 | 1. 进入日报管理<br>2. 验证 KPI 卡片 | 显示：总日报数、待审核、异常待处理、已锁定 | P0 | :construction: |
| TC-B2-FN-003 | 状态 Tab 筛选 | 有多状态日报 | 1. 点击"待审核" Tab | 只显示 trend_pending 和 final_pending 状态 | P1 | :construction: |
| TC-B2-FN-004 | 日期筛选 | 有历史数据 | 1. 选择日期范围 | 按日期过滤显示 | P1 | :construction: |
| TC-B2-FN-005 | 团队筛选 | 有多团队数据 | 1. 选择特定团队 | 只显示该团队日报 | P1 | :construction: |
| TC-B2-FN-006 | **[SMOKE]** CPL计算显示 | 有消耗和进粉 | 1. 查看 CPL 列 | CPL = raw_spend / follows_count，保留2位小数 | P0 | :construction: |
| TC-B2-FN-007 | 导出功能 | 以 finance 登录，有数据 | 1. 点击导出 | 下载 XLSX 文件 | P2 | :construction: |

### 6.5 数据完整性测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-B2-DI-001 | 消耗SoT一致 | Phase1 环境 | 1. 对比日报消耗和 ad_spend_daily<br>2. 验证数据来源 | 消耗来自 ad_spend_daily.spend，不可手动修改 | P0 | :construction: |
| TC-B2-DI-002 | 审计日志记录 | 执行状态变更 | 1. 变更状态<br>2. 查询 audit_logs 表 | 每次状态变更有审计记录，包含操作人、时间、前后状态 | P1 | :construction: |
| TC-B2-DI-003 | **[SMOKE]** 锁定后不可修改 | status=final_locked | 1. 尝试调用修改 API | 返回 400，提示"已锁定不可修改" | P0 | :construction: |

### 6.6 权限测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-B2-PM-001 | **[SMOKE]** 投手创建日报 | 以 pitcher 登录 | 1. 创建日报 | 允许创建，只能为自己账户创建 | P0 | :construction: |
| TC-B2-PM-002 | 投手只看自己 | 以 pitcher 登录 | 1. 查看列表 | 只显示自己的日报 | P0 | :construction: |
| TC-B2-PM-003 | 主管趋势审核 | 以 supervisor 登录 | 1. 审核日报 | 可以通过/标记异常，只能审核下属日报 | P0 | :construction: |
| TC-B2-PM-004 | 财务终审 | 以 finance 登录 | 1. 终审确认 | 允许终审确认 | P0 | :construction: |
| TC-B2-PM-005 | 投手无审核权 | 以 pitcher 登录 | 1. 尝试审核 | 无审核按钮，或操作被拒绝 | P0 | :construction: |

---

## 7. B3 周度简报

**模块优先级**: P2
**规格书**: [B3-weekly-brief.md](./B3-weekly-brief.md)
**实现状态**: 待开发

### 7.1 功能测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-B3-FN-001 | **[SMOKE]** 创建周报 | 以 project_owner 登录 | 1. 点击创建周报<br>2. 选择项目和周次<br>3. 填写内容 | 创建成功，状态为 draft | P0 | :construction: |
| TC-B3-FN-002 | 自动汇总周数据 | 有本周消耗和进粉 | 1. 创建周报<br>2. 验证自动填充 | 自动填充周消耗、周进粉、周CPL | P0 | :construction: |
| TC-B3-FN-003 | 编辑草稿 | status=draft | 1. 修改内容<br>2. 保存 | 修改成功 | P1 | :construction: |
| TC-B3-FN-004 | 提交周报 | status=draft | 1. 点击提交 | 状态变更为 submitted | P0 | :construction: |
| TC-B3-FN-005 | 已提交不可编辑 | status=submitted | 1. 尝试编辑 | 编辑被拒绝，显示只读视图 | P1 | :construction: |
| TC-B3-FN-006 | 周次选择器 | 驾驶舱已加载 | 1. 点击周次选择器<br>2. 选择上周 | 加载上周周报数据 | P1 | :construction: |
| TC-B3-FN-007 | 环比计算 | 有上周数据 | 1. 查看环比 | 显示(本周-上周)/上周×100% | P1 | :construction: |

### 7.2 边界测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-B3-BD-001 | 重复创建 | 已有本周周报 | 1. 尝试再次创建 | 被拒绝，提示"本周周报已存在" | P0 | :construction: |
| TC-B3-BD-002 | 无上周数据环比 | 无上周数据 | 1. 查看环比 | 环比显示"--" | P1 | :construction: |
| TC-B3-BD-003 | 零进粉周 CPL | 周进粉=0 | 1. 查看周 CPL | 显示"--" | P1 | :construction: |

### 7.3 权限测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-B3-PM-001 | 项目负责人创建 | 以 project_owner 登录 | 1. 创建自己项目的周报 | 允许创建 | P0 | :construction: |
| TC-B3-PM-002 | 无法创建他人项目 | 以 project_owner 登录 | 1. 尝试创建他人项目周报 | 项目选择器中无他人项目 | P0 | :construction: |
| TC-B3-PM-003 | CEO 查看全部 | 以 ceo 登录 | 1. 进入周度简报 | 可见全部项目周报 | P0 | :construction: |
| TC-B3-PM-004 | 主管查看团队 | 以 supervisor 登录 | 1. 进入周度简报 | 只能看到团队项目周报 | P1 | :construction: |

---

## 8. C1 项目管理

**模块优先级**: P0
**规格书**: [C1-project-mgmt.md](./C1-project-mgmt.md)

### 8.1 状态机测试 (5 状态)

**状态机定义 (C1-project-mgmt.md §6.1):**
```
planning → active → completed
    ↓         ↓
cancelled   paused → active
```

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-C1-ST-001 | **[SMOKE]** planning→active | status=planning | 1. 点击启动项目 | 状态变更为 active | P0 | :construction: |
| TC-C1-ST-002 | active→paused | status=active | 1. 点击暂停 | 状态变更为 paused | P0 | :construction: |
| TC-C1-ST-003 | paused→active | status=paused | 1. 点击恢复 | 状态变更为 active | P0 | :construction: |
| TC-C1-ST-004 | active→completed | status=active | 1. 点击完成 | 状态变更为 completed | P0 | :construction: |
| TC-C1-ST-005 | planning→cancelled | status=planning | 1. 点击取消 | 状态变更为 cancelled | P1 | :construction: |
| TC-C1-ST-006 | 终态不可编辑 | status=completed | 1. 尝试编辑 | 编辑按钮禁用，显示只读 | P0 | :construction: |

### 8.2 非法状态转换测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-C1-ST-007 | completed 不可回退 | status=completed | 1. 尝试调用 API 回退到 active | 返回 400 错误码 ST-002 | P0 | :construction: |
| TC-C1-ST-008 | cancelled 不可恢复 | status=cancelled | 1. 尝试调用 API 转换到 active | 返回 400 错误码 ST-001 | P1 | :construction: |

### 8.3 功能测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-C1-FN-001 | **[SMOKE]** 创建项目 | 以 ceo 或 project_owner 登录 | 1. 点击新建<br>2. 填写名称、预算等<br>3. 保存 | 创建成功，状态为 planning | P0 | :construction: |
| TC-C1-FN-002 | 编辑项目 | status 非终态 | 1. 点击编辑<br>2. 修改信息<br>3. 保存 | 修改成功 | P1 | :construction: |
| TC-C1-FN-003 | 管理成员 | 有项目 | 1. 点击成员管理<br>2. 添加/移除成员 | 成员列表更新 | P1 | :construction: |
| TC-C1-FN-004 | 统计卡片 | 有项目数据 | 1. 查看统计卡片 | 显示：项目总数、进行中、总预算、总消耗 | P1 | :construction: |
| TC-C1-FN-005 | 状态筛选 | 有多状态项目 | 1. 选择"进行中" | 只显示 active 状态项目 | P1 | :construction: |
| TC-C1-FN-006 | 搜索功能 | 有多个项目 | 1. 输入客户名搜索 | 按客户名过滤显示 | P1 | :construction: |
| TC-C1-FN-007 | 分页功能 | 项目数>页大小 | 1. 点击下一页 | 正确加载下一页数据 | P2 | :construction: |
| TC-C1-FN-008 | 预算进度显示 | 有消耗数据 | 1. 查看进度列 | 显示进度条和百分比 | P1 | :construction: |

### 8.4 边界测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-C1-BD-001 | 预算为0 | budget=0 | 1. 查看进度 | 进度显示 0% | P1 | :construction: |
| TC-C1-BD-002 | 预算为空 | budget=null | 1. 查看进度 | 进度显示"--" | P1 | :construction: |
| TC-C1-BD-003 | 负责人为空 | owner_id=null | 1. 查看负责人列 | 显示"未分配" | P1 | :construction: |
| TC-C1-BD-004 | 目标 CPL 为空 | target_cpl=null | 1. 查看 CPL 目标 | 显示"--" | P2 | :construction: |

### 8.5 权限测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-C1-PM-001 | **[SMOKE]** CEO 创建项目 | 以 ceo 登录 | 1. 创建项目 | 允许创建 | P0 | :construction: |
| TC-C1-PM-002 | 项目负责人创建 | 以 project_owner 登录 | 1. 创建项目 | 允许创建 | P0 | :construction: |
| TC-C1-PM-003 | 投手无法创建 | 以 pitcher 登录 | 1. 尝试创建 | 无按钮或被拒绝 | P0 | :construction: |
| TC-C1-PM-004 | 项目负责人只看自己 | 以 project_owner 登录 | 1. 查看列表 | 只显示自己负责的项目 | P0 | :construction: |
| TC-C1-PM-005 | 非管理员无法删除 | 以 project_owner 登录 | 1. 尝试删除 | 无删除按钮或被拒绝 | P0 | :construction: |

---

## 9. C2 投手管理

**模块优先级**: P2
**规格书**: [C2-pitcher-mgmt.md](./C2-pitcher-mgmt.md)

### 9.1 功能测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-C2-FN-001 | **[SMOKE]** 投手列表显示 | 有投手数据 | 1. 进入投手管理 | 显示：姓名、用户名、团队、主管、负责账户、状态 | P0 | :construction: |
| TC-C2-FN-002 | 创建投手账号 | 以 admin 登录 | 1. 点击添加<br>2. 填写信息<br>3. 保存 | 创建成功，role=pitcher | P0 | :construction: |
| TC-C2-FN-003 | 编辑投手信息 | 有投手 | 1. 点击编辑<br>2. 修改信息<br>3. 保存 | 修改成功 | P1 | :construction: |
| TC-C2-FN-004 | 停用投手 | 以 admin 登录 | 1. 点击停用 | is_active 变为 false | P1 | :construction: |
| TC-C2-FN-005 | 启用投手 | 投手已停用 | 1. 点击启用 | is_active 变为 true | P1 | :construction: |
| TC-C2-FN-006 | 分配账户 | 以 supervisor 登录 | 1. 点击分配账户<br>2. 选择账户<br>3. 确认 | 账户分配给投手 | P1 | :construction: |
| TC-C2-FN-007 | 查看负责账户 | 投手有账户 | 1. 点击查看账户 | 显示投手负责的账户列表 | P1 | :construction: |
| TC-C2-FN-008 | 搜索筛选 | 有多个投手 | 1. 输入姓名搜索 | 按姓名过滤 | P1 | :construction: |
| TC-C2-FN-009 | 主管筛选 | 有多个主管 | 1. 选择特定主管 | 只显示该主管下属 | P1 | :construction: |

### 9.2 权限测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-C2-PM-001 | **[SMOKE]** 主管看团队 | 以 supervisor 登录 | 1. 进入投手管理 | 只显示自己团队的投手 | P0 | :construction: |
| TC-C2-PM-002 | 投手看自己 | 以 pitcher 登录 | 1. 进入投手管理 | 只显示自己的信息 | P0 | :construction: |
| TC-C2-PM-003 | 主管分配账户 | 以 supervisor 登录 | 1. 分配账户 | 允许分配 | P1 | :construction: |
| TC-C2-PM-004 | 投手无法分配 | 以 pitcher 登录 | 1. 尝试分配账户 | 被拒绝 | P1 | :construction: |
| TC-C2-PM-005 | 只有 admin 创建 | 以 supervisor 登录 | 1. 尝试创建投手 | 无按钮或被拒绝 | P0 | :construction: |

---

## 10. C3 消耗明细

**模块优先级**: P1
**规格书**: [C3-spend-detail.md](./C3-spend-detail.md)

### 10.1 功能测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-C3-FN-001 | **[SMOKE]** 消耗列表显示 | 有消耗数据 | 1. 进入消耗明细 | 显示：账户、项目、渠道、日期、消耗、曝光、点击、粉数、CPA | P0 | :construction: |
| TC-C3-FN-002 | 日期筛选 | 有历史数据 | 1. 选择日期范围 | 按日期过滤显示 | P0 | :construction: |
| TC-C3-FN-003 | 项目筛选 | 有多项目数据 | 1. 选择特定项目 | 只显示该项目消耗 | P1 | :construction: |
| TC-C3-FN-004 | 渠道筛选 | 有多渠道数据 | 1. 选择特定渠道 | 只显示该渠道消耗 | P1 | :construction: |
| TC-C3-FN-005 | 账户筛选 | 有多账户数据 | 1. 选择特定账户 | 只显示该账户消耗 | P1 | :construction: |
| TC-C3-FN-006 | KPI 卡片统计 | 有数据 | 1. 查看 KPI 卡片 | 显示：总消耗、总粉数、平均 CPA、平均 CTR | P1 | :construction: |
| TC-C3-FN-007 | 分页功能 | 数据量>页大小 | 1. 翻页 | 正确加载下一页 | P1 | :construction: |
| TC-C3-FN-008 | 排序功能 | 有多条数据 | 1. 点击消耗表头 | 按消耗排序 | P1 | :construction: |
| TC-C3-FN-009 | 导出功能 | 以 finance 登录 | 1. 点击导出 | 下载 Excel 文件 | P2 | :construction: |
| TC-C3-FN-010 | 导入功能 | 以 admin 登录 | 1. 上传 Excel<br>2. 确认导入 | 数据导入成功 | P1 | :construction: |

### 10.2 计算测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-C3-CAL-001 | **[SMOKE]** CPA 计算 | spend=1000, conversions=50 | 1. 查看 CPA | CPA=20 | P0 | :construction: |
| TC-C3-CAL-002 | CTR 计算 | clicks=100, impressions=5000 | 1. 查看 CTR | CTR=2% | P1 | :construction: |
| TC-C3-CAL-003 | CPC 计算 | spend=1000, clicks=100 | 1. 查看 CPC | CPC=10 | P1 | :construction: |
| TC-C3-CAL-004 | 汇总统计 | 有多条数据 | 1. 查看汇总 | 总消耗=SUM(spend) | P0 | :construction: |

### 10.3 权限测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-C3-PM-001 | **[SMOKE]** 投手看自己账户 | 以 pitcher 登录 | 1. 进入消耗明细 | 只显示自己负责账户的消耗 | P0 | :construction: |
| TC-C3-PM-002 | 主管看团队 | 以 supervisor 登录 | 1. 进入消耗明细 | 显示团队消耗数据 | P0 | :construction: |
| TC-C3-PM-003 | 财务导出 | 以 finance 登录 | 1. 点击导出 | 允许导出 | P1 | :construction: |
| TC-C3-PM-004 | 投手无法导出 | 以 pitcher 登录 | 1. 尝试导出 | 无按钮或被拒绝 | P1 | :construction: |
| TC-C3-PM-005 | 只有 admin 导入 | 以 finance 登录 | 1. 尝试导入 | 无按钮或被拒绝 | P0 | :construction: |

---

## 11. D1 月度结算

**模块优先级**: P2
**规格书**: [D1-monthly-settlement.md](./D1-monthly-settlement.md)

### 11.1 状态机测试 (4 状态)

**状态机定义 (D1-monthly-settlement.md §6.1):**
```
pending → draft → confirmed → locked
```

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-D1-ST-001 | pending→draft | 月份结束 | 1. 点击生成结算 | 状态变更为 draft | P0 | :construction: |
| TC-D1-ST-002 | draft→confirmed | status=draft | 1. 点击确认结算 | 状态变更为 confirmed | P0 | :construction: |
| TC-D1-ST-003 | confirmed→locked | status=confirmed | 1. 点击锁定 | 状态变更为 locked | P0 | :construction: |
| TC-D1-ST-004 | **[SMOKE]** locked 不可修改 | status=locked | 1. 尝试修改 | 修改被拒绝 | P0 | :construction: |
| TC-D1-ST-005 | admin 解锁 | status=locked, 以 admin 登录 | 1. 点击解锁 | 状态变回 confirmed | P1 | :construction: |

### 11.2 非法状态转换测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-D1-ST-006 | pending 不可跳转 locked | status=pending | 1. 尝试直接调用 API 转换到 locked | 返回 400 错误码 ST-001 | P0 | :construction: |
| TC-D1-ST-007 | 非 admin 不可解锁 | status=locked, 以 finance 登录 | 1. 尝试解锁 | 返回 403，提示权限不足 | P1 | :construction: |

### 11.3 功能测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-D1-FN-001 | **[SMOKE]** 生成月度结算 | 有本月数据 | 1. 选择月份<br>2. 点击生成 | 生成结算记录，汇总消耗和进粉 | P0 | :construction: |
| TC-D1-FN-002 | 月度结算列表 | 有结算数据 | 1. 进入月度结算 | 按项目显示：消耗、进粉、CPL、毛利、状态 | P0 | :construction: |
| TC-D1-FN-003 | 汇总统计 | 有多项目结算 | 1. 查看 KPI 卡片 | 显示：总消耗、总进粉、总毛利、毛利率 | P1 | :construction: |
| TC-D1-FN-004 | 月份选择 | 有历史数据 | 1. 选择其他月份 | 加载该月结算数据 | P1 | :construction: |
| TC-D1-FN-005 | 导出报表 | 以 finance 登录 | 1. 点击导出 | 下载 Excel 报表 | P2 | :construction: |
| TC-D1-FN-006 | 查看明细 | 有结算数据 | 1. 点击某行 | 打开结算明细抽屉 | P1 | :construction: |

### 11.4 计算测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-D1-CAL-001 | **[SMOKE]** 总消耗计算 | 有 ad_spend_daily 数据 | 1. 生成结算<br>2. 对比数据库 | 总消耗=SUM(ad_spend_daily.spend) | P0 | :construction: |
| TC-D1-CAL-002 | 总进粉计算 | 有 daily_reports 数据 | 1. 生成结算<br>2. 对比数据库 | 总进粉=SUM(daily_reports.conversions) | P0 | :construction: |
| TC-D1-CAL-003 | 预计收入计算 | 有 unit_price | 1. 查看收入 | 收入=总进粉×unit_price | P0 | :construction: |
| TC-D1-CAL-004 | 毛利计算 | 有收入和消耗 | 1. 查看毛利 | 毛利=收入-消耗 | P0 | :construction: |
| TC-D1-CAL-005 | 毛利率计算 | 有毛利和收入 | 1. 查看毛利率 | 毛利率=(毛利/收入)×100% | P1 | :construction: |

### 11.5 权限测试

| 用例编号 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-D1-PM-001 | **[SMOKE]** 财务生成结算 | 以 finance 登录 | 1. 生成结算 | 允许生成 | P0 | :construction: |
| TC-D1-PM-002 | 财务确认 | 以 finance 登录 | 1. 确认结算 | 允许确认 | P0 | :construction: |
| TC-D1-PM-003 | CEO 锁定 | 以 ceo 登录 | 1. 锁定结算 | 允许锁定 | P0 | :construction: |
| TC-D1-PM-004 | 财务锁定 | 以 finance 登录 | 1. 锁定结算 | 允许锁定 | P1 | :construction: |
| TC-D1-PM-005 | 项目负责人只读 | 以 project_owner 登录 | 1. 查看结算 | 只能看自己项目，无操作权限 | P0 | :construction: |
| TC-D1-PM-006 | 只有 admin 解锁 | 以 finance 登录 | 1. 尝试解锁 | 无按钮或被拒绝 | P0 | :construction: |

---

## 12. 跨模块集成测试

**测试目标**: 验证多模块间数据流转和业务流程完整性

### 12.1 端到端业务流程

| 用例编号 | 用例名称 | 涉及模块 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-INT-001 | **[SMOKE]** 充值→消耗→结算完整流程 | B1, C3, D1 | 1. 创建并完成充值<br>2. 导入消耗数据<br>3. 生成月度结算 | 充值金额反映在资金总览，消耗正确汇总，结算计算正确 | P0 | :construction: |
| TC-INT-002 | 日报→周报数据联动 | B2, B3 | 1. 创建本周日报<br>2. 创建周报 | 周报自动汇总本周日报数据 | P1 | :construction: |
| TC-INT-003 | 项目状态影响其他模块 | C1, B1, B2 | 1. 将项目状态改为 paused<br>2. 尝试创建充值和日报 | 暂停项目不允许新建充值，但可继续提交日报（Phase 1 软性） | P1 | :construction: |
| TC-INT-004 | 驾驶舱数据来源验证 | A1, B2, C3 | 1. 修改日报数据<br>2. 刷新驾驶舱 | 驾驶舱 KPI 更新反映最新数据 | P0 | :construction: |

### 12.2 数据一致性测试

| 用例编号 | 用例名称 | 涉及模块 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-INT-005 | 消耗数据多模块一致 | A1, A2, C3, D1 | 1. 记录 C3 总消耗<br>2. 验证 A1, A2, D1 消耗 | 各模块消耗数据一致 | P0 | :construction: |
| TC-INT-006 | 充值数据 ledger 一致 | B1, A2 | 1. 完成充值流程<br>2. 验证 ledger_entries<br>3. 验证 A2 资金总览 | ledger 记录正确，A2 数据与 ledger 一致 | P0 | :construction: |

### 12.3 权限边界测试

| 用例编号 | 用例名称 | 涉及模块 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|---------|--------|------|
| TC-INT-007 | 跨项目数据隔离 | C1, B2, A3 | 1. 以 project_owner 登录<br>2. 访问各模块 | 只能看到自己项目数据，无法访问其他项目 | P0 | :construction: |
| TC-INT-008 | 角色权限全局一致 | 所有模块 | 1. 以 pitcher 登录<br>2. 遍历所有模块 | 所有模块权限控制一致，无越权访问 | P0 | :construction: |

---

## 13. UI 通用测试

### 13.1 响应式布局

| 用例编号 | 用例名称 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|--------|------|
| TC-UI-001 | 桌面端布局 (1440px) | 1. 设置视窗 1440×900<br>2. 访问各模块 | 侧边栏+主内容区正常显示，表格不横向滚动 | P2 | :construction: |
| TC-UI-002 | 平板端布局 (1024px) | 1. 设置视窗 1024×768<br>2. 访问各模块 | 布局自适应，侧边栏可收起 | P2 | :construction: |
| TC-UI-003 | 移动端布局 (375px) | 1. 设置视窗 375×667<br>2. 访问各模块 | 移动端布局适配，侧边栏隐藏为汉堡菜单 | P3 | :construction: |

### 13.2 主题切换

| 用例编号 | 用例名称 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|--------|------|
| TC-UI-004 | 暗色模式切换 | 1. 点击主题切换按钮<br>2. 验证所有组件 | 所有组件正确显示暗色主题，文字可读 | P3 | :construction: |
| TC-UI-005 | 主题持久化 | 1. 切换暗色模式<br>2. 刷新页面 | 主题设置保持 | P3 | :construction: |

### 13.3 表格通用功能

| 用例编号 | 用例名称 | 测试步骤 | 预期结果 | 优先级 | 状态 |
|---------|---------|---------|---------|--------|------|
| TC-UI-006 | 表格列排序 | 1. 点击可排序列表头 | 按该列升序/降序排列 | P2 | :construction: |
| TC-UI-007 | 表格分页 | 1. 翻页<br>2. 切换每页条数 | 分页正确，条数切换后数据刷新 | P2 | :construction: |
| TC-UI-008 | 表格空状态 | 1. 筛选无结果 | 显示"暂无数据"提示 | P2 | :construction: |

---

## 附录

### A. 测试环境要求

| 环境 | 说明 |
|------|------|
| 开发环境 | localhost:3000 (前端) + localhost:8000 (后端) |
| 测试数据库 | Supabase 测试实例 |
| 测试账号 | 每个角色至少 1 个测试账号 |

### B. 测试数据准备

| 数据类型 | 要求 |
|----------|------|
| 项目 | 至少 5 个项目，各状态至少 1 个 |
| 日报 | 至少 100 条，覆盖各状态 |
| 充值 | 至少 20 条，覆盖各状态 |
| 用户 | 每角色至少 2 个账号 |

### C. 测试用例统计 (v2.0)

| 模块 | 功能 | 边界 | 权限 | 状态机 | 数据 | UI | 网络 | 合计 |
|------|------|------|------|--------|------|----|----- |------|
| A1 驾驶舱 | 9 | 6 | 6 | - | - | 3 | 2 | 26 |
| A2 资金总览 | 6 | 2 | 5 | - | 3 | - | - | 16 |
| A3 项目盈亏 | 9 | 5 | 3 | - | - | - | - | 17 |
| B1 充值审批 | 5 | - | 4 | 11 | - | - | - | 20 |
| B2 日报审核 | 7 | - | 5 | 11 | 3 | - | - | 26 |
| B3 周度简报 | 7 | 3 | 4 | - | - | - | - | 14 |
| C1 项目管理 | 8 | 4 | 5 | 8 | - | - | - | 25 |
| C2 投手管理 | 9 | - | 5 | - | - | - | - | 14 |
| C3 消耗明细 | 10 | - | 5 | - | 4 | - | - | 19 |
| D1 月度结算 | 6 | - | 6 | 7 | 5 | - | - | 24 |
| 跨模块集成 | 4 | - | 2 | - | 2 | - | - | 8 |
| UI 通用 | - | - | - | - | - | 8 | - | 8 |
| **合计** | **80** | **20** | **50** | **37** | **17** | **11** | **2** | **217** |

### D. 优先级分布 (v2.0)

| 优先级 | 用例数 | 占比 | 说明 |
|--------|--------|------|------|
| P0 (核心) | ~35 | 16% | 每次构建必测 |
| P1 (重要) | ~90 | 41% | 每日测试 |
| P2 (一般) | ~70 | 32% | 回归测试 |
| P3 (边缘) | ~22 | 10% | 发布前 |

### E. Smoke Test 子集 (~25 用例)

带有 **[SMOKE]** 标记的用例构成冒烟测试子集，约 25 个核心用例，覆盖：
- 各模块核心功能入口
- 关键计算公式验证
- 主要权限验证
- 状态机终态验证

### F. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2025-12-23 | 修复缺陷：添加 A2 权限测试、B1/B2 非法状态转换测试、完善状态机覆盖、添加跨模块集成测试、UI 通用测试、网络异常测试、优化 P0 比例、添加 Smoke Test 标记 |
| v1.0 | 2025-12-23 | 初始版本，覆盖 10 个模块 |

---

**维护者**: AI 广告代投系统开发团队
**关联文档**: docs/10.module-specs/
