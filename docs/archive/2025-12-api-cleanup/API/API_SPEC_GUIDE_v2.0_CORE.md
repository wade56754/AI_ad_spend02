# API 规格书编写指南 v2.0

> **文档定位**: 指导 AI 编写 API 规格书的强制规范
> **分层设计**: 核心层（必读） + 详细层（按需） + 示例层（参考）
> **本文件**: 🔴 核心层 - AI 必须完整读取

---

## 快速索引

| 我要查... | 跳转 |
|-----------|------|
| 字段命名 | §1 标准字段名 |
| HTTP 方法选择 | §2 决策规则 |
| 状态码选择 | §2 决策规则 |
| 禁止事项 | §3 禁止清单 |
| 错误码 | §4 错误码清单 |
| 自检 | §6 自检清单 |
| 常见错误修复 | §5 错误模式 |
| 完整示例 | → API_SPEC_EXAMPLES.md |
| 详细规范 | → API_SPEC_DETAILED.md |

---

## §1 标准字段名（强制）

> ⚠️ 必须使用以下名称，禁止自创

### 1.1 通用字段

| 含义 | ✅ 必须用 | ❌ 禁止用 |
|------|----------|----------|
| 主键 | `id` | ID, _id, uuid |
| 创建时间 | `createdAt` | created_at, createTime |
| 更新时间 | `updatedAt` | updated_at, updateTime |
| 创建人 | `createdBy` | created_by, creator |
| 更新人 | `updatedBy` | updated_by, updater |
| 删除时间 | `deletedAt` | deleted_at, deleteTime |

### 1.2 分页字段

| 含义 | ✅ 必须用 | ❌ 禁止用 |
|------|----------|----------|
| 页码 | `page` | pageNum, p, pageNo |
| 每页数量 | `pageSize` | page_size, limit, size |
| 总记录数 | `total` | count, totalCount |
| 总页数 | `totalPages` | total_pages, pageCount |

### 1.3 筛选字段

| 含义 | ✅ 必须用 | ❌ 禁止用 |
|------|----------|----------|
| 排序字段 | `sortBy` | sort_by, orderBy |
| 排序方向 | `sortOrder` | sort_order, order |
| 关键词 | `keyword` | keywords, search, q |
| 开始日期 | `dateFrom` | date_from, startDate |
| 结束日期 | `dateTo` | date_to, endDate |

### 1.4 命名模式

| 类型 | 模式 | 示例 |
|------|------|------|
| 外键 | {资源}Id | projectId, userId |
| 嵌套对象 | {资源} | project, user |
| 数组 | {资源}s | projects, users |
| 布尔-状态 | is{形容词} | isActive, isDeleted |
| 布尔-拥有 | has{名词} | hasChildren |
| 布尔-权限 | can{动词} | canEdit, canDelete |

---

## §2 决策规则（强制）

> ⚠️ 遇到选择时，按此表决定

### 2.1 HTTP 方法

| 场景 | ✅ 必须 | ❌ 禁止 |
|------|--------|--------|
| 获取列表/详情 | GET | POST |
| 创建资源 | POST | PUT |
| 部分更新 | PATCH | PUT |
| 完整替换 | PUT | PATCH |
| 删除资源 | DELETE | POST |
| 执行操作 | POST /{id}/action | GET |
| 批量操作 | POST /batch-xxx | GET |

### 2.2 HTTP 状态码

| 场景 | ✅ 必须返回 |
|------|------------|
| GET 成功 | 200 |
| POST 创建成功 | 201 |
| DELETE 成功 | 204 |
| PATCH/PUT 成功 | 200 |
| 操作执行成功 | 200 |
| 参数验证失败 | 400 |
| 未登录/Token无效 | 401 |
| 已登录但无权限 | 403 |
| 资源不存在 | 404 |
| 资源冲突/重复 | 409 |
| 服务器错误 | 500 |

### 2.3 空值处理

| 场景 | ✅ 正确处理 |
|------|------------|
| 列表为空 | `{ "items": [], "pagination": {...} }` + 200 |
| 资源不存在 | 404 错误 |
| 可选字段无值 | 不返回该字段 或 返回 null |
| 数组字段无值 | 返回 `[]`，不返回 null |

### 2.4 URL 命名

| 规则 | ✅ 正确 | ❌ 错误 |
|------|--------|--------|
| 使用 kebab-case | /daily-reports | /dailyReports |
| 使用复数 | /projects | /project |
| 最多2层嵌套 | /projects/:id/members | /a/:id/b/:id/c |

---

## §3 禁止清单（红线）

> 🔴 违反任何一条即为不合格

### 3.1 命名禁止

