---
version: v1.0
status: ready_for_production
layer: dev-guide
owner: wade
last_reviewed: 2025-11-27
baseline: MASTER.md v4.4, SoT Freeze v2.6
---

# AI广告代投系统 - 故障排查指南（Troubleshooting Guide）

> **适用范围**: 全栈开发者、运维人员、测试工程师
> **文档定位**: 系统问题诊断与恢复操作手册

---

## 📌 文档说明

本文档基于以下SoT文档编写，所有错误码、状态机、业务规则严格对齐：

- **ERROR_CODES_SOT.md** v2.1 - 错误码定义
- **STATE_MACHINE.md** v2.6 - 8状态流程
- **AUTH_SPEC.md** v2.0 - 认证授权规范
- **API_SOT.md** v9.0 - API契约规范
- **MASTER.md** v3.4 - 数据库不变式（INV-001/002/003）

---

## 目录

1. [快速诊断流程](#1-快速诊断流程)
2. [错误码参考速查表](#2-错误码参考速查表)
3. [认证授权问题（AUTH-*）](#3-认证授权问题auth)
4. [状态机问题（STATE-*）](#4-状态机问题state)
5. [业务逻辑问题（BIZ-*）](#5-业务逻辑问题biz)
6. [参数验证问题（VALIDATION-*）](#6-参数验证问题validation)
7. [系统错误（SYS-*）](#7-系统错误sys)
8. [数据库问题（DB-*）](#8-数据库问题db)
9. [趋势风控问题（TREND-*）](#9-趋势风控问题trend)
10. [不变式违反问题（INV-*）](#10-不变式违反问题inv)
11. [性能问题诊断](#11-性能问题诊断)
12. [数据库连接问题](#12-数据库连接问题)
13. [API契约违反问题](#13-api契约违反问题)
14. [前端常见问题](#14-前端常见问题)
15. [日志分析模式](#15-日志分析模式)
16. [恢复操作手册](#16-恢复操作手册)

---

## 1. 快速诊断流程

### 1.1 诊断决策树

```
用户报告问题
    ↓
[1] 检查请求日志（request_id）
    ├─ 有日志 → 提取error.code → 参考第2章错误码速查表
    └─ 无日志 → 检查网络连接 → 参考第12章数据库连接问题
    ↓
[2] 根据错误码前缀分类
    ├─ AUTH_* → 第3章认证授权问题
    ├─ STATE_* → 第4章状态机问题
    ├─ BIZ_* → 第5章业务逻辑问题
    ├─ VALIDATION_* → 第6章参数验证问题
    ├─ SYS_* → 第7章系统错误
    ├─ DB_* → 第8章数据库问题
    └─ TREND_* → 第9章趋势风控问题
    ↓
[3] 定位具体问题
    └─ 参考具体章节的"症状→诊断→解决"流程
    ↓
[4] 应用恢复操作
    └─ 参考第16章恢复操作手册
```

### 1.2 日志查询命令

```bash
# 查询指定request_id的完整请求链路
grep "550e8400-e29b-41d4-a716-446655440000" logs/app.log

# 查询最近100条错误日志
tail -n 100 logs/app.log | grep "ERROR"

# 查询特定错误码的所有出现
grep "AUTH_500" logs/app.log | tail -n 50

# 查询特定用户的操作日志
grep "user_id=550e8400" logs/app.log | tail -n 50

# 查询数据库慢查询日志（超过1秒）
grep "duration > 1000" logs/db.log
```

---

## 2. 错误码参考速查表

> **引用**: ERROR_CODES_SOT.md v2.1

### 2.1 认证授权类（AUTH_*）

| 错误码 | HTTP | 消息 | 常见场景 | 快速修复 |
|--------|------|------|----------|----------|
| `AUTH_001` | 401 | 用户名或密码错误 | 登录失败 | 检查用户名/密码拼写 |
| `AUTH_002` | 403 | 账户已被禁用 | `is_active=false` | 联系admin启用账户 |
| `AUTH_003` | 401 | 令牌已被撤销 | Token失效 | 重新登录获取新Token |
| `AUTH_004` | 404 | 用户不存在 | 用户记录缺失 | 检查users表数据 |
| `AUTH_400` | 401 | 未提供认证令牌 | 缺少Authorization头 | 添加`Authorization: Bearer <token>` |
| `AUTH_401` | 401 | 无效的认证令牌 | Token格式错误 | 检查Token格式是否正确 |
| `AUTH_402` | 401 | 令牌已过期 | Token超过1小时 | 刷新Token或重新登录 |
| `AUTH_500` | 403 | 权限不足 | 角色不满足要求 | 检查用户角色是否正确 |

### 2.2 状态机类（STATE_*）

| 错误码 | HTTP | 消息 | 常见场景 | 快速修复 |
|--------|------|------|----------|----------|
| `STATE_400` | 400 | 非法状态流转 | 不在白名单的流转 | 查阅STATE_MACHINE.md白名单 |
| `STATE_401` | 400 | 跳过必要步骤 | 跳过审批流程 | 按正确流程操作 |
| `STATE_402` | 400 | 终态非法回退 | 终态→非终态（非admin） | 使用admin账号或禁止回退 |
| `STATE_403` | 403 | 系统无权限流转 | system尝试禁止操作 | 检查自动化逻辑 |
| `STATE_405` | 400 | 绝对禁止的流转 | 已完成充值回退 | 使用红冲机制修正 |
| `STATE_409` | 409 | 并发冲突 | version不匹配 | 重新查询最新数据后重试 |

### 2.3 业务逻辑类（BIZ_*）

| 错误码 | HTTP | 消息 | 常见场景 | 快速修复 |
|--------|------|------|----------|----------|
| `BIZ_001` | 400 | 无效的操作 | SOD规则违反 | 更换审核人 |
| `BIZ_002` | 404 | 资源不存在 | ID查询失败 | 检查资源ID是否正确 |
| `BIZ_003` | 409 | 资源已存在 | 唯一约束冲突 | 检查重复数据 |
| `BIZ_100` | 400 | 金额无效 | 负数或零 | 确保金额>0且格式正确 |
| `BIZ_101` | 400 | 余额不足 | 项目余额不足 | 发起充值申请 |
| `BIZ_200` | 400 | 日期范围无效 | 开始>结束 | 检查日期逻辑 |
| `BIZ_201` | 400 | 日期不能为未来 | 日报日期>今天 | 修改为今天或之前 |
| `BIZ_300` | 400 | 状态无效 | 枚举值不存在 | 检查STATE_MACHINE.md |
| `BIZ_301` | 400 | 状态转换不允许 | 违反状态机规则 | 查阅状态流转白名单 |

### 2.4 参数验证类（VALIDATION_*）

| 错误码 | HTTP | 消息 | 常见场景 | 快速修复 |
|--------|------|------|----------|----------|
| `VALIDATION_001` | 400 | 必填字段缺失 | Pydantic校验失败 | 补充缺失字段 |
| `VALIDATION_002` | 400 | 格式无效 | 日期/金额格式错误 | 检查字段格式 |
| `VALIDATION_003` | 400 | 邮箱格式无效 | 邮箱不符合规范 | 修改为标准邮箱格式 |

### 2.5 系统错误类（SYS_*）

| 错误码 | HTTP | 消息 | 常见场景 | 快速修复 |
|--------|------|------|----------|----------|
| `SYS_001` | 500 | 系统内部错误 | 未捕获异常 | 查看日志定位问题 |
| `SYS_002` | 503 | 服务暂时不可用 | 服务过载/维护 | 稍后重试或联系运维 |

### 2.6 数据库类（DB_*）

| 错误码 | HTTP | 消息 | 常见场景 | 快速修复 |
|--------|------|------|----------|----------|
| `DB_004` | 409 | 唯一性约束违反 | UNIQUE冲突 | 检查重复数据 |

### 2.7 趋势风控类（TREND_*）

| 错误码 | HTTP | 消息 | 常见场景 | 快速修复 |
|--------|------|------|----------|----------|
| `TREND_001` | 200 | 趋势风控触发 | TF-001/002/003规则 | 运营复核确认 |
| `TREND_002` | 400 | 风控复核未完成 | trend_flagged跳过 | 完成复核后继续 |
| `TREND_010` | 400 | 复核原因缺失 | trend_resolution_note为空 | 填写复核说明 |

---

## 3. 认证授权问题（AUTH-*）

> **引用**: AUTH_SPEC.md v2.0, ERROR_CODES_SOT.md v2.1 4.1节

### 3.1 AUTH_001: 用户名或密码错误

#### 症状
```json
{
  "success": false,
  "error": {
    "code": "AUTH_001",
    "message": "用户名或密码错误"
  }
}
```

#### 诊断步骤
```bash
# 1. 检查用户是否存在
psql -d ai_ad_spend -c "SELECT id, username, email, is_active FROM users WHERE email='user@example.com';"

# 2. 检查Supabase Auth记录
# 登录Supabase Dashboard → Authentication → Users

# 3. 检查密码复杂度要求（AUTH_SPEC.md 3.1）
# - 最少8位
# - 至少包含1个数字、1个字母
```

#### 解决方案

**场景1: 密码确实错误**
```bash
# 重置密码（使用Supabase Dashboard或API）
# 1. 登录Supabase Dashboard
# 2. Authentication → Users → 选择用户 → Reset password
```

**场景2: 用户在auth.users但不在users表**
```sql
-- 同步users表
INSERT INTO users (id, username, full_name, email, role, is_active)
SELECT
    au.id,
    split_part(au.email, '@', 1) AS username,
    au.raw_user_meta_data->>'full_name' AS full_name,
    au.email,
    'media_buyer' AS role,
    true AS is_active
FROM auth.users au
WHERE NOT EXISTS (
    SELECT 1 FROM users u WHERE u.id = au.id
);
```

#### 预防措施
- 用户注册后立即同步users表
- 实施密码策略提示（前端验证）
- 记录登录失败审计日志

---

### 3.2 AUTH_400: 未提供认证令牌

#### 症状
```json
{
  "success": false,
  "error": {
    "code": "AUTH_400",
    "message": "未提供认证令牌"
  }
}
```

#### 诊断步骤
```bash
# 检查请求头
curl -v https://api.example.com/api/v1/projects

# 应该看到：
# > GET /api/v1/projects HTTP/1.1
# > Authorization: Bearer eyJhbGc...  # 此行缺失时触发AUTH_400
```

#### 解决方案

**场景1: 前端未发送Token**
```typescript
// ❌ 错误：直接使用fetch
fetch('/api/v1/projects')

// ✅ 正确：使用apiFetch（自动注入Token）
import { apiFetch } from '@/lib/api';
const projects = await apiFetch('/api/v1/projects');
```

**场景2: Token存储失败**
```typescript
// 检查localStorage
console.log(localStorage.getItem('access_token'));

// 如果为null，重新登录
await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
});
```

**场景3: 后端未正确提取Token**
```python
# 检查FastAPI依赖注入
from fastapi.security import HTTPBearer

security = HTTPBearer()

@router.get("/projects")
async def get_projects(
    credentials: HTTPAuthorizationCredentials = Depends(security)  # 必须
):
    token = credentials.credentials
```

#### 预防措施
- 统一使用`lib/api.ts::apiFetch`
- 前端路由守卫检查Token
- 后端全局异常处理

---

### 3.3 AUTH_402: 令牌已过期

#### 症状
```json
{
  "success": false,
  "error": {
    "code": "AUTH_402",
    "message": "令牌已过期"
  }
}
```

#### 诊断步骤
```bash
# 1. 解码JWT Token（仅用于调试，生产禁止前端解析）
echo "eyJhbGc..." | base64 -d | jq .

# 输出示例：
# {
#   "sub": "550e8400-e29b-41d4-a716-446655440000",
#   "exp": 1705914000,  # Unix timestamp
#   "iat": 1705910400
# }

# 2. 检查当前时间
date +%s  # 1705920000 > exp → Token已过期
```

#### 解决方案

**自动刷新Token（推荐）**
```typescript
// lib/api.ts
export async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const { data: { session } } = await supabase.auth.getSession();

  if (!session) {
    window.location.href = '/login';
    throw new Error('未登录');
  }

  // 检查Token是否即将过期（剩余5分钟）
  const expiresAt = session.expires_at * 1000;
  if (Date.now() > expiresAt - 5 * 60 * 1000) {
    // 自动刷新
    const { data, error } = await supabase.auth.refreshSession();
    if (error) {
      window.location.href = '/login';
      throw error;
    }
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      'Authorization': `Bearer ${session.access_token}`,
      ...options?.headers
    }
  });

  return response.json();
}
```

**手动刷新Token**
```typescript
// 用户点击"刷新"按钮
const { data, error } = await supabase.auth.refreshSession();
if (error) {
  alert('刷新失败，请重新登录');
  window.location.href = '/login';
}
```

#### 预防措施
- 实施自动刷新机制（Token剩余5分钟时）
- 显示Token过期倒计时
- 后端增加Token延长策略（可选）

---

### 3.4 AUTH_500: 权限不足

#### 症状
```json
{
  "success": false,
  "error": {
    "code": "AUTH_500",
    "message": "权限不足"
  }
}
```

#### 诊断步骤
```sql
-- 1. 检查用户角色
SELECT id, username, role FROM users WHERE id = '550e8400-e29b-41d4-a716-446655440000';

-- 2. 检查API端点要求的角色（参考API_SOT.md权限矩阵）
-- 例如：POST /topup-requests/{id}/approve 需要 finance 角色

-- 3. 检查SOD规则（BUSINESS_RULES.md BR-FIN-002）
SELECT created_by, approved_by FROM daily_reports WHERE id = 123;
-- 如果 created_by = approved_by → 违反SOD
```

#### 解决方案

**场景1: 用户角色不匹配**
```sql
-- 修改用户角色（仅admin可操作，需审计）
UPDATE users
SET role = 'finance', updated_by = 'admin_user_id', updated_at = NOW()
WHERE id = '550e8400-e29b-41d4-a716-446655440000';

-- 记录审计日志
INSERT INTO audit_logs (
    module, action, entity_id, performed_by, role,
    payload_before, payload_after
) VALUES (
    'users', 'role_change', '550e8400-...', 'admin_user_id', 'admin',
    '{"role": "media_buyer"}'::jsonb,
    '{"role": "finance", "reason": "晋升为财务"}'::jsonb
);
```

**场景2: SOD规则冲突**
```python
# 更换审核人（不能自己审核自己提交的）
# 前端：提示用户联系其他data_operator审核
# 后端：Service层检查
if report.created_by == current_user["user_id"]:
    raise BusinessRuleException(
        code="BIZ_001",
        message="不能审核自己提交的日报（职责分离）"
    )
```

**场景3: 数据权限过滤**
```python
# media_buyer只能看到自己的日报
if user_role == "media_buyer":
    query = query.filter(DailyReport.created_by == user_id)
elif user_role == "account_manager":
    # 仅可见自己管理的项目的日报
    managed_project_ids = get_managed_projects(user_id)
    query = query.join(AdAccount).filter(AdAccount.project_id.in_(managed_project_ids))
```

#### 预防措施
- 前端根据角色隐藏无权限按钮
- 后端Service层统一过滤数据
- 权限变更记录审计日志

---

## 4. 状态机问题（STATE-*）

> **引用**: STATE_MACHINE.md v2.6, ERROR_CODES_SOT.md v2.1 4.6节

### 4.1 STATE_400: 非法状态流转

#### 症状
```json
{
  "success": false,
  "error": {
    "code": "STATE_400",
    "message": "非法状态流转",
    "details": {
      "from": "raw_submitted",
      "to": "final_confirmed",
      "help": "查阅STATE_MACHINE.md第8章"
    }
  }
}
```

#### 诊断步骤
```bash
# 1. 查看STATE_MACHINE.md白名单
grep -A 10 "daily_reports.status" docs/2.sot/STATE_MACHINE.md

# 输出：
# "daily_reports.status": {
#     "raw_submitted": ["trend_pending"],
#     "trend_pending": ["trend_ok", "trend_flagged"],
#     "trend_ok": ["final_pending"],
#     ...
# }

# 2. 检查当前状态
psql -d ai_ad_spend -c "SELECT id, status FROM daily_reports WHERE id = 123;"
```

#### 解决方案

**正确的8状态流程**（STATE_MACHINE.md 8.2节）
```
raw_submitted → trend_pending → trend_ok → final_pending → final_confirmed → final_locked
                              ↓
                         trend_flagged → trend_resolved → final_pending
```

**常见错误流转**
| 错误流转 | 原因 | 正确做法 |
|---------|------|---------|
| `raw_submitted` → `final_confirmed` | 跳过趋势风控 | 必须先经过trend_pending检查 |
| `trend_flagged` → `final_pending` | 未复核异常 | 必须先`trend_flagged` → `trend_resolved` |
| `final_locked` → `final_pending` | 终态回退 | 使用红冲机制（REVERSAL） |

**代码示例**
```python
# backend/services/daily_report_service.py
from backend.core.state_machine import validate_state_transition

def update_status(self, report_id: int, target_status: str, user: Dict):
    report = self.db.query(DailyReport).filter(DailyReport.id == report_id).first()

    # 验证状态流转
    if not validate_state_transition("daily_reports.status", report.status, target_status):
        raise BusinessRuleException(
            code="STATE_400",
            message=f"非法流转：{report.status} → {target_status}",
            details={
                "from": report.status,
                "to": target_status,
                "help": "查阅STATE_MACHINE.md第8章"
            }
        )

    # 执行流转
    report.status = target_status
    self.db.commit()
```

#### 预防措施
- 后端Service层统一验证状态机
- 前端根据当前状态禁用不合法按钮
- 单元测试覆盖所有非法流转

---

### 4.2 STATE_402: 终态非法回退

#### 症状
```json
{
  "success": false,
  "error": {
    "code": "STATE_402",
    "message": "终态非法回退",
    "details": {
      "current_status": "final_locked",
      "target_status": "final_pending",
      "help": "终态不可回退，请使用红冲机制"
    }
  }
}
```

#### 诊断步骤
```sql
-- 检查状态是否为终态
SELECT id, status FROM daily_reports WHERE id = 123;
-- status = 'final_locked' → 终态

-- 检查操作者角色
SELECT role FROM users WHERE id = '550e8400...';
-- role != 'admin' → 无权限回退终态
```

#### 解决方案

**仅admin可回退终态（需审计）**
```python
def admin_rollback_final_state(self, report_id: int, reason: str, user: Dict):
    """admin强制回退终态（需审计）"""
    if user["role"] != "admin":
        raise AuthorizationException(code="AUTH_500", message="仅admin可回退终态")

    if not reason or len(reason) < 10:
        raise ValidationException(code="VALIDATION_001", message="必须填写详细原因（至少10字符）")

    report = self.db.query(DailyReport).filter(DailyReport.id == report_id).first()

    if report.status != "final_locked":
        raise BusinessRuleException(code="BIZ_001", message="仅final_locked可回退")

    # 执行回退
    old_status = report.status
    report.status = "final_pending"

    # 记录审计日志
    audit_log = AuditLog(
        module="daily_reports",
        action="admin_rollback_final",
        entity_id=str(report_id),
        performed_by=user["user_id"],
        role="admin",
        payload_before={"status": old_status},
        payload_after={"status": "final_pending", "reason": reason},
        tags=["ADMIN_OVERRIDE", "FINAL_STATE_ROLLBACK"]
    )
    self.db.add(audit_log)
    self.db.commit()
```

**推荐方式：使用红冲机制**
```python
def reversal_final_report(self, report_id: int, correct_conversions: int, reason: str, user: Dict):
    """红冲修正final_locked数据（推荐）"""
    if user["role"] != "admin":
        raise AuthorizationException(code="AUTH_500")

    report = self.db.query(DailyReport).filter(DailyReport.id == report_id).first()

    if report.status != "final_locked":
        raise BusinessRuleException(code="BIZ_001", message="仅final_locked可红冲")

    # Step 1: 创建红冲Ledger记录
    original_revenue = report.conversions_final * report.unit_price
    reversal_entry = LedgerEntry(
        ledger_type="PROJECT",
        entry_type="REVERSAL",
        project_id=report.project_id,
        amount=-original_revenue,
        notes=f"红冲日报#{report_id}，原因：{reason}"
    )
    self.db.add(reversal_entry)

    # Step 2: 生成新的正确Ledger记录
    correct_revenue = correct_conversions * report.unit_price
    new_entry = LedgerEntry(
        ledger_type="PROJECT",
        entry_type="REVENUE",
        project_id=report.project_id,
        amount=correct_revenue,
        notes=f"修正后的正确记录（原日报#{report_id}）"
    )
    self.db.add(new_entry)

    # Step 3: 更新项目余额
    project = self.db.query(Project).filter(Project.id == report.project_id).first()
    project.balance += (-original_revenue + correct_revenue)

    # Step 4: 记录审计
    audit_log = AuditLog(
        module="ledger",
        action="reversal",
        entity_id=str(report_id),
        performed_by=user["user_id"],
        role="admin",
        payload_before={"conversions_final": report.conversions_final, "revenue": original_revenue},
        payload_after={"conversions_final": correct_conversions, "revenue": correct_revenue, "reason": reason},
        tags=["REVERSAL", "ADMIN_OVERRIDE"]
    )
    self.db.add(audit_log)

    self.db.commit()
```

#### 预防措施
- 优先使用红冲机制而非直接回退
- admin回退必须填写详细原因
- 所有终态变更记录审计日志

---

### 4.3 STATE_409: 并发冲突

#### 症状
```json
{
  "success": false,
  "error": {
    "code": "STATE_409",
    "message": "数据已被其他用户修改",
    "details": {
      "expected_version": 5,
      "current_version": 6
    }
  }
}
```

#### 诊断步骤
```sql
-- 检查版本号
SELECT id, status, version FROM topup_requests WHERE id = 123;
-- version = 6（数据库）
-- expected_version = 5（前端提交）

-- 查看最近修改记录
SELECT * FROM audit_logs
WHERE module = 'topup_requests' AND entity_id = '123'
ORDER BY created_at DESC LIMIT 5;
```

#### 解决方案

**乐观锁检查（后端）**
```python
def approve_topup(self, topup_id: int, expected_version: int, user: Dict):
    """审批充值（带乐观锁）"""
    topup = self.db.query(TopupRequest).filter(TopupRequest.id == topup_id).first()

    # 乐观锁检查
    if topup.version != expected_version:
        raise ConcurrencyConflictError(
            code="STATE_409",
            message=f"数据已被其他用户修改（当前版本：{topup.version}）",
            details={
                "expected_version": expected_version,
                "current_version": topup.version
            }
        )

    # 执行审批
    topup.status = "finance_approve"
    topup.version += 1  # 版本号+1
    topup.approved_by = user["user_id"]
    topup.approved_at = datetime.now(timezone.utc)

    self.db.commit()
```

**前端重试逻辑**
```typescript
async function approveTopup(topupId: number, expectedVersion: number) {
  try {
    await apiFetch(`/api/v1/topup-requests/${topupId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ expected_version: expectedVersion })
    });
    alert('审批成功');
  } catch (error) {
    if (error.code === 'STATE_409') {
      // 并发冲突，提示用户刷新
      const shouldRetry = confirm('数据已被其他用户修改，是否刷新后重试？');
      if (shouldRetry) {
        window.location.reload();
      }
    }
  }
}
```

#### 预防措施
- 涉及余额/计费的表启用version字段
- 前端提交时携带expected_version
- 提供用户友好的冲突提示

---

## 5. 业务逻辑问题（BIZ-*）

> **引用**: BUSINESS_RULES.md v4.1, ERROR_CODES_SOT.md v2.1 4.2节

### 5.1 BIZ_001: 无效的操作（SOD规则违反）

#### 症状
```json
{
  "success": false,
  "error": {
    "code": "BIZ_001",
    "message": "不能审核自己提交的日报（职责分离）"
  }
}
```

#### 诊断步骤
```sql
-- 检查提交者与审核者
SELECT id, created_by, approved_by FROM daily_reports WHERE id = 123;
-- created_by = approved_by → 违反SOD

-- 检查用户角色
SELECT id, username, role FROM users WHERE id = '550e8400...';
```

#### 解决方案

**更换审核人**
```python
# Service层检查SOD
def approve_report(self, report_id: int, user: Dict):
    report = self.db.query(DailyReport).filter(DailyReport.id == report_id).first()

    # SOD检查
    if report.created_by == user["user_id"]:
        raise BusinessRuleException(
            code="BIZ_001",
            message="不能审核自己提交的日报（职责分离）"
        )

    # 执行审核
    report.status = "trend_ok"
    report.approved_by = user["user_id"]
    self.db.commit()
```

**admin强制审核（绕过SOD）**
```python
def admin_force_approve(self, report_id: int, reason: str, user: Dict):
    """admin强制审核（绕过SOD，需审计）"""
    if user["role"] != "admin":
        raise AuthorizationException(code="AUTH_500")

    if not reason or len(reason) < 10:
        raise ValidationException(code="VALIDATION_001", message="必须填写详细原因")

    report = self.db.query(DailyReport).filter(DailyReport.id == report_id).first()

    report.status = "trend_ok"
    report.approved_by = user["user_id"]

    # 记录审计日志（带SOD_BYPASS标记）
    audit_log = AuditLog(
        module="daily_reports",
        action="admin_force_approve",
        entity_id=str(report_id),
        performed_by=user["user_id"],
        role="admin",
        payload_before={"status": "raw_submitted", "created_by": report.created_by},
        payload_after={"status": "trend_ok", "reason": reason},
        tags=["ADMIN_OVERRIDE", "SOD_BYPASS"]
    )
    self.db.add(audit_log)
    self.db.commit()
```

#### 预防措施
- 前端根据created_by隐藏审核按钮
- 后端Service层统一SOD检查
- admin绕过必须记录审计

---

### 5.2 BIZ_101: 余额不足

#### 症状
```json
{
  "success": false,
  "error": {
    "code": "BIZ_101",
    "message": "项目余额不足",
    "details": {
      "required": "10000.00",
      "current_balance": "5000.00"
    }
  }
}
```

#### 诊断步骤
```sql
-- 检查项目余额
SELECT id, name, balance FROM projects WHERE id = 123;
-- balance = 5000.00

-- 检查待审批的充值
SELECT id, amount, status FROM topup_requests
WHERE project_id = 123 AND status IN ('pending_review', 'finance_approve', 'paid')
ORDER BY created_at DESC;

-- 检查Ledger记录
SELECT ledger_type, entry_type, amount, created_at
FROM ledger_entries
WHERE project_id = 123
ORDER BY created_at DESC LIMIT 20;
```

#### 解决方案

**发起充值申请**
```python
# 前端提示用户
if (project.balance < required_amount) {
    alert(`项目余额不足（当前：${project.balance}，需要：${required_amount}），请发起充值申请`);
    router.push(`/topup-requests/create?project_id=${project.id}`);
}
```

**检查Ledger一致性**
```sql
-- 计算Ledger总额
SELECT
    SUM(CASE WHEN entry_type = 'REVENUE' THEN amount ELSE 0 END) AS total_revenue,
    SUM(CASE WHEN entry_type = 'REVERSAL' THEN amount ELSE 0 END) AS total_reversal
FROM ledger_entries
WHERE ledger_type = 'PROJECT' AND project_id = 123;

-- 对比projects.balance
-- projects.balance 应等于 (total_revenue + total_reversal)
```

**修复余额不一致（需admin）**
```sql
-- 重新计算余额
UPDATE projects p
SET balance = (
    SELECT COALESCE(SUM(amount), 0)
    FROM ledger_entries
    WHERE ledger_type = 'PROJECT' AND project_id = p.id
)
WHERE id = 123;

-- 记录审计日志
INSERT INTO audit_logs (module, action, entity_id, performed_by, role, payload_after)
VALUES ('projects', 'balance_recalculation', '123', 'admin_user_id', 'admin',
        '{"reason": "修复余额不一致"}'::jsonb);
```

#### 预防措施
- 所有余额变更通过Ledger记录
- 定期对账检查一致性
- 前端实时显示余额

---

### 5.3 BIZ_201: 日期不能为未来

#### 症状
```json
{
  "success": false,
  "error": {
    "code": "BIZ_201",
    "message": "日期不能为未来",
    "details": {
      "report_date": "2025-12-01",
      "today": "2025-11-27"
    }
  }
}
```

#### 诊断步骤
```python
# 检查日期逻辑
from datetime import date

report_date = date(2025, 12, 1)
today = date.today()  # 2025-11-27

if report_date > today:
    raise BusinessRuleException(code="BIZ_201", message="日期不能为未来")
```

#### 解决方案

**前端日期限制**
```typescript
// 使用日期选择器限制最大日期
<DatePicker
  maxDate={new Date()}
  onChange={(date) => setReportDate(date)}
/>
```

**后端验证**
```python
# backend/schemas/daily_reports.py
from pydantic import BaseModel, field_validator
from datetime import date

class DailyReportCreate(BaseModel):
    report_date: date

    @field_validator('report_date')
    def validate_not_future(cls, v):
        if v > date.today():
            raise ValueError('日期不能为未来')
        return v
```

#### 预防措施
- 前端日期选择器限制最大日期
- Pydantic Schema层验证
- 后端Service层二次检查

---

## 6. 参数验证问题（VALIDATION-*）

> **引用**: ERROR_CODES_SOT.md v2.1 4.3节

### 6.1 VALIDATION_001: 必填字段缺失

#### 症状
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_001",
    "message": "必填字段缺失",
    "details": {
      "field": "conversions_raw",
      "location": "body"
    }
  }
}
```

#### 诊断步骤
```bash
# 检查请求Payload
curl -X POST https://api.example.com/api/v1/daily-reports \
  -H "Content-Type: application/json" \
  -d '{
    "ad_account_id": 123,
    "report_date": "2025-11-27"
    # 缺少 conversions_raw
  }'
```

#### 解决方案

**检查Pydantic Schema定义**
```python
# backend/schemas/daily_reports.py
class DailyReportCreate(BaseModel):
    ad_account_id: int
    report_date: date
    conversions_raw: int  # 必填字段
    raw_spend: Decimal
```

**前端表单验证**
```typescript
// 使用react-hook-form
const { register, handleSubmit, formState: { errors } } = useForm();

<input
  {...register("conversions_raw", { required: "粉数为必填项" })}
  type="number"
/>
{errors.conversions_raw && <span>{errors.conversions_raw.message}</span>}
```

#### 预防措施
- 前端表单必填项标记
- Pydantic Schema严格定义
- OpenAPI文档生成自动检查

---

### 6.2 VALIDATION_002: 格式无效

#### 症状
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_002",
    "message": "金额格式无效",
    "details": {
      "field": "amount",
      "value": "1000.123",
      "expected": "DECIMAL(15,2)"
    }
  }
}
```

#### 诊断步骤
```python
# 检查金额格式
from decimal import Decimal

amount = Decimal("1000.123")  # 三位小数
# 应该是: Decimal("1000.12")  # 两位小数
```

#### 解决方案

**Pydantic自动舍入**
```python
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal, ROUND_HALF_UP

class TopupRequestCreate(BaseModel):
    amount: Decimal = Field(..., ge=0, description="金额DECIMAL(15,2)")

    @field_validator('amount')
    def validate_amount(cls, v):
        # 强制两位小数（HALF_UP舍入）
        return v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
```

**前端格式化**
```typescript
// 格式化为两位小数
const formatAmount = (value: number): string => {
  return value.toFixed(2);
};

<input
  type="number"
  step="0.01"
  onBlur={(e) => e.target.value = formatAmount(parseFloat(e.target.value))}
/>
```

#### 预防措施
- 前端input step="0.01"
- Pydantic field_validator舍入
- 数据库CHECK约束

---

## 7. 系统错误（SYS-*）

> **引用**: ERROR_CODES_SOT.md v2.1 4.4节

### 7.1 SYS_001: 系统内部错误

#### 症状
```json
{
  "success": false,
  "error": {
    "code": "SYS_001",
    "message": "系统内部错误"
  }
}
```

#### 诊断步骤
```bash
# 1. 查看应用日志
tail -n 100 logs/app.log | grep "ERROR"

# 2. 检查堆栈跟踪
grep "Traceback" logs/app.log | tail -n 50

# 3. 检查数据库连接
psql -d ai_ad_spend -c "SELECT 1;"

# 4. 检查Supabase连接
curl -H "apikey: YOUR_SUPABASE_KEY" \
  https://your-project.supabase.co/rest/v1/users?select=id&limit=1
```

#### 解决方案

**场景1: 数据库连接池耗尽**
```bash
# 检查连接数
psql -d ai_ad_spend -c "SELECT count(*) FROM pg_stat_activity WHERE datname='ai_ad_spend';"

# 修改连接池配置（backend/core/database.py）
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # 增加连接池大小
    max_overflow=10,
    pool_pre_ping=True  # 连接健康检查
)
```

**场景2: 未捕获异常**
```python
# 全局异常处理器（backend/main.py）
from fastapi import FastAPI, Request
from backend.core.response import error_response
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return error_response(
        code="SYS_001",
        message="系统内部错误",
        status_code=500
    )
```

**场景3: Supabase Auth超时**
```python
# 增加超时配置
from supabase import create_client

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
    options={
        'timeout': 30  # 30秒超时
    }
)
```

#### 预防措施
- 全局异常处理器
- 详细日志记录
- 健康检查端点
- 监控告警

---

### 7.2 SYS_002: 服务暂时不可用

#### 症状
```json
{
  "success": false,
  "error": {
    "code": "SYS_002",
    "message": "服务暂时不可用"
  }
}
```

#### 诊断步骤
```bash
# 1. 检查服务状态
systemctl status ai_ad_spend_api

# 2. 检查负载
top
htop

# 3. 检查磁盘空间
df -h

# 4. 检查内存
free -h
```

#### 解决方案

**重启服务**
```bash
# Uvicorn/Gunicorn重启
systemctl restart ai_ad_spend_api

# 检查日志
journalctl -u ai_ad_spend_api -f
```

**增加限流保护**
```python
# backend/middleware/rate_limit.py
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=lambda request: request.client.host)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": {
                "code": "SYS_004",
                "message": "请求过于频繁，请稍后重试"
            }
        }
    )
```

#### 预防措施
- 负载均衡
- API限流
- 自动扩容
- 健康检查

---

## 8. 数据库问题（DB-*）

> **引用**: ERROR_CODES_SOT.md v2.1 4.5节

### 8.1 DB_004: 唯一性约束违反

#### 症状
```json
{
  "success": false,
  "error": {
    "code": "DB_004",
    "message": "唯一性约束违反",
    "details": {
      "constraint": "daily_reports_ad_account_id_report_date_key",
      "value": "(123, 2025-11-27)"
    }
  }
}
```

#### 诊断步骤
```sql
-- 检查重复数据
SELECT id, ad_account_id, report_date, created_at
FROM daily_reports
WHERE ad_account_id = 123 AND report_date = '2025-11-27';

-- 检查唯一约束定义
\d daily_reports
-- UNIQUE (ad_account_id, report_date)
```

#### 解决方案

**幂等性检查（推荐）**
```python
def create_daily_report(self, data: DailyReportCreate, user: Dict):
    """创建日报（幂等性）"""
    # 检查是否已存在
    existing = self.db.query(DailyReport).filter(
        DailyReport.ad_account_id == data.ad_account_id,
        DailyReport.report_date == data.report_date
    ).first()

    if existing:
        # 如果状态为raw_submitted，允许更新
        if existing.status == "raw_submitted" and existing.created_by == user["user_id"]:
            existing.conversions_raw = data.conversions_raw
            existing.raw_spend = data.raw_spend
            existing.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            return existing
        else:
            raise ConflictException(
                code="DB_004",
                message=f"日报已存在（状态：{existing.status}）"
            )

    # 创建新日报
    report = DailyReport(**data.model_dump(), created_by=user["user_id"])
    self.db.add(report)
    self.db.commit()
    return report
```

**前端防重复提交**
```typescript
const [isSubmitting, setIsSubmitting] = useState(false);

const handleSubmit = async (data: DailyReportCreateData) => {
  if (isSubmitting) return;  // 防止重复提交

  setIsSubmitting(true);
  try {
    await apiFetch('/api/v1/daily-reports', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    alert('提交成功');
  } catch (error) {
    if (error.code === 'DB_004') {
      alert('该日期的日报已存在');
    }
  } finally {
    setIsSubmitting(false);
  }
};
```

#### 预防措施
- 前端防重复提交
- 后端幂等性检查
- 数据库唯一约束

---

## 9. 趋势风控问题（TREND-*）

> **引用**: STATE_MACHINE.md v2.6 8.3节, ERROR_CODES_SOT.md v2.1 4.7节

### 9.1 TREND_001: 趋势风控触发

#### 症状
```json
{
  "success": true,
  "data": {
    "status": "trend_flagged",
    "trend_flag_reason": "TF-001: 粉数骤降50%"
  },
  "code": "TREND_001",
  "message": "趋势风控触发，需人工复核"
}
```

#### 诊断步骤
```sql
-- 检查昨日数据
SELECT ad_account_id, report_date, conversions_raw, raw_spend
FROM daily_reports
WHERE ad_account_id = 123
  AND report_date BETWEEN '2025-11-20' AND '2025-11-27'
ORDER BY report_date DESC;

-- 输出示例：
-- 2025-11-27: conversions_raw = 50  (今天)
-- 2025-11-26: conversions_raw = 120 (昨天最大值)
-- 50 < 120 × 0.5 → TF-001触发
```

#### 解决方案

**运营复核流程**
```python
def resolve_trend_flag(self, report_id: int, resolution_note: str, user: Dict):
    """运营复核趋势异常"""
    if user["role"] not in ["data_operator", "admin"]:
        raise AuthorizationException(code="AUTH_500")

    if not resolution_note or len(resolution_note) < 10:
        raise ValidationException(code="TREND_010", message="必须填写复核说明")

    report = self.db.query(DailyReport).filter(DailyReport.id == report_id).first()

    if report.status != "trend_flagged":
        raise BusinessRuleException(code="BIZ_001", message="仅trend_flagged可复核")

    # 执行复核
    report.status = "trend_resolved"
    report.trend_resolution_note = resolution_note
    report.resolved_by = user["user_id"]
    report.resolved_at = datetime.now(timezone.utc)

    self.db.commit()
```

**趋势风控规则检查**
```python
# backend/services/trend_check_service.py
def check_trend_risk(self, report: DailyReport):
    """趋势风控检查（TF-001/002/003）"""
    yesterday_data = self.get_yesterday_max_conversions(report.ad_account_id)

    # TF-001: 粉数骤降
    if report.conversions_raw < yesterday_data.conversions_raw * 0.5:
        report.status = "trend_flagged"
        report.trend_flag_reason = f"TF-001: 粉数骤降{((1 - report.conversions_raw / yesterday_data.conversions_raw) * 100):.1f}%"
        return "trend_flagged"

    # TF-002: 粉数骤增
    if report.conversions_raw > yesterday_data.conversions_raw * 3:
        report.status = "trend_flagged"
        report.trend_flag_reason = f"TF-002: 粉数骤增{((report.conversions_raw / yesterday_data.conversions_raw - 1) * 100):.1f}%"
        return "trend_flagged"

    # TF-003: 消耗异常
    if report.raw_spend > yesterday_data.raw_spend * 2:
        report.status = "trend_flagged"
        report.trend_flag_reason = f"TF-003: 消耗异常{((report.raw_spend / yesterday_data.raw_spend - 1) * 100):.1f}%"
        return "trend_flagged"

    # 通过检查
    report.status = "trend_ok"
    return "trend_ok"
```

#### 预防措施
- 运营定期检查trend_flagged报告
- 前端显示趋势图辅助判断
- 记录复核说明

---

### 9.2 TREND_002: 风控复核未完成

#### 症状
```json
{
  "success": false,
  "error": {
    "code": "TREND_002",
    "message": "trend_flagged状态必须复核",
    "details": {
      "current_status": "trend_flagged",
      "trend_flag_reason": "TF-001: 粉数骤降50%"
    }
  }
}
```

#### 诊断步骤
```sql
-- 检查状态
SELECT id, status, trend_flag_reason FROM daily_reports WHERE id = 123;
-- status = 'trend_flagged'

-- 检查是否跳过复核
-- 如果直接尝试 trend_flagged → final_pending → 触发TREND_002
```

#### 解决方案

**必须先复核**
```python
def update_real_spend(self, report_id: int, real_spend: Decimal, user: Dict):
    """录入real_spend（trend_flagged状态禁止）"""
    report = self.db.query(DailyReport).filter(DailyReport.id == report_id).first()

    if report.status == "trend_flagged":
        raise BusinessRuleException(
            code="TREND_002",
            message="trend_flagged状态必须复核",
            details={
                "current_status": report.status,
                "trend_flag_reason": report.trend_flag_reason,
                "help": "请先调用 /daily-reports/{id}/resolve-trend 完成复核"
            }
        )

    # 允许的状态：trend_ok, trend_resolved
    if report.status not in ["trend_ok", "trend_resolved"]:
        raise BusinessRuleException(code="BIZ_301")

    report.real_spend = real_spend
    report.status = "final_pending"
    self.db.commit()
```

#### 预防措施
- 前端根据status显示复核按钮
- 后端Service层强制检查
- 状态机白名单验证

---

## 10. 不变式违反问题（INV-*）

> **引用**: MASTER.md v4.4

### 10.1 INV-001: Ledger-Balance一致性

#### 症状
```
项目余额与Ledger记录不一致
projects.balance = 10000.00
Ledger总额 = 9500.00
差异: 500.00
```

#### 诊断步骤
```sql
-- 检查Ledger总额
SELECT
    project_id,
    SUM(CASE WHEN entry_type = 'REVENUE' THEN amount ELSE 0 END) AS total_revenue,
    SUM(CASE WHEN entry_type = 'REVERSAL' THEN amount ELSE 0 END) AS total_reversal,
    (SUM(CASE WHEN entry_type = 'REVENUE' THEN amount ELSE 0 END) +
     SUM(CASE WHEN entry_type = 'REVERSAL' THEN amount ELSE 0 END)) AS ledger_total
FROM ledger_entries
WHERE ledger_type = 'PROJECT' AND project_id = 123
GROUP BY project_id;

-- 对比projects.balance
SELECT id, balance FROM projects WHERE id = 123;

-- 如果 balance != ledger_total → INV-001违反
```

#### 解决方案

**修复一致性（需admin）**
```sql
-- 重新计算balance
UPDATE projects p
SET balance = (
    SELECT COALESCE(SUM(amount), 0)
    FROM ledger_entries
    WHERE ledger_type = 'PROJECT' AND project_id = p.id
)
WHERE id = 123;

-- 记录审计
INSERT INTO audit_logs (module, action, entity_id, performed_by, role, payload_after)
VALUES ('projects', 'balance_recalculation', '123', 'admin_user_id', 'admin',
        '{"reason": "修复INV-001违反", "old_balance": 10000.00, "new_balance": 9500.00}'::jsonb);
```

**预防性检查**
```python
# backend/services/ledger_service.py
def create_ledger_entry(self, data: LedgerEntryCreate):
    """创建Ledger记录（带一致性检查）"""
    # 创建记录
    entry = LedgerEntry(**data.model_dump())
    self.db.add(entry)

    # 更新项目余额
    if data.ledger_type == "PROJECT":
        project = self.db.query(Project).filter(Project.id == data.project_id).first()
        project.balance += data.amount

    self.db.commit()

    # 验证一致性
    self.verify_balance_consistency(data.project_id)

def verify_balance_consistency(self, project_id: int):
    """验证balance与Ledger一致性"""
    ledger_total = self.db.query(func.sum(LedgerEntry.amount)).filter(
        LedgerEntry.ledger_type == "PROJECT",
        LedgerEntry.project_id == project_id
    ).scalar() or 0

    project = self.db.query(Project).filter(Project.id == project_id).first()

    if abs(project.balance - ledger_total) > 0.01:  # 允许0.01误差
        raise InvariantViolation(
            code="INV_001",
            message=f"balance不一致: {project.balance} != {ledger_total}"
        )
```

#### 预防措施
- 所有余额变更通过Ledger
- 定期对账检查
- 事务内更新balance

---

### 10.2 INV-002: 三数据流分离

#### 症状
```
使用raw_spend计算成本（违反三数据流原则）
cost = raw_spend  # 错误
应该：cost = real_spend
```

#### 诊断步骤
```bash
# 检查代码是否使用raw_spend计算成本
grep -r "raw_spend" backend/services/ | grep "cost"

# 检查是否跳过final计费
grep -r "conversions_raw" backend/services/ | grep "revenue"
```

#### 解决方案

**正确使用三数据流**
```python
# ✅ 正确：使用real_spend计算成本
def create_cost_entry(self, report: DailyReport):
    cost = report.real_spend + report.fee  # real_spend，非raw_spend

    entry = LedgerEntry(
        ledger_type="SUPPLIER",
        entry_type="COST",
        supplier_id=report.ad_account.supplier_id,
        amount=-cost  # 成本为负数
    )
    self.db.add(entry)

# ✅ 正确：使用conversions_final计费
def create_revenue_entry(self, report: DailyReport):
    if report.status != "final_locked":
        raise BusinessRuleException(code="BIZ_001", message="仅final_locked可计费")

    revenue = report.conversions_final * report.unit_price  # final，非raw

    entry = LedgerEntry(
        ledger_type="PROJECT",
        entry_type="REVENUE",
        project_id=report.project_id,
        amount=revenue
    )
    self.db.add(entry)
```

**代码审查检查点**
```bash
# 检查是否违反INV-002
# 1. 禁止使用raw_spend计算成本
grep -r "raw_spend" backend/services/ | grep -E "(cost|ledger)"

# 2. 禁止使用conversions_raw计费
grep -r "conversions_raw" backend/services/ | grep -E "(revenue|ledger)"
```

#### 预防措施
- Code Review检查
- 单元测试覆盖
- 文档明确三数据流用途

---

### 10.3 INV-003: 8状态流程完整性

#### 症状
```
跳过趋势风控直接确认final
raw_submitted → final_confirmed  # 违反8状态流程
应该：raw_submitted → trend_pending → trend_ok → final_pending → final_confirmed
```

#### 诊断步骤
```sql
-- 检查状态跳跃
SELECT id, status, created_at FROM daily_reports
WHERE ad_account_id = 123 AND report_date = '2025-11-27'
ORDER BY created_at;

-- 如果看到 raw_submitted → final_confirmed（没有trend_*） → 违反INV-003
```

#### 解决方案

**强制趋势风控检查**
```python
def submit_daily_report(self, data: DailyReportCreate, user: Dict):
    """提交日报（自动触发趋势风控）"""
    # 创建日报
    report = DailyReport(
        **data.model_dump(),
        status="raw_submitted",
        created_by=user["user_id"]
    )
    self.db.add(report)
    self.db.flush()

    # 自动触发趋势风控
    report.status = "trend_pending"
    self.db.commit()

    # 异步执行风控检查
    trend_result = self.trend_check_service.check_trend_risk(report)

    return report
```

**状态机白名单验证**
```python
# backend/core/state_machine.py
STATE_TRANSITIONS = {
    "daily_reports.status": {
        "raw_submitted": ["trend_pending"],
        "trend_pending": ["trend_ok", "trend_flagged"],
        "trend_ok": ["final_pending"],
        "trend_flagged": ["trend_resolved", "raw_submitted"],
        "trend_resolved": ["final_pending"],
        "final_pending": ["final_confirmed"],
        "final_confirmed": ["final_locked"],
        "final_locked": []  # 终态
    }
}

def validate_state_transition(table_status: str, from_status: str, to_status: str) -> bool:
    """验证状态流转是否合法"""
    allowed = STATE_TRANSITIONS.get(table_status, {}).get(from_status, [])
    return to_status in allowed
```

#### 预防措施
- 状态机白名单强制检查
- 自动触发趋势风控
- 单元测试覆盖所有流程

---

## 11. 性能问题诊断

### 11.1 慢查询定位

#### 症状
```
API响应时间 > 3秒
页面加载卡顿
```

#### 诊断步骤
```sql
-- 1. 开启慢查询日志
ALTER DATABASE ai_ad_spend SET log_min_duration_statement = 1000;  -- 1秒

-- 2. 查看pg_stat_statements
SELECT
    query,
    calls,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;

-- 3. 分析执行计划
EXPLAIN ANALYZE
SELECT * FROM daily_reports
WHERE ad_account_id = 123
ORDER BY report_date DESC
LIMIT 20;
```

#### 解决方案

**场景1: 缺少索引**
```sql
-- 检查索引
\d daily_reports

-- 添加缺失索引
CREATE INDEX idx_daily_reports_ad_account_date
ON daily_reports(ad_account_id, report_date DESC);
```

**场景2: N+1查询**
```python
# ❌ 错误：N+1查询
reports = db.query(DailyReport).all()
for report in reports:
    account = db.query(AdAccount).filter(AdAccount.id == report.ad_account_id).first()

# ✅ 正确：使用joinedload
from sqlalchemy.orm import joinedload

reports = db.query(DailyReport)\
    .options(joinedload(DailyReport.ad_account))\
    .all()
```

**场景3: 全表扫描**
```python
# ❌ 错误：查询所有数据
all_reports = db.query(DailyReport).all()

# ✅ 正确：分页+过滤
reports = db.query(DailyReport)\
    .filter(DailyReport.report_date >= '2025-11-01')\
    .offset((page - 1) * page_size)\
    .limit(page_size)\
    .all()
```

#### 预防措施
- 定期ANALYZE表
- 监控慢查询
- Code Review检查ORM使用

---

### 11.2 数据库连接池问题

#### 症状
```
TimeoutError: QueuePool limit exceeded
```

#### 诊断步骤
```sql
-- 检查当前连接数
SELECT count(*) FROM pg_stat_activity WHERE datname = 'ai_ad_spend';

-- 检查最大连接数
SHOW max_connections;  -- 默认100

-- 检查空闲连接
SELECT count(*) FROM pg_stat_activity
WHERE datname = 'ai_ad_spend' AND state = 'idle';
```

#### 解决方案

**调整连接池配置**
```python
# backend/core/database.py
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # 增加连接池大小
    max_overflow=10,       # 允许超出pool_size的连接数
    pool_timeout=30,       # 连接超时（秒）
    pool_recycle=3600,     # 连接回收时间（秒）
    pool_pre_ping=True     # 连接健康检查
)
```

**修复连接泄漏**
```python
# ❌ 错误：未关闭连接
def get_data():
    db = SessionLocal()
    data = db.query(User).all()
    return data  # 连接未关闭

# ✅ 正确：使用依赖注入
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # 自动关闭

@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()
```

#### 预防措施
- 使用依赖注入管理连接
- 监控连接池指标
- 定期检查空闲连接

---

## 12. 数据库连接问题

### 12.1 连接失败

#### 症状
```
OperationalError: could not connect to server
```

#### 诊断步骤
```bash
# 1. 检查PostgreSQL服务
systemctl status postgresql

# 2. 检查连接字符串
echo $DATABASE_URL
# 应该类似：postgresql://user:password@localhost:5432/ai_ad_spend

# 3. 测试连接
psql -h localhost -U user -d ai_ad_spend
```

#### 解决方案

**场景1: PostgreSQL未启动**
```bash
# 启动PostgreSQL
systemctl start postgresql

# 设置开机自启
systemctl enable postgresql
```

**场景2: 连接凭证错误**
```bash
# 检查.env文件
cat .env | grep DATABASE_URL

# 修改密码
psql -U postgres
ALTER USER user WITH PASSWORD 'new_password';

# 更新.env
DATABASE_URL=postgresql://user:new_password@localhost:5432/ai_ad_spend
```

**场景3: 防火墙阻止**
```bash
# 检查5432端口
netstat -tuln | grep 5432

# 开放端口
sudo ufw allow 5432/tcp
```

#### 预防措施
- 健康检查端点
- 连接重试机制
- 监控告警

---

### 12.2 Supabase连接问题

#### 症状
```
AuthError: Invalid API key
```

#### 诊断步骤
```bash
# 1. 检查Supabase URL和Key
echo $SUPABASE_URL
echo $SUPABASE_KEY

# 2. 测试连接
curl -H "apikey: $SUPABASE_KEY" \
  $SUPABASE_URL/rest/v1/users?select=id&limit=1
```

#### 解决方案

**更新Supabase配置**
```bash
# .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGc...  # anon key
SUPABASE_SERVICE_KEY=eyJhbGc...  # service_role key (后端使用)
```

**检查RLS策略**
```sql
-- 查看RLS策略
SELECT schemaname, tablename, policyname, permissive, roles, qual
FROM pg_policies
WHERE tablename = 'users';

-- 禁用RLS（仅开发环境）
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
```

#### 预防措施
- 使用service_role key（后端）
- 配置正确的RLS策略
- 定期轮换API Key

---

## 13. API契约违反问题

> **引用**: API_SOT.md v9.3

### 13.1 响应格式不符合Envelope

#### 症状
```json
// ❌ 错误：FastAPI默认格式
{
  "detail": "Not Found"
}

// ✅ 正确：Envelope格式
{
  "success": false,
  "error": {
    "code": "BIZ_002",
    "message": "资源不存在"
  }
}
```

#### 诊断步骤
```bash
# 检查响应格式
curl -X GET https://api.example.com/api/v1/projects/999 | jq .

# 如果看到 {"detail": "..."}  → 未使用Envelope
```

#### 解决方案

**统一使用Envelope**
```python
# backend/core/response.py
from typing import Optional, Any
from uuid import uuid4
from datetime import datetime

def success_response(data: Any = None, message: str = "操作成功", code: str = "SUCCESS"):
    return {
        "success": True,
        "data": data,
        "message": message,
        "code": code,
        "request_id": str(uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def error_response(code: str, message: str, details: Optional[dict] = None, status_code: int = 400):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details
            },
            "request_id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )
```

**全局异常处理**
```python
# backend/main.py
from fastapi.exceptions import RequestValidationError
from fastapi import FastAPI, Request

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return error_response(
        code="VALIDATION_001",
        message="参数验证失败",
        details={"errors": exc.errors()},
        status_code=422
    )
```

#### 预防措施
- 全局异常处理器
- Code Review检查
- OpenAPI文档生成

---

### 13.2 字段名不符合SoT定义

#### 症状
```json
// ❌ 错误：使用conversion（单数）
{
  "conversion": 100
}

// ✅ 正确：使用conversions_raw（DATA_SCHEMA.md定义）
{
  "conversions_raw": 100
}
```

#### 诊断步骤
```bash
# 检查Schema定义
grep -A 20 "class DailyReportCreate" backend/schemas/daily_reports.py

# 检查DATA_SCHEMA.md
grep "conversions_raw" docs/2.sot/DATA_SCHEMA.md
```

#### 解决方案

**严格对齐DATA_SCHEMA.md**
```python
# backend/schemas/daily_reports.py
class DailyReportCreate(BaseModel):
    """创建日报 - 字段严格对应DATA_SCHEMA.md 3.3.1节"""
    ad_account_id: int = Field(..., description="广告账户ID")
    report_date: date = Field(..., description="日报日期")
    conversions_raw: int = Field(..., ge=0, description="原始粉数（投手提交）")
    raw_spend: Decimal = Field(..., ge=0, description="原始消耗（投手提交）")
```

#### 预防措施
- Schema开发前查阅DATA_SCHEMA.md
- Pydantic Field添加description
- 单元测试验证字段名

---

## 14. 前端常见问题

### 14.1 Token自动刷新失败

#### 症状
```
用户登录后1小时Token过期，但未自动刷新
```

#### 诊断步骤
```typescript
// 检查lib/api.ts
console.log('Session expires_at:', session.expires_at);
console.log('Current time:', Date.now() / 1000);
```

#### 解决方案

**实现自动刷新**
```typescript
// lib/api.ts
export async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const { data: { session } } = await supabase.auth.getSession();

  if (!session) {
    window.location.href = '/login';
    throw new Error('未登录');
  }

  // 检查Token是否即将过期（剩余5分钟）
  const expiresAt = session.expires_at * 1000;
  if (Date.now() > expiresAt - 5 * 60 * 1000) {
    console.log('Token即将过期，自动刷新...');
    const { data, error } = await supabase.auth.refreshSession();
    if (error) {
      console.error('刷新失败:', error);
      window.location.href = '/login';
      throw error;
    }
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json',
      ...options?.headers
    }
  });

  const data = await response.json();

  if (!data.success) {
    // 统一错误处理
    handleApiError(data.error);
    throw new Error(data.error.message);
  }

  return data.data as T;
}
```

#### 预防措施
- 实施自动刷新机制
- 显示Token倒计时
- 后端增加Token延长策略

---

### 14.2 前端直接解析JWT

#### 症状
```typescript
// ❌ 危险：前端解析JWT
const token = session.access_token;
const payload = JSON.parse(atob(token.split('.')[1]));
const userId = payload.sub;
```

#### 诊断步骤
```bash
# 检查前端代码是否解析JWT
grep -r "atob" frontend/src/
grep -r "jwt_decode" frontend/src/
```

#### 解决方案

**使用API获取用户信息**
```typescript
// ✅ 正确：调用GET /auth/me
const user = await apiFetch<User>('/api/v1/auth/me');
const userId = user.id;  // 由后端验证Token后返回
```

#### 预防措施
- Code Review禁止前端解析JWT
- 使用GET /auth/me获取用户信息
- 教育开发者安全原则

---

## 15. 日志分析模式

### 15.1 请求链路追踪

#### 日志格式
```
2025-11-27 10:30:00 INFO [550e8400-e29b-41d4-a716-446655440000] POST /api/v1/daily-reports user_id=550e8400 role=media_buyer
2025-11-27 10:30:01 DEBUG [550e8400-e29b-41d4-a716-446655440000] Validating schema: DailyReportCreate
2025-11-27 10:30:02 DEBUG [550e8400-e29b-41d4-a716-446655440000] Checking trend risk: TF-001/002/003
2025-11-27 10:30:03 INFO [550e8400-e29b-41d4-a716-446655440000] Trend check passed: trend_ok
2025-11-27 10:30:04 INFO [550e8400-e29b-41d4-a716-446655440000] Response 201 {"success": true}
```

#### 查询命令
```bash
# 追踪单个请求的完整链路
grep "550e8400-e29b-41d4-a716-446655440000" logs/app.log

# 提取所有ERROR
grep "550e8400-e29b-41d4-a716-446655440000" logs/app.log | grep "ERROR"
```

---

### 15.2 错误码统计

#### 统计命令
```bash
# 统计过去24小时的错误码分布
tail -n 10000 logs/app.log | grep '"code":' | \
  sed -E 's/.*"code": "([A-Z_0-9]+)".*/\1/' | \
  sort | uniq -c | sort -rn

# 输出示例：
#  150 AUTH_402
#   80 STATE_400
#   50 BIZ_001
#   30 VALIDATION_001
```

#### 分析建议
- `AUTH_402`高频 → Token过期问题，检查刷新机制
- `STATE_400`高频 → 状态机流转错误，检查前端逻辑
- `BIZ_001`高频 → SOD规则冲突，检查审核流程

---

## 16. 恢复操作手册

### 16.1 数据库备份与恢复

#### 备份
```bash
# 全库备份
pg_dump -U postgres -d ai_ad_spend -F c -f backup_$(date +%Y%m%d_%H%M%S).dump

# 仅数据备份（不含schema）
pg_dump -U postgres -d ai_ad_spend -a -F c -f data_backup_$(date +%Y%m%d_%H%M%S).dump

# 单表备份
pg_dump -U postgres -d ai_ad_spend -t daily_reports -F c -f daily_reports_backup.dump
```

#### 恢复
```bash
# 全库恢复
pg_restore -U postgres -d ai_ad_spend -c backup_20251127_103000.dump

# 单表恢复
pg_restore -U postgres -d ai_ad_spend -t daily_reports daily_reports_backup.dump

# 仅数据恢复
pg_restore -U postgres -d ai_ad_spend -a data_backup_20251127_103000.dump
```

---

### 16.2 Ledger红冲操作

#### 场景：final_locked数据错误

```sql
-- Step 1: 查询原始记录
SELECT * FROM ledger_entries
WHERE ledger_type = 'PROJECT' AND project_id = 123
ORDER BY created_at DESC LIMIT 5;

-- 假设错误记录ID=12345，amount=5000.00

-- Step 2: 创建红冲记录
INSERT INTO ledger_entries (
    ledger_type, entry_type, project_id, amount, notes
) VALUES (
    'PROJECT', 'REVERSAL', 123, -5000.00, '红冲记录#12345，原因：粉数错误'
);

-- Step 3: 创建正确记录
INSERT INTO ledger_entries (
    ledger_type, entry_type, project_id, amount, notes
) VALUES (
    'PROJECT', 'REVENUE', 123, 4750.00, '修正后的正确记录（原#12345）'
);

-- Step 4: 更新项目余额
UPDATE projects
SET balance = balance - 5000.00 + 4750.00
WHERE id = 123;

-- Step 5: 记录审计日志
INSERT INTO audit_logs (
    module, action, entity_id, performed_by, role,
    payload_before, payload_after
) VALUES (
    'ledger', 'reversal', '12345', 'admin_user_id', 'admin',
    '{"amount": 5000.00, "conversions_final": 100}'::jsonb,
    '{"amount": 4750.00, "conversions_final": 95, "reason": "粉数错误修正"}'::jsonb
);
```

---

### 16.3 强制终态回退（紧急）

#### 场景：final_locked需要回退

```sql
-- ⚠️ 仅admin操作，需详细审计

BEGIN;

-- Step 1: 备份原始数据
CREATE TEMP TABLE daily_reports_backup AS
SELECT * FROM daily_reports WHERE id = 123;

-- Step 2: 回退状态
UPDATE daily_reports
SET status = 'final_pending',
    updated_by = 'admin_user_id',
    updated_at = NOW()
WHERE id = 123;

-- Step 3: 记录审计日志
INSERT INTO audit_logs (
    module, action, entity_id, performed_by, role,
    payload_before, payload_after, tags
) VALUES (
    'daily_reports', 'admin_rollback_final', '123', 'admin_user_id', 'admin',
    '{"status": "final_locked"}'::jsonb,
    '{"status": "final_pending", "reason": "紧急修正数据错误"}'::jsonb,
    ARRAY['ADMIN_OVERRIDE', 'FINAL_STATE_ROLLBACK', 'EMERGENCY']
);

COMMIT;
```

---

### 16.4 账户禁用与解封

#### 禁用账户
```sql
UPDATE users
SET is_active = false,
    updated_by = 'admin_user_id',
    updated_at = NOW()
WHERE id = '550e8400-e29b-41d4-a716-446655440000';

-- 审计日志
INSERT INTO audit_logs (module, action, entity_id, performed_by, role, payload_after)
VALUES ('users', 'account_disable', '550e8400...', 'admin_user_id', 'admin',
        '{"reason": "安全风险"}'::jsonb);
```

#### 解封账户
```sql
UPDATE users
SET is_active = true,
    updated_by = 'admin_user_id',
    updated_at = NOW()
WHERE id = '550e8400-e29b-41d4-a716-446655440000';

-- 审计日志
INSERT INTO audit_logs (module, action, entity_id, performed_by, role, payload_after)
VALUES ('users', 'account_enable', '550e8400...', 'admin_user_id', 'admin',
        '{"reason": "风险已解除"}'::jsonb);
```

---

## 附录：参考文档

| SoT文档 | 版本 | 引用章节 | 说明 |
|---------|------|---------|------|
| **ERROR_CODES_SOT.md** | v2.1 | 全文 | 错误码定义 |
| **STATE_MACHINE.md** | v2.6 | 第8章 | 8状态流程 |
| **AUTH_SPEC.md** | v2.0 | 全文 | 认证授权规范 |
| **API_SOT.md** | v9.0 | 第4章 | API响应格式 |
| **DATA_SCHEMA.md** | v5.2 | 第3章 | 数据库表结构 |
| **BUSINESS_RULES.md** | v3.1 | BR-* | 业务规则 |
| **MASTER.md** | v3.4 | INV-* | 数据库不变式 |

---

**文档维护者**: 系统架构团队
**最后审核**: 2025-11-27
**下次审核**: 季度性审核或重大变更时

---

**END OF DOCUMENT**
