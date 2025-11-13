# 充值管理API使用指南

> **模块名称**: 充值管理 (Top-up Management)
> **API版本**: v1.0
> **文档版本**: 1.0
> **更新日期**: 2025-11-12
> **开发人员**: Claude协作开发

---

## 📋 概述

充值管理API提供了完整的充值申请、审核、审批、打款和凭证管理功能，支持基于角色的权限控制，确保资金安全和流程透明。

### 核心特性
- ✅ **充值申请管理** - 创建、查询、更新充值申请
- ✅ **审核流程控制** - 数据审核、财务审批的完整流程
- ✅ **打款凭证管理** - 上传、管理支付凭证
- ✅ **统计分析报表** - 多维度的充值数据分析
- ✅ **权限精细控制** - 基于角色的操作权限
- ✅ **审计日志追踪** - 完整的操作记录和日志

---

## 🔑 认证与授权

所有API端点都需要在请求头中包含有效的JWT访问令牌：

```
Authorization: Bearer <access_token>
```

### 权限矩阵

| 角色 | 创建申请 | 数据审核 | 财务审批 | 打款 | 查看统计 | 导出数据 |
|------|----------|----------|----------|------|----------|----------|
| **admin** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **finance** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **data_operator** | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ |
| **account_manager** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **media_buyer** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 📚 API端点详情

### 1. 获取充值申请列表

获取充值申请列表，支持分页和多种过滤条件。

**请求**
```http
GET /api/v1/topups?page=1&page_size=20&status=pending&urgency=high&ad_account_id=1
```

**查询参数**
| 参数 | 类型 | 必填 | 描述 | 示例 |
|------|------|------|------|------|
| page | integer | 否 | 页码，从1开始 | 1 |
| page_size | integer | 否 | 每页数量，1-100 | 20 |
| status | string | 否 | 申请状态过滤 | pending |
| urgency | string | 否 | 紧急程度过滤 | high |
| ad_account_id | integer | 否 | 广告账户ID | 1 |
| project_id | integer | 否 | 项目ID | 2 |
| start_date | date | 否 | 开始日期 | 2025-01-01 |
| end_date | date | 否 | 结束日期 | 2025-12-31 |
| request_no | string | 否 | 申请单号模糊查询 | TOP2025 |

**响应**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "request_no": "TOP20251112143045001",
        "ad_account_id": 1,
        "ad_account_name": "Facebook广告账户",
        "project_id": 1,
        "project_name": "测试项目",
        "requested_amount": "1000.00",
        "actual_amount": "950.00",
        "currency": "USD",
        "urgency_level": "normal",
        "reason": "广告投放充值",
        "status": "finance_approve",
        "requested_by": 1,
        "requested_by_name": "张投手",
        "created_at": "2025-11-12T10:00:00Z",
        "updated_at": "2025-11-12T11:00:00Z"
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
  "message": "获取充值申请列表成功"
}
```

### 2. 创建充值申请

创建新的充值申请，媒体买家和账户管理员有权限。

**请求**
```http
POST /api/v1/topups
```

**请求体**
```json
{
  "ad_account_id": 1,
  "requested_amount": "5000.00",
  "currency": "USD",
  "urgency_level": "high",
  "reason": "账户余额不足，需要紧急充值",
  "notes": "本周有重要推广活动",
  "expected_date": "2025-11-15"
}
```

**字段说明**
| 字段 | 类型 | 必填 | 验证规则 | 描述 |
|------|------|------|----------|------|
| ad_account_id | integer | ✅ | > 0 | 广告账户ID |
| requested_amount | decimal | ✅ | 0.01-100000 | 申请金额 |
| currency | string | ❌ | 3位货币代码 | 货币类型 |
| urgency_level | enum | ❌ | low/normal/high/urgent | 紧急程度 |
| reason | string | ✅ | 1-1000字符 | 充值原因 |
| notes | string | ❌ | 最大1000字符 | 补充说明 |
| expected_date | date | ❌ | ≥明天 | 期望到账日期 |

**成功响应 (201)**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "request_no": "TOP20251112143045002",
    "ad_account_id": 1,
    "requested_amount": "5000.00",
    "status": "pending",
    "created_at": "2025-11-12T10:00:00Z"
  },
  "message": "充值申请创建成功"
}
```

