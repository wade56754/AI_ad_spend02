# 测试指南（Testing Guide）

> 测试范围与要求以 SoT 为准：`docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md`

## 重点覆盖
- Envelope 响应格式（success/data/code/message/request_id/timestamp）
- 鉴权与 RBAC（受保护路由必须依赖 `get_current_user`）
- 金额与时间（Decimal 两位、ROUND_HALF_UP；UTC）
- 分页（`?page` 1-based、`?size` ≤100）

## 建议
- 后端：pytest 单元/集成
- 前端：Vitest + 组件测试；必要时端到端





