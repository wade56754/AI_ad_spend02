---
description: "OpenSpec 验证: 全面检查 change proposal 的完整性和 SoT 合规性"
argument-hint: "[change-id]"
---

# OpenSpec 验证器

对 OpenSpec change proposal 进行全面验证。

## 验证目标

用户输入: `$ARGUMENTS`

- 如果指定 change-id，验证该 change
- 如果为空，列出所有 active changes 并提示选择

## 验证步骤

### Step 1: 基础结构验证

检查 `openspec/changes/$ARGUMENTS/` 目录：

```
必需文件:
├── proposal.md      # Why + What Changes + Impact
├── tasks.md         # Implementation checklist
└── specs/           # Delta specs 目录
    └── [capability]/
        └── spec.md  # ADDED/MODIFIED/REMOVED Requirements
```

**检查项:**
- [ ] proposal.md 存在且包含 Why/What Changes/Impact 三个章节
- [ ] tasks.md 存在且包含带 checkbox 的任务列表
- [ ] specs/ 目录存在且至少有一个 capability 子目录
- [ ] 每个 capability 下有 spec.md 文件

### Step 2: Spec Delta 格式验证

检查 `specs/[capability]/spec.md`:

**必须包含以下操作标记之一:**
- `## ADDED Requirements` - 新增需求
- `## MODIFIED Requirements` - 修改需求
- `## REMOVED Requirements` - 删除需求
- `## RENAMED Requirements` - 重命名需求

**每个 Requirement 必须:**
- 使用 `### Requirement: <名称>` 格式
- 包含至少一个 `#### Scenario: <场景名>` (4个#)
- Scenario 内有 `- **WHEN**` 和 `- **THEN**` 条件

**常见错误检查:**
```markdown
# ❌ 错误格式
- **Scenario: xxx**        # 不能用列表
**Scenario**: xxx          # 不能加粗
### Scenario: xxx          # 必须是 4 个 #

# ✅ 正确格式
#### Scenario: Success case
- **WHEN** user performs action
- **THEN** expected result
```

### Step 3: SoT 交叉引用验证

根据 proposal.md 的 Impact 章节，检查引用的 SoT 文档版本：

**SoT 裁判链优先级:**
```
1. STATE_MACHINE.md v2.6   - 状态枚举、转换规则
2. DATA_SCHEMA.md v5.2     - 数据模型、字段类型
3. BUSINESS_RULES.md v3.1  - 业务规则编号
4. API_SOT.md v9.0         - API 端点、请求响应
5. ERROR_CODES_SOT.md v2.1 - 错误码格式
6. LEDGER_SOT.md v1.1      - 账本操作规则
7. PROFIT_SOT.md v1.1      - 利润计算规则
```

**验证项:**
- [ ] 引用的 SoT 文档版本与 docs/sot/ 中实际版本一致
- [ ] 新增的状态枚举在 STATE_MACHINE.md 中有定义或明确标记为 ADDED
- [ ] 新增的错误码遵循 ERROR_CODES_SOT.md 的命名规范
- [ ] 新增的 API 端点遵循 API_SOT.md 的响应格式

### Step 4: 代码-规范一致性验证

如果 change 已有部分实现，检查代码与规范的一致性：

**Models 检查:**
```python
# 检查 backend/models/ 中是否有对应模型
# 验证字段类型与 DATA_SCHEMA.md 一致
```

**Routers 检查:**
```python
# 检查 backend/routers/ 中是否有对应端点
# 验证路径、方法、权限与 API_SOT.md 一致
```

**Error Codes 检查:**
```python
# 检查 backend/core/error_codes.py 中是否定义了新错误码
# 验证错误码格式与 ERROR_CODES_SOT.md 一致
```

### Step 5: 回归测试要求检查

如果 change 影响以下目录，必须包含回归测试任务：

```
触发条件:
- backend/routers/*
- backend/services/*
- docs/sot/*
- .claude/skills/ai-ad-api-automation-test/*
```

**检查 tasks.md 是否包含:**
```markdown
## Regression Test Verification
- [ ] Run regression test suite: `python run_tests.py --type regression`
- [ ] Verify all tests pass (compare with baseline v1.0)
```

## 输出格式

```
## OpenSpec 验证报告

### Change: $ARGUMENTS
- 状态: DRAFT | IN_PROGRESS | READY_FOR_ARCHIVE
- 路径: openspec/changes/$ARGUMENTS/

### 结构验证 ✅/❌
| 文件 | 状态 | 问题 |
|------|------|------|
| proposal.md | ✅ | - |
| tasks.md | ✅ | - |
| specs/profit/spec.md | ❌ | 缺少 Scenario |

### Spec Delta 验证 ✅/❌
| Capability | Operation | Requirements | Scenarios | 问题 |
|------------|-----------|--------------|-----------|------|
| profit | ADDED | 3 | 5 | ✅ |
| ledger | MODIFIED | 1 | 0 | ❌ 缺少 Scenario |

### SoT 引用验证 ✅/❌
| 引用文档 | 声明版本 | 实际版本 | 状态 |
|---------|---------|---------|------|
| DATA_SCHEMA.md | v5.2 | v5.2 | ✅ |
| API_SOT.md | v9.0 | v9.1 | ⚠️ 版本不匹配 |

### 回归测试要求 ✅/❌
- 影响路径: backend/routers/finance_profit.py
- tasks.md 包含回归测试任务: ✅/❌

### 总结
- 通过项: N
- 警告项: M
- 失败项: K
- 建议: [修复建议列表]

### CLI 验证命令
\`\`\`bash
openspec validate $ARGUMENTS --strict
\`\`\`
```

## 快速修复指南

### 问题: 缺少 Scenario
```markdown
# 在 ### Requirement: 后添加
#### Scenario: Success case
- **WHEN** user performs action
- **THEN** expected result occurs
```

### 问题: SoT 版本不匹配
1. 检查 `docs/sot/[DOC].md` 顶部的版本号
2. 更新 proposal.md 中的版本引用
3. 如果需要修改 SoT，先创建相应的 OpenSpec change

### 问题: 缺少回归测试任务
```markdown
# 在 tasks.md 中添加
## Regression Test Verification
- [ ] Run `python run_tests.py --type regression`
- [ ] Compare with baseline v1.0
- [ ] Document any failures
```
