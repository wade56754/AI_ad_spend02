# 对账管理 API 文档

> **模块名称**: 对账管理 (Reconciliation Management)
> **API版本**: v1
> **文档版本**: 1.0
> **更新日期**: 2025-11-12

---

## 📋 概述

对账管理API提供完整的财务对账功能，包括自动对账、差异管理、调整记录和报告生成等功能。系统支持多渠道、多币种的广告消耗数据与内部记录进行精确比对，确保财务数据的准确性。

### 核心功能
- **自动对账**: 定期自动比对平台消耗与内部记录
- **差异管理**: 记录、审核、处理所有对账差异
- **调整记录**: 创建和跟踪财务调整
- **统计分析**: 提供多维度的对账统计报告
- **数据导出**: 支持Excel、PDF、JSON格式导出

### 认证方式
所有API请求都需要在Header中包含JWT Token：
```
Authorization: Bearer <your-jwt-token>
```

---

## 🔗 API端点列表

| 方法 | 端点 | 描述 | 权限要求 |
|------|------|------|----------|
| GET | `/api/v1/reconciliations` | 获取对账批次列表 | 相关角色 |
| POST | `/api/v1/reconciliations/batches` | 创建对账批次 | admin, finance |
| GET | `/api/v1/reconciliations/batches/{id}` | 获取对账批次详情 | 相关角色 |
| POST | `/api/v1/reconciliations/batches/{id}/run` | 执行对账 | admin, finance |
| GET | `/api/v1/reconciliations/batches/{id}/details` | 获取对账详情列表 | 相关角色 |
| PUT | `/api/v1/reconciliations/details/{id}/review` | 审核对账差异 | admin, finance |
| POST | `/api/v1/reconciliations/details/{id}/adjust` | 创建调整记录 | admin, finance |
| GET | `/api/v1/reconciliations/statistics` | 获取对账统计 | admin, finance, data_operator |
| GET | `/api/v1/reconciliations/export` | 导出对账数据 | admin, finance |
| GET | `/api/v1/reconciliations/reports` | 获取对账报告列表 | 相关角色 |
| POST | `/api/v1/reconciliations/reports` | 生成对账报告 | admin, finance |

---

## 📝 API详情

### 1. 获取对账批次列表

获取对账批次列表，支持分页和过滤。

**请求**
```http
GET /api/v1/reconciliations?page=1&page_size=20&status=completed&date_from=2025-11-01&date_to=2025-11-30
```

**查询参数**
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20，最大100 |
| status | string | 否 | 对账状态过滤 |
| date_from | date | 否 | 开始日期过滤 |
| date_to | date | 否 | 结束日期过滤 |

**响应**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "batch_no": "REC20251112143000123",
        "reconciliation_date": "2025-11-10",
        "status": "completed",
        "total_accounts": 100,
        "matched_accounts": 95,
        "mismatched_accounts": 5,
        "total_platform_spend": "10000.00",
        "total_internal_spend": "9950.00",
        "total_difference": "50.00",
        "auto_matched": 90,
        "manual_reviewed": 5,
        "started_at": "2025-11-10T10:30:00Z",
        "completed_at": "2025-11-10T10:35:00Z",
        "created_by": 1,
        "created_by_name": "张三",
        "created_at": "2025-11-10T10:30:00Z",
        "updated_at": "2025-11-10T10:35:00Z",
        "notes": "11月10日对账批次",
        "match_rate": 95.0,
        "difference_rate": 0.5,
        "processing_duration": 0.083
      }
    ],
    "meta": {
      "total": 1,
      "page": 1,
      "page_size": 20,
      "total_pages": 1
    }
  },
  "message": "操作成功",
  "code": "SUCCESS",
  "timestamp": "2025-11-12T10:30:00Z"
}
```

### 2. 创建对账批次

创建新的对账批次。

**请求**
```http
POST /api/v1/reconciliations/batches
```

**请求体**
```json
{
  "reconciliation_date": "2025-11-10",
  "channel_ids": [1, 2, 3],
  "auto_match": true,
  "threshold": "100.00",
  "notes": "11月10日对账批次"
}
```

**请求参数**
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| reconciliation_date | date | 是 | 对账日期 |
| channel_ids | array | 否 | 渠道ID列表 |
| auto_match | boolean | 否 | 是否自动匹配，默认true |
| threshold | decimal | 否 | 差异阈值 |
| notes | string | 否 | 备注说明 |

**响应**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "batch_no": "REC20251112143000123",
    "reconciliation_date": "2025-11-10",
    "status": "pending",
    "total_accounts": 0,
    "matched_accounts": 0,
    "mismatched_accounts": 0,
    "total_platform_spend": "0.00",
    "total_internal_spend": "0.00",
    "total_difference": "0.00",
    "auto_matched": 0,
    "manual_reviewed": 0,
    "started_at": null,
    "completed_at": null,
    "created_by": 1,
    "created_by_name": "张三",
    "created_at": "2025-11-12T10:30:00Z",
    "updated_at": "2025-11-12T10:30:00Z",
    "notes": "11月10日对账批次"
  },
  "message": "对账批次创建成功",
  "code": "SUCCESS",
  "timestamp": "2025-11-12T10:30:00Z"
}
```

### 3. 执行对账

对指定的批次执行对账操作。

**请求**
```http
POST /api/v1/reconciliations/batches/{batch_id}/run
```

**响应**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "batch_no": "REC20251112143000123",
    "status": "completed",
    "total_accounts": 100,
    "matched_accounts": 95,
    "mismatched_accounts": 5,
    "started_at": "2025-11-12T10:30:00Z",
    "completed_at": "2025-11-12T10:35:00Z"
  },
  "message": "对账执行成功",
  "code": "SUCCESS",
  "timestamp": "2025-11-12T10:30:00Z"
}
```

### 4. 审核对账差异

审核处理对账差异。

**请求**
```http
PUT /api/v1/reconciliations/details/{detail_id}/review
```

**请求体**
```json
{
  "action": "approve",
  "is_matched": true,
  "match_status": "matched",
  "review_notes": "审核通过，差异在可接受范围内",
  "auto_confidence": "0.95",
  "difference_type": "amount_mismatch",
  "difference_reason": "汇率波动导致的小额差异"
}
```

**请求参数**
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| action | string | 是 | 审核动作：approve/reject/investigate |
| is_matched | boolean | 是 | 是否确认匹配 |
| match_status | string | 否 | 最终匹配状态 |
| review_notes | string | 否 | 审核说明 |
| auto_confidence | decimal | 否 | 自动匹配置信度 |
| difference_type | string | 否 | 差异类型 |
| difference_reason | string | 否 | 差异原因 |

### 5. 创建调整记录

对差异项创建财务调整记录。

**请求**
```http
POST /api/v1/reconciliations/details/{detail_id}/adjust
```

**请求体**
```json
{
  "adjustment_type": "spend_adjustment",
  "original_amount": "1000.00",
  "adjustment_amount": "-50.00",
  "adjustment_reason": "data_error",
  "detailed_reason": "平台数据延迟导致的差异，已核实正确金额",
  "evidence_url": "https://example.com/evidence.pdf",
  "notes": "已附上平台截图证据"
}
```

### 6. 获取对账统计

获取对账统计数据。

**请求**
```http
GET /api/v1/reconciliations/statistics?date_from=2025-11-01&date_to=2025-11-30
```

**响应**
```json
{
  "success": true,
  "data": {
    "total_batches": 30,
    "completed_batches": 28,
    "exception_batches": 1,
    "resolved_batches": 1,
    "total_accounts": 3000,
    "matched_accounts": 2850,
    "mismatched_accounts": 150,
    "total_platform_spend": "300000.00",
    "total_internal_spend": "299500.00",
    "total_difference": "500.00",
    "total_adjustments": "200.00",
    "net_difference": "300.00",
    "auto_match_rate": 95.0,
    "manual_review_rate": 5.0,
    "resolution_rate": 96.67,
    "avg_processing_time_hours": 0.15,
    "difference_rate": 0.17,
    "monthly_trends": [
      {
        "month": "2025-11",
        "batches": 30,
        "accounts": 3000,
        "match_rate": 95.0,
        "difference": "500.00"
      }
    ],
    "top_difference_reasons": [
      {
        "reason": "汇率波动",
        "count": 80,
        "amount": "300.00"
      },
      {
        "reason": "时间差异",
        "count": 50,
        "amount": "150.00"
      }
    ],
    "channel_performance": [
      {
        "channel_name": "Facebook",
        "accounts": 1500,
        "match_rate": 96.0,
        "difference": "200.00"
      }
    ],
    "top_mismatched_accounts": [
      {
        "account_name": "Account-001",
        "mismatches": 5,
        "total_difference": "50.00"
      }
    ]
  },
  "message": "操作成功",
  "code": "SUCCESS",
  "timestamp": "2025-11-12T10:30:00Z"
}
```

### 7. 导出对账数据

导出对账数据到文件。

**请求**
```http
GET /api/v1/reconciliations/export?format_type=excel&date_from=2025-11-01&date_to=2025-11-30
```

**查询参数**
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| batch_id | integer | 否 | 批次ID |
| date_from | date | 否 | 开始日期 |
| date_to | date | 否 | 结束日期 |
| format_type | string | 否 | 导出格式：excel/pdf/json，默认excel |

**响应**
根据format_type返回不同格式的文件下载。

---

## 🔐 权限矩阵

| 角色 | 创建批次 | 执行对账 | 审核差异 | 创建调整 | 查看统计 | 导出数据 |
|------|----------|----------|----------|----------|----------|----------|
| admin | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| finance | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| data_operator | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| account_manager | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| media_buyer | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

**说明**:
- ✅: 有权限
- ❌: 无权限
- 账户管理员和媒体买家只能查看自己项目/账户的数据

---

## ⚠️ 错误码

| 错误码 | HTTP状态码 | 描述 | 解决方案 |
|--------|------------|------|----------|
| SYS_004 | 404 | 资源不存在 | 检查ID是否正确 |
| BIZ_301 | 400 | 对账日期无效 | 日期不能是未来或超过30天前 |
| BIZ_302 | 400 | 重复对账 | 该日期已存在对账批次 |
| BIZ_303 | 403 | 无权限操作 | 联系管理员分配权限 |
| BIZ_304 | 400 | 差异超阈值 | 差异超过设定阈值，需要人工审核 |
| BIZ_305 | 400 | 调整金额无效 | 调整金额格式错误或超出范围 |
| BIZ_306 | 422 | 状态转换无效 | 当前状态不允许此操作 |

---

## 📋 业务规则

### 对账规则
1. **对账频率**: 每日自动对账前日数据
2. **差异阈值**: 默认100USD，超过阈值需要人工审核
3. **自动匹配**: 差异小于1USD且置信度>0.8自动标记为匹配
4. **状态流转**: pending → processing → completed/exception → resolved

### 调整规则
1. **调整类型**: 支持金额调整和时间调整
2. **审批要求**: 所有调整都需要创建人审批
3. **财务确认**: 金额调整需要财务二次确认
4. **证据要求**: 超过1000USD的调整必须提供证据

### 导出规则
1. **数据范围**: 只能导出有权限的数据
2. **时间限制**: 单次导出最多90天数据
3. **格式限制**: Excel最多10000行，PDF需要分页

---

## 📊 示例代码

### JavaScript (Axios)

```javascript
// 创建对账批次
const createBatch = async () => {
  try {
    const response = await axios.post('/api/v1/reconciliations/batches', {
      reconciliation_date: '2025-11-10',
      auto_match: true,
      notes: '11月10日对账'
    }, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    console.log('批次创建成功:', response.data);
  } catch (error) {
    console.error('创建失败:', error.response.data);
  }
};

// 获取对账统计
const getStatistics = async () => {
  try {
    const response = await axios.get('/api/v1/reconciliations/statistics', {
      params: {
        date_from: '2025-11-01',
        date_to: '2025-11-30'
      },
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    console.log('统计数据:', response.data);
  } catch (error) {
    console.error('获取失败:', error.response.data);
  }
};
```

### Python (Requests)

```python
import requests
from datetime import date

# 创建对账批次
def create_reconciliation_batch(token):
    url = "http://localhost:8000/api/v1/reconciliations/batches"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "reconciliation_date": str(date.today()),
        "auto_match": True,
        "notes": "Python API测试"
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print("批次创建成功:", response.json())
    else:
        print("创建失败:", response.json())

# 审核对账差异
def review_detail(token, detail_id):
    url = f"http://localhost:8000/api/v1/reconciliations/details/{detail_id}/review"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "action": "approve",
        "is_matched": True,
        "match_status": "matched",
        "review_notes": "审核通过"
    }

    response = requests.put(url, headers=headers, json=data)
    if response.status_code == 200:
        print("审核成功:", response.json())
    else:
        print("审核失败:", response.json())
```

---

## 📝 更新日志

### v1.0 (2025-11-12)
- 初始版本发布
- 实现基础对账功能
- 支持自动对账和人工审核
- 提供完整的统计和导出功能

---

## 📞 技术支持

如有问题或建议，请联系：
- **技术支持**: tech-support@example.com
- **文档反馈**: docs@example.com
- **Bug报告**: https://github.com/your-org/ai-ad-spend/issues