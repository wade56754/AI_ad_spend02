# P2 阶段遗留项记录

> **文档用途**: 记录 P2 阶段未处理的遗留文件和待办事项
> **创建日期**: 2025-11-20
> **状态**: 待后续阶段处理

---

## 🔴 遗留文件：`app/api/v1/auth.py`

### 基本信息

| 项目 | 详情 |
|------|------|
| **文件路径** | `backend/app/api/v1/auth.py` |
| **文件状态** | 已标记为废弃，但**仍在使用中** |
| **认证方式** | 自建 JWT（旧版） |
| **创建时间** | P1 阶段之前 |
| **废弃标记** | P1 阶段添加（第 8-13 行） |

---

### 当前引用情况

#### ✅ 确认：仍在 `main.py` 中被引用

**引用位置**：
- **导入**：`app/main.py:18`
  ```python
  from app.api.v1.auth import router as auth_router
  ```
- **注册**：`app/main.py:252`
  ```python
  app.include_router(auth_router, prefix=settings.API_PREFIX)
  ```

**影响范围**：
- 该路由仍然对外提供服务
- 路由前缀：`{API_PREFIX}/auth`（如 `/api/v1/auth`）
- 包含的端点：
  - `POST /auth/login`
  - `POST /auth/refresh`
  - `POST /auth/logout`
  - `POST /auth/change-password`
  - `GET /auth/me`
  - `GET /auth/verify-token`

---

### 与新版认证的冲突情况

#### 🔄 路由冲突分析

| 端点 | 旧版路由（app/api/v1/auth.py） | 新版路由 | 冲突情况 |
|------|-------------------------------|----------|---------|
| GET /auth/me | ✅ 存在 | `app/routers/auth.py` ✅ 存在 | 🔴 **路由冲突** |
| - | - | `app/routers/me.py` (GET /me) | 🟢 无冲突（路径不同） |

**潜在问题**：
1. **路由冲突**：`GET /auth/me` 同时在 `app/api/v1/auth.py` 和 `app/routers/auth.py` 中定义
2. **认证方式不一致**：
   - 旧版：使用自建 JWT + `security_manager.verify_token()`
   - 新版：使用 Supabase Auth + `supabase_auth_service.verify_token()`
3. **响应格式不一致**：
   - 旧版：使用 `create_api_response()`，缺少 `request_id`
   - 新版：使用 `success_response()`，包含 `request_id`

---

### 文件内容概要

#### 提供的功能
```python
@router.post("/login")           # 用户登录（自建 JWT）
@router.post("/refresh")         # 刷新令牌
@router.post("/logout")          # 用户登出
@router.post("/change-password") # 修改密码
@router.get("/me")               # 获取当前用户信息
@router.get("/verify-token")     # 验证令牌有效性

# 依赖函数
async def get_current_user()     # ⚠️ 与 app/dependencies.py 同名但实现不同
async def get_current_admin_user() # 管理员权限检查
```

#### 使用的依赖
- `app.services.auth_service.AuthService` - 旧版认证服务
- `app.utils.security.security_manager` - 旧版安全管理器（自建 JWT）
- `app.schemas.user.*` - 用户数据模式
- `app.utils.response.create_api_response` - 旧版响应格式

---

### 与 AUTH_SPEC.md 规范的冲突

#### ❌ 违反规范的地方

1. **认证方式**（违反 AUTH_SPEC.md 第 2.2 节）
   - 规范要求：使用 Supabase Auth
   - 当前实现：使用自建 JWT + `security_manager`

2. **密码存储**（违反 AUTH_SPEC.md 第 2.1 节）
   - 规范要求：密码由 Supabase Auth 管理，业务数据库不存储
   - 当前实现：使用 `auth_service.authenticate_user()` 验证本地密码

3. **角色来源**（违反 AUTH_SPEC.md 第 3.2 节）
   - 规范要求：角色必须从 users 表查询
   - 当前实现：虽然也从 users 表查询，但使用旧的认证服务

---

### 推荐处理方案

#### 方案 A：逐步迁移（推荐）

**执行阶段**：P2.5 或 P3

**步骤**：
1. **保留新旧路由并存**（当前状态）
   - 旧版：`/api/v1/auth/*`
   - 新版：`/api/v1/auth/me` 和 `/me`

2. **前端逐步切换**
   - 通知前端团队新版路由地址
   - 前端代码逐步从旧版切换到新版
   - 保留旧版路由一段时间（如 2 周）

3. **监控旧版路由使用情况**
   - 在 `app/api/v1/auth.py` 的每个端点添加日志
   - 记录调用次数和来源
   - 当调用次数降为 0 时，安全移除

