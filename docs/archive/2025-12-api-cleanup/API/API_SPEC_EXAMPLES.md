# API 规格书完整示例

> **文档层级**: 🟢 示例层 - 参考查阅
> **前置依赖**: API_SPEC_GUIDE_v2.0_CORE.md

---

## 示例 1：CRUD 模块（日报）

```markdown
# API 规格书: 日报模块

## §1 概述

| 属性 | 值 |
|------|-----|
| 模块 | 日报管理 |
| 版本 | v1 |
| 基础路径 | /api/v1/daily-reports |
| 后端规划书 | docs/backend/B1-daily-report.md |

## §2 端点清单

| 方法 | 端点 | 描述 | 权限 |
|------|------|------|------|
| GET | /daily-reports | 获取列表 | 登录用户 |
| GET | /daily-reports/:id | 获取详情 | 数据权限 |
| POST | /daily-reports | 创建 | pitcher |
| PATCH | /daily-reports/:id | 更新 | 所有者(draft) |
| DELETE | /daily-reports/:id | 删除 | 所有者(draft) |
| POST | /daily-reports/:id/submit | 提交 | 所有者 |

## §3 端点详情

### 3.1 获取列表

| 属性 | 值 |
|------|-----|
| 端点 | GET /daily-reports |
| 描述 | 获取日报列表（按角色过滤数据） |
| 权限 | 登录用户 |

**Query 参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | number | 否 | 1 | 页码 |
| pageSize | number | 否 | 20 | 每页数量(1-100) |
| dateFrom | string | 否 | - | 开始日期 |
| dateTo | string | 否 | - | 结束日期 |
| status | string | 否 | - | 状态，逗号分隔 |
| projectId | string | 否 | - | 项目ID |
| sortBy | string | 否 | createdAt | 排序字段 |
| sortOrder | string | 否 | desc | 排序方向 |

**数据权限**

| 角色 | 可见范围 |
|------|----------|
| ceo | 所有 |
| supervisor | 下属 |
| pitcher | 仅自己 |

**成功响应 (200)**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "date": "2024-12-23",
      "project": {
        "id": "project-001",
        "name": "项目A"
      },
      "pitcher": {
        "id": "user-001",
        "name": "张三"
      },
      "conversions": 100,
      "spend": 5000.00,
      "cpl": 50.00,
      "status": "draft",
      "createdAt": "2024-12-23T02:30:00Z",
      "updatedAt": "2024-12-23T02:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "total": 1,
    "totalPages": 1
  }
}
```

**错误响应**

| HTTP | 错误码 | 场景 |
|------|--------|------|
| 401 | UNAUTHORIZED | 未登录 |

---

### 3.2 获取详情

| 属性 | 值 |
|------|-----|
| 端点 | GET /daily-reports/:id |
| 描述 | 获取日报详情 |
| 权限 | 数据所有者/上级 |

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 日报ID (UUID) |

**成功响应 (200)**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "date": "2024-12-23",
  "project": {
    "id": "project-001",
    "name": "项目A"
  },
  "pitcher": {
    "id": "user-001",
    "name": "张三"
  },
  "conversions": 100,
  "spend": 5000.00,
  "cpl": 50.00,
  "impressions": 10000,
  "clicks": 500,
  "ctr": 5.00,
  "status": "draft",
  "notes": "备注信息",
  "warnings": [],
  "createdAt": "2024-12-23T02:30:00Z",
  "updatedAt": "2024-12-23T02:30:00Z",
  "createdBy": {
    "id": "user-001",
    "name": "张三"
  }
}
```

**错误响应**

| HTTP | 错误码 | 场景 |
|------|--------|------|
| 401 | UNAUTHORIZED | 未登录 |
| 403 | FORBIDDEN | 无权限 |
| 404 | NOT_FOUND | 不存在 |

---

### 3.3 创建日报

| 属性 | 值 |
|------|-----|
| 端点 | POST /daily-reports |
| 描述 | 创建新日报 |
| 权限 | pitcher |
| 幂等性 | 通过 X-Request-ID |

**请求体**

```typescript
interface CreateDailyReportRequest {
  date: string;         // 必填，YYYY-MM-DD，不能是未来
  projectId: string;    // 必填，用户所属项目
  conversions: number;  // 必填，整数，≥0
  spend: number;        // 必填，≥0，2位小数
  impressions?: number; // 可选，整数，≥0
  clicks?: number;      // 可选，整数，≥0
  notes?: string;       // 可选，最大1000字符
}
```

**成功响应 (201)**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "date": "2024-12-23",
  "status": "draft",
  "createdAt": "2024-12-23T02:30:00Z"
}
```

