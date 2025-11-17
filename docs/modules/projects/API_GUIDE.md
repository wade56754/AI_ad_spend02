# API 使用指引 · Projects

> 本文仅提供通过 BFF（/api/v1）调用的示例与注意事项；任何定义性结构以 SoT 为准：
> - SoT-Implementation：`docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md`
> - SoT-Data：`docs/DATA_SCHEMA.md`

## 请求约束（引用 SoT）
- 统一响应 Envelope（禁止返回 `{detail}`）
- 统一分页参数：`?page`（1-based）、`?size`（≤100）
- 认证：`Authorization: Bearer <token>` 通过 `lib/api.ts::apiFetch` 发起

## 示例
```http
GET /api/v1/projects?page=1&size=20
Authorization: Bearer <token>
```





