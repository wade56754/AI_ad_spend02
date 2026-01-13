# 项目简介

> AI 每次对话必读此文件

## 项目名称

AI 广告代投管理系统

## 技术栈

- 后端: FastAPI + SQLAlchemy 2.x + Pydantic v2
- 前端: Next.js 16 + TanStack Query v5 + shadcn/ui
- 数据库: PostgreSQL (Supabase)
- 认证: Supabase Auth

## 核心业务

- 广告账户管理 (AdAccount)
- 日报审核流程 (DailyReport) - 8 状态机
- 充值与对账 (Topup/Reconciliation)
- 财务账本 (Ledger)

## SoT 文档

- MASTER.md v4.8 - 架构宪法
- STATE_MACHINE.md v2.8 - 状态机定义
- DATA_SCHEMA.md v5.7 - 数据模型

## 关键约束

- 角色白名单: admin, finance, account_manager, media_buyer
- 日报状态: 8 状态机，禁止使用 draft/pending/approved
- 余额修改: 必须通过 ledger，禁止直接修改 balance
