# 日报管理API使用指南

> **模块名称**: 日报管理 (Daily Report)
> **API版本**: v1.0
> **最后更新**: 2025-11-12

---

## 📋 概述

日报管理模块是AI广告代投系统的核心功能，支持投手提交每日广告投放数据，数据员审核确认，以及财务对账等功能。

### 核心功能
- 📝 日报创建和管理
- ✅ 数据审核流程
- 📊 数据统计和分析
- 📥 批量导入/导出
- 📈 实时数据监控
- 🔍 操作审计日志

---

## 🚀 快速开始

### 1. 认证授权

所有API请求都需要在请求头中包含JWT token：

```bash
Authorization: Bearer YOUR_JWT_TOKEN
```

### 2. 基础URL

```
https://your-domain.com/api/v1/daily-reports
```

---

## 📚 API端点列表

### 基础CRUD操作

| 方法 | 端点 | 描述 | 权限要求 |
|------|------|------|----------|
| GET | `/api/v1/daily-reports` | 获取日报列表 | 所有角色 |
| POST | `/api/v1/daily-reports` | 创建日报 | media_buyer, admin, data_operator |
| GET | `/api/v1/daily-reports/{id}` | 获取日报详情 | 相关角色 |
| PUT | `/api/v1/daily-reports/{id}` | 更新日报 | creator, admin |
| DELETE | `/api/v1/daily-reports/{id}` | 删除日报 | admin |

### 审核管理

| 方法 | 端点 | 描述 | 权限要求 |
|------|------|------|----------|
| POST | `/api/v1/daily-reports/{id}/approve` | 审核通过 | data_operator, admin |
| POST | `/api/v1/daily-reports/{id}/reject` | 驳回报日 | data_operator, admin |
| GET | `/api/v1/daily-reports/{id}/audit-logs` | 查看审核日志 | 相关角色 |

### 数据处理

| 方法 | 端点 | 描述 | 权限要求 |
|------|------|------|----------|
| POST | `/api/v1/daily-reports/batch-import` | 批量导入JSON | data_operator, admin |
| POST | `/api/v1/daily-reports/import-file` | 文件导入Excel | data_operator, admin |
| GET | `/api/v1/daily-reports/export` | 导出Excel | finance, admin, data_operator |
| GET | `/api/v1/daily-reports/statistics` | 获取统计数据 | data_operator, admin, finance |

---

## 💡 使用示例

### 1. 创建日报

```bash
curl -X POST "https://your-domain.com/api/v1/daily-reports" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "report_date": "2024-01-15",
    "ad_account_id": 1,
    "campaign_name": "春季促销活动",
    "ad_group_name": "年轻用户群体",
    "ad_creative_name": "创意视频001",
    "impressions": 10000,
    "clicks": 500,
    "spend": 100.00,
    "conversions": 10,
    "new_follows": 20,
    "cpa": 10.00,
    "roas": 5.00,
    "notes": "数据表现良好"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 123,
    "report_date": "2024-01-15",
    "ad_account_id": 1,
    "ad_account_name": "Facebook账户001",
    "status": "pending",
    "impressions": 10000,
    "clicks": 500,
    "spend": "100.00",
    "ctr": 5.0,
    "cpc": 0.20,
    "conversion_rate": 2.0,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "message": "日报创建成功",
  "code": "SUCCESS",
  "request_id": "uuid-string",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2. 获取日报列表

```bash
curl -X GET "https://your-domain.com/api/v1/daily-reports?page=1&page_size=20&status=pending" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 123,
        "report_date": "2024-01-15",
        "status": "pending",
        "campaign_name": "春季促销活动",
        "created_by_name": "张三"
      }
    ],
    "meta": {
      "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 100,
        "total_pages": 5
      }
    }
  },
  "message": "操作成功",
  "code": "SUCCESS"
}
```

### 3. 审核日报

```bash
curl -X POST "https://your-domain.com/api/v1/daily-reports/123/approve" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "audit_notes": "数据准确，审核通过"
  }'
```

### 4. 批量导入

```bash
curl -X POST "https://your-domain.com/api/v1/daily-reports/batch-import" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "reports": [
      {
        "report_date": "2024-01-15",
        "ad_account_id": 1,
        "impressions": 10000,
        "clicks": 500,
        "spend": 100.00
      }
    ],
    "skip_errors": false
  }'
