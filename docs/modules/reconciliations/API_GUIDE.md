# API 使用指引 · Reconciliations

> 仅提供 BFF 调用示例，不重新定义结构；权威请见：
> - `docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md`
> - `docs/DATA_SCHEMA.md`

## 调用约束（引用 SoT）
- 路由：`/api/v1`（分页、错误码、Envelope 统一）
- 认证：`Authorization: Bearer <token>`，经 `lib/api.ts::apiFetch`

## 示例
```http
GET /api/v1/reconciliations?page=1&size=20
Authorization: Bearer <token>
```





