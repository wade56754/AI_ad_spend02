---
description: "OpenSpec Archive: 归档已部署的 change 并更新规范"
argument-hint: "<change-id>"
---

# OpenSpec 归档助手

归档已完成部署的 OpenSpec change。

## 归档前提条件

用户输入: `$ARGUMENTS`

### 必须满足:
- [ ] 所有 tasks.md 任务已完成 (`- [x]`)
- [ ] 回归测试全部通过
- [ ] proposal.md 状态为 READY_FOR_ARCHIVE
- [ ] 代码已合并到主分支

## Step 1: 预检查

### 1.1 验证完成状态

```bash
# 显示 change 详情
openspec show $ARGUMENTS --json --deltas-only

# 验证格式
openspec validate $ARGUMENTS --strict
```

### 1.2 检查 tasks.md 完成度

读取 `openspec/changes/$ARGUMENTS/tasks.md`，确认:
- 所有 `- [ ]` 已改为 `- [x]`
- 无未完成的必需任务

### 1.3 验证代码实现

检查 proposal.md 中列出的文件是否都已实现:
- Models: backend/models/
- Services: backend/services/
- Routers: backend/routers/
- Tests: backend/tests/

## Step 2: 归档执行

### 2.1 标准归档（含 spec 更新）

```bash
openspec archive $ARGUMENTS --yes
```

此命令会:
1. 移动 `changes/$ARGUMENTS/` → `changes/archive/YYYY-MM-DD-$ARGUMENTS/`
2. 将 delta specs 合并到 `specs/[capability]/spec.md`
3. 清理临时文件

### 2.2 工具类归档（跳过 spec 更新）

如果 change 仅涉及工具/配置，不影响业务规范:

```bash
openspec archive $ARGUMENTS --skip-specs --yes
```

## Step 3: 后归档验证

### 3.1 验证归档目录

确认文件已移动:
```
openspec/changes/archive/YYYY-MM-DD-$ARGUMENTS/
├── proposal.md
├── tasks.md
└── specs/
    └── [capability]/
        └── spec.md
```

### 3.2 验证 specs 更新

如果非 `--skip-specs`，检查 `openspec/specs/[capability]/spec.md`:
- ADDED Requirements 已合并
- MODIFIED Requirements 已更新
- REMOVED Requirements 已删除

### 3.3 运行最终验证

```bash
openspec validate --strict
```

## Step 4: SoT 文档同步

### 4.1 检查需要更新的 SoT 文档

根据 proposal.md 的 Impact 章节，更新:

| 变更类型 | 需要更新的 SoT |
|---------|---------------|
| 数据模型 | DATA_SCHEMA.md |
| API 端点 | API_SOT.md |
| 错误码 | ERROR_CODES_SOT.md |
| 状态机 | STATE_MACHINE.md |
| 业务规则 | BUSINESS_RULES.md |
| 账本规则 | LEDGER_SOT.md |

### 4.2 更新 SoT 版本

如果 SoT 文档有变更:
1. 更新文档头部的版本号（如 v5.2 → v5.3）
2. 在变更历史中记录本次更新
3. 确保 PROJECT_MEMORY.md 中的版本引用也同步更新

## Step 5: 回归基线更新（如需要）

如果本次 change 新增了测试模块:

### 5.1 更新回归测试文档

在 `REGRESSION_TEST_SUITE.md` 中:
- 添加新模块的测试条目
- 更新测试总数统计

### 5.2 考虑创建新基线

如果变更较大，考虑创建新的回归基线:
```bash
# 运行全量测试并保存结果
python run_tests.py --type all --baseline
```

## 输出格式

```
## OpenSpec 归档报告

### Change: $ARGUMENTS
- 归档时间: YYYY-MM-DD HH:MM
- 归档路径: openspec/changes/archive/YYYY-MM-DD-$ARGUMENTS/

### 归档操作
| 操作 | 状态 |
|------|------|
| 移动文件到 archive/ | ✅ |
| 合并 ADDED specs | ✅ |
| 更新 MODIFIED specs | ✅ |
| 删除 REMOVED specs | ✅ |

### Specs 变更汇总
| Capability | ADDED | MODIFIED | REMOVED |
|------------|-------|----------|---------|
| profit | 3 | 0 | 0 |
| ledger | 0 | 1 | 0 |

### SoT 文档更新
| 文档 | 旧版本 | 新版本 | 变更内容 |
|------|-------|-------|---------|
| DATA_SCHEMA.md | v5.2 | v5.3 | 新增 §3.6 |
| API_SOT.md | v9.0 | v9.1 | 新增 §13 |

### 验证结果
- `openspec validate --strict`: ✅ PASSED
- 回归测试: 220/220 passed

### 清理建议
1. 更新 PROJECT_MEMORY.md 中的 SoT 版本引用
2. 在下次会话中运行 `/sot-check` 确认合规性
```

## 回滚指南

如果归档后发现问题，需要回滚:

### 1. 恢复 change 目录

```bash
# 手动移回
mv openspec/changes/archive/YYYY-MM-DD-$ARGUMENTS openspec/changes/$ARGUMENTS
```

### 2. 回滚 specs 变更

如果使用了标准归档（非 --skip-specs）:
- 使用 git 回滚 `openspec/specs/` 的变更
- 或手动移除合并的 Requirements

### 3. 更新状态

将 proposal.md 状态改回 IN_PROGRESS

## 最佳实践

1. **归档前务必验证** - 先运行 `openspec validate --strict`
2. **保留 PR 引用** - 在 proposal.md 中记录合并的 PR 编号
3. **及时更新 SoT** - 归档后立即同步 SoT 文档
4. **维护版本一致性** - 确保所有版本引用都已更新