```

### 5. 导出日报

```bash
curl -X GET "https://your-domain.com/api/v1/daily-reports/export?report_date_start=2024-01-01&report_date_end=2024-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o daily_reports.xlsx
```

---

## 🔍 查询参数

### 通用查询参数

| 参数 | 类型 | 必填 | 描述 | 示例 |
|------|------|------|------|------|
| page | integer | 否 | 页码，默认1 | 1 |
| page_size | integer | 否 | 每页数量，默认20，最大100 | 50 |
| report_date_start | string | 否 | 开始日期 (YYYY-MM-DD) | 2024-01-01 |
| report_date_end | string | 否 | 结束日期 (YYYY-MM-DD) | 2024-01-31 |
| ad_account_id | integer | 否 | 广告账户ID | 123 |
| status | string | 否 | 审核状态 | pending/approved/rejected |
| media_buyer_id | integer | 否 | 投手ID | 456 |
| project_id | integer | 否 | 项目ID | 789 |

---

## 📊 响应格式

### 成功响应

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功",
  "code": "SUCCESS",
  "request_id": "uuid-string",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 分页响应

```json
{
  "success": true,
  "data": {
    "items": [ ... ],
    "meta": {
      "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 100,
        "total_pages": 5
      }
    }
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "BIZ_001",
    "message": "日报已存在",
    "details": { ... }
  },
  "request_id": "uuid-string",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 🚨 错误码说明

### 系统错误 (SYS_xxx)

| 错误码 | HTTP状态码 | 描述 |
|--------|------------|------|
| SYS_001 | 400 | 请求参数错误 |
| SYS_002 | 401 | 未授权访问 |
| SYS_003 | 403 | 权限不足 |
| SYS_004 | 404 | 资源不存在 |
| SYS_005 | 409 | 资源冲突 |
| SYS_500 | 500 | 服务器内部错误 |

### 业务错误 (BIZ_xxx)

| 错误码 | HTTP状态码 | 描述 |
|--------|------------|------|
| BIZ_001 | 409 | 日报已存在 |
| BIZ_002 | 403 | 日报状态不允许修改 |
| BIZ_003 | 400 | 日期范围错误 |
| BIZ_004 | 422 | 数据验证失败 |
| BIZ_005 | 403 | 超出导入限制 |
| BIZ_006 | 400 | 文件格式错误 |
| BIZ_007 | 403 | 无权查看该日报 |

---

## 🎯 最佳实践

### 1. 数据验证

- 在提交前验证数据格式
- 确保点击数 ≤ 展示数
- 确保转化数 ≤ 点击数

### 2. 批量操作

- 批量导入时建议每批不超过100条
- 使用 `skip_errors=true` 避免单条错误影响整批
- 导入后检查错误列表

### 3. 性能优化

- 使用日期范围查询减少数据量
- 合理使用分页，避免一次查询过多数据
- 导出数据时添加日期限制

### 4. 错误处理

- 始终检查响应中的 `success` 字段
- 根据错误码进行相应的错误处理
- 记录 `request_id` 用于问题追踪

---

## 📝 SDK示例

### Python SDK示例

```python
import requests
from datetime import date

class DailyReportAPI:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def create_report(self, report_data: dict):
        """创建日报"""
        response = requests.post(
            f"{self.base_url}/api/v1/daily-reports",
            json=report_data,
            headers=self.headers
        )
        return response.json()

    def list_reports(self, **params):
        """获取日报列表"""
        response = requests.get(
            f"{self.base_url}/api/v1/daily-reports",
            params=params,
            headers=self.headers
        )
        return response.json()

    def approve_report(self, report_id: int, notes: str):
        """审核通过日报"""
        response = requests.post(
            f"{self.base_url}/api/v1/daily-reports/{report_id}/approve",
            json={"audit_notes": notes},
            headers=self.headers
        )
        return response.json()

# 使用示例
api = DailyReportAPI("https://your-domain.com", "your-token")

# 创建日报
report = api.create_report({
    "report_date": "2024-01-15",
    "ad_account_id": 1,
    "impressions": 10000,
    "clicks": 500,
    "spend": 100.00
})

print(f"日报ID: {report['data']['id']}")
```

---

## 🔗 相关文档

- [API开发指南](./BACKEND_API_GUIDE.md)
- [错误码参考](./ERROR_CODES.md)
- [权限管理文档](./PERMISSION_GUIDE.md)
- [数据库设计文档](./DATABASE_SCHEMA.md)

---

## 📞 技术支持

- **文档维护**: 开发团队
- **技术问题**: 提交GitHub Issue
- **紧急支持**: 联系运维团队

**更新日志**:
- v1.0 (2025-11-12): 初始版本发布
- 支持完整的CRUD操作
- 支持批量导入导出
- 支持审核流程