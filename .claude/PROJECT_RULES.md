# AI广告代投系统 - 开发强制规范

> **文档版本**: v1.0
> **文档类型**: 项目强制规范（SoT总纲）
> **适用范围**: 所有开发工作
> **规范级别**: 🔴 强制执行

---

## 📚 文档真相源（SoT）层级结构

### 1. SoT-Data（数据库唯一真相）
**文档**: `docs/core/DATA_SCHEMA.md v3.0`

- 所有表结构、字段名、字段类型、主外键关系的唯一来源
- 金额字段统一：`NUMERIC(15,2)`，费率字段：`NUMERIC(5,4)`
- 时间字段统一：`TIMESTAMP WITH TIME ZONE`
- 主键统一：`UUID (gen_random_uuid())`

### 2. SoT-State（状态机唯一真相）
**文档**: `docs/core/STATE_MACHINE.md`

- 充值流程状态：`draft → pending_review → approved/rejected → pending_payment → paid → posted`
- 广告账户生命周期：`new → testing → active → suspended → dead → archived`
- 所有状态转换必须符合此文档定义，禁止自创状态值

### 3. SoT-Implementation（实现规范唯一真相）
**文档**: `docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md`

- 合法角色**仅限5个**：`admin`, `finance`, `data_operator`, `account_manager`, `media_buyer`
- 禁止使用旧角色名：`manager`, `data_clerk`, `trader` 等
- 技术栈：FastAPI + Supabase PostgreSQL + Next.js

### 4. SoT-API（API开发流程唯一真相）
**文档**: `docs/core/API_DEVELOPMENT_FLOW.md v7.0`

- **响应格式强制Envelope**: 必须使用 `success_response`/`error_response`，禁止直接返回dict
- **前端调用强制apiFetch**: 禁止使用原生fetch或其他HTTP库，必须通过FastAPI BFF
- **开发顺序强制**: Schema → Service → Router → Test → Exception Handler
- 金额类型强制：Python用`Decimal`，TypeScript用`number`（展示）/`string`（传输）

---

## 🚫 五大不可违背规则

1. **数据库字段禁止自创** - 所有字段必须在DATA_SCHEMA.md中定义
2. **角色限定为5个** - 使用旧角色名视为错误
3. **状态值禁止自创** - 必须符合STATE_MACHINE.md定义
4. **前端禁止绕过BFF** - 必须通过apiFetch调用FastAPI，禁止直连Supabase
5. **API响应禁止裸数据** - 必须使用Envelope格式

---

## 🏗️ 架构约束

- **认证**: Supabase Auth（前端）+ JWT验证（后端）
- **数据访问**: 前端通过FastAPI BFF，后端通过SQLAlchemy访问PostgreSQL
- **禁止前端直接操作数据库**（除Supabase Auth外）
- **所有业务逻辑必须在后端实现**

---

## 💻 代码生成规则

- 所有模型必须与DATA_SCHEMA.md完全一致
- 外键必须指向实际存在的表（如`users.id`，非虚构的`user_profiles.id`）
- 时间字段必须使用`DateTime(timezone=True)`
- 金额字段必须使用`Numeric(15, 2)`
- CHECK约束必须与DATA_SCHEMA.md定义一致

---

## ✅ AI 自检清单（每次生成代码前必查）

### 🔍 数据层检查
- [ ] 所有表名是否在`DATA_SCHEMA.md § 2`中存在？
- [ ] 所有字段名是否在对应表定义中存在？
- [ ] 字段类型是否与DATA_SCHEMA.md完全一致？
  - 金额：`NUMERIC(15,2)` / `Decimal(15, 2)`
  - 费率：`NUMERIC(5,4)` / `Decimal(5, 4)`
  - 时间：`TIMESTAMP WITH TIME ZONE` / `DateTime(timezone=True)`
  - 主键：`UUID` / `UUID(as_uuid=True)`
- [ ] 外键关系是否与DATA_SCHEMA.md一致？
- [ ] CHECK约束是否与DATA_SCHEMA.md一致？

### 👤 角色与权限检查
- [ ] 使用的角色是否仅限于以下5个？
  - ✅ `admin`, `finance`, `data_operator`, `account_manager`, `media_buyer`
  - ❌ 禁止：`manager`, `data_clerk`, `trader`, `clerk` 等旧名
- [ ] 权限判断逻辑是否参考AI_AD_SYSTEM_MAIN_DOCUMENT.md权限矩阵？

### 🔄 状态机检查
- [ ] 使用的状态值是否在`STATE_MACHINE.md`对应状态机中定义？
- [ ] 状态转换是否符合状态机流转规则？
- [ ] 是否有非法的状态跳转？

### 🌐 API层检查
- [ ] 响应是否使用`success_response`/`error_response`（Envelope格式）？
- [ ] 前端调用是否通过`apiFetch`而非直接fetch？
- [ ] 是否绕过FastAPI BFF直接访问数据库？
- [ ] 错误处理是否使用项目定义的异常类？
- [ ] 开发顺序是否符合：Schema → Service → Router → Test？

### 📝 命名与规范检查
- [ ] 表名是否使用小写+下划线（如`ad_spend_daily`）？
- [ ] 字段名是否使用小写+下划线（如`created_at`）？
- [ ] 是否混用了新旧表名（如`topups` vs `topup_requests`）？
- [ ] 是否发明了不在SoT中的辅助表？

### 🚫 绝对禁止事项
- [ ] 是否创建了不在DATA_SCHEMA.md中的表？
- [ ] 是否创建了不在DATA_SCHEMA.md中的字段？
- [ ] 是否使用了Float处理金额（必须用Decimal）？
- [ ] 是否使用了没有时区的DateTime？
- [ ] 是否跳过了Envelope直接返回裸数据？
- [ ] 是否让前端直接访问Supabase做业务操作（Auth除外）？

---

## 📋 快速参考

### 合法角色（仅5个）
```python
VALID_ROLES = [
    'admin',           # 系统管理员
    'finance',         # 财务人员
    'data_operator',   # 数据运营
    'account_manager', # 账户管理员
    'media_buyer'      # 广告投手
]
```

### 充值状态（示例）
```python
TOPUP_STATES = [
    'draft',            # 草稿
    'pending_review',   # 待审核
    'approved',         # 已批准
    'rejected',         # 已拒绝
    'pending_payment',  # 待支付
    'paid',            # 已支付
    'posted',          # 已入账
    'cancelled'        # 已取消
]
```

### 标准响应格式
```python
# 成功响应
return success_response(
    data=result,
    message="操作成功"
)

# 错误响应
return error_response(
    message="错误信息",
    code="ERROR_CODE",
    status_code=400
)
```

---

**最后更新**: 2024-11-18
**维护责任**: 项目规则总监