### 3. 获取充值申请详情

获取指定充值申请的详细信息。

**请求**
```http
GET /api/v1/topups/{request_id}
```

**路径参数**
| 参数 | 类型 | 描述 |
|------|------|------|
| request_id | integer | 充值申请ID |

### 4. 数据员审核

数据员审核充值申请的合理性。

**请求**
```http
PUT /api/v1/topups/{request_id}/review
```

**请求体**
```json
{
  "action": "approve",
  "notes": "充值需求合理，金额符合账户情况"
}
```

**字段说明**
| 字段 | 类型 | 必填 | 可选值 |
|------|------|------|--------|
| action | string | ✅ | approve/reject |
| notes | string | ❌ | 审核说明 |

### 5. 财务审批

财务人员审批充值申请并确定实际打款金额。

**请求**
```http
PUT /api/v1/topups/{request_id}/approve
```

**请求体**
```json
{
  "action": "approve",
  "actual_amount": "4950.00",
  "payment_method": "bank_transfer",
  "notes": "审批通过，银行转账处理"
}
```

**字段说明**
| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| action | string | ✅ | approve/reject |
| actual_amount | decimal | action=approve时必填 | 实际打款金额 |
| payment_method | enum | action=approve时建议 | 支付方式 |
| notes | string | ❌ | 审批说明 |

### 6. 标记为已打款

财务人员标记申请为已打款。

**请求**
```http
PUT /api/v1/topups/{request_id}/pay
```

**请求体**
```json
{
  "transaction_id": "TXN20251112143045",
  "notes": "已通过银行转账打款"
}
```

### 7. 上传打款凭证

上传银行转账凭证等支付证明文件。

**请求**
```http
POST /api/v1/topups/{request_id}/receipt
```

**请求体**
```json
{
  "receipt_url": "https://example.com/receipts/bank_transfer_001.jpg",
  "transaction_id": "TXN20251112143045",
  "notes": "银行转账凭证"
}
```

### 8. 获取审批日志

获取充值申请的所有审批和操作日志。

**请求**
```http
GET /api/v1/topups/{request_id}/logs
```

