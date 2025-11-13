# 项目管理API使用指南

> **模块名称**: 项目管理 (Project Management)
> **API版本**: v1.0
> **文档版本**: 1.0
> **更新日期**: 2025-11-12
> **开发人员**: Claude协作开发

---

## 📋 概述

项目管理API提供了完整的项目生命周期管理功能，包括项目创建、更新、删除、成员管理、费用记录和统计分析等功能。支持基于角色的权限控制，确保数据安全和访问隔离。

### 核心特性
- ✅ **项目CRUD操作** - 创建、查询、更新、删除项目
- ✅ **成员管理** - 分配、移除项目成员
- ✅ **费用记录** - 管理项目相关费用
- ✅ **统计分析** - 项目数据统计和报表
- ✅ **权限控制** - 基于角色的细粒度权限
- ✅ **数据分页** - 大数据量分页查询支持

---

## 🔑 认证与授权

所有API端点都需要在请求头中包含有效的JWT访问令牌：

```
Authorization: Bearer <access_token>
```

### 权限矩阵

| 角色 | 创建 | 查看 | 更新 | 删除 | 成员管理 | 费用管理 | 统计查看 |
|------|------|------|------|------|----------|----------|----------|
| **admin** | ✅ | 全部 | ✅ | ✅ | ✅ | ✅ | ✅ |
| **finance** | ❌ | 只读 | ❌ | ❌ | ❌ | ❌ | ✅ |
| **data_operator** | ❌ | 只读 | ❌ | ❌ | ❌ | ❌ | ✅ |
| **account_manager** | ❌ | 自己的 | ✅ | ❌ | ✅ | ✅ | ❌ |
| **media_buyer** | ❌ | 参与的 | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 📚 API端点详情

### 1. 获取项目列表

获取项目列表，支持分页和过滤。

**请求**
```http
GET /api/v1/projects?page=1&page_size=20&status=active&client_name=客户A&manager_id=1
```

**查询参数**
| 参数 | 类型 | 必填 | 描述 | 示例 |
|------|------|------|------|------|
| page | integer | 否 | 页码，从1开始 | 1 |
| page_size | integer | 否 | 每页数量，1-100 | 20 |
| status | string | 否 | 项目状态过滤 | active |
| manager_id | integer | 否 | 按账户经理过滤 | 1 |
| client_name | string | 否 | 按客户名称过滤 | 客户A |

**响应**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "测试项目",
        "client_name": "客户A",
        "client_company": "客户公司A",
        "description": "项目描述",
        "status": "active",
        "budget": "10000.00",
        "currency": "USD",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "account_manager_id": 2,
        "account_manager_name": "张经理",
        "total_spent": "2500.00",
        "total_accounts": 5,
        "active_accounts": 4,
        "created_by": 1,
        "created_by_name": "管理员",
        "created_at": "2025-11-12T10:00:00Z",
        "updated_at": "2025-11-12T10:00:00Z"
      }
    ],
    "meta": {
      "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 50,
        "total_pages": 3
      }
    }
  },
  "message": "获取项目列表成功",
  "code": "SUCCESS",
  "request_id": "uuid",
  "timestamp": "2025-11-12T10:00:00Z"
}
```

---

### 2. 创建项目

创建新项目，仅管理员有权限。

**请求**
```http
POST /api/v1/projects
```

**请求体**
```json
{
  "name": "新项目名称",
  "client_name": "客户名称",
  "client_company": "客户公司",
  "description": "项目描述",
  "budget": "50000.00",
  "currency": "USD",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "account_manager_id": 2
}
```

**字段验证**
| 字段 | 类型 | 必填 | 验证规则 |
|------|------|------|----------|
| name | string | ✅ | 1-200字符，唯一性检查 |
| client_name | string | ✅ | 1-200字符 |
| client_company | string | ✅ | 1-200字符 |
| description | string | ❌ | 最大1000字符 |
| budget | decimal | ✅ | ≥ 0，2位小数 |
| currency | string | ❌ | 3位货币代码，默认USD |
| start_date | date | ❌ | ISO格式日期 |
| end_date | date | ❌ | 必须晚于start_date |

**成功响应 (201)**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "name": "新项目名称",
    "client_name": "客户名称",
    "status": "planning",
    "budget": "50000.00",
    "created_at": "2025-11-12T10:00:00Z"
  },
  "message": "项目创建成功",
  "code": "SUCCESS"
}
```

**错误响应**
```json
{
  "success": false,
  "error": {
    "code": "BIZ_101",
    "message": "项目名称已存在"
  }
}
```

---

### 3. 获取项目详情

获取指定项目的详细信息。

**请求**
```http
GET /api/v1/projects/{project_id}
```

**路径参数**
| 参数 | 类型 | 描述 |
|------|------|------|
| project_id | integer | 项目ID |

