---
version: v0.1
status: deprecated
layer: dev-guide
owner: wade
last_reviewed: 2025-11-27
baseline: SoT Freeze v1.0, MASTER.md v3.4
replacement: FRONTEND_DEVELOPMENT_RULES.md v1.0 (partial)
deprecated_date: 2025-11-27
---

# 前端开发环境与运行指南（Frontend Setup）

> **⚠️ 本文档已废弃，等待完整前端开发指南**
>
> **部分替代**: [FRONTEND_DEVELOPMENT_RULES.md](FRONTEND_DEVELOPMENT_RULES.md) v1.0
> **规划中**: FRONTEND_DEV_GUIDE.md (预计 2026-Q1)
>
> 前端开发规范目前分散在多个文档中，计划整合为完整的前端开发指南。

## 栈与运行
- 框架：Next.js 16（App Router）
- 语言：TypeScript
- 样式：Tailwind CSS
- UI：shadcn/ui + Radix UI

## 数据访问约束
- 统一使用 `lib/api.ts::apiFetch` 调用 BFF（/api/v1），自动附加 `Authorization: Bearer <token>`
- 禁止组件内直接 `fetch()` 命中业务数据与直连 DB/Supabase/外部服务
- `NEXT_PUBLIC_API_URL` 为 Origin（不含 `/api`）





