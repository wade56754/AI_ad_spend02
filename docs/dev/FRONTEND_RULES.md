# 前端强制规则（Frontend Rules）

> 约束性规则的唯一来源：`docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md`

## 必须遵守
- BFF 边界：所有业务读写仅通过 `/api/v1`，不得绕过服务层
- 统一响应：Envelope；前端只读 `success`/`data`/`code`/`message`
- 鉴权：JWT 放入 `Authorization` 头，由 `apiFetch` 统一处理
- 技术版本：Next.js 16；文档中任何 Next.js 13/15 的“现状”描述均无效
- 安全：CORS 使用白名单；不得使用 `*`（生产）





