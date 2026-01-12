# 仪表盘加载失败诊断指南

## 问题现象

仪表盘加载失败，显示错误信息：
- "加载仪表盘失败"
- "CEO 驾驶舱仅限老板和管理员访问"
- "当前用户角色可能没有访问权限，请联系系统管理员"

## 可能原因

### 1. 用户未登录或 Token 无效

**症状**：
- API 返回 401 错误
- 错误码：`AUTH_400` 或 `AUTH_401`

**检查方法**：
1. 打开浏览器开发者工具（F12）
2. 查看 Network 标签页
3. 找到 `/api/v1/dashboards/ceo/v3/overview` 请求
4. 查看 Response 状态码和内容

**解决方案**：
1. 重新登录系统
2. 检查 localStorage 中是否有 `auth-token`
3. 清除浏览器缓存和 localStorage，重新登录

### 2. 用户角色权限不足

**症状**：
- API 返回 403 错误
- 错误码：`PERMISSION_DENIED`
- 后端日志显示：`denied access to CEO dashboard`

**检查方法**：
1. 查看后端日志中的 `CEO dashboard access check` 信息
2. 确认用户的实际角色值
3. 检查用户角色是否为 `admin` 或 `ceo`

**解决方案**：
1. 使用管理员账号登录（`admin@test.local` / `admin123456`）
2. 或者将用户角色更新为 `admin`

### 3. API 路径不匹配

**症状**：
- API 返回 404 错误
- 错误信息：`Not Found`

**检查方法**：
1. 确认前端调用的 API 路径：`/api/v1/dashboards/ceo/v3/overview`
2. 确认后端路由定义：`/ceo/v3/overview`（在 `/dashboards` 前缀下）

**解决方案**：
- 路径应该是正确的，如果出现 404，检查后端路由注册

### 4. 前端构建错误

**症状**：
- 页面显示构建错误
- 控制台有 TypeScript 或导入错误

**检查方法**：
1. 查看浏览器控制台错误
2. 检查前端构建日志

**解决方案**：
- 运行 `npm run build` 检查构建错误
- 修复所有 TypeScript 错误

## 诊断步骤

### Step 1: 检查用户登录状态

```javascript
// 在浏览器控制台执行
console.log('Token:', localStorage.getItem('auth-token'));
console.log('User:', localStorage.getItem('auth-user'));
```

### Step 2: 检查 API 请求

1. 打开浏览器开发者工具（F12）
2. 切换到 Network 标签页
3. 刷新仪表盘页面
4. 找到 `/api/v1/dashboards/ceo/v3/overview` 请求
5. 查看：
   - Request Headers 中的 `Authorization` 字段
   - Response 状态码
   - Response Body 内容

### Step 3: 检查后端日志

查看后端日志中的权限检查信息：
```
CEO dashboard access check: user_id=..., email=..., user_role=..., allowed_roles=['admin', 'ceo']
```

### Step 4: 测试 API 端点

使用管理员账号登录后，在浏览器控制台执行：

```javascript
const token = localStorage.getItem('auth-token');
fetch('http://localhost:8000/api/v1/dashboards/ceo/v3/overview', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(r => r.json())
.then(console.log)
.catch(console.error);
```

## 常见错误码

| 错误码 | 含义 | 解决方案 |
|--------|------|----------|
| `AUTH_400` | 未提供认证令牌 | 重新登录 |
| `AUTH_401` | 认证令牌无效或过期 | 重新登录 |
| `PERMISSION_DENIED` | 权限不足 | 使用管理员账号或更新用户角色 |
| `404` | API 路径不存在 | 检查路由注册 |

## 快速修复

### 方案 1: 使用管理员账号

1. 退出当前账号
2. 使用管理员账号登录：
   - 邮箱：`admin@test.local`
   - 密码：`admin123456`

### 方案 2: 更新用户角色

如果当前用户需要访问 CEO 仪表盘，可以更新用户角色为 `admin`：

```python
# 在数据库中执行
UPDATE users SET role = 'admin' WHERE email = 'your-email@example.com';
```

### 方案 3: 清除缓存重新登录

1. 清除浏览器缓存和 localStorage
2. 重新登录系统
3. 再次访问仪表盘

## 相关文件

- `backend/routers/dashboard.py` - CEO 仪表盘路由和权限检查
- `frontend/src/features/dashboard/components/CEODashboardV3.tsx` - 前端仪表盘组件
- `frontend/src/features/dashboard/hooks/useDashboardData.ts` - 数据获取 Hook
- `frontend/src/lib/api.ts` - API 客户端和错误处理

## 更新日期

2026-01-12