```
❌ 禁止 snake_case 字段名
   错误: { "project_id": "xxx" }
   正确: { "projectId": "xxx" }

❌ 禁止非标准字段名
   错误: { "create_time": "xxx" }
   正确: { "createdAt": "xxx" }

❌ 禁止中文字段名
   错误: { "项目名": "xxx" }
   正确: { "projectName": "xxx" }
```

### 3.2 设计禁止

```
❌ 禁止 GET 请求带请求体
   错误: GET /reports { "filter": {} }
   正确: GET /reports?status=draft

❌ 禁止 URL 传敏感信息
   错误: GET /login?password=xxx
   正确: POST /login { "password": "xxx" }

❌ 禁止返回密码字段
   错误: { "password": "hashed..." }
   正确: 不返回 password 字段
```

### 3.3 状态码禁止

```
❌ 禁止 200 表示错误
   错误: 200 { "success": false, "error": "xxx" }
   正确: 400 { "error": { "code": "xxx" } }

❌ 禁止自创状态码
   错误: 返回 600, 700
   正确: 只用标准状态码
```

### 3.4 错误码禁止

```
❌ 禁止自创错误码
   错误: { "code": "MY_CUSTOM_ERROR" }
   正确: 从 §4 错误码清单选择

❌ 禁止中文错误码
   错误: { "code": "参数错误" }
   正确: { "code": "VALIDATION_ERROR" }
```

### 3.5 格式禁止

```
❌ 禁止非 ISO 8601 时间
   错误: "2024/12/23 10:30:00"
   正确: "2024-12-23T10:30:00Z"

❌ 禁止数组返回 null
   错误: { "items": null }
   正确: { "items": [] }
```

---

## §4 错误码清单（完整）

> ⚠️ 只能从此清单选择，禁止自创

### 4.1 通用错误码

| 错误码 | HTTP | 场景 |
|--------|------|------|
| VALIDATION_ERROR | 400 | 参数验证失败 |
| INVALID_REQUEST | 400 | 请求格式错误 |
| UNAUTHORIZED | 401 | 未登录/Token失效 |
| FORBIDDEN | 403 | 无权限 |
| NOT_FOUND | 404 | 资源不存在 |
| CONFLICT | 409 | 资源冲突 |
| TOO_MANY_REQUESTS | 429 | 请求频率超限 |
| INTERNAL_ERROR | 500 | 服务器错误 |

### 4.2 业务错误码

| 模块 | 错误码 | HTTP | 场景 |
|------|--------|------|------|
| 通用 | DUPLICATE_ENTRY | 409 | 重复记录 |
| 通用 | INVALID_STATUS_TRANSITION | 400 | 无效状态转换 |
| 日报 | FUTURE_DATE_NOT_ALLOWED | 400 | 未来日期 |
| 日报 | REPORT_LOCKED | 400 | 日报已锁定 |
| 项目 | PROJECT_NOT_ACTIVE | 400 | 项目未激活 |
| 项目 | NOT_PROJECT_MEMBER | 403 | 非项目成员 |
| 用户 | INVALID_CREDENTIALS | 401 | 凭证错误 |
| 用户 | USER_DISABLED | 403 | 用户已禁用 |
| 充值 | INSUFFICIENT_BALANCE | 400 | 余额不足 |
| 充值 | AMOUNT_EXCEEDS_LIMIT | 400 | 金额超限 |

### 4.3 新增错误码

如需新增，必须在规格书中标注：

```markdown
## 新增错误码申请
- 错误码: XXX_ERROR
- HTTP: 400
- 场景: {描述}
- 模块: {模块名}
⚠️ 待人工审核
```

---

## §5 错误模式识别与修复

> AI 完成编写后，对照此表自检修复

### 5.1 命名错误

| 错误特征 | 示例 | 修复方法 |
|----------|------|----------|
| 包含下划线 | `created_at` | → `createdAt` |
| 使用 limit | `limit: 20` | → `pageSize: 20` |
| 使用 offset | `offset: 0` | → `page: 1` |
| 使用 pageNum | `pageNum: 1` | → `page: 1` |
| 使用 orderBy | `orderBy: "id"` | → `sortBy: "id"` |

### 5.2 响应错误

| 错误特征 | 示例 | 修复方法 |
|----------|------|----------|
| 200+error | `200 {"error":...}` | → 使用 4xx 状态码 |
| 列表返回null | `{"items": null}` | → `{"items": []}` |
| 缺少分页 | `{"items": [...]}` | → 添加 pagination |
| 创建返回200 | `200 Created` | → `201 Created` |
| 删除返回200 | `200 Deleted` | → `204 No Content` |

### 5.3 时间格式错误

