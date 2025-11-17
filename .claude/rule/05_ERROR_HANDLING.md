# 错误处理与响应标准

📌 标准 API 返回结构：
{
  "data": null,
  "error": {
    "code": "AUTH_403",
    "message": "无权限"
  }
}

⚠️ 任何出现以下内容的输出均视为错误：
- {"detail": "xxx"}
- 没有统一错误包装
- 没有错误码