**响应**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "action": "submitted",
      "actor_name": "张投手",
      "actor_role": "media_buyer",
      "notes": "提交充值申请",
      "previous_status": null,
      "new_status": "pending",
      "ip_address": "192.168.1.100",
      "created_at": "2025-11-12T10:00:00Z"
    },
    {
      "id": 2,
      "action": "data_reviewed",
      "actor_name": "李审核",
      "actor_role": "data_operator",
      "notes": "审核通过",
      "previous_status": "pending",
      "new_status": "data_review",
      "created_at": "2025-11-12T10:30:00Z"
    }
  ]
}
```

### 9. 获取充值统计

获取充值相关的统计数据，管理员、财务、数据员有权限。

**请求**
```http
GET /api/v1/topups/statistics?start_date=2025-11-01&end_date=2025-11-30
```

**响应**
```json
{
  "success": true,
  "data": {
    "total_requests": 150,
    "pending_requests": 10,
    "data_review_requests": 5,
    "finance_approve_requests": 3,
    "approved_requests": 120,
    "paid_requests": 115,
    "completed_requests": 110,
    "rejected_requests": 5,
    "total_amount_requested": "500000.00",
    "total_amount_approved": "485000.00",
    "total_amount_paid": "475000.00",
    "avg_processing_time_hours": 24.5,
    "success_rate": 73.33,
    "urgent_requests": 15,
    "high_requests": 25,
    "overdue_requests": 2,
    "monthly_stats": [
      {
        "month": "2025-11",
        "count": 50,
        "amount": 150000.00
      }
    ],
    "top_projects": [
      {
        "project_id": 1,
        "project_name": "重要客户项目",
        "total_amount": 100000.00,
        "request_count": 20
      }
    ]
  }
}
```

### 10. 获取仪表板数据

获取充值仪表板的汇总数据。

**请求**
```http
GET /api/v1/topups/dashboard
```

**响应**
```json
{
  "success": true,
  "data": {
    "pending_reviews": 10,
    "pending_approvals": 5,
    "pending_payments": 3,
    "overdue_items": 2,
    "today_requests": 5,
    "today_amount": "25000.00",
    "today_completed": 3,
    "month_requests": 100,
    "month_amount": "400000.00",
    "month_completed": 80,
    "recent_requests": [],
    "statistics": {}
  }
}
```

### 11. 获取账户余额

获取指定广告账户的余额信息。

**请求**
```http
GET /api/v1/topups/accounts/{account_id}/balance
```

**响应**
```json
{
  "success": true,
  "data": {
    "ad_account_id": 1,
    "ad_account_name": "Facebook广告账户",
    "current_balance": "150000.00",
    "currency": "USD",
    "max_balance": "500000.00",
    "available_topup": "350000.00"
  }
}
```

### 12. 导出充值记录

导出充值记录为Excel或CSV格式，管理员和财务有权限。

**请求**
```http
GET /api/v1/topups/export?start_date=2025-11-01&end_date=2025-11-30&status=completed
```

**响应**
```json
{
  "success": true,
  "data": [
    {
      "申请单号": "TOP20251112143045001",
      "项目名称": "测试项目",
      "广告账户": "Facebook广告账户",
      "申请金额": 1000.00,
      "实际金额": 950.00,
      "货币": "USD",
      "状态": "completed",
      "申请时间": "2025-11-12 10:00:00",
      "完成时间": "2025-11-12 15:00:00"
    }
  ]
}
```

---

## ⚠️ 错误码说明

| 错误码 | HTTP状态码 | 描述 | 触发条件 |
|--------|------------|------|----------|
| SYS_004 | 404 | 充值申请不存在 | ID不存在 |
| BIZ_201 | 400 | 充值金额超出限制 | > 10万或 ≤ 0 |
| BIZ_202 | 400 | 账户余额超出上限 | 充值后 > 50万 |
| BIZ_203 | 422 | 状态转换无效 | 非法状态流转 |
| BIZ_204 | 400 | 超出申请频次限制 | 24h内 > 3次 |
| BIZ_205 | 400 | 期望日期无效 | 早于明天 |
| BIZ_206 | 403 | 无权限操作申请 | 权限不足 |
| BIZ_207 | 409 | 重复打款 | 已标记为paid |

---

## 🔧 使用示例

### Python示例

```python
import httpx
from decimal import Decimal

# 配置
BASE_URL = "http://localhost:8000"
TOKEN = "your_access_token_here"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 创建充值申请
request_data = {
    "ad_account_id": 1,
    "requested_amount": "5000.00",
    "reason": "账户充值",
    "urgency_level": "normal"
}

response = httpx.post(
    f"{BASE_URL}/api/v1/topups",
    json=request_data,
    headers=headers
)

if response.status_code == 201:
    request = response.json()["data"]
    print(f"申请创建成功，申请号: {request['request_no']}")
else:
    print(f"创建失败: {response.json()}")

# 查询申请状态
response = httpx.get(
    f"{BASE_URL}/api/v1/topups",
    headers=headers,
    params={"status": "pending"}
)

if response.status_code == 200:
    requests = response.json()["data"]["items"]
    print(f"找到 {len(requests)} 个待处理申请")
```

### cURL示例

```bash
# 创建充值申请
curl -X POST http://localhost:8000/api/v1/topups \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "ad_account_id": 1,
    "requested_amount": "10000.00",
    "reason": "广告投放充值",
    "urgency_level": "high"
  }'

# 查询申请列表
curl -X GET "http://localhost:8000/api/v1/topups?status=pending&page=1&page_size=20" \
  -H "Authorization: Bearer <token>"

