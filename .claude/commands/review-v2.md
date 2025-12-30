---
description: "代码审查: 质量检查 + SoT 合规验证"
argument-hint: "<file-path> [--sot] [--fix]"
---

# 代码审查 Skill

## 使用方式

```bash
/review backend/services/daily_report_service.py        # 完整审查
/review backend/routers/daily_reports.py --sot          # 仅 SoT 合规
/review backend/services/ledger_service.py --fix        # 审查并自动修复
```

## 审查维度

### 1. 代码质量检查

| 检查项 | 规则 | 严重级别 |
|--------|------|----------|
| 类型注解 | 所有公开函数必须有类型注解 | WARNING |
| 文档字符串 | 公开函数必须有 docstring | WARNING |
| 复杂度 | 单函数不超过 50 行 | WARNING |
| 异常处理 | 不允许裸 `except:` | ERROR |
| 硬编码 | 不允许硬编码密钥/密码 | BLOCKING |

### 2. SoT 合规检查 (BLOCKING)

#### 状态值验证
```python
# ✅ 正确 - 使用白名单状态
status = DailyReportStatus.DRAFT  # draft
status = "trend_pending"

# ❌ 错误 - 非法状态
status = "approved"      # 不在白名单
status = "pending"       # 应该是 pending_review
```

**8 状态白名单**:
```
draft, pending_review, trend_pending, trend_ok,
real_pending, real_filled, final_pending, final_confirmed
```

#### 角色值验证
```python
# ✅ 正确
if user.role == "pitcher":
if user.role in ["finance", "admin"]:

# ❌ 错误
if user.role == "supervisor":     # 已废弃
if user.role == "data_operator":  # 应该用 project_owner
```

**6 角色白名单**:
```
ceo, admin, project_owner, finance, pitcher, account_manager
```

#### 错误码验证
```python
# ✅ 正确
raise BusinessError("BIZ_001", "业务规则错误")
raise AuthError("AUTH_401", "未授权")

# ❌ 错误
raise BusinessError("ERR_001", "错误")  # 非法前缀
raise Exception("CUSTOM_ERROR")          # 非标准错误
```

**16 错误码前缀**:
```
AUTH_, BIZ_, FIN_, LEDGER_, STATE_, VALIDATION_,
DB_, SYS_, API_, PERM_, RES_, DATA_, RECON_, REPORT_, RPT_, IMPORT_
```

### 3. Phase 1 原则检查 (BLOCKING)

检测禁止的阻断模式:

```python
# ❌ 禁止 - 自动阻断
raise HTTPException(status_code=403, detail="禁止操作")
account.suspend()
user.freeze()
request.reject()

# ✅ 允许 - 仅提示
logger.warning("检测到异常操作")
return {"warning": "建议检查", "data": result}
report.add_flag("需要人工确认")
```

### 4. 模块边界检查

| 模块 | 可读 | 可写 | 禁止 |
|------|------|------|------|
| pitcher | 所有 | `daily_reports.*` | `ledger.*` 写入 |
| finance | 所有 | `ledger.*`, `topup.*` | `daily_reports.status` |
| ad_account | 所有 | `ad_accounts.*` | `ledger.*` 写入 |
| project | 所有 | `projects.*`, `users.*` | 无 |

## 执行流程

### Step 1: 静态分析
```bash
ruff check <file> --select=E,W,F
mypy <file> --ignore-missing-imports
```

### Step 2: SoT 扫描

扫描文件中的:
- 所有字符串字面量，匹配状态/角色模式
- 所有 `raise` 语句，提取错误码
- 所有 HTTP 响应，检查阻断模式

### Step 3: 生成报告

```
📋 代码审查报告: backend/services/daily_report_service.py

✅ 通过检查: 12 项
⚠️ 警告: 3 项
  - L45: 函数 `process_report` 缺少类型注解
  - L78: 函数过长 (62 行 > 50 行)
  - L112: 建议添加 docstring

🚫 阻断问题: 1 项
  - L89: 使用了非法状态 "approved"，应改为 "final_confirmed"

📊 SoT 合规率: 92%
```

### Step 4: 自动修复 (--fix)

可自动修复的问题:
- 状态值替换 (approved → final_confirmed)
- 角色值替换 (supervisor → project_owner)
- 导入排序
- 格式化

不能自动修复的问题:
- 复杂度过高 (需要重构)
- 阻断逻辑 (需要业务评估)

## 输出格式

```
┌─────────────────────────────────────────────────────────┐
│ 📋 代码审查报告                                          │
├─────────────────────────────────────────────────────────┤
│ 文件: backend/services/daily_report_service.py          │
│ 行数: 245                                               │
│ 审查时间: 2025-12-30 15:30:00                           │
├─────────────────────────────────────────────────────────┤
│ ✅ 通过: 15 项                                          │
│ ⚠️ 警告: 3 项                                           │
│ 🚫 阻断: 0 项                                           │
├─────────────────────────────────────────────────────────┤
│ SoT 合规率: 100%                                        │
│ 代码质量分: 8.5/10                                      │
└─────────────────────────────────────────────────────────┘
```

## 与其他命令集成

```bash
# 生成代码后自动审查
/gen be 创建日报接口 && /review backend/routers/daily_reports.py

# 批量审查
/review backend/services/*.py --sot
```
