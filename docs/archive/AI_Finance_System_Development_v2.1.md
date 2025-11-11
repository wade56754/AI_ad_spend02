# AI 财务与投手管理系统项目开发文档 v2.1（优化版）

> 本文基于 v1.0 版本开发文档的缺陷审查结果进行优化，旨在让团队成员（产品、前端、后端、财务、户管、运营）对业务逻辑、接口约束、数据流和权限规则达成一致。

---

## 一、项目概述

### 1. 项目名称
AI 财务与投手管理系统（AI Finance System）

### 2. 项目目标
构建广告代投业务内部管理平台，实现：
- 账户、项目、渠道、投手、财务全链条数据闭环；
- 自动化日报、对账、充值审批；
- 账户生命周期追踪与渠道质量分析。

### 3. 技术栈
| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Next.js 14 + TypeScript + Tailwind CSS | SSR + 组件化 |
| 后端 | FastAPI + SQLAlchemy + Supabase (PostgreSQL) | 支持 RLS + JWT |
| 文件服务 | Supabase Storage | 财务导入文件存储 |
| 部署 | 宝塔 + Nginx + PM2 | 分层部署 |
| 鉴权 | Supabase Auth + JWT | 角色分级访问 |
| 定时任务 | APScheduler / Supabase Edge Function | 自动状态更新 |

---

## 二、架构与模块

### 1. 系统架构
```
前端 (Next.js)
   ↓ REST API
FastAPI (业务逻辑层)
   ↓ ORM
PostgreSQL (Supabase)
```

### 2. 模块关系
```
项目(Project)
 ├─ 渠道(Channel)
 │   └─ 广告账户(AdAccount)
 │        └─ 投手日报(AdSpendDaily)
 │
 └─ 财务模块(Finance)
      ├─ 充值申请(Topup)
      ├─ 财务流水(Ledger)
      └─ 对账(Reconciliation)
```

---

## 三、数据模型

### 1. 项目与渠道逻辑约束
- **每个广告账户必须绑定一个项目和一个渠道**。
- 项目删除后，关联账户自动归档。
- 渠道停用时，其下账户禁止充值。

### 2. 状态机设计

#### 账户状态（ad_account_status）
| 当前状态 | 允许转向 | 自动触发条件 |
|-----------|-----------|---------------|
| new | testing, archived | 创建后超过3天未使用 → archived |
| testing | active, suspended, dead | 连续3天有消耗 → active |
| active | suspended, dead | 7天无消耗 → suspended |
| suspended | active, dead | 户管手动恢复 |
| dead | archived | 渠道反馈封禁 |
| archived | - | 不可再编辑 |

#### 充值状态（topup_status）
| 状态 | 说明 | 允许操作人 |
|------|------|-------------|
| pending | 投手发起 | 投手 |
| approved | 户管审核 | 户管 |
| paid | 财务付款 | 财务 |
| done | 到账确认 | 户管 |
| rejected | 驳回 | 户管/财务 |

---

## 四、数据库结构（关键表）

### ad_accounts
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| channel_id | UUID | 渠道ID |
| project_id | UUID | 项目ID |
| name | TEXT | 广告账户名 |
| status | ENUM | 生命周期状态 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| dead_reason | TEXT | 死户原因 |

### ad_spend_daily
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| ad_account_id | UUID | 账户 |
| user_id | UUID | 投手 |
| date | DATE | 日期 |
| spend | DECIMAL | 消耗金额 |
| leads_count | INT | 引流数 |
| cost_per_lead | DECIMAL | 自动计算 |
| anomaly_flag | BOOL | 异常标记 |
| anomaly_reason | TEXT | 异常原因（波动、无进粉等） |

### reconciliation
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| ledger_id | UUID | 财务流水ID |
| ad_spend_id | UUID | 日报ID |
| match_score | FLOAT | 匹配分（0~1） |
| matched_by | TEXT | auto/manual |
| remark | TEXT | 备注 |

---

## 五、自动化逻辑