**错误响应**

| HTTP | 错误码 | 场景 |
|------|--------|------|
| 400 | VALIDATION_ERROR | 参数错误 |
| 400 | FUTURE_DATE_NOT_ALLOWED | 未来日期 |
| 401 | UNAUTHORIZED | 未登录 |
| 403 | FORBIDDEN | 非pitcher |
| 403 | NOT_PROJECT_MEMBER | 非项目成员 |
| 409 | DUPLICATE_ENTRY | 重复日报 |

**示例**

请求:
```http
POST /api/v1/daily-reports HTTP/1.1
Authorization: Bearer {token}
Content-Type: application/json
X-Request-ID: req-123-456

{
  "date": "2024-12-23",
  "projectId": "project-001",
  "conversions": 100,
  "spend": 5000.00
}
```

成功响应:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "date": "2024-12-23",
  "status": "draft",
  "createdAt": "2024-12-23T02:30:00Z"
}
```

错误响应:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数验证失败",
    "details": {
      "date": ["不能选择未来日期"],
      "conversions": ["必须大于等于0"]
    }
  }
}
```

---

### 3.4 更新日报

| 属性 | 值 |
|------|-----|
| 端点 | PATCH /daily-reports/:id |
| 描述 | 更新日报（仅draft状态） |
| 权限 | 所有者 |

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 日报ID |

**请求体**

```typescript
interface UpdateDailyReportRequest {
  conversions?: number;
  spend?: number;
  impressions?: number;
  clicks?: number;
  notes?: string;
}
```

> 注意：date 和 projectId 不可修改

**成功响应 (200)**

返回更新后的完整日报对象。

**错误响应**

| HTTP | 错误码 | 场景 |
|------|--------|------|
| 400 | VALIDATION_ERROR | 参数错误 |
| 400 | INVALID_STATUS_TRANSITION | 非draft状态 |
| 401 | UNAUTHORIZED | 未登录 |
| 403 | FORBIDDEN | 非所有者 |
| 404 | NOT_FOUND | 不存在 |

---

### 3.5 删除日报

| 属性 | 值 |
|------|-----|
| 端点 | DELETE /daily-reports/:id |
| 描述 | 删除日报（仅draft状态） |
| 权限 | 所有者 |

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 日报ID |

**成功响应 (204)**

无响应体。

**错误响应**

| HTTP | 错误码 | 场景 |
|------|--------|------|
| 400 | INVALID_STATUS_TRANSITION | 非draft状态 |
| 401 | UNAUTHORIZED | 未登录 |
| 403 | FORBIDDEN | 非所有者 |
| 404 | NOT_FOUND | 不存在 |

---

### 3.6 提交日报

| 属性 | 值 |
|------|-----|
| 端点 | POST /daily-reports/:id/submit |
| 描述 | 提交日报（draft → raw_submitted） |
| 权限 | 所有者 |

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 日报ID |

**请求体**

无

**成功响应 (200)**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "raw_submitted",
  "submittedAt": "2024-12-23T03:00:00Z",
  "warnings": [
    {
      "field": "cpl",
      "type": "HIGH_CPL",
      "message": "CPL 高于项目平均值",
      "severity": "warning"
    }
  ]
}
```

> Phase 1：有 warnings 也允许提交成功

**错误响应**

| HTTP | 错误码 | 场景 |
|------|--------|------|
| 400 | INVALID_STATUS_TRANSITION | 非draft状态 |
| 401 | UNAUTHORIZED | 未登录 |
| 403 | FORBIDDEN | 非所有者 |
| 404 | NOT_FOUND | 不存在 |

---

## §4 数据类型

```typescript
type DailyReportStatus = 
  | 'draft'
  | 'raw_submitted'
  | 'trend_pending'
  | 'trend_ok'
  | 'trend_flagged'
  | 'final_pending'
  | 'final_confirmed'
  | 'final_locked';

interface DailyReport {
  id: string;
  date: string;
  project: { id: string; name: string };
  pitcher: { id: string; name: string };
  conversions: number;
  spend: number;
  cpl: number | null;
  impressions?: number;
  clicks?: number;
  ctr?: number | null;
  status: DailyReportStatus;
  notes?: string;
  warnings?: Warning[];
  createdAt: string;
  updatedAt: string;
  createdBy?: { id: string; name: string };
}

