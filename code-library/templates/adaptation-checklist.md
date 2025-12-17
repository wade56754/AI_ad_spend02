# 代码适配检查清单

> **版本**: v1.0
> **更新日期**: 2025-12-17
> **用途**: 代码工厂适配外部代码时的检查清单

---

## 1. 技术栈适配 (Tech Stack)

### 1.1 Python 后端

- [ ] **Pydantic 版本检查**
  - 本项目使用 Pydantic v2
  - 检查 `@validator` → `@field_validator`
  - 检查 `class Config:` → `model_config = ConfigDict(...)`
  - 检查 `orm_mode` → `from_attributes`

- [ ] **SQLAlchemy 版本检查**
  - 本项目使用 SQLAlchemy 2.x
  - 检查 `session.query()` → `session.execute(select())`
  - 检查结果提取 `.scalars().all()`

- [ ] **FastAPI 版本检查**
  - 本项目使用 FastAPI >= 0.100
  - 检查依赖注入模式
  - 检查响应模型定义

- [ ] **Python 版本检查**
  - 本项目使用 Python >= 3.10
  - 检查类型注解语法 (`list[str]` vs `List[str]`)
  - 检查 match-case 语句兼容性

### 1.2 TypeScript 前端

- [ ] **Next.js 版本检查**
  - 本项目使用 Next.js 14 (App Router)
  - 检查路由模式 (pages/ vs app/)
  - 检查服务端/客户端组件标记

- [ ] **TanStack Query 版本检查**
  - 本项目使用 TanStack Query v5
  - 检查 hook 签名变化
  - 检查 queryKey 格式

- [ ] **TypeScript 版本检查**
  - 检查类型语法兼容性
  - 检查 satisfies 操作符

---

## 2. 项目规范适配 (Project Standards)

### 2.1 响应格式

- [ ] **统一响应结构**
  ```python
  # 成功响应
  return success_response(data=result)

  # 错误响应
  return error_response(code=ErrorCode.XXX, message="...")

  # 分页响应
  return paginated_response(items=items, total=total, page=page, page_size=page_size)
  ```

- [ ] **导入项目响应模块**
  ```python
  from backend.core.response import success_response, error_response, paginated_response
  ```

### 2.2 错误码

- [ ] **使用项目错误码**
  ```python
  from backend.core.error_codes import (
      SystemErrorCodes,
      BusinessErrorCodes,
      ValidationErrorCodes,
      AuthErrorCodes
  )
  ```

- [ ] **禁止自定义错误码**
  - 所有错误码必须来自 `ERROR_CODES_SOT.md`

### 2.3 异常处理

- [ ] **使用项目自定义异常**
  ```python
  from backend.exceptions.custom_exceptions import (
      BusinessLogicError,
      ResourceNotFoundError,
      PermissionDeniedError,
      ResourceConflictError
  )
  ```

### 2.4 命名规范

- [ ] **后端文件命名**
  - Router: `{entity}.py` 或 `{entity}_router.py`
  - Service: `{entity}_service.py`
  - Schema: `{entity}.py`
  - Model: `{entity}.py`

- [ ] **前端文件命名**
  - Hook: `use{Entity}.ts`
  - API: `{entity}Api.ts`
  - Types: `{entity}.types.ts`
  - Component: `{ComponentName}.tsx` (PascalCase)

---

## 3. SoT 合规适配 (SoT Compliance)

### 3.1 状态机检查

- [ ] **日报状态 (DailyReportStatus)**
  - 8 状态: raw_submitted → trend_pending → trend_ok/trend_flagged → trend_resolved → final_pending → final_confirmed → final_locked
  - 检查外部代码是否使用了不存在的状态

- [ ] **充值状态 (TopupRequestStatus)**
  - 7 状态: draft, pending_review, finance_approve, paid, completed, rejected, cancelled

- [ ] **对账状态 (ReconciliationBatchStatus)**
  - 5 状态: draft, pending_review, approved, needs_adjustment, completed

- [ ] **禁止创建新状态**
  - 不得发明 SoT 中未定义的状态值

### 3.2 字段检查

- [ ] **检查字段名称**
  - 对照 `DATA_SCHEMA.md` 检查字段名
  - 不得发明新字段

- [ ] **检查字段类型**
  - UUID 类型: `id`, `project_id`, `user_id` 等
  - Decimal 类型: 金额字段
  - Enum 类型: 状态字段

### 3.3 业务规则检查

- [ ] **检查业务规则引用**
  - 对照 `BUSINESS_RULES.md` 检查规则编号
  - 不得发明新业务规则

---

## 4. 来源标注 (Source Attribution)

### 4.1 代码来源注释

- [ ] **添加来源标注**
  ```python
  """
  [ADAPTED FROM] {source}: {path}
  [ADAPTATION] 基于参考代码适配，非从零生成
  [ORIGINAL LICENSE] {license}
  """
  ```

### 4.2 改动标注

- [ ] **标注所有改动点**
  ```python
  # [ADAPTED] 原因: 适配 Pydantic v2
  # [ADAPTED] 原因: 使用项目标准响应格式
  ```

---

## 5. 最终检查 (Final Checklist)

- [ ] 代码可以通过 `mypy` 类型检查
- [ ] 代码可以通过 `ruff` lint 检查
- [ ] 代码符合项目目录结构
- [ ] 所有导入路径正确
- [ ] 没有硬编码的配置值
- [ ] 没有安全漏洞 (SQL 注入, XSS 等)
- [ ] 添加了必要的日志记录
- [ ] 添加了来源标注

---

## 适配率计算

```
适配率 = (保留的原代码行数 / 原代码总行数) × 100%

目标:
- 技术栈适配: 保留 > 80%
- 项目规范适配: 保留 > 70%
- SoT 合规适配: 保留 > 60%
- 功能定制: 保留 > 50%
```

---

**文档结束**
