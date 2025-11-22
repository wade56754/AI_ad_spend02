# API 使用指引 · Topup Requests（充值申请）

> **唯一真相源**: [`docs/core/API_SOT.md`](../../core/API_SOT.md)
>
> 本文档仅提供模块特定说明，所有通用规范、开发流程、响应格式等请参考 API_SOT.md

## 快速链接

- **完整API规范**: [`docs/core/API_SOT.md`](../../core/API_SOT.md)
- **数据表结构**: [`docs/core/DATA_SCHEMA.md`](../../core/DATA_SCHEMA.md) - 第 3.4 节
- **状态机定义**: [`docs/core/STATE_MACHINE.md`](../../core/STATE_MACHINE.md) - 第 2 章

## 端点概览

参见 [`API_SOT.md 第 5.2 节`](../../core/API_SOT.md#52-topup-requests充值申请)

**Base URL**: `/api/v1/topup-requests`

**状态机**: `draft` → `pending` → `approved`/`rejected`/`cancelled`

**关键业务规则**:
- 最小充值金额: ¥100
- 单笔上限: ¥1,000,000
- 审批权限: 仅 `finance` 角色

## 调用示例

### 创建充值申请

```http
POST /api/v1/topup-requests
Authorization: Bearer <token>
Content-Type: application/json

{
  "project_id": 1,
  "ad_account_id": 1,
  "requested_amount": "10000.00",
  "reason": "Facebook广告账户余额不足，需要补充推广预算"
}
```

### 状态转换

```http
POST /api/v1/topup-requests/{request_id}/transition
Authorization: Bearer <token>
Content-Type: application/json

{
  "to_status": "approved",
  "actual_amount": "9500.00"
}
```

### 前端调用（TypeScript）

```typescript
import { apiFetch } from '@/lib/api';

// 创建充值申请
const result = await apiFetch<TopupRequestResponse>('/api/v1/topup-requests', {
  method: 'POST',
  body: JSON.stringify({
    project_id: 1,
    ad_account_id: 1,
    requested_amount: "10000.00",
    reason: "Facebook广告账户余额不足，需要补充推广预算"
  })
});

// 状态转换
const updated = await apiFetch<TopupRequestResponse>(
  `/api/v1/topup-requests/${requestId}/transition`,
  {
    method: 'POST',
    body: JSON.stringify({
      to_status: 'approved',
      actual_amount: "9500.00"
    })
  }
);
```