interface Warning {
  field: string;
  type: string;
  message: string;
  severity: 'info' | 'warning' | 'error';
}
```

## §5 错误码

| 错误码 | HTTP | 场景 |
|--------|------|------|
| VALIDATION_ERROR | 400 | 参数验证失败 |
| FUTURE_DATE_NOT_ALLOWED | 400 | 未来日期 |
| INVALID_STATUS_TRANSITION | 400 | 无效状态转换 |
| UNAUTHORIZED | 401 | 未登录 |
| FORBIDDEN | 403 | 无权限 |
| NOT_PROJECT_MEMBER | 403 | 非项目成员 |
| NOT_FOUND | 404 | 不存在 |
| DUPLICATE_ENTRY | 409 | 重复日报 |
```

---

## 示例 2：批量操作

```markdown
# 批量审核接口

### 批量审核通过

| 属性 | 值 |
|------|-----|
| 端点 | POST /daily-reports/batch-approve |
| 描述 | 批量审核通过 |
| 权限 | supervisor, ceo |

**请求体**

```typescript
interface BatchApproveRequest {
  ids: string[];      // 1-50个
  comment?: string;   // 审核意见
}
```

**成功响应 (200)**

```json
{
  "success": ["uuid-1", "uuid-3"],
  "failed": [
    {
      "id": "uuid-2",
      "error": {
        "code": "INVALID_STATUS_TRANSITION",
        "message": "状态不允许审核"
      }
    }
  ]
}
```

**错误响应**

| HTTP | 错误码 | 场景 |
|------|--------|------|
| 400 | VALIDATION_ERROR | ids为空或超过50 |
| 401 | UNAUTHORIZED | 未登录 |
| 403 | FORBIDDEN | 无审核权限 |
```

---

## 示例 3：文件上传

```markdown
# 文件上传接口

### 上传附件

| 属性 | 值 |
|------|-----|
| 端点 | POST /attachments |
| 描述 | 上传文件附件 |
| 权限 | 登录用户 |
| Content-Type | multipart/form-data |

**请求**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 文件(最大10MB) |
| type | string | 是 | 类型: report/avatar/document |

**成功响应 (201)**

```json
{
  "id": "att-123",
  "filename": "report.xlsx",
  "originalName": "日报_20241223.xlsx",
  "url": "https://cdn.example.com/attachments/xxx.xlsx",
  "size": 102400,
  "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "createdAt": "2024-12-23T02:30:00Z"
}
```

**错误响应**

| HTTP | 错误码 | 场景 |
|------|--------|------|
| 400 | VALIDATION_ERROR | 文件类型不支持 |
| 400 | FILE_TOO_LARGE | 超过10MB |
| 401 | UNAUTHORIZED | 未登录 |
```

---

## 示例 4：聚合统计

```markdown
# 统计接口

### 获取日报统计

| 属性 | 值 |
|------|-----|
| 端点 | GET /daily-reports/summary |
| 描述 | 获取日报汇总统计 |
| 权限 | supervisor, ceo |

**Query 参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dateFrom | string | 是 | 开始日期 |
| dateTo | string | 是 | 结束日期 |
| projectId | string | 否 | 项目ID |
| pitcherId | string | 否 | 投手ID |

**成功响应 (200)**

```json
{
  "totalConversions": 10000,
  "totalSpend": 500000.00,
  "averageCpl": 50.00,
  "reportCount": 365,
  "projectCount": 5,
  "pitcherCount": 10,
  "dateRange": {
    "from": "2024-01-01",
    "to": "2024-12-31"
  }
}
```

**错误响应**

| HTTP | 错误码 | 场景 |
|------|--------|------|
| 400 | VALIDATION_ERROR | 日期范围无效 |
| 401 | UNAUTHORIZED | 未登录 |
| 403 | FORBIDDEN | 无权限 |
```

---

## 示例 5：导出下载

```markdown
# 导出接口

### 导出日报

| 属性 | 值 |
|------|-----|
| 端点 | POST /daily-reports/export |
| 描述 | 导出日报到Excel |
| 权限 | supervisor, ceo |

**请求体**

```typescript
interface ExportRequest {
  dateFrom: string;
  dateTo: string;
  projectId?: string;
  format: 'xlsx' | 'csv';
}
```

**成功响应 (200)**

小文件直接返回:
```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="daily-reports-2024.xlsx"

