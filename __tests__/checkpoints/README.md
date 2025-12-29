# Checkpoints - 测试检查点清单

> **基准文档**: AI_TEST_GUIDE_v2.1.md
> **创建日期**: 2025-12-23

---

## 目录结构

```
__tests__/checkpoints/
├── README.md                      # 本文件
├── A1-dashboard.yaml              # 老板驾驶舱
├── A2-fund-overview.yaml          # 资金总览
├── A3-project-pnl.yaml            # 项目盈亏
├── B1-topup-approval.yaml         # 充值审批
├── B2-daily-report-review.yaml    # 日报审核
├── B3-weekly-brief.yaml           # 周度简报
├── C1-project-mgmt.yaml           # 项目管理
├── C2-pitcher-mgmt.yaml           # 投手管理
├── C3-spend-detail.yaml           # 消耗明细
├── D1-monthly-settlement.yaml     # 月度结算
└── integration.yaml               # 跨模块集成
```

---

## 检查点格式

每个 YAML 文件包含以下结构：

```yaml
module: "{模块编号}-{模块名}"
spec_file: "docs/10.module-specs/{规格书}.md"
page_path: "/{页面路径}"
priority: P0/P1/P2

# 状态机（如适用）
state_machine:
  states: [...]
  transitions: [...]
  terminal_states: [...]

# 检查点列表
checkpoints:
  - id: CP-{MODULE}-{NNN}
    category: permission|ui|data|function|phase1
    description: "{描述}"
    spec_ref: "{规格书引用}"
    cases:
      - { ... }

# 覆盖统计
summary:
  total_checkpoints: N
  total_cases: N
```

---

## 5 类检查点

| 类型 | category | 说明 | 必须 |
|------|----------|------|------|
| 权限测试 | permission | 7 角色访问控制 | ✅ |
| 页面渲染 | ui | 元素可见性、文本内容 | ✅ |
| 数据状态 | data | loading/empty/error/success | ✅ |
| 功能操作 | function | CRUD、状态转换 | 按需 |
| Phase 1 规则 | phase1 | 高亮不阻断 | ✅ |

---

## 角色权限

每个模块的权限测试必须覆盖全部 7 个角色：

| 角色 | 说明 |
|------|------|
| ceo | 老板 |
| finance | 财务 |
| supervisor | 主管 |
| pitcher | 投手 |
| project_owner | 项目负责人 |
| account_manager | 户管 |
| admin | 管理员 |

---

## 检查点统计

| 模块 | 权限 | UI | 数据 | 功能 | Phase1 | 合计 |
|------|------|-----|------|------|--------|------|
| A1 驾驶舱 | 7 | 8 | 4 | 5 | 2 | 26 |
| A2 资金总览 | 7 | 7 | 4 | 3 | 2 | 23 |
| A3 项目盈亏 | 7 | 4 | 4 | 4 | 2 | 21 |
| B1 充值审批 | 7 | 4 | 4 | 8 | 1 | 24 |
| B2 日报审核 | 7 | 4 | 4 | 11 | 2 | 28 |
| B3 周度简报 | 7 | 3 | 4 | 4 | 1 | 19 |
| C1 项目管理 | 7 | 4 | 4 | 7 | 1 | 23 |
| C2 投手管理 | 7 | 2 | 4 | 5 | 1 | 19 |
| C3 消耗明细 | 7 | 3 | 4 | 5 | 1 | 20 |
| D1 月度结算 | 7 | 3 | 4 | 5 | 1 | 20 |
| 跨模块集成 | 2 | - | 2 | 4 | - | 8 |
| **合计** | **72** | **42** | **42** | **61** | **14** | **231** |

---

## 使用方法

### 1. 阅读检查点清单

在编写测试代码前，先阅读对应模块的 YAML 文件，了解需要覆盖的测试点。

### 2. 编写测试代码

根据检查点清单编写 Playwright 测试代码：

```typescript
// __tests__/e2e/a1-dashboard/dashboard.spec.ts

/**
 * @checkpoint checkpoints/A1-dashboard.yaml
 */
test.describe('CP-A1-001: 权限测试', () => {
  // 根据 YAML 中的 cases 编写测试
});
```

### 3. 验证覆盖率

测试完成后，对照 YAML 文件验证所有检查点是否覆盖。

---

## 关联文档

- [AI_TEST_GUIDE_v2.1.md](../../docs/3.dev-guides/AI_TEST_GUIDE_v2.1.md) - 测试编写指南
- [TEST_CASES_v3.md](../../docs/10.module-specs/TEST_CASES_v3.md) - 测试用例文档
- [docs/10.module-specs/](../../docs/10.module-specs/) - 模块规格书