4. **移除旧版路由**
   - 从 `main.py` 移除 `auth_router` 导入和注册
   - 删除或归档 `app/api/v1/auth.py` 文件
   - 更新文档

**优点**：
- ✅ 不破坏现有功能
- ✅ 给前端充足的迁移时间
- ✅ 可监控迁移进度

**缺点**：
- ❌ 需要维护两套代码一段时间
- ❌ 存在路由冲突风险

---

#### 方案 B：立即替换（高风险）

**执行阶段**：不推荐

**步骤**：
1. 从 `main.py` 移除旧版路由
2. 注册新版路由
3. 强制前端立即切换

**优点**：
- ✅ 快速清理遗留代码

**缺点**：
- ❌ 可能破坏前端现有功能
- ❌ 需要前端同步修改
- ❌ 高风险

---

#### 方案 C：路由隔离（临时方案）

**执行阶段**：立即可执行

**步骤**：
1. 修改旧版路由前缀
   ```python
   # main.py 第 252 行
   app.include_router(auth_router, prefix="/api/v1/auth-legacy")
   ```
2. 新版路由使用标准前缀
   ```python
   app.include_router(new_auth_router, prefix="/api/v1/auth")
   app.include_router(me_router, prefix="/api/v1")
   ```
3. 通知前端：
   - 旧版：`/api/v1/auth-legacy/*`（即将废弃）
   - 新版：`/api/v1/auth/*` 和 `/api/v1/me`

**优点**：
- ✅ 解决路由冲突
- ✅ 新旧版本明确分离
- ✅ 易于监控和切换

**缺点**：
- ❌ 仍需维护两套代码

---

### 建议的执行时间表

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| **P2.5** | 错误码统一，同时评估旧版路由使用情况 | 2-3 小时 |
| **P2.5 后** | 与前端团队沟通迁移计划 | 1 周 |
| **P3** | 前端切换到新版路由 | 2-4 周 |
| **P3 后** | 监控旧版路由调用（应为 0） | 1-2 周 |
| **P4** | 移除旧版路由和相关代码 | 1-2 小时 |

---

### 相关依赖清理

当 `app/api/v1/auth.py` 被移除后，以下文件可能也需要清理或重构：

| 文件 | 当前用途 | 处理方式 |
|------|----------|----------|
| `app/services/auth_service.py` | 旧版认证服务（自建 JWT） | ⚠️ 检查是否仍被其他地方使用，如无则删除 |
| `app/utils/security.py:SecurityManager` | 旧版安全管理器（自建 JWT） | ⚠️ 已标记为废弃，保留 SupabaseAuthService |
| `app/schemas/user.py:UserInDB` | 用户数据模式（曾包含 hashed_password） | ✅ P1 阶段已清理 hashed_password 字段 |

---

### 当前推荐的唯一认证入口

#### ✅ 新版认证路由（推荐使用）

| 端点 | 文件 | 认证方式 | 响应格式 | 包含 request_id |
|------|------|----------|----------|----------------|
| `GET /auth/me` | `app/routers/auth.py` | Supabase Auth | `success_response()` | ✅ 是 |
| `GET /me` | `app/routers/me.py` | Supabase Auth | `success_response()` | ✅ 是 |

**特点**：
- ✅ 符合 AUTH_SPEC.md 规范
- ✅ 使用 Supabase Auth（第三方认证）
- ✅ 角色从 users 表查询
- ✅ 统一响应格式（包含 `request_id`）
- ✅ P2.3/P2.4 阶段已完成修改

---

### 遗留项标记

| 优先级 | 类型 | 描述 | 建议处理阶段 |
|--------|------|------|-------------|
| 🔴 高 | 代码清理 | 移除 `app/api/v1/auth.py` 路由注册 | P2.5 或 P3 |
| 🟡 中 | 依赖清理 | 检查并清理旧版认证服务依赖 | P3 |
| 🟢 低 | 文档更新 | 更新 API 文档，标注废弃端点 | P2.5 |

---

## 📌 重要提醒

1. **不要立即删除代码**：在确认前端完全切换前，保留旧版路由
2. **监控使用情况**：添加日志记录旧版路由的调用情况
3. **通知前端团队**：提前沟通迁移计划和时间表
4. **保留回滚能力**：在移除前确保有回滚方案

---

## ✅ 结论

- **当前状态**：旧版认证路由仍在使用中，与新版路由存在冲突
- **风险评估**：中等（功能可用，但存在维护负担）
- **推荐方案**：方案 A（逐步迁移）或方案 C（路由隔离）
- **执行时机**：P2.5 阶段评估，P3 阶段执行
- **责任人**：后端团队协调前端团队完成迁移

---

**更新日期**: 2025-11-20
**下次审查**: P2.5 阶段开始时