(文件二进制内容)
```

大文件返回下载链接:
```json
{
  "taskId": "task-123",
  "status": "processing",
  "message": "正在生成，请稍后下载"
}
```

### 获取导出状态

| 属性 | 值 |
|------|-----|
| 端点 | GET /exports/:taskId |

**成功响应 (200)**

```json
{
  "taskId": "task-123",
  "status": "completed",
  "downloadUrl": "https://cdn.example.com/exports/xxx.xlsx",
  "expiresAt": "2024-12-24T02:30:00Z"
}
```
```

---

## 示例 6：认证授权

```markdown
# 认证接口

### 登录

| 属性 | 值 |
|------|-----|
| 端点 | POST /auth/login |
| 描述 | 用户登录 |
| 权限 | 公开 |

**请求体**

```typescript
interface LoginRequest {
  email: string;
  password: string;
}
```

**成功响应 (200)**

```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
  "expiresIn": 86400,
  "user": {
    "id": "user-001",
    "email": "user@example.com",
    "name": "张三",
    "role": "pitcher"
  }
}
```

**错误响应**

| HTTP | 错误码 | 场景 |
|------|--------|------|
| 400 | VALIDATION_ERROR | 参数错误 |
| 401 | INVALID_CREDENTIALS | 凭证错误 |
| 403 | USER_DISABLED | 用户禁用 |

---

### 刷新Token

| 属性 | 值 |
|------|-----|
| 端点 | POST /auth/refresh |
| 描述 | 刷新访问令牌 |
| 权限 | 需要 refreshToken |

**请求体**

```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

**成功响应 (200)**

```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "expiresIn": 86400
}
```

---

### 登出

| 属性 | 值 |
|------|-----|
| 端点 | POST /auth/logout |
| 描述 | 用户登出 |
| 权限 | 登录用户 |

**成功响应 (204)**

无响应体。
```

---

## 代码生成模板

AI 可按此顺序生成结构化代码：

### 1. 端点常量

```typescript
// endpoints.ts
export const DAILY_REPORT_ENDPOINTS = {
  LIST: 'GET /api/v1/daily-reports',
  DETAIL: 'GET /api/v1/daily-reports/:id',
  CREATE: 'POST /api/v1/daily-reports',
  UPDATE: 'PATCH /api/v1/daily-reports/:id',
  DELETE: 'DELETE /api/v1/daily-reports/:id',
  SUBMIT: 'POST /api/v1/daily-reports/:id/submit',
} as const;
```

### 2. 类型定义

```typescript
// types.ts
export interface DailyReport {
  id: string;
  date: string;
  project: { id: string; name: string };
  pitcher: { id: string; name: string };
  conversions: number;
  spend: number;
  cpl: number | null;
  status: DailyReportStatus;
  createdAt: string;
  updatedAt: string;
}

export type DailyReportStatus = 
  | 'draft' 
  | 'raw_submitted'
  | 'trend_pending'
  | 'trend_ok'
  | 'trend_flagged'
  | 'final_pending'
  | 'final_confirmed'
  | 'final_locked';

export interface CreateDailyReportRequest {
  date: string;
  projectId: string;
  conversions: number;
  spend: number;
  impressions?: number;
  clicks?: number;
  notes?: string;
}

export interface ListDailyReportsParams {
  page?: number;
  pageSize?: number;
  dateFrom?: string;
  dateTo?: string;
  status?: string;
  projectId?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}
```

### 3. Zod 验证

```typescript
// validation.ts
import { z } from 'zod';

export const createDailyReportSchema = z.object({
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, '日期格式错误'),
  projectId: z.string().uuid('项目ID格式错误'),
  conversions: z.number().int().min(0, '进粉数必须≥0'),
  spend: z.number().min(0, '消耗必须≥0'),
  impressions: z.number().int().min(0).optional(),
  clicks: z.number().int().min(0).optional(),
  notes: z.string().max(1000).optional(),
});

export const listDailyReportsSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  pageSize: z.coerce.number().int().min(1).max(100).default(20),
  dateFrom: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  dateTo: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  status: z.string().optional(),
  projectId: z.string().uuid().optional(),
  sortBy: z.enum(['date', 'createdAt', 'spend']).default('createdAt'),
  sortOrder: z.enum(['asc', 'desc']).default('desc'),
});
```

---

## 文档引用

- 核心规则：API_SPEC_GUIDE_v2.0_CORE.md
- 详细规范：API_SPEC_DETAILED.md
- JSON Schema：API_SPEC_SCHEMAS.md
