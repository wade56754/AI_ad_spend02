# API文档

## 📌 概述

本目录包含AI广告代投系统的所有API接口文档，包括认证授权、接口定义和调用示例。

## 📂 文档结构

```
api/
├── README.md                          # API文档索引（本文件）
├── authentication.md                  # 认证授权机制
├── error-codes.md                    # 错误码定义
├── endpoints/                        # 接口定义
│   ├── projects.md                  # 项目管理接口
│   ├── accounts.md                  # 广告账户接口
│   ├── reports.md                   # 日报管理接口
│   ├── topups.md                    # 充值申请接口
│   └── finance.md                   # 财务对账接口
├── reconciliation_management_api.md  # 对账管理 API 完整文档
└── examples/                        # 调用示例
    ├── python.md                    # Python示例
    ├── javascript.md                # JavaScript示例
    └── postman.json                 # Postman集合
```

## 📝 已实现的API模块

- **[reconciliation_management_api.md](./reconciliation_management_api.md)** - 对账管理 API 完整文档
  - 对账批次管理
  - 差异审核和调整
  - 统计报告和数据导出

## 🔑 认证授权

所有API接口都需要JWT Token认证。详见 [认证授权文档](./authentication.md)

### 获取Token
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

### 使用Token
```http
GET /api/v1/projects
Authorization: Bearer <your-jwt-token>
```

## 📋 接口列表

### 项目管理
- `GET /api/v1/projects` - 获取项目列表
- `POST /api/v1/projects` - 创建新项目
- `GET /api/v1/projects/{id}` - 获取项目详情
- `PUT /api/v1/projects/{id}` - 更新项目信息
- `DELETE /api/v1/projects/{id}` - 删除项目

### 广告账户
- `GET /api/v1/accounts` - 获取账户列表
- `POST /api/v1/accounts` - 创建新账户
- `GET /api/v1/accounts/{id}` - 获取账户详情
- `PUT /api/v1/accounts/{id}` - 更新账户状态
- `POST /api/v1/accounts/{id}/assign` - 分配账户

### 日报管理
- `GET /api/v1/reports` - 获取日报列表
- `POST /api/v1/reports` - 提交新日报
- `GET /api/v1/reports/{id}` - 获取日报详情
- `PUT /api/v1/reports/{id}` - 更新日报
- `POST /api/v1/reports/{id}/approve` - 审批日报

### 充值申请
- `GET /api/v1/topups` - 获取充值列表
- `POST /api/v1/topups` - 创建充值申请
- `GET /api/v1/topups/{id}` - 获取充值详情
- `PUT /api/v1/topups/{id}/approve` - 审批充值
- `PUT /api/v1/topups/{id}/reject` - 拒绝充值

## 📊 响应格式

所有 API 遵循统一的响应格式和权限控制标准，详见 [API开发流程](../core/API_DEVELOPMENT_FLOW.md)

### 成功响应
```json
{
  "success": true,
  "data": {
    // 返回数据
  },
  "message": "操作成功",
  "code": "SUCCESS",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-11-18T10:30:00Z"
}
```

### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数验证失败",
    "details": {
      "field": "email",
      "reason": "格式不正确"
    }
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-11-18T10:30:00Z"
}
```

## 🔄 分页规范

支持分页的接口都使用统一的分页参数：

```http
GET /api/v1/projects?page=1&size=20&sort=created_at:desc
```

分页响应格式：
```json
{
  "success": true,
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "size": 20,
    "pages": 5
  }
}
```

## 🚦 限流策略

- 认证用户: 1000 请求/小时
- 未认证用户: 100 请求/小时
- 单个IP: 2000 请求/小时

超出限制会返回 `429 Too Many Requests`

## 📝 版本管理

当前API版本: **v1**

API版本通过URL路径指定：
- v1: `/api/v1/...`
- v2: `/api/v2/...` (计划中)

## 📚 相关文档

- [API开发流程](../core/API_DEVELOPMENT_FLOW.md) - API 开发规范和流程
- [项目开发规则](../../.claude/PROJECT_RULES.md) - 开发强制规范
- [开发文档](../development/README.md) - 各模块的详细设计文档

## 🔗 相关链接

- [Swagger文档](http://localhost:8000/docs)
- [ReDoc文档](http://localhost:8000/redoc)
- [Postman集合](./examples/postman.json)

---

*最后更新: 2024-11-18*
