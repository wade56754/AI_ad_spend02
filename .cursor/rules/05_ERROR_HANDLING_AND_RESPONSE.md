所有接口必须使用 Envelope 格式：
{
  data: ...,
  error: null
}

错误示例：
{
  "detail": "Unauthorized"
}
❌ 直接返回 detail 是禁止的，必须包裹在统一结构。
