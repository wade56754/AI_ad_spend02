# Postman Environments

本目录存放 Postman 环境配置文件。

## 环境文件

| 文件名 | 描述 | 用途 |
|--------|------|------|
| local.json | 本地开发环境 | 本地测试 |
| staging.json | 预发布环境 | 集成测试 |
| production.json | 生产环境 | 冒烟测试 |

## 环境变量

必需的环境变量：

```json
{
  "base_url": "http://localhost:8000",
  "api_version": "v1",
  "admin_token": "{{admin_jwt_token}}",
  "test_project_id": "{{uuid}}"
}
```

## 安全说明

- 🔴 禁止提交真实的生产环境凭据
- ✅ 使用占位符或环境变量
- ✅ 在 CI 中通过 secrets 注入

## 基准文档

- AUTOMATION_TEST_SPEC_v1.4.md 第 6.3 节
