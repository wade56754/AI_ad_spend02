# 前端开发环境与运行指南（Frontend Setup）

> 定义性技术规范以 SoT 为准：
> - `docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md`

## 栈与运行
- 框架：Next.js 16（App Router）
- 语言：TypeScript
- 样式：Tailwind CSS
- UI：shadcn/ui + Radix UI

## 数据访问约束
- 统一使用 `lib/api.ts::apiFetch` 调用 BFF（/api/v1），自动附加 `Authorization: Bearer <token>`
- 禁止组件内直接 `fetch()` 命中业务数据与直连 DB/Supabase/外部服务
- `NEXT_PUBLIC_API_URL` 为 Origin（不含 `/api`）





