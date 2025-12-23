# API 规格书详细规范

> **文档层级**: 🟡 详细层 - 按需读取
> **前置依赖**: 必须先读取 API_SPEC_GUIDE_v2.0_CORE.md

---

## §1 请求规范

### 1.1 请求头

```http
Content-Type: application/json
Authorization: Bearer {token}
Accept-Language: zh-CN
X-Request-ID: {uuid}
```

| 头部 | 必须 | 说明 |
|------|------|------|
| Content-Type | ✅ | POST/PATCH/PUT 必须 |
| Authorization | ✅ | 除公开接口外必须 |
| X-Request-ID | 建议 | 用于幂等性和追踪 |

### 1.2 Content-Type

| 场景 | Content-Type |
|------|--------------|
| JSON 数据 | application/json |
| 文件上传 | multipart/form-data |
| 表单 | application/x-www-form-urlencoded |

### 1.3 Query 参数规范

```
# 分页
?page=1&pageSize=20

# 筛选（精确）
?status=draft

# 筛选（多值）
?status=draft,submitted

# 日期范围
?dateFrom=2024-01-01&dateTo=2024-12-31

# 排序
?sortBy=createdAt&sortOrder=desc

# 组合
?page=1&pageSize=20&status=draft&sortBy=createdAt&sortOrder=desc
```

---

## §2 响应规范

### 2.1 成功响应结构

#### 单个对象

```typescript
// 200 OK 或 201 Created
interface SingleResponse {
  id: string;
  // 资源字段...
  createdAt: string;
  updatedAt: string;
}
```

#### 列表（分页）

```typescript
// 200 OK
interface ListResponse<T> {
  items: T[];
  pagination: {
    page: number;        // 当前页，从1开始
    pageSize: number;    // 每页数量
    total: number;       // 总记录数
    totalPages: number;  // 总页数
  };
}
```

#### 批量操作结果

```typescript
// 200 OK
interface BatchResponse {
  success: string[];     // 成功的ID列表
  failed: Array<{
    id: string;
    error: {
      code: string;
      message: string;
    };
  }>;
}
```

#### 无内容

```typescript
// 204 No Content
// 响应体为空
```

### 2.2 错误响应结构

```typescript
// 4xx 或 5xx
interface ErrorResponse {
  error: {
    code: string;        // 错误码（从清单选择）
    message: string;     // 中文错误信息
    details?: {          // 字段级错误（可选）
      [field: string]: string[];
    };
    traceId?: string;    // 追踪ID（可选）
  };
}
```

### 2.3 分页边界处理

| 参数 | 最小值 | 最大值 | 超出处理 |
|------|--------|--------|----------|
| page | 1 | - | <1 返回 400 |
| pageSize | 1 | 100 | >100 自动设为 100 |

---

## §3 数据类型规范

### 3.1 基础类型

| 类型 | 格式 | 示例 |
|------|------|------|
| ID | UUID 字符串 | "550e8400-e29b-41d4-a716-446655440000" |
| 日期 | YYYY-MM-DD | "2024-12-23" |
| 时间戳 | ISO 8601 UTC | "2024-12-23T02:30:00Z" |
| 金额 | number (2位小数) | 5000.00 |
| 百分比 | number (2位小数) | 12.34 |
| 布尔 | boolean | true / false |

### 3.2 枚举类型

```typescript
// 状态枚举示例
type Status = 'draft' | 'active' | 'archived';

// 角色枚举
type Role = 
  | 'ceo'
  | 'finance'
  | 'supervisor'
  | 'pitcher'
  | 'project_owner'
  | 'account_manager'
  | 'admin';
```

### 3.3 嵌套对象

```typescript
// 关联资源简化表示
interface ResourceRef {
  id: string;
  name: string;
}

// 使用示例
interface Report {
  id: string;
  project: ResourceRef;  // 而非 projectId + projectName
  pitcher: ResourceRef;
}
```

---

## §4 权限规范

### 4.1 权限说明格式

```markdown
#### 数据权限

| 角色 | 可见范围 |
|------|----------|
| ceo | 所有数据 |
| supervisor | 下属数据 |
| pitcher | 仅自己数据 |
| 其他 | 无 |
```

### 4.2 7角色矩阵模板

```markdown
| 操作 | ceo | finance | supervisor | pitcher | project_owner | account_manager | admin |
|------|-----|---------|------------|---------|---------------|-----------------|-------|
| 查看所有 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 查看下属 | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| 创建 | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| 编辑 | ❌ | ❌ | ❌ | ✅* | ❌ | ❌ | ❌ |
| 删除 | ❌ | ❌ | ❌ | ✅* | ❌ | ❌ | ❌ |

* 仅限自己的数据且状态为 draft
```

---

## §5 版本控制规范

### 5.1 URL 版本

```
/api/v1/resources
/api/v2/resources
```

### 5.2 兼容性规则

| 变更类型 | 兼容性 | 处理方式 |
|----------|--------|----------|
| 新增可选字段 | ✅ 兼容 | 直接添加 |
| 新增必填字段 | ❌ 不兼容 | 升级版本 |
| 删除字段 | ❌ 不兼容 | 先废弃再删除 |
| 修改字段类型 | ❌ 不兼容 | 升级版本 |
| 新增枚举值 | ✅ 兼容 | 直接添加 |
| 删除枚举值 | ❌ 不兼容 | 升级版本 |

