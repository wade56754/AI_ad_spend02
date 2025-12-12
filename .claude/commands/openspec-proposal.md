---
description: "OpenSpec Proposal: 创建新的 change proposal 并严格验证"
argument-hint: "<change-name>"
---

# OpenSpec 提案创建器

创建新的 OpenSpec change proposal。

## 创建流程

用户输入: `$ARGUMENTS`

如果 change-name 为空，询问用户:
- 变更的简要描述是什么？
- 这是新功能、修改还是删除？

## Step 1: 命名规范检查

### Change ID 格式
- 使用 kebab-case
- 动词开头: `add-`, `update-`, `remove-`, `refactor-`, `fix-`
- 简短描述: 3-5 个单词

**示例:**
```
✅ add-two-factor-auth
✅ update-profit-calculation
✅ remove-legacy-api
✅ refactor-ledger-service
❌ new_feature          # 不是 kebab-case
❌ authentication       # 缺少动词前缀
```

### 唯一性检查
```bash
openspec list
# 确认 $ARGUMENTS 不与现有 change 重名
```

## Step 2: 脚手架创建

### 2.1 创建目录结构

```bash
mkdir -p openspec/changes/$ARGUMENTS/specs
```

### 2.2 创建 proposal.md

```markdown
# Change: [简要描述]

**Status**: DRAFT
**Version**: 1.0
**Date**: YYYY-MM-DD

## Why

### 原始问题
[描述当前系统的问题或需要添加的功能]

### 业务价值
[解释这个变更带来的价值]

## What Changes

### 1. [变更类别]

| 组件 | 操作 | 说明 |
|------|------|------|
| xxx | 新建/修改/删除 | 描述 |

## Impact

### 影响范围

- **Affected specs**: [列出受影响的 capability]
- **Affected code**:
  - backend/models/ (...)
  - backend/services/ (...)
  - backend/routers/ (...)
- **Affected tests**: [列出需要新增/修改的测试]

### 兼容性

- **Breaking changes**: 无 / 有（描述）
- **向后兼容**: 是/否

### 依赖关系

| 依赖文档 | 版本 | 用途 |
|---------|------|------|
| STATE_MACHINE.md | v2.6 | ... |
| DATA_SCHEMA.md | v5.2 | ... |

## Migration

[如有数据迁移，描述迁移策略]

## Risks & Rollback

### 风险评估

| 风险 | 等级 | 缓解措施 |
|------|------|---------|
| ... | 低/中/高 | ... |

### 回滚策略

[描述如何回滚]

## Scope

### In Scope
- ✅ ...

### Out of Scope
- ❌ ...

## Done 条件

### 验收清单
- [ ] ...
```

### 2.3 创建 tasks.md

```markdown
# Tasks: [Change Name]

**Status**: NOT_STARTED
**Last Updated**: YYYY-MM-DD

---

## Phase 0: SoT & Scope Confirmation

- [ ] 0.1 确认依赖的 SoT 文档版本
- [ ] 0.2 确认 Out of Scope 项
- [ ] 0.3 Review proposal.md 完整性

---

## Phase 1: [第一阶段名称]

- [ ] 1.1 [任务描述]
- [ ] 1.2 [任务描述]

---

## Phase 2: [第二阶段名称]

- [ ] 2.1 [任务描述]
- [ ] 2.2 [任务描述]

---

## Phase 3: Testing & Regression

- [ ] 3.1 编写单元测试
- [ ] 3.2 编写集成测试
- [ ] 3.3 运行回归测试: `python run_tests.py --type regression`
- [ ] 3.4 验证基线对比 (v1.0)

---

## Phase 4: Documentation & Archive

- [ ] 4.1 更新相关 SoT 文档
- [ ] 4.2 运行 `openspec validate $ARGUMENTS --strict`
- [ ] 4.3 运行 `openspec archive $ARGUMENTS --yes`

---

## Summary

| Phase | Tasks | Status |
|-------|-------|--------|
| Phase 0 | N | ⏳ |
| Phase 1 | N | ⏳ |
| Phase 2 | N | ⏳ |
| Phase 3 | N | ⏳ |
| Phase 4 | N | ⏳ |
```

### 2.4 创建 spec delta

根据变更类型，在 `specs/[capability]/spec.md` 创建:

```markdown
## ADDED Requirements

### Requirement: [需求名称]
[系统] SHALL [做什么]

#### Scenario: [成功场景]
- **WHEN** [条件]
- **THEN** [结果]

#### Scenario: [失败场景]
- **WHEN** [条件]
- **THEN** [结果]

---

## MODIFIED Requirements

### Requirement: [现有需求名称]
[复制并修改原有需求的完整内容]

#### Scenario: [场景]
- **WHEN** [条件]
- **THEN** [结果]

---

## REMOVED Requirements

### Requirement: [要删除的需求名称]
**Reason**: [删除原因]
**Migration**: [迁移说明]
```

## Step 3: 验证

### 3.1 格式验证

```bash
openspec validate $ARGUMENTS --strict
```

### 3.2 常见问题检查

- [ ] proposal.md 包含 Why/What Changes/Impact 章节
- [ ] tasks.md 包含带 checkbox 的任务列表
- [ ] spec delta 使用正确的 `#### Scenario:` 格式
- [ ] 每个 Requirement 至少有一个 Scenario
- [ ] SoT 版本引用与实际一致

## Step 4: 提交审批

### 4.1 更新状态

将 proposal.md 的 Status 改为:
```markdown
**Status**: PENDING_APPROVAL
```

### 4.2 提示用户

```
OpenSpec 提案已创建:

📁 openspec/changes/$ARGUMENTS/
├── proposal.md    (变更说明)
├── tasks.md       (任务清单)
└── specs/
    └── [capability]/
        └── spec.md (规范变更)

下一步:
1. Review proposal.md 确认内容完整
2. 运行 `openspec validate $ARGUMENTS --strict` 验证格式
3. 获取审批后运行 `/openspec:apply $ARGUMENTS` 开始实现
```

## 输出格式

```
## OpenSpec 提案创建报告

### Change: $ARGUMENTS
- 创建时间: YYYY-MM-DD HH:MM
- 路径: openspec/changes/$ARGUMENTS/

### 创建的文件
| 文件 | 状态 |
|------|------|
| proposal.md | ✅ Created |
| tasks.md | ✅ Created |
| specs/[capability]/spec.md | ✅ Created |

### 验证结果
```bash
openspec validate $ARGUMENTS --strict
```
- 结构检查: ✅ PASSED
- Spec 格式: ✅ PASSED
- Scenario 完整性: ✅ PASSED

### 下一步操作
1. [ ] Review proposal.md
2. [ ] 获取审批
3. [ ] 运行 `/openspec:apply $ARGUMENTS`
```

## 决策树

```
新请求?
├─ Bug fix (恢复规范行为)? → 直接修复，无需提案
├─ 文档/注释修改? → 直接修复，无需提案
├─ 新功能/能力? → 创建提案 ✅
├─ Breaking change? → 创建提案 ✅
├─ 架构变更? → 创建提案 ✅
└─ 不确定? → 创建提案（更安全）✅
```