# 获取统计数据
curl -X GET http://localhost:8000/api/v1/topups/statistics \
  -H "Authorization: Bearer <token>"
```

### JavaScript示例

```javascript
// 使用fetch API
const BASE_URL = "http://localhost:8000";
const TOKEN = "your_access_token_here";

const headers = {
  "Authorization": `Bearer ${TOKEN}`,
  "Content-Type": "application/json"
};

// 创建充值申请
async function createTopupRequest(requestData) {
  const response = await fetch(`${BASE_URL}/api/v1/topups`, {
    method: "POST",
    headers,
    body: JSON.stringify(requestData)
  });

  if (response.ok) {
    const result = await response.json();
    console.log("申请创建成功:", result.data);
    return result.data;
  } else {
    const error = await response.json();
    console.error("创建失败:", error);
  }
}

// 获取统计数据
async function getStatistics(startDate, endDate) {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const response = await fetch(
    `${BASE_URL}/api/v1/topups/statistics?${params}`,
    { headers }
  );

  if (response.ok) {
    const stats = await response.json();
    return stats.data;
  }
}
```

---

## 📈 业务流程示例

### 完整的充值流程

1. **媒体买家创建申请**
```json
POST /api/v1/topups
{
  "ad_account_id": 1,
  "requested_amount": "10000.00",
  "reason": "双十一推广活动预算",
  "urgency_level": "urgent"
}
```

2. **数据员审核**
```json
PUT /api/v1/topups/{id}/review
{
  "action": "approve",
  "notes": "充值需求合理，符合账户情况"
}
```

3. **财务审批**
```json
PUT /api/v1/topups/{id}/approve
{
  "action": "approve",
  "actual_amount": "10000.00",
  "payment_method": "bank_transfer"
}
```

4. **财务打款**
```json
PUT /api/v1/topups/{id}/pay
{
  "transaction_id": "BANK202511121234567"
}
```

5. **上传凭证**
```json
POST /api/v1/topups/{id}/receipt
{
  "receipt_url": "https://cdn.example.com/receipts/123.jpg",
  "notes": "银行电子回单"
}
```

---

## 📊 性能指标

| 操作 | 响应时间 (P95) | 并发支持 | 限制 |
|------|----------------|----------|------|
| 列表查询 | < 300ms | 100 | 最大100条/页 |
| 创建申请 | < 200ms | 50 | - |
| 状态更新 | < 100ms | 50 | - |
| 统计查询 | < 500ms | 30 | - |
| 导出数据 | < 5s | 10 | 最大1000条 |

---

## 🔍 最佳实践

1. **申请创建**
   - 提供清晰准确的充值原因
   - 根据紧急程度合理设置优先级
   - 避免频繁的小额申请

2. **审核流程**
   - 及时处理待审核申请
   - 在审核说明中记录关键决策点
   - 保持审核标准的一致性

3. **财务操作**
   - 打款后立即标记并上传凭证
   - 保留完整的银行流水记录
   - 定期对账确保数据准确

4. **异常处理**
   - 超时申请需要特殊说明原因
   - 金额异常时需要提供更多证明
   - 保存所有沟通记录和审批文件

---

## 🆘 故障排除

### 常见问题

**Q: 创建申请时返回BIZ_204错误？**
A: 24小时内同一账户申请次数超过3次，请合并申请或等待明天。

**Q: 无法查看统计数据？**
A: 只有管理员、财务、数据员角色有权限查看统计数据。

**Q: 财务审批时找不到实际金额字段？**
A: 只有在action为"approve"时才需要填写actual_amount。

**Q: 无法上传凭证？**
A: 确保申请已标记为已打款状态，且您有财务权限。

---

## 📞 技术支持

- **文档**: [开发文档中心](../)
- **问题反馈**: [GitHub Issues](https://github.com/your-org/ai_ad_spend02/issues)
- **技术支持**: dev-team@your-domain.com

---

**文档维护**: 开发团队
**最后更新**: 2025-11-12
**版本**: v1.0