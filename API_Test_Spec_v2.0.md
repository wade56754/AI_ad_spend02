# AI Finance System 接口测试文档 v2.0

> 目的：验证后端接口是否符合《Cursor 项目开发规则 v2.0》规定的统一返回结构、业务状态机、跨表校验和日志落库要求。

---

## 0. 测试约定

- **API 前缀**：`http://localhost:8000/api`  
  部署到宝塔后改为你的域名，例如：`https://ai-finance.xxx.com/api`
- **统一返回结构**：
  ```json
  {
    "data": ...,
    "error": null,
    "meta": {
      "timestamp": "2025-11-08T12:00:00Z",
      "pagination": null
    }
  }
  ```
- 所有 `POST` / `PATCH` 都用 `Content-Type: application/json`
- 所有写操作都应在 `logs` 表里出现对应记录

---

## 1. 健康检查

### 1.1 系统健康

**接口**  
`GET /api/healthz`

**预期**
- HTTP 200
- `data.status = "ok"`

**curl**
```bash
curl -X GET http://localhost:8000/api/healthz
```

---

## 2. 项目模块（projects）

### 2.1 获取项目列表

**接口**  
`GET /api/projects`

**预期**
- 返回数组，字段包含：`id, name, currency, status, created_at`

```bash
curl -X GET http://localhost:8000/api/projects
```

---

### 2.2 创建项目

**接口**  
`POST /api/projects`

```bash
curl -X POST http://localhost:8000/api/projects   -H "Content-Type: application/json"   -d '{
    "name": "印度投放A",
    "client_name": "客户A",
    "currency": "USD"
  }'
```

**预期**
- 201
- `data.id` 不为空
- `logs` 有 `create_project`

---

## 3. 渠道模块（channels）

### 3.1 获取渠道列表

```bash
curl -X GET http://localhost:8000/api/channels
```

**预期**
- 字段包含：`name, service_fee_type, service_fee_value, is_active`

---

### 3.2 创建渠道

```bash
curl -X POST http://localhost:8000/api/channels   -H "Content-Type: application/json"   -d '{
    "name": "Facebook-IN",
    "service_fee_type": "percent",
    "service_fee_value": 5.0,
    "is_active": true
  }'
```

**预期**
- 唯一约束验证，重复时返回 409

---

## 4. 广告账户（ad_accounts）

### 4.1 获取账户列表

```bash
curl -X GET "http://localhost:8000/api/ad-accounts"
```

**预期**
- 字段包含：`id, name, project_id, channel_id, status`

---

### 4.2 创建账户

```bash
curl -X POST http://localhost:8000/api/ad-accounts   -H "Content-Type: application/json"   -d '{
    "name": "FB-IN-001",
    "project_id": "<PROJECT_ID>",
    "channel_id": "<CHANNEL_ID>",
    "assigned_user_id": "<USER_ID>"
  }'
```

**预期**
- 创建成功返回 201

---

### 4.3 修改账户状态

```bash
curl -X PATCH http://localhost:8000/api/ad-accounts/<ACCOUNT_ID>/status   -H "Content-Type: application/json"   -d '{"next_status": "active"}'
```

**预期**
- 状态流转合法返回 200，否则返回 422 并记录日志

---

## 5. 日报模块（ad_spend_daily）

### 5.1 新增日报

```bash
curl -X POST http://localhost:8000/api/ad-spend   -H "Content-Type: application/json"   -d '{
    "ad_account_id": "<ACCOUNT_ID>",
    "date": "2025-11-08",
    "spend": 300.5,
    "leads_count": 12,
    "note": "正常投放"
  }'
```

**预期**
- 自动计算 `cost_per_lead`
- 返回 200 且 `error = null`

---

### 5.2 重复日报测试

**预期**
- 同日同账户录入返回 409 或业务错误 `E1001`

---

## 6. 充值模块（topups）

### 6.1 发起充值

```bash
curl -X POST http://localhost:8000/api/topups   -H "Content-Type: application/json"   -d '{
    "ad_account_id": "<ACCOUNT_ID>",
    "amount": 1000,
    "remark": "11月预算"
  }'
```

**预期**
- 状态 `pending`
- 校验 project/channel 一致性

---

### 6.2 审批充值

```bash
curl -X POST http://localhost:8000/api/topups/<TOPUP_ID>/approve
```

**预期**
- `pending → approved`
- 自动计算 `service_fee_amount`

---

### 6.3 财务付款与确认到账

```bash
curl -X POST http://localhost:8000/api/topups/<TOPUP_ID>/pay
curl -X POST http://localhost:8000/api/topups/<TOPUP_ID>/confirm
```

**预期**
- 严格按状态流转，否则返回 422

---

## 7. 财务模块（ledgers）

```bash
curl -X POST http://localhost:8000/api/finance/ledgers   -H "Content-Type: application/json"   -d '{
    "type": "recharge",
    "project_id": "<PROJECT_ID>",
    "channel_id": "<CHANNEL_ID>",
    "ad_account_id": "<ACCOUNT_ID>",
    "amount": 5000,
    "currency": "USD",
    "occurred_at": "2025-11-08T00:00:00Z",
    "remark": "线下补款"
  }'
```

**预期**
- 记录写入成功并在日志中可见

---

## 8. 对账模块（reconciliations）

### 8.1 自动对账

```bash
curl -X POST http://localhost:8000/api/finance/reconcile/auto
```

**预期**
- 匹配账户、金额误差 ≤5%、日期差 ≤1 天

---

### 8.2 人工对账

```bash
curl -X POST http://localhost:8000/api/finance/reconcile/manual   -H "Content-Type: application/json"   -d '{
    "ledger_id": "<LEDGER_ID>",
    "ad_spend_id": "<AD_SPEND_ID>",
    "remark": "手动配平"
  }'
```

**预期**
- 非匹配账户返回 422

---

## 9. 日志模块（logs）

```bash
curl -X GET "http://localhost:8000/api/logs?target_table=topups"
```

**预期**
- 包含 `actor_id, action, target_table, target_id, created_at`

---

## 10. 验收 Checklist

- [ ] 返回结构统一 `{data, error, meta}`
- [ ] 所有写操作生成日志
- [ ] 重复日报阻止
- [ ] 充值流转合法
- [ ] 跨表一致性校验生效
- [ ] 金额序列化正确
- [ ] API 路径不重复 `/api/api`
