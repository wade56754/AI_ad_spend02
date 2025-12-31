# 代码审查提示词 (Review Prompt)

## 目标

全面审查代码质量，发现潜在问题，提出改进建议。

## 审查维度

### 1. SoT 合规性 (最高优先级)
- 状态值是否来自 STATE_MACHINE.md？
- 角色值是否来自 AUTH_SPEC.md？
- 错误码是否来自 ERROR_CODES_SOT.md？
- 字段定义是否符合 DATA_SCHEMA.md？

### 2. 安全性
- 是否有 SQL 注入风险？
- 是否有 XSS 风险？
- 是否暴露敏感信息？
- 认证授权是否正确？

### 3. 代码质量
- 是否遵循项目代码风格？
- 是否有重复代码？
- 是否有过度复杂的逻辑？
- 命名是否清晰？

### 4. 性能
- 是否有 N+1 查询问题？
- 是否有不必要的循环？
- 是否有内存泄漏风险？

### 5. 可维护性
- 是否有足够的注释？
- 是否有测试覆盖？
- 是否便于扩展？

## 审查清单

### Python 后端
```
□ 使用 Pydantic v2 语法 (ConfigDict, model_dump)
□ 使用 SQLAlchemy 2.x 语法 (select, execute)
□ 响应使用 success_response / error_response
□ 错误使用 BusinessError + 注册的错误码
□ 异步函数正确使用 async/await
□ 类型注解完整
□ 无硬编码的敏感信息
```

### TypeScript 前端
```
□ 使用 TypeScript 严格模式
□ 使用 shadcn/ui 组件
□ 使用 TanStack Query v5 管理状态
□ 使用 apiFetch 而非直接 fetch
□ 组件有 Props 接口定义
□ 无 any 类型
□ 有 'use client' 指令 (客户端组件)
```

### 通用
```
□ 有 SoT 来源标注
□ 无调试代码 (console.log, print)
□ 无注释掉的代码
□ 无硬编码的魔法数字/字符串
□ 错误处理完整
```

## 问题严重级别

| 级别 | 说明 | 处理方式 |
|------|------|----------|
| 🔴 BLOCKING | 必须修复，阻止合并 | 立即修复 |
| 🟠 MAJOR | 应该修复，影响质量 | 尽快修复 |
| 🟡 MINOR | 建议修复，改进代码 | 可选修复 |
| 🟢 SUGGESTION | 可选改进 | 记录待办 |

## 输出格式

```markdown
# 代码审查报告

## 摘要
- 审查文件: {文件列表}
- 发现问题: {数量}
- 阻断问题: {数量}

## 问题列表

### 🔴 BLOCKING

#### [B-001] {问题标题}
- **文件**: `path/to/file.py`
- **行号**: L42-L45
- **问题**: {问题描述}
- **建议**: {修复建议}
```python
# 建议的修复代码
```

### 🟠 MAJOR

#### [M-001] {问题标题}
...

### 🟡 MINOR

#### [N-001] {问题标题}
...

## 正面反馈

- ✅ {做得好的地方}
- ✅ {做得好的地方}

## 总体评价

{总体评价文字}

建议: {通过 / 需修改后通过 / 不通过}
```

## 常见问题模式

### SoT 违规
```python
# ❌ 问题: 使用未定义的状态
status = "pending"  # 不在 STATE_MACHINE.md 中

# ✅ 修复: 使用定义的状态
status = "raw_submitted"  # SoT: STATE_MACHINE.md#daily_report
```

### 旧语法
```python
# ❌ 问题: Pydantic v1 语法
class Config:
    orm_mode = True

# ✅ 修复: Pydantic v2 语法
model_config = ConfigDict(from_attributes=True)
```

### 安全问题
```python
# ❌ 问题: SQL 注入风险
query = f"SELECT * FROM users WHERE id = {user_id}"

# ✅ 修复: 使用参数化查询
stmt = select(User).where(User.id == user_id)
```

### 错误处理
```python
# ❌ 问题: 自定义错误码
raise HTTPException(400, "Invalid status")

# ✅ 修复: 使用注册的错误码
raise BusinessError(code=BusinessErrorCodes.INVALID_STATE_TRANSITION)
```