| 功能 | 触发方式 | 说明 |
|------|------------|------|
| 账户状态更新 | 定时任务 | 检查7天无消耗自动转suspended |
| 对账匹配 | 定时任务 | 金额差≤5%、日期差≤1天自动匹配 |
| 异常检测 | 提交日报时 | 金额波动>30%或进粉为0标红 |
| 渠道死户率计算 | 每月1日 | 更新报表缓存 |

---

## 六、API 规范

统一响应格式：
```json
{
  "data": {...},
  "error": null,
  "meta": { "timestamp": "2025-11-08T12:00:00Z" }
}
```

### 核心接口

#### 1. 提交日报  
`POST /api/adspend/report`
```json
{
  "ad_account_id": "uuid",
  "date": "2025-11-08",
  "spend": 500,
  "leads_count": 25,
  "note": "新素材测试"
}
```

#### 2. 自动对账  
`POST /api/reconciliation/auto`
- 匹配条件：金额差≤5%，日期差≤1天。  
- 失败项标记为 `manual_review`，供财务审核。

#### 3. 充值审批流
- `/api/topup/approve` — 户管审核  
- `/api/topup/pay` — 财务执行  
- `/api/topup/confirm` — 户管确认到账  
- 每次变更写入 `logs`。

---

## 七、权限与安全

| 模块 | 投手 | 户管 | 财务 | 管理层 | 管理员 |
|------|------|------|------|--------|--------|
| 日报 | 仅本人 | 全部 | 只读 | 汇总 | 全权限 |
| 充值 | 发起 | 审批 | 执行 | 只读 | 全权限 |
| 账户 | 只读 | 编辑 | 只读 | 汇总 | 全权限 |
| 对账 | 无 | 无 | 审核 | 汇总 | 全权限 |
| 渠道 | 无 | 编辑 | 无 | 汇总 | 全权限 |

- **RLS 规则**：所有数据访问都以 `user_id` + 角色判定。  
- **操作日志表 logs**：记录 `actor_id, action, target_id, before, after, ip`。

---

## 八、导入与异常处理

### 1. 财务导入模板
| 字段 | 示例值 | 说明 |
|------|----------|------|
| 日期 | 2025-11-08 | 日期 |
| 项目名 | 投资A | 收入归属 |
| 渠道 | XX代理 | 来源渠道 |
| 金额 | 5000 | 支出或充值额 |
| 币种 | USD | 币种统一 |

错误记录存入 `import_jobs`：  
`id, type, status, error_log, created_by`。

### 2. 错误码规范
| 代码 | 含义 |
|------|------|
| 4001 | 权限不足 |
| 4002 | 状态不允许操作 |
| 4003 | 对账冲突 |
| 4004 | 导入格式错误 |
| 5000 | 系统异常 |

---

## 九、分析报表与数据口径

| 报表类型 | 指标 | 数据来源 |
|-----------|--------|----------|
| 投手绩效 | 投放量、单粉成本、异常天数 | 日报表 |
| 项目盈利 | 收入、支出、利润 | 对账结果 |
| 渠道质量 | 死户率、平均寿命、服务费 | 账户与充值表 |

> 数据以对账完成后为准，日报仅用于趋势展示。

---

## 十、部署方案

### 环境变量
```
SUPABASE_URL=...
SUPABASE_KEY=...
JWT_SECRET=...
ENV=production
```

### 部署步骤
1. 安装依赖并构建前端：`npm run build && npm run start`
2. 启动后端：`uvicorn main:app --host 0.0.0.0 --port 8000`
3. Nginx 反向代理：`/api → localhost:8000`
4. 启用 HTTPS、日志与监控。

---

## 十一、后续规划
- KPI 模块自动生成。
- 报警系统（Webhook + Telegram）。
- 渠道健康度分析。
- 多币种支持与汇率同步。
- 前端移动端适配。

---

**版本号**：v2.1  
**日期**：2025-11-08  
**作者**：产品负责人 / 架构师  
