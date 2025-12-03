# Change: Backend Regression Baseline v1.0

**Status**: READY FOR VALIDATION
**Version**: 1.0
**Date**: 2025-12-02

## Why

### 原始问题

当前项目已有完整的后端回归测试套件和基础设施，但缺少制度层面的规范约束：

1. **回归基线未正式登记**
   - 已有 `BACKEND_REGRESSION_FREEZE_REPORT_v1.0.md` 冻结报告
   - 但未在 OpenSpec 体系中登记，无法追踪变更影响
   - 未明确作为后续版本对比的基准线

2. **测试规范未明确回归基线章节**
   - `AUTOMATION_TEST_SPEC_v1.4.md` 已有第 11 章「后端回归测试门槛」
   - 但缺少「回归基线」章节，未明确基线版本和对比方法

3. **Skill 文档未引用回归基线**
   - `ai-ad-api-automation-test/SKILL.md` 未明确引用回归基线报告
   - 未说明回归测试与基线的对比要求

4. **项目约定未强制回归测试任务**
   - 任何涉及 API/状态机的 change，tasks.md 中未强制要求回归测试任务
   - 缺少明确的「运行回归测试并保持全绿」的约定

## What Changes

### 1. OpenSpec Change 登记

| 文件 | 变更 |
|------|------|
| `openspec/changes/backend-regression-baseline-v1/proposal.md` | 新建变更提案（本文件） |
| `openspec/changes/backend-regression-baseline-v1/tasks.md` | 新建任务追踪清单 |

### 2. 测试规范更新 (`docs/testing/AUTOMATION_TEST_SPEC_v1.4.md`)

| 章节 | 变更 |
|------|------|
| 新增第 11.7 节「回归基线管理」 | 明确回归基线 v1.0 的定义、用途和维护方法 |

### 3. Skill 文档更新 (`.claude/skills/ai-ad-api-automation-test/SKILL.md`)

| 章节 | 变更 |
|------|------|
| 新增「回归基线引用」说明 | 引用 `BACKEND_REGRESSION_FREEZE_REPORT_v1.0.md` |
| 更新「回归测试执行」说明 | 明确与基线对比的要求 |

### 4. 项目约定更新 (`openspec/AGENTS.md` 或相关文档)

| 约定 | 变更 |
|------|------|
| API/状态机 change 强制任务 | 任何涉及 `backend/routers/*`、`backend/services/*`、`docs/2.sot/*` 的 change，tasks.md **MUST** 包含回归测试任务 |

## Impact

### 影响范围

- **Affected specs**: AUTOMATION_TEST_SPEC (文档更新)
- **Affected skills**: ai-ad-api-automation-test (文档更新)
- **Affected conventions**: OpenSpec change 流程约定（文档更新）

### 兼容性

- **NOT breaking**: 仅文档和流程层面的更新，不修改代码
- **向后兼容**: 不影响现有测试执行和 CI/CD 流程
- **无代码变更**: 不涉及任何业务代码修改

### 制度约束

- **强制回归测试**: 任何 API/状态机相关的 change，必须包含回归测试任务
- **基线对比**: 回归测试结果应与基线 v1.0 对比，识别回归问题
- **CI/CD 集成**: GitHub Actions 已配置回归测试 workflow，本 change 强化制度约束

## Migration

### 当前状态

- **回归测试套件**: 已完整实现，198 个测试用例全部通过
- **回归基线报告**: 已创建 `BACKEND_REGRESSION_FREEZE_REPORT_v1.0.md`
- **CI/CD 配置**: 已配置 `.github/workflows/regression-tests.yml`
- **测试脚本**: 已实现 `run_tests.py --type regression`

### 基线定义

**Backend Regression Baseline v1.0**：
- **日期**: 2025-12-02
- **测试结果**: 198 passed, 3 deselected, 0 failed
- **覆盖模块**: 6 个核心模块（Daily Reports, Trend Risk, Ledger, Ad Accounts, Topup, Transfers）
- **报告文档**: `docs/4.testing/BACKEND_REGRESSION_FREEZE_REPORT_v1.0.md`
- **执行命令**: `python run_tests.py --type regression`

### 后续维护

- **基线更新**: 当测试套件发生重大变更时，应创建新的基线版本（v1.1, v1.2, ...）
- **对比方法**: 后续版本回归测试结果应与最新基线对比，识别新增失败用例
- **文档同步**: 基线更新时同步更新 AUTOMATION_TEST_SPEC 和 SKILL.md

---

## Changes Summary

### 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `openspec/changes/backend-regression-baseline-v1/proposal.md` | 新建 | 变更提案文档 |
| `openspec/changes/backend-regression-baseline-v1/tasks.md` | 新建 | 任务追踪清单 |
| `docs/testing/AUTOMATION_TEST_SPEC_v1.4.md` | 修改 | 新增第 11.7 节「回归基线管理」 |
| `.claude/skills/ai-ad-api-automation-test/SKILL.md` | 修改 | 新增回归基线引用说明 |
| `openspec/AGENTS.md` | 修改 | 更新 change 流程约定，强制回归测试任务 |

### 已验证的基础设施

以下基础设施已确认就绪：

- **回归测试脚本** (`run_tests.py`)
  - `--type regression` 参数已实现
  - 覆盖 6 个核心测试套件

- **CI/CD 配置** (`.github/workflows/regression-tests.yml`)
  - 触发条件：推送到 `main` 或 `sot-fix-*` 分支
  - 执行回归测试并阻止失败合并

- **回归基线报告** (`docs/4.testing/BACKEND_REGRESSION_FREEZE_REPORT_v1.0.md`)
  - 详细记录了基线测试结果和统计信息
  - 包含各模块测试覆盖详情

---

## Archive Recommendation

### 验证步骤

1. 确认文档更新完成：
   - [x] AUTOMATION_TEST_SPEC 新增回归基线章节
   - [x] SKILL.md 新增回归基线引用
   - [x] OpenSpec AGENTS.md 更新 change 流程约定

2. 验证回归测试仍可通过：
```bash
python run_tests.py --type regression
```

3. 如果所有文档更新完成且测试通过，执行归档：
```bash
openspec validate backend-regression-baseline-v1 --strict
openspec archive backend-regression-baseline-v1 --yes
```

### 归档验证清单

- [x] OpenSpec change 文件已创建
- [x] AUTOMATION_TEST_SPEC 已更新
- [x] SKILL.md 已更新
- [x] OpenSpec 约定已更新
- [ ] 回归测试运行验证通过（待执行）
- [ ] OpenSpec validate 通过（待执行）

