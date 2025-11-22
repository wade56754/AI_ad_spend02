# API 使用指引 · Daily Reports（日报管理）

> **唯一真相源**: [`docs/core/API_SOT.md`](../../core/API_SOT.md)
>
> 本文档仅提供模块特定说明，所有通用规范、开发流程、响应格式等请参考 API_SOT.md

## 快速链接

- **完整API规范**: [`docs/core/API_SOT.md`](../../core/API_SOT.md)
- **数据表结构**: [`docs/core/DATA_SCHEMA.md`](../../core/DATA_SCHEMA.md) - 第 3.3 节
- **状态机定义**: [`docs/core/STATE_MACHINE.md`](../../core/STATE_MACHINE.md) - 第 3 章

## 端点概览

参见 [`API_SOT.md 第 5.3 节`](../../core/API_SOT.md#53-daily-reports日报管理)

**Base URL**: `/api/v1/daily-reports`

**状态机**: `draft` → `submitted` → `approved`/`rejected`

## 调用示例

### 获取日报列表

```http
GET /api/v1/daily-reports?page=1&page_size=20
Authorization: Bearer <token>
```

### 提交日报

```http
POST /api/v1/daily-reports
Authorization: Bearer <token>
Content-Type: application/json

{
  "project_id": 1,
  "ad_account_id": 1,
  "report_date": "2025-11-22",
  "spend": "1500.00",
  "impressions": 50000,
  "clicks": 1200,
  "conversions": 45
}
```

### 审核日报

```http
POST /api/v1/daily-reports/{report_id}/approve
Authorization: Bearer <token>
Content-Type: application/json

{
  "approved": true,
  "comment": "数据准确，审核通过"
}
```

### 前端调用（TypeScript）

```typescript
import { apiFetch } from '@/lib/api';

// 获取日报列表
const reports = await apiFetch<DailyReportListResponse>(
  '/api/v1/daily-reports?page=1&page_size=20'
);

// 提交日报
const newReport = await apiFetch<DailyReportResponse>(
  '/api/v1/daily-reports',
  {
    method: 'POST',
    body: JSON.stringify({
      project_id: 1,
      ad_account_id: 1,
      report_date: "2025-11-22",
      spend: "1500.00",
      impressions: 50000,
      clicks: 1200,
      conversions: 45
    })
  }
);
```





