---
description: "OpenSpec Apply: 实现已批准的 change 并保持任务同步"
argument-hint: "<change-id>"
---

# OpenSpec 实现助手

实现已批准的 OpenSpec change proposal。

## 实现流程

用户输入: `$ARGUMENTS`

如果 change-id 为空，先运行:
```bash
openspec list
```
然后提示用户选择要实现的 change。

## Step 1: 预检查

### 1.1 验证 change 状态
```bash
openspec show $ARGUMENTS --json
```

检查:
- [ ] proposal.md 状态为 APPROVED 或 IN_PROGRESS
- [ ] 未被其他开发者锁定
- [ ] 依赖的 changes 已完成（如有）

### 1.2 运行 OpenSpec 验证
```bash
openspec validate $ARGUMENTS --strict
```

如果验证失败，先修复问题再继续。

### 1.3 读取关键文件
按顺序阅读:
1. `openspec/changes/$ARGUMENTS/proposal.md` - 理解变更目的
2. `openspec/changes/$ARGUMENTS/tasks.md` - 获取任务清单
3. `openspec/changes/$ARGUMENTS/specs/*/spec.md` - 理解规范变更

## Step 2: 任务执行

### 2.1 同步 tasks.md 到 TodoWrite

将 tasks.md 中的任务同步到当前会话的 Todo 列表：

```
tasks.md 格式:
## Phase 1: Database
- [ ] 1.1 Create migration
- [ ] 1.2 Run migration

转换为 TodoWrite:
- "Phase 1.1: Create migration" (pending)
- "Phase 1.2: Run migration" (pending)
```

### 2.2 按顺序执行任务

对于每个任务:
1. 标记 TodoWrite 状态为 `in_progress`
2. 执行实现工作
3. 验证实现符合规范
4. 标记 TodoWrite 状态为 `completed`
5. 更新 tasks.md 中对应项为 `- [x]`

### 2.3 实现检查点

每完成一个 Phase:
- 运行相关测试
- 验证与 SoT 一致性
- 提交代码（如适用）

## Step 3: SoT 同步检查

### 3.1 数据模型变更

如果 proposal.md 影响 DATA_SCHEMA.md:

```bash
# 检查模型定义
grep -r "class.*Model" backend/models/

# 验证字段类型一致性
# 对比 DATA_SCHEMA.md 中的定义
```

### 3.2 API 端点变更

如果 proposal.md 影响 API_SOT.md:

```bash
# 检查路由定义
grep -r "@router\." backend/routers/

# 验证端点路径、方法、权限
```

### 3.3 错误码变更

如果 proposal.md 影响 ERROR_CODES_SOT.md:

```bash
# 检查错误码定义
grep -r "class.*ErrorCodes" backend/core/error_codes.py

# 验证错误码格式
```

## Step 4: 回归测试

如果 change 影响 backend/routers/* 或 backend/services/*:

```bash
# 运行回归测试
python run_tests.py --type regression

# 对比基线
# 参考: docs/4.testing/BACKEND_REGRESSION_FREEZE_REPORT_v1.0.md
```

## Step 5: 完成确认

### 5.1 更新 tasks.md

确保所有任务标记为完成:
```markdown
## Phase 1: Database
- [x] 1.1 Create migration ✅
- [x] 1.2 Run migration ✅
```

### 5.2 更新 proposal.md 状态

```markdown
**Status**: READY_FOR_ARCHIVE
```

### 5.3 运行最终验证

```bash
openspec validate $ARGUMENTS --strict
```

## 输出格式

```
## OpenSpec 实现报告

### Change: $ARGUMENTS
- 开始时间: YYYY-MM-DD HH:MM
- 完成时间: YYYY-MM-DD HH:MM

### 任务完成情况
| Phase | 任务数 | 已完成 | 状态 |
|-------|-------|-------|------|
| Phase 1 | 5 | 5 | ✅ |
| Phase 2 | 10 | 10 | ✅ |
| Phase 3 | 8 | 8 | ✅ |

### SoT 同步状态
| 文档 | 需要更新 | 已更新 | 状态 |
|------|---------|-------|------|
| DATA_SCHEMA.md | ✅ | ✅ | ✅ |
| API_SOT.md | ✅ | ✅ | ✅ |
| ERROR_CODES_SOT.md | ✅ | ✅ | ✅ |

### 回归测试结果
- 现有模块: 198 passed, 0 failed
- 新增模块: 22 passed, 0 failed
- 总计: 220 passed, 0 failed ✅

### 下一步
1. 运行 `/openspec:archive $ARGUMENTS`
2. 创建 PR 合并到主分支
```

## 常见问题处理

### 问题: 任务依赖冲突
- 检查其他 active changes
- 协调冲突的任务顺序
- 必要时暂停当前 change

### 问题: 回归测试失败
- 分析失败原因
- 修复代码或更新基线（需审批）
- 重新运行测试

### 问题: SoT 版本变更
- 更新 proposal.md 中的版本引用
- 验证变更不影响实现
- 重新运行 openspec validate