| 错误特征 | 示例 | 修复方法 |
|----------|------|----------|
| 斜杠分隔 | `2024/12/23` | → `2024-12-23` |
| 无时区 | `2024-12-23T10:30:00` | → 添加 `Z` |
| 本地时区 | `+08:00` | → 转换为 UTC `Z` |
| 非ISO格式 | `Dec 23, 2024` | → `2024-12-23` |

### 5.4 结构错误

| 错误特征 | 修复方法 |
|----------|----------|
| GET 带请求体 | 改用 Query 参数 |
| URL 超过2层嵌套 | 扁平化 URL |
| URL 用 camelCase | 改用 kebab-case |
| 缺少错误响应列表 | 补充可能的错误码 |

---

## §6 自检清单（必须完成）

> AI 输出 API 规格书前，逐项检查

### 6.1 优先级说明

| 标记 | 含义 | 违反后果 |
|------|------|----------|
| 🔴 P0 | 红线 | 直接不合格 |
| 🟡 P1 | 重要 | 需要修复 |
| 🟢 P2 | 建议 | 建议修复 |

### 6.2 检查清单

```markdown
## 🔴 P0 红线检查（全部通过才合格）

□ 无 snake_case 字段名
□ 无自创字段名（使用标准字段名）
□ 无自创错误码（使用清单错误码）
□ 无 GET 请求带请求体
□ 无 200 状态表示错误
□ 无非 ISO 8601 时间格式
□ 无数组返回 null
□ 无返回密码字段

## 🟡 P1 重要检查

□ 已对照后端模块规划书
□ 字段名与后端数据模型一致
□ 枚举值与后端状态机一致
□ 权限与后端权限矩阵一致
□ 每个端点有成功响应定义
□ 每个端点有错误响应列表
□ 每个端点有至少一个示例

## 🟢 P2 建议检查

□ URL 使用 kebab-case
□ 资源名使用复数
□ 有完整的分页定义
□ 有数据权限说明
```

---

## §7 响应格式模板

### 7.1 成功-单个对象

```json
{
  "id": "uuid",
  "name": "示例",
  "status": "active",
  "createdAt": "2024-12-23T02:30:00Z"
}
```

### 7.2 成功-列表

```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "total": 100,
    "totalPages": 5
  }
}
```

### 7.3 成功-无内容

```
204 No Content
（空响应体）
```

### 7.4 错误响应

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数验证失败",
    "details": {
      "date": ["日期格式错误"],
      "amount": ["必须大于0"]
    }
  }
}
```

---

## §8 端点定义模板

```markdown
### X.X {操作名称}

| 属性 | 值 |
|------|-----|
| 端点 | {METHOD} {path} |
| 描述 | {描述} |
| 权限 | {角色} |

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| xxx | string | 是 | xxx |

**请求体**（POST/PATCH/PUT）

```typescript
interface XxxRequest {
  field1: string;   // 必填，说明
  field2?: number;  // 可选，说明
}
```

**成功响应** {状态码}

```typescript
interface XxxResponse {
  id: string;
}
```

**错误响应**

| HTTP | 错误码 | 场景 |
|------|--------|------|
| 400 | VALIDATION_ERROR | 参数错误 |
| 404 | NOT_FOUND | 不存在 |

**示例**

请求:
```http
POST /api/v1/xxx
{ "field1": "value" }
```

响应:
```json
{ "id": "uuid" }
```
```

---

## §9 与后端对照规则

### 9.1 对照关系

| 后端规划书 | API规格书 | 一致性要求 |
|------------|-----------|------------|
| §2 数据模型 | §数据类型 | 字段名(camelCase) |
| §3 API设计 | §端点详情 | 路径、方法 |
| §4 权限控制 | 权限说明 | 7角色矩阵 |
| §5.1 状态机 | 枚举定义 | 状态值 |
| §5.2 验证规则 | 字段验证 | 规则一致 |

### 9.2 编写流程

```
1. 先读取后端模块规划书
2. 提取字段定义（转 camelCase）
3. 提取端点定义
4. 提取权限矩阵
5. 提取状态枚举
6. 编写 API 规格书
7. 对照检查一致性
```

---

## 文档导航

| 文件 | 内容 | 何时读取 |
|------|------|----------|
| **本文件** | 核心规则 | 🔴 必须读取 |
| API_SPEC_DETAILED.md | 详细规范 | 按需读取 |
| API_SPEC_EXAMPLES.md | 完整示例 | 参考查阅 |
| API_SPEC_SCHEMAS.md | JSON Schema | 自动验证 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-23 | 初始版本 |
| v1.1 | 2025-12-23 | 增加防幻觉机制 |
| v2.0 | 2025-12-23 | 分层重构：核心层+详细层+示例层 |