**响应**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "项目详情",
    "client_name": "客户B",
    "client_company": "客户公司B",
    "description": "详细的项目描述",
    "status": "active",
    "budget": "10000.00",
    "currency": "USD",
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "account_manager_id": 2,
    "account_manager_name": "李经理",
    "total_spent": "3500.00",
    "total_accounts": 10,
    "active_accounts": 8,
    "created_by": 1,
    "created_by_name": "管理员",
    "created_at": "2025-11-10T08:00:00Z",
    "updated_at": "2025-11-12T09:30:00Z"
  },
  "message": "获取项目详情成功"
}
```

---

### 4. 更新项目

更新项目信息，管理员和账户管理员有权限。

**请求**
```http
PUT /api/v1/projects/{project_id}
```

**请求体**
```json
{
  "name": "更新后的项目名",
  "client_name": "更新后的客户",
  "status": "active",
  "budget": "60000.00",
  "account_manager_id": 3
}
```

**响应**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "更新后的项目名",
    "client_name": "更新后的客户",
    "status": "active",
    "budget": "60000.00",
    "updated_at": "2025-11-12T11:00:00Z"
  },
  "message": "项目更新成功"
}
```

---

### 5. 删除项目

删除项目，仅管理员有权限。

**请求**
```http
DELETE /api/v1/projects/{project_id}
```

**响应 (204)**
无内容返回

---

### 6. 分配项目成员

为项目分配成员，管理员和账户管理员有权限。

**请求**
```http
POST /api/v1/projects/{project_id}/members
```

**请求体**
```json
{
  "user_id": 5,
  "role": "media_buyer"
}
```

**字段说明**
| 字段 | 类型 | 可选值 |
|------|------|--------|
| user_id | integer | 用户ID |
| role | string | account_manager, media_buyer, analyst |

**响应**
```json
{
  "success": true,
  "data": {
    "id": 10,
    "user_id": 5,
    "user_name": "王投手",
    "user_email": "buyer@example.com",
    "user_role": "media_buyer",
    "project_role": "media_buyer",
    "joined_at": "2025-11-12T10:00:00Z"
  },
  "message": "成员分配成功"
}
```

---

### 7. 获取项目成员列表

获取项目的所有成员。

**请求**
```http
GET /api/v1/projects/{project_id}/members
```

**响应**
```json
{
  "success": true,
  "data": [
    {
      "id": 10,
      "user_id": 5,
      "user_name": "王投手",
      "user_email": "buyer@example.com",
      "user_role": "media_buyer",
      "project_role": "media_buyer",
      "joined_at": "2025-11-12T10:00:00Z"
    },
    {
      "id": 11,
      "user_id": 6,
      "user_name": "李分析",
      "user_email": "analyst@example.com",
      "user_role": "analyst",
      "project_role": "analyst",
      "joined_at": "2025-11-12T11:00:00Z"
    }
  ],
  "message": "获取项目成员列表成功"
}
```

---

### 8. 移除项目成员

从项目中移除成员。

**请求**
```http
DELETE /api/v1/projects/{project_id}/members/{user_id}
```

**响应 (204)**
无内容返回

---

### 9. 添加项目费用

为项目添加费用记录。

**请求**
```http
POST /api/v1/projects/{project_id}/expenses
```

**请求体**
```json
{
  "expense_type": "media_spend",
  "amount": "1500.00",
  "description": "Facebook广告费",
  "expense_date": "2025-11-12"
}
```

**字段说明**
| 字段 | 类型 | 可选值 |
|------|------|--------|
| expense_type | string | media_spend, service_fee, other |
| amount | decimal | > 0，2位小数 |
| expense_date | date | ISO格式日期 |

**响应**
```json
{
  "success": true,
  "data": {
    "id": 20,
    "expense_type": "media_spend",
    "amount": "1500.00",
    "description": "Facebook广告费",
    "expense_date": "2025-11-12",
    "created_by_name": "张经理",
    "created_at": "2025-11-12T12:00:00Z"
  },
  "message": "费用添加成功"
}
```

---

### 10. 获取项目费用列表

获取项目的费用记录，支持分页。

**请求**
```http
GET /api/v1/projects/{project_id}/expenses?page=1&page_size=20
```