### 5.3 废弃标记

```typescript
interface Response {
  newField: string;
  
  /**
   * @deprecated 将在 v2 移除，请使用 newField
   */
  oldField?: string;
}
```

---

## §6 幂等性规范

### 6.1 方法幂等性

| 方法 | 幂等 | 说明 |
|------|------|------|
| GET | ✅ | 多次调用结果相同 |
| PUT | ✅ | 相同数据多次调用结果相同 |
| DELETE | ✅ | 删除后再删返回404或204 |
| POST | ❌ | 需要通过机制保证 |
| PATCH | ⚠️ | 取决于实现 |

### 6.2 POST 幂等性保证

```http
POST /api/v1/reports
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{ "date": "2024-12-23", ... }
```

后端逻辑：
1. 检查 X-Request-ID 是否已处理
2. 已处理则返回之前的结果
3. 未处理则正常创建

---

## §7 安全规范

### 7.1 敏感数据处理

| 数据类型 | 处理方式 |
|----------|----------|
| 密码 | 永不返回 |
| 手机号 | 脱敏 138****1234 |
| 邮箱 | 脱敏 z***@example.com |
| 身份证 | 脱敏 110***********1234 |
| Token | 永不在URL中传递 |

### 7.2 错误信息安全

```typescript
// ❌ 错误：暴露内部信息
{
  "error": {
    "message": "SELECT * FROM users WHERE id = '1' failed",
    "stack": "Error at line 123..."
  }
}

// ✅ 正确：隐藏内部信息
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "服务器内部错误"
  }
}
```

---

## §8 特殊场景规范

### 8.1 文件上传

```markdown
### 上传文件

| 属性 | 值 |
|------|-----|
| 端点 | POST /attachments |
| Content-Type | multipart/form-data |

**请求**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 文件 |
| type | string | 是 | 文件类型 |

**成功响应 (201)**

```json
{
  "id": "uuid",
  "filename": "report.xlsx",
  "url": "https://cdn.example.com/xxx",
  "size": 102400,
  "mimeType": "application/...",
  "createdAt": "2024-12-23T02:30:00Z"
}
```

**错误响应**

| HTTP | 错误码 | 场景 |
|------|--------|------|
| 400 | VALIDATION_ERROR | 文件类型不支持 |
| 400 | FILE_TOO_LARGE | 文件超过限制 |
```

### 8.2 批量操作

```markdown
### 批量删除

| 属性 | 值 |
|------|-----|
| 端点 | POST /resources/batch-delete |
| 权限 | 管理员 |

**请求体**

```json
{
  "ids": ["uuid-1", "uuid-2", "uuid-3"]
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
        "code": "FORBIDDEN",
        "message": "无权限删除"
      }
    }
  ]
}
```
```

### 8.3 聚合查询

```markdown
### 获取统计摘要

| 属性 | 值 |
|------|-----|
| 端点 | GET /reports/summary |
| 权限 | supervisor+ |

**Query 参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dateFrom | string | 是 | 开始日期 |
| dateTo | string | 是 | 结束日期 |

**成功响应 (200)**

```json
{
  "totalCount": 365,
  "totalAmount": 500000.00,
  "averageAmount": 1369.86,
  "dateRange": {
    "from": "2024-01-01",
    "to": "2024-12-31"
  }
}
```
```

### 8.4 导出/下载

```markdown
### 导出报表

| 属性 | 值 |
|------|-----|
| 端点 | GET /reports/export |
| 权限 | supervisor+ |

**Query 参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| format | string | 是 | xlsx / csv |
| dateFrom | string | 是 | 开始日期 |
| dateTo | string | 是 | 结束日期 |

**成功响应**

- 小文件：直接返回文件流
  - Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
  - Content-Disposition: attachment; filename="report.xlsx"

- 大文件：返回下载链接
  ```json
  {
    "downloadUrl": "https://cdn.example.com/exports/xxx.xlsx",
    "expiresAt": "2024-12-24T02:30:00Z"
  }
  ```
```

---

## §9 边界条件完整清单

### 9.1 参数边界

| 类型 | 边界 | 超出处理 |
|------|------|----------|
| page | ≥1 | 400 错误 |
| pageSize | 1-100 | >100 自动设为100 |
| 字符串 | 见字段定义 | 400 错误 |
| 数组 | 见字段定义 | 400 错误 |
| 日期 | 合法日期 | 400 错误 |

### 9.2 业务边界

| 场景 | 处理 |
|------|------|
| 未来日期 | 400 FUTURE_DATE_NOT_ALLOWED |
| 重复记录 | 409 DUPLICATE_ENTRY |
| 状态不允许操作 | 400 INVALID_STATUS_TRANSITION |
| 已锁定 | 400 RESOURCE_LOCKED |

### 9.3 并发边界

| 场景 | 处理方式 |
|------|----------|
| 同时编辑 | 后者覆盖 或 409 CONFLICT |
| 删除已删除 | 404 或 204 |
| 创建重复 | 409 DUPLICATE_ENTRY |

---

## §10 文档引用

- 核心规则：API_SPEC_GUIDE_v2.0_CORE.md
- 完整示例：API_SPEC_EXAMPLES.md
- JSON Schema：API_SPEC_SCHEMAS.md
