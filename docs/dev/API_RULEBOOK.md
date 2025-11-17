# API 设计与使用规则（API Rulebook）

> 定义性内容以 SoT 为准：`docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md`

## 统一约束
- 路由前缀：`/api/v1`
- 认证：JWT（Supabase Auth）
- 响应：Envelope（禁止 `{detail}`）
- 分页：`?page`（1-based）与 `?size`（≤100）
- 金额/时间：Decimal 两位（HALF_UP）、UTC

## 前端调用
- 统一 `lib/api.ts::apiFetch`
- 禁止组件内直接 `fetch()` 命中业务数据





