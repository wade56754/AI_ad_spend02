---
version: v1.0
status: active
owner: AI 广告代投系统开发团队
last_updated: 2026-01-16
baseline: PRD v5.1
sot_binding: MASTER v4.9, STATE_MACHINE v2.9, DATA_SCHEMA v5.11, BUSINESS_RULES v5.2, API_SOT v9.7, AUTH_SPEC v2.2, ERROR_CODES v2.2
---

# 系统架构视图

> **目标**: 给出系统上下文、服务组件、数据流、部署/运行形态的统一视图，所有规则以 SoT 为准。

## 1. SoT 版本绑定

| SoT 文档 | 版本 | 关键约束 |
|---|---|---|
| MASTER.md | v4.9 | 系统宪法、角色定义、Phase 1/2 边界 |
| STATE_MACHINE.md | v2.9 | 日报 8 状态 + Phase 1 简化边界、充值 7 状态 |
| DATA_SCHEMA.md | v5.11 | 数据模型；账本规则唯一来源 §3.4.4 |
| BUSINESS_RULES.md | v5.2 | 业务规则与计算公式 |
| API_SOT.md | v9.7 | API 契约与端点 |
| AUTH_SPEC.md | v2.2 | Supabase Auth 授权与角色映射 |
| ERROR_CODES_SOT.md | v2.2 | 错误码注册表 |

## 2. 系统上下文 (System Context)

```
[老板/项目负责人/财务/投手/户管/管理员]
            |
         Web UI (Next.js)
            |
      BFF/API (FastAPI)
            |
   PostgreSQL (Supabase)
        /         \
[Supabase Auth]  [平台数据/结算输入]
```

说明:
- Web UI 仅通过 API 通信，禁止直连数据库。
- Supabase Auth 负责认证与用户身份，API 层做权限校验。
- 平台数据 (ad_spend_daily) 与结算数据 (conversions_final) 是成本/收入 SoT。

## 3. 服务组件 (Service Components)

```
Frontend (Next.js)
  - App Router + TanStack Query
  - apiFetch 访问后端 API

Backend (FastAPI)
  - routers/  : API 入口 (thin layer)
  - services/ : 业务逻辑与状态机
  - schemas/  : Pydantic v2 模式
  - models/   : SQLAlchemy 2.x ORM

Data Services
  - PostgreSQL (Supabase)
  - ledger_entries: 账本核心表 (DATA_SCHEMA.md §3.4.4)

Auth
  - Supabase Auth (JWT + RLS)
```

## 4. 核心数据流 (Data Flow)

### 4.1 日报与成本 SoT
```
投手日报 (daily_reports)
  -> 审核流转 (STATE_MACHINE) -> final_confirmed/final_locked
平台消耗 (ad_spend_daily)
  -> 成本 SoT (用于结算与利润计算)
结算确认 (conversions_final)
  -> 收入 SoT
```

### 4.2 充值与账本
```
投手/户管发起 topup_request
  -> finance 审批/标记付款
     -> ledger_entries 写入
        -> 余额派生 (禁止直接修改 balance)
```

### 4.3 对账
```
reconciliation_batch (draft)
  -> pending_review -> approved/needs_adjustment -> completed
     -> 差异记录 -> ledger_entries 调整
```

## 5. 部署/运行形态 (Deployment & Runtime)

### 5.1 本地开发
- 后端: `uvicorn main:app --reload --port 8000`
- 前端: `pnpm run dev` (端口 3000)
- 可选: `docker-compose.dev.yml` 提供 Postgres/Redis

### 5.2 生产部署 (以 runbook 为准)
- 后端: Docker 镜像发布，K8s/容器编排运行
- 前端: Vercel 或 Node + PM2 部署
- 认证: Supabase Auth (服务端校验 + 前端登录)

> 参考: `docs/runbooks/deploy.md` 与 `deploy/DEPLOY_GUIDE.md`
