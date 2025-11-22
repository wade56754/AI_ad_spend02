# API 设计与使用规则（API Rulebook）

> **⚠️ 本文档已废弃，请使用新的唯一真相源**
>
> **唯一真相源**: [`docs/core/API_SOT.md`](../core/API_SOT.md)
>
> 本文档已被合并到 API_SOT.md 中，请参考该文档获取最新、最完整的API规范。

## 快速跳转

- **完整 API 规范**: [`docs/core/API_SOT.md`](../core/API_SOT.md)
- **统一约束**: [`API_SOT.md 第 2 章`](../core/API_SOT.md#2-统一规范)
- **响应格式**: [`API_SOT.md 第 4 章`](../core/API_SOT.md#4-响应格式规范)
- **前端调用**: [`API_SOT.md 第 6.3 节`](../core/API_SOT.md#63-前端调用规范)

---

## 统一约束（摘要）

- **路由前缀**: `/api/v1`
- **认证**: JWT（Supabase Auth）
- **响应**: Envelope（禁止 `{detail}`）
- **分页**: `?page`（1-based）与 `?page_size`（≤100）
- **金额/时间**: Decimal 两位（HALF_UP）、UTC

## 前端调用（摘要）

- ✅ 统一使用 `lib/api.ts::apiFetch`
- ❌ 禁止组件内直接 `fetch()` / `axios` 调用业务数据

**详细说明请参考**: [`docs/core/API_SOT.md`](../core/API_SOT.md)





