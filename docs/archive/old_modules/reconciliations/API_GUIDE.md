# API 使用指引 · Reconciliations

> **唯一真相源**: [`docs/core/API_SOT.md`](../../core/API_SOT.md)
>
> 本文档仅提供模块特定说明，所有通用规范、开发流程、响应格式等请参考 API_SOT.md

## 快速链接

- **完整API规范**: [`docs/core/API_SOT.md`](../../core/API_SOT.md)
- **数据表结构**: [`docs/core/DATA_SCHEMA.md`](../../core/DATA_SCHEMA.md) - 第 3.5 节
- **状态机定义**: [`docs/core/STATE_MACHINE.md`](../../core/STATE_MACHINE.md) - 第 4 章

## 端点概览

参见 [`API_SOT.md 第 5.4 节`](../../core/API_SOT.md#54-reconciliations对账管理)

**Base URL**: `/api/v1/reconciliations`

**状态机**: `processing` → `completed` → `confirmed`/`disputed`

## 调用示例

```http
GET /api/v1/reconciliations?page=1&page_size=20
Authorization: Bearer <token>
```

```typescript
// 前端调用（使用 apiFetch）
import { apiFetch } from '@/lib/api';

const reconciliations = await apiFetch<ReconciliationListResponse>(
  '/api/v1/reconciliations?page=1&page_size=20'
);
```





