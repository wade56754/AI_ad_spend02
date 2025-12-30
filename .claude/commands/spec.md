---
description: "规范管理: SoT变更提案/验证/应用/归档"
argument-hint: "<proposal|validate|apply|archive> [name]"
---

# 规范管理 Skill (OpenSpec)

## 使用方式

```bash
/spec proposal add-new-status     # 创建变更提案
/spec validate add-new-status     # 验证提案合规性
/spec apply add-new-status        # 应用已批准的变更
/spec archive add-new-status      # 归档已部署的变更
```

## 变更生命周期

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ proposal │ → │ validate │ → │  apply   │ → │ archive  │
│  (草案)   │    │  (验证)   │    │  (应用)   │    │  (归档)   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

---

## 子命令详解

### 1. /spec proposal

创建 SoT 变更提案:

```bash
/spec proposal add-cancelled-status
```

**执行流程**:
```
Step 1: 创建提案目录
        → docs/changes/add-cancelled-status/

Step 2: 生成提案模板
        → PROPOSAL.md
        → IMPACT.md
        → MIGRATION.md

Step 3: 填充基本信息
        - 变更原因
        - 影响范围
        - 回滚计划
```

**提案模板**:
```markdown
# 变更提案: add-cancelled-status

## 元信息
- 提案人: [自动填充]
- 创建日期: 2025-12-30
- 状态: draft
- 影响 SoT: STATE_MACHINE.md

## 变更内容

### 新增状态
```yaml
name: cancelled
description: 日报被取消
allowed_from: [draft, pending_review]
allowed_to: []  # 终态
```

### 变更原因
[待填写]

### 影响分析
- 涉及代码: backend/models/enums.py
- 涉及测试: tests/test_state_machine.py
- 前端影响: 状态显示组件

## 审批记录
- [ ] 技术评审
- [ ] 业务评审
- [ ] 安全评审
```

---

### 2. /spec validate

验证提案合规性:

```bash
/spec validate add-cancelled-status
```

**验证规则**:

| 检查项 | 规则 | 级别 |
|--------|------|------|
| 格式完整 | PROPOSAL.md 必填字段齐全 | BLOCKING |
| 命名规范 | 状态名小写+下划线 | BLOCKING |
| 无冲突 | 不与现有状态冲突 | BLOCKING |
| 有回滚 | 必须有回滚计划 | WARNING |
| 有测试 | 必须有测试用例 | WARNING |

**输出**:
```
┌─────────────────────────────────────────┐
│ 📋 提案验证报告: add-cancelled-status   │
├─────────────────────────────────────────┤
│ ✅ 格式检查: 通过                        │
│ ✅ 命名规范: 通过                        │
│ ✅ 冲突检测: 无冲突                      │
│ ⚠️ 回滚计划: 建议补充详细步骤            │
│ ✅ 测试用例: 已包含                      │
├─────────────────────────────────────────┤
│ 验证结果: 通过 (可进入审批流程)          │
└─────────────────────────────────────────┘
```

---

### 3. /spec apply

应用已批准的变更:

```bash
/spec apply add-cancelled-status
```

**前置条件**:
- 提案状态必须为 `approved`
- 必须通过 validate 检查
- 必须有审批记录

**执行流程**:
```
Step 1: 检查审批状态
        → 确认所有审批已通过

Step 2: 备份现有 SoT
        → docs/sot/STATE_MACHINE.md.bak

Step 3: 应用变更
        → 修改 STATE_MACHINE.md
        → 更新版本号

Step 4: 生成代码变更
        → 更新 backend/models/enums.py
        → 更新测试文件

Step 5: 创建迁移记录
        → docs/changes/add-cancelled-status/APPLIED.md
```

**输出**:
```
✅ 变更已应用

📄 修改文件:
  - docs/sot/STATE_MACHINE.md (v2.8 → v2.9)
  - backend/models/enums.py
  - backend/tests/test_state_machine.py

📋 下一步:
  1. 运行测试: pytest backend/tests/
  2. 部署验证
  3. 归档: /spec archive add-cancelled-status
```

---

### 4. /spec archive

归档已部署的变更:

```bash
/spec archive add-cancelled-status
```

**执行流程**:
```
Step 1: 确认部署成功
        → 检查生产环境状态

Step 2: 更新变更日志
        → docs/sot/CHANGELOG.md

Step 3: 移动提案到归档
        → docs/changes/archived/add-cancelled-status/

Step 4: 更新版本清单
        → docs/sot/VERSION_MANIFEST.md
```

**输出**:
```
✅ 变更已归档

📂 归档位置: docs/changes/archived/add-cancelled-status/

📋 变更记录:
  - STATE_MACHINE.md: v2.8 → v2.9
  - 变更日期: 2025-12-30
  - 部署确认: 生产环境验证通过
```

---

## SoT 变更规则

### 允许的变更

| 变更类型 | 需要审批 | 自动验证 |
|----------|----------|----------|
| 新增状态 | ✅ | ✅ |
| 新增角色 | ✅ | ✅ |
| 新增错误码 | ✅ | ✅ |
| 修改描述 | ⚠️ | ✅ |
| 新增字段 | ✅ | ✅ |

### 禁止的变更

| 变更类型 | 原因 |
|----------|------|
| 删除状态 | 破坏性变更，需迁移 |
| 重命名状态 | 影响现有数据 |
| 修改状态流转 | 可能破坏业务逻辑 |
| 删除角色 | 影响权限系统 |

---

## 快速参考

```bash
# 完整流程
/spec proposal my-change    # 1. 创建提案
# ... 编辑提案文档 ...
/spec validate my-change    # 2. 验证提案
# ... 审批流程 ...
/spec apply my-change       # 3. 应用变更
# ... 部署验证 ...
/spec archive my-change     # 4. 归档
```