**响应**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 20,
        "expense_type": "media_spend",
        "amount": "1500.00",
        "description": "Facebook广告费",
        "expense_date": "2025-11-12",
        "created_by_name": "张经理",
        "created_at": "2025-11-12T12:00:00Z"
      }
    ],
    "meta": {
      "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 15,
        "total_pages": 1
      }
    }
  },
  "message": "获取费用列表成功"
}
```

---

### 11. 获取项目统计

获取项目统计数据，仅管理员、财务、数据员有权限。

**请求**
```http
GET /api/v1/projects/statistics
```

**响应**
```json
{
  "success": true,
  "data": {
    "total_projects": 100,
    "active_projects": 45,
    "paused_projects": 10,
    "completed_projects": 40,
    "cancelled_projects": 5,
    "total_budget": "5000000.00",
    "total_spent": "2500000.00",
    "total_clients": 80,
    "avg_project_value": "50000.00",
    "top_performers": [
      {
        "project_id": 1,
        "project_name": "高绩效项目",
        "client_name": "优质客户",
        "roi": 5.5,
        "spent_percentage": 85.5
      }
    ]
  },
  "message": "获取统计信息成功"
}
```

---

## ⚠️ 错误码说明

| 错误码 | HTTP状态码 | 描述 | 解决方案 |
|--------|------------|------|----------|
| SYS_004 | 404 | 资源不存在 | 检查项目ID是否正确 |
| BIZ_101 | 400 | 项目名称已存在 | 使用不同的项目名称 |
| BIZ_102 | 422 | 项目状态转换无效 | 检查状态转换规则 |
| BIZ_103 | 400 | 结束日期无效 | 确保结束日期晚于开始日期 |
| BIZ_104 | 403 | 无权限操作项目 | 检查用户角色和权限 |
| BIZ_105 | 400 | 预算不能为负 | 预算必须≥0 |
| BIZ_106 | 400 | 有关联数据不能删除 | 先删除关联的广告账户 |
| VALIDATION_ERROR | 422 | 参数验证失败 | 检查请求参数格式 |

---

## 🔧 使用示例

### Python示例

```python
import httpx

# 配置
BASE_URL = "http://localhost:8000"
TOKEN = "your_access_token_here"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 创建项目
project_data = {
    "name": "我的新项目",
    "client_name": "测试客户",
    "client_company": "测试公司",
    "budget": "10000.00"
}

response = httpx.post(
    f"{BASE_URL}/api/v1/projects",
    json=project_data,
    headers=headers
)

if response.status_code == 201:
    project = response.json()["data"]
    print(f"项目创建成功，ID: {project['id']}")
else:
    print(f"创建失败: {response.json()}")

# 获取项目列表
response = httpx.get(
    f"{BASE_URL}/api/v1/projects",
    headers=headers,
    params={"page": 1, "page_size": 10, "status": "active"}
)

if response.status_code == 200:
    projects = response.json()["data"]["items"]
    print(f"找到 {len(projects)} 个活跃项目")
```

### cURL示例

```bash
# 创建项目
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API测试项目",
    "client_name": "测试客户",
    "client_company": "测试公司",
    "budget": "50000.00"
  }'

# 获取项目列表
curl -X GET "http://localhost:8000/api/v1/projects?status=active&page=1&page_size=20" \
  -H "Authorization: Bearer <token>"

# 获取项目统计
curl -X GET http://localhost:8000/api/v1/projects/statistics \
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

// 创建项目
async function createProject(projectData) {
  const response = await fetch(`${BASE_URL}/api/v1/projects`, {
    method: "POST",
    headers,
    body: JSON.stringify(projectData)
  });

  if (response.ok) {
    const result = await response.json();
    console.log("项目创建成功:", result.data);
    return result.data;
  } else {
    const error = await response.json();
    console.error("创建失败:", error);
  }
}

// 获取项目列表
async function getProjects(filters = {}) {
  const params = new URLSearchParams(filters);
  const response = await fetch(
    `${BASE_URL}/api/v1/projects?${params}`,
    { headers }
  );

  if (response.ok) {
    const result = await response.json();
    return result.data.items;
  }
}
```

---

## 📈 性能指标

| 操作 | 响应时间 (P95) | 并发支持 | 限制 |
|------|----------------|----------|------|
| 列表查询 | < 300ms | 100 | 最大100条/页 |
| 创建项目 | < 200ms | 50 | - |
| 更新项目 | < 150ms | 50 | - |
| 获取统计 | < 500ms | 30 | - |
| 费用查询 | < 200ms | 100 | 最大100条/页 |

---

## 🔍 最佳实践

1. **分页查询**
   - 使用合理的分页大小（建议20-50）
   - 避免请求过大的页码

2. **状态管理**
   - 遵循项目状态流转规则
   - 避免非法状态转换

3. **权限控制**
   - 前端应根据用户角色控制功能显示
   - 后端始终进行权限验证

4. **错误处理**
   - 根据错误码进行适当的错误处理
   - 提供友好的错误提示

5. **数据验证**
   - 客户端先进行基本验证
   - 不要信任服务端的响应结构

---

## 🆘 故障排除

### 常见问题

**Q: 创建项目时返回403错误？**
A: 检查用户是否为admin角色，只有管理员可以创建项目。

**Q: 无法查看某些项目？**
A: 确认用户是否有权限访问该项目，账户管理员只能查看自己管理的项目。

**Q: 更新项目失败？**
A: 确认用户是否为admin或account_manager，且项目由该账户管理员管理。

**Q: 分配成员失败？**
A: 检查用户是否已存在，每个用户在每个项目中只能有一个角色。

---

## 📞 技术支持

- **文档**: [开发文档中心](../)
- **问题反馈**: [GitHub Issues](https://github.com/your-org/ai_ad_spend02/issues)
- **技术支持**: dev-team@your-domain.com

---

**文档维护**: 开发团队
**最后更新**: 2025-11-12
**版本**: v1.0