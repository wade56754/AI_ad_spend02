# API 开发流程（必须遵循）

⚙️ 该文档为 API 全生命周期规范，完整内容在：
docs/core/API_DEVELOPMENT_FLOW.md

要求摘要：
- 所有 API 需有 Schema → Service → Controller → Router
- 响应返回必须是 Envelope 格式
- 错误码必须来自用 error_codes.py（不硬编码）
- 前端调用必须使用 apiFetch

⚠️ 禁止：
- 直接使用 fetch / axios
- 返回 FastAPI 默认 {detail: "..."} 响应
