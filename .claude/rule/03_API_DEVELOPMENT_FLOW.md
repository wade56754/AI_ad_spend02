# API 开发流程（必须遵循）

> **唯一真相源**: [`docs/core/API_SOT.md`](../../docs/core/API_SOT.md)
>
> ⚙️ 该文档为 API 全生命周期规范的快速引用，完整内容请参考 API_SOT.md

## 核心要求摘要

### 开发流程（强制顺序）
1. Schema → Service → Router → Test → Exception Handler
2. 所有字段必须来自 `DATA_SCHEMA.md`
3. 状态转换必须符合 `STATE_MACHINE.md`
4. 权限检查必须在 Service 层实现

### 响应格式（强制）
- ✅ 使用 `success_response` / `error_response`（Envelope 格式）
- ❌ 禁止返回 FastAPI 默认 `{detail: "..."}` 响应

### 前端调用（强制）
- ✅ 使用 `lib/api.ts::apiFetch`
- ❌ 禁止直接使用 `fetch` / `axios`

### 数据类型（强制）
- 金额：`Decimal`（两位小数）
- 时间：`datetime`（UTC）
- 角色：仅限 5 个标准角色

## 快速链接

- **完整 API 规范**: [`docs/core/API_SOT.md`](../../docs/core/API_SOT.md)
- **开发流程详解**: [`API_SOT.md 第 3 章`](../../docs/core/API_SOT.md#3-api-开发流程)
- **响应格式**: [`API_SOT.md 第 4 章`](../../docs/core/API_SOT.md#4-响应格式规范)
- **AI 工具指导**: [`API_SOT.md 第 9 章`](../../docs/core/API_SOT.md#9-ai-工具开发指导)
- **检查清单**: [`API_SOT.md 第 10 章`](../../docs/core/API_SOT.md#10-检查清单)

## 常见违规

| 违规 | 正确做法 |
|------|---------|
| 字段名自创 | 使用 DATA_SCHEMA.md 定义 |
| 使用 `manager` 角色 | 使用 `account_manager` |
| 状态自创 | 参考 STATE_MACHINE.md |
| `return {"data": ...}` | `return success_response(...)` |
| `amount: float` | `amount: Decimal` |
