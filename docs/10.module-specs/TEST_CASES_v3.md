# MVP 模块 E2E 测试用例文档

> **版本**: v3.0
> **创建日期**: 2025-12-23
> **基准**: AI_TEST_GUIDE_v2.1.md + docs/10.module-specs/
> **技术栈**: Playwright + TypeScript
> **覆盖模块**: A1-A3, B1-B3, C1-C3, D1

---

## 目录

1. [测试规范与约定](#1-测试规范与约定)
2. [测试基础设施](#2-测试基础设施)
3. [A1 老板驾驶舱](#3-a1-老板驾驶舱)
4. [A2 资金总览](#4-a2-资金总览)
5. [A3 项目盈亏](#5-a3-项目盈亏)
6. [B1 充值审批](#6-b1-充值审批)
7. [B2 日报审核](#7-b2-日报审核)
8. [B3 周度简报](#8-b3-周度简报)
9. [C1 项目管理](#9-c1-项目管理)
10. [C2 投手管理](#10-c2-投手管理)
11. [C3 消耗明细](#11-c3-消耗明细)
12. [D1 月度结算](#12-d1-月度结算)
13. [跨模块集成测试](#13-跨模块集成测试)
14. [覆盖率汇总](#14-覆盖率汇总)

---

## 1. 测试规范与约定

### 1.1 检查点类型 (5 类必须覆盖)

| 类型 | 代码 | 说明 | 必须 |
|------|------|------|------|
| 权限测试 | permission | 7 角色访问控制 | ✅ |
| 页面渲染 | ui | 元素可见性、文本内容 | ✅ |
| 数据状态 | data | loading/empty/error/success | ✅ |
| 功能操作 | function | CRUD、状态转换 | 按需 |
| Phase 1 规则 | phase1 | 高亮不阻断 | ✅ |

### 1.2 合法角色清单 (7 角色)

```typescript
type TestRole = 'ceo' | 'finance' | 'supervisor' | 'pitcher' | 'project_owner' | 'account_manager' | 'admin';
```

| 角色 | 中文名 | 职责 |
|------|--------|------|
| ceo | 老板 | 资金安全、公司盈亏、最终决策 |
| finance | 财务 | 资金出入准确、数据真实、对账 |
| supervisor | 主管 | 团队产出、投手管理、日常监督 |
| pitcher | 投手 | CPL 达标、日报准确、执行投放 |
| project_owner | 项目负责人 | 项目盈亏、资金使用效率 |
| account_manager | 户管 | 账户分配、账户状态监控 |
| admin | 管理员 | 系统配置（不参与业务） |

### 1.3 检查点编号规则

```
CP-{MODULE}-{NNN}

MODULE: A1/A2/A3/B1/B2/B3/C1/C2/C3/D1/INT
NNN: 001-999

示例: CP-A1-001 (A1 模块第 1 个检查点)
```

### 1.4 断言规范

```typescript
// ✅ 确定性断言
await expect(page).toHaveURL('/daily-reports');
await expect(page.locator('h1')).toHaveText('日报管理');
await expect(page.locator('[data-testid="table"]')).toBeVisible();
await expect(page.locator('button')).toBeEnabled();

// ❌ 禁止使用
expect(text).toContain('日报');  // 模糊
await page.waitForTimeout(3000); // 硬编码等待
```

### 1.5 选择器优先级

```
1️⃣ data-testid (推荐)
2️⃣ role + aria-label
3️⃣ 唯一 ID
4️⃣ 组合选择器
❌ 纯文本、路径选择器、索引选择器
```

---

## 2. 测试基础设施

### 2.1 目录结构

```
__tests__/
├── e2e/
│   ├── a1-dashboard/
│   │   └── dashboard.spec.ts
│   ├── a2-fund-overview/
│   │   └── fund-overview.spec.ts
│   ├── a3-project-pnl/
│   │   └── project-pnl.spec.ts
│   ├── b1-topup-approval/
│   │   └── topup-approval.spec.ts
│   ├── b2-daily-report-review/
│   │   └── daily-report-review.spec.ts
│   ├── b3-weekly-brief/
│   │   └── weekly-brief.spec.ts
│   ├── c1-project-mgmt/
│   │   └── project-mgmt.spec.ts
│   ├── c2-pitcher-mgmt/
│   │   └── pitcher-mgmt.spec.ts
│   ├── c3-spend-detail/
│   │   └── spend-detail.spec.ts
│   ├── d1-monthly-settlement/
│   │   └── monthly-settlement.spec.ts
│   └── integration/
│       └── cross-module.spec.ts
│
├── fixtures/
│   ├── test-accounts.ts
│   └── test-data.ts
│
└── utils/
    ├── auth.ts
    └── assertions.ts
```

### 2.2 测试账号配置

```typescript
// __tests__/fixtures/test-accounts.ts

export const TEST_ACCOUNTS = {
  ceo: {
    email: 'ceo@test.local',
    password: 'test123',
  },
  finance: {
    email: 'finance@test.local',
    password: 'test123',
  },
  supervisor: {
    email: 'supervisor@test.local',
    password: 'test123',
  },
  pitcher: {
    email: 'pitcher@test.local',
    password: 'test123',
  },
  project_owner: {
    email: 'owner@test.local',
    password: 'test123',
  },
  account_manager: {
    email: 'am@test.local',
    password: 'test123',
  },
  admin: {
    email: 'admin@test.local',
    password: 'test123',
  },
} as const;

export type TestRole = keyof typeof TEST_ACCOUNTS;
```

### 2.3 登录辅助函数

```typescript
// __tests__/utils/auth.ts

import { Page } from '@playwright/test';
import { TEST_ACCOUNTS, TestRole } from '../fixtures/test-accounts';

export async function loginAs(page: Page, role: TestRole): Promise<void> {
  const account = TEST_ACCOUNTS[role];

  await page.goto('/login');
  await page.fill('[data-testid="email-input"]', account.email);
  await page.fill('[data-testid="password-input"]', account.password);
  await page.click('[data-testid="login-button"]');

  // 等待登录完成
  await page.waitForURL(/^(?!.*\/login).*$/);
}

export async function logout(page: Page): Promise<void> {
  await page.click('[data-testid="user-menu"]');
  await page.click('[data-testid="logout-button"]');
  await page.waitForURL('/login');
}
```

---

## 3. A1 老板驾驶舱

**规格书**: [A1-dashboard.md](./A1-dashboard.md)
**页面路径**: `/`
**模块优先级**: P0

### 3.1 检查点清单

```yaml
# checkpoints/A1-dashboard.yaml

module: "A1-dashboard"
spec_file: "docs/10.module-specs/A1-dashboard.md"
page_path: "/"

checkpoints:
  # ===== CP-A1-001: 权限测试 =====
  - id: CP-A1-001
    category: permission
    description: 驾驶舱页面访问权限
    spec_ref: "§1.2 用户角色"
    cases:
      - { role: ceo, expected: allowed, scope: "全公司数据" }
      - { role: finance, expected: allowed, scope: "财务指标" }
      - { role: supervisor, expected: allowed, scope: "团队数据" }
      - { role: pitcher, expected: allowed, scope: "个人数据" }
      - { role: project_owner, expected: allowed, scope: "项目数据" }
      - { role: account_manager, expected: allowed, scope: "账户数据" }
      - { role: admin, expected: allowed, scope: "系统概览" }

  # ===== CP-A1-002: 页面渲染测试 =====
  - id: CP-A1-002
    category: ui
    description: 页面元素渲染
    spec_ref: "§3 UI 规范"
    cases:
      - { element: 页面标题, selector: "h1", expected: "仪表盘" }
      - { element: KPI卡片区, selector: "[data-testid='kpi-cards']", expected: visible }
      - { element: 本月消耗卡片, selector: "[data-testid='kpi-spend']", expected: visible }
      - { element: 本月进粉卡片, selector: "[data-testid='kpi-conversions']", expected: visible }
      - { element: 整体CPL卡片, selector: "[data-testid='kpi-cpl']", expected: visible }
      - { element: 预计毛利卡片, selector: "[data-testid='kpi-profit']", expected: visible }
      - { element: 运营状态区, selector: "[data-testid='ops-status']", expected: visible }
      - { element: Top列表区, selector: "[data-testid='top-lists']", expected: visible }

  # ===== CP-A1-003: 数据状态测试 =====
  - id: CP-A1-003
    category: data
    description: 数据加载状态
    spec_ref: "§2 数据需求"
    cases:
      - { scenario: loading, expected: 骨架屏, selector: "[data-testid='loading-skeleton']" }
      - { scenario: empty, expected: "暂无数据", selector: "[data-testid='empty-state']" }
      - { scenario: error, expected: 错误提示+重试, selector: "[data-testid='error-state']" }
      - { scenario: success, expected: KPI数据显示 }

  # ===== CP-A1-004: 功能操作测试 =====
  - id: CP-A1-004
    category: function
    description: 核心功能操作
    spec_ref: "§5 API 接口"
    cases:
      - { action: 时间范围切换, expected: 数据刷新 }
      - { action: KPI卡片点击, expected: 趋势图联动 }
      - { action: Top项目点击, expected: 跳转项目详情 }
      - { action: 待处理事项点击, expected: 跳转对应页面 }
      - { action: 手动刷新, expected: 重新加载数据 }

  # ===== CP-A1-005: Phase 1 规则测试 =====
  - id: CP-A1-005
    category: phase1
    description: Phase 1 不阻断规则
    spec_ref: "MASTER.md §3.1"
    cases:
      - { scenario: CPL超标项目, expected: 红色高亮+仍可点击 }
      - { scenario: 异常项目数>0, expected: 黄色高亮+不阻断导航 }

summary:
  total_checkpoints: 5
  permission_cases: 7
  ui_cases: 8
  data_cases: 4
  function_cases: 5
  phase1_cases: 2
  total_cases: 26
```

### 3.2 测试代码

```typescript
// __tests__/e2e/a1-dashboard/dashboard.spec.ts

import { test, expect } from '@playwright/test';
import { loginAs } from '../../utils/auth';
import { TestRole } from '../../fixtures/test-accounts';

/**
 * A1 老板驾驶舱测试
 *
 * @spec docs/10.module-specs/A1-dashboard.md
 * @checkpoint checkpoints/A1-dashboard.yaml
 */

// ============================================================
// CP-A1-001: 权限测试
// ============================================================
test.describe('CP-A1-001: 权限测试', () => {
  // 所有角色都可访问驾驶舱，但数据范围不同
  const allRoles: TestRole[] = ['ceo', 'finance', 'supervisor', 'pitcher', 'project_owner', 'account_manager', 'admin'];

  for (const role of allRoles) {
    test(`${role} 可以访问驾驶舱`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto('/');

      await expect(page).toHaveURL('/');
      await expect(page.locator('h1')).toBeVisible();
    });
  }

  test('ceo 可见全公司数据', async ({ page }) => {
    await loginAs(page, 'ceo');
    await page.goto('/');

    // 验证无筛选限制提示
    await expect(page.locator('[data-testid="data-scope-all"]')).toBeVisible();
  });

  test('pitcher 只见个人数据', async ({ page }) => {
    await loginAs(page, 'pitcher');
    await page.goto('/');

    // 验证有数据范围提示
    await expect(page.locator('[data-testid="data-scope-personal"]')).toBeVisible();
  });
});

// ============================================================
// CP-A1-002: 页面渲染测试
// ============================================================
test.describe('CP-A1-002: 页面渲染', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'ceo');
    await page.goto('/');
  });

  test('显示页面标题', async ({ page }) => {
    await expect(page.locator('h1')).toHaveText('仪表盘');
  });

  test('显示 4 个 KPI 卡片', async ({ page }) => {
    await expect(page.locator('[data-testid="kpi-cards"]')).toBeVisible();
    await expect(page.locator('[data-testid="kpi-spend"]')).toBeVisible();
    await expect(page.locator('[data-testid="kpi-conversions"]')).toBeVisible();
    await expect(page.locator('[data-testid="kpi-cpl"]')).toBeVisible();
    await expect(page.locator('[data-testid="kpi-profit"]')).toBeVisible();
  });

  test('显示运营状态区域', async ({ page }) => {
    await expect(page.locator('[data-testid="ops-status"]')).toBeVisible();
  });

  test('显示 Top 列表', async ({ page }) => {
    await expect(page.locator('[data-testid="top-lists"]')).toBeVisible();
    await expect(page.locator('[data-testid="top-spend"]')).toBeVisible();
    await expect(page.locator('[data-testid="top-roas-worst"]')).toBeVisible();
  });
});

// ============================================================
// CP-A1-003: 数据状态测试
// ============================================================
test.describe('CP-A1-003: 数据状态', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'ceo');
  });

  test('加载中显示骨架屏', async ({ page }) => {
    await page.route('/api/v1/dashboard*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.continue();
    });

    await page.goto('/');
    await expect(page.locator('[data-testid="loading-skeleton"]')).toBeVisible();
  });

  test('空数据显示提示', async ({ page }) => {
    await page.route('/api/v1/dashboard*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          kpi: { spend: 0, conversions: 0, cpl: null, profit: 0 },
          top_spend: [],
          top_roas_worst: []
        }),
      });
    });

    await page.goto('/');
    await expect(page.locator('[data-testid="empty-state"]')).toBeVisible();
  });

  test('错误时显示错误提示', async ({ page }) => {
    await page.route('/api/v1/dashboard*', (route) => {
      route.fulfill({ status: 500 });
    });

    await page.goto('/');
    await expect(page.locator('[data-testid="error-state"]')).toBeVisible();
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
  });

  test('成功加载显示 KPI 数据', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('[data-testid="kpi-spend"]');

    // KPI 卡片应该显示数值
    const spendCard = page.locator('[data-testid="kpi-spend"]');
    await expect(spendCard).toContainText('¥');
  });
});

// ============================================================
// CP-A1-004: 功能操作测试
// ============================================================
test.describe('CP-A1-004: 功能操作', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'ceo');
    await page.goto('/');
    await page.waitForSelector('[data-testid="kpi-cards"]');
  });

  test('时间范围切换刷新数据', async ({ page }) => {
    // 监听 API 请求
    const requestPromise = page.waitForRequest(req =>
      req.url().includes('/api/v1/dashboard') && req.url().includes('period=7d')
    );

    await page.click('[data-testid="time-filter"]');
    await page.click('[data-testid="time-option-7d"]');

    await requestPromise;
  });

  test('KPI 卡片点击联动趋势图', async ({ page }) => {
    await page.click('[data-testid="kpi-spend"]');

    // 验证趋势图切换到消耗指标
    await expect(page.locator('[data-testid="trend-chart-spend"]')).toBeVisible();
    // 验证卡片选中状态
    await expect(page.locator('[data-testid="kpi-spend"]')).toHaveClass(/selected|active/);
  });

  test('Top 项目点击跳转详情', async ({ page }) => {
    await page.click('[data-testid="top-spend"] [data-testid="top-item-0"]');

    await expect(page).toHaveURL(/\/projects\/\d+/);
  });

  test('待处理事项点击跳转', async ({ page }) => {
    await page.click('[data-testid="pending-topups"]');

    await expect(page).toHaveURL(/\/topups.*status=pending/);
  });

  test('刷新按钮重新加载', async ({ page }) => {
    const requestPromise = page.waitForRequest(req =>
      req.url().includes('/api/v1/dashboard')
    );

    await page.click('[data-testid="refresh-button"]');

    await requestPromise;
  });
});

// ============================================================
// CP-A1-005: Phase 1 规则测试
// ============================================================
test.describe('CP-A1-005: Phase 1 不阻断规则', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'ceo');
  });

  test('CPL 超标项目高亮但可点击', async ({ page }) => {
    // Mock 包含 CPL 超标项目的数据
    await page.route('/api/v1/dashboard*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          kpi: { spend: 100000, conversions: 50, cpl: 2000, profit: -50000 },
          top_spend: [{
            id: 'proj-1',
            name: '超标项目',
            cpl: 2000,
            target_cpl: 100,
            is_abnormal: true,
          }],
          top_roas_worst: [],
        }),
      });
    });

    await page.goto('/');
    await page.waitForSelector('[data-testid="top-spend"]');

    // 1. 验证高亮样式
    const abnormalItem = page.locator('[data-testid="top-item-0"]');
    await expect(abnormalItem).toHaveClass(/bg-red-50|text-red|warning/);

    // 2. 验证仍可点击（Phase 1 不阻断）
    await expect(abnormalItem).toBeEnabled();
    await abnormalItem.click();
    await expect(page).toHaveURL(/\/projects\/proj-1/);
  });

  test('异常项目数高亮但导航不阻断', async ({ page }) => {
    await page.route('/api/v1/dashboard*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          kpi: { spend: 100000, conversions: 100, cpl: 1000, profit: 0 },
          ops_status: {
            active_projects: 10,
            abnormal_projects: 3,  // 有异常项目
            pending_topups: 5,
          },
          top_spend: [],
          top_roas_worst: [],
        }),
      });
    });

    await page.goto('/');

    // 验证异常项目数高亮
    const abnormalCount = page.locator('[data-testid="abnormal-projects"]');
    await expect(abnormalCount).toHaveClass(/text-amber|text-yellow|warning/);

    // 验证导航正常工作
    await page.click('[data-testid="nav-projects"]');
    await expect(page).toHaveURL('/projects');
  });
});
```

### 3.3 覆盖率报告

```markdown
## 测试覆盖率报告: A1 老板驾驶舱

### 1. 检查点覆盖

| 检查点 | 描述 | 用例数 | 状态 |
|--------|------|--------|------|
| CP-A1-001 | 权限测试 | 9 | ✅ |
| CP-A1-002 | 页面渲染 | 5 | ✅ |
| CP-A1-003 | 数据状态 | 4 | ✅ |
| CP-A1-004 | 功能操作 | 5 | ✅ |
| CP-A1-005 | Phase 1 | 2 | ✅ |

### 2. 角色权限覆盖

| 角色 | 预期 | 数据范围 | 测试 |
|------|------|----------|------|
| ceo | allowed | 全公司 | ✅ |
| finance | allowed | 财务指标 | ✅ |
| supervisor | allowed | 团队 | ✅ |
| pitcher | allowed | 个人 | ✅ |
| project_owner | allowed | 项目 | ✅ |
| account_manager | allowed | 账户 | ✅ |
| admin | allowed | 系统概览 | ✅ |

### 3. 总计

- 测试文件: 1 (dashboard.spec.ts)
- 测试用例: 25
- 覆盖率: 100%

### 4. 追溯

- 规格书: docs/10.module-specs/A1-dashboard.md
- 检查点: checkpoints/A1-dashboard.yaml
```

---

## 4. A2 资金总览

**规格书**: [A2-fund-overview.md](./A2-fund-overview.md)
**页面路径**: `/fund`
**模块优先级**: P0

### 4.1 检查点清单

```yaml
# checkpoints/A2-fund-overview.yaml

module: "A2-fund-overview"
spec_file: "docs/10.module-specs/A2-fund-overview.md"
page_path: "/fund"

checkpoints:
  # ===== CP-A2-001: 权限测试 =====
  - id: CP-A2-001
    category: permission
    description: 资金总览页访问权限
    spec_ref: "§1.2 用户角色"
    cases:
      - { role: ceo, expected: allowed, scope: "全公司" }
      - { role: finance, expected: allowed, scope: "全公司+导出" }
      - { role: supervisor, expected: denied }
      - { role: pitcher, expected: denied }
      - { role: project_owner, expected: allowed, scope: "项目关联" }
      - { role: account_manager, expected: allowed, scope: "管理账户" }
      - { role: admin, expected: denied }

  # ===== CP-A2-002: 页面渲染测试 =====
  - id: CP-A2-002
    category: ui
    description: 页面元素渲染
    spec_ref: "§3 UI 规范"
    cases:
      - { element: 页面标题, selector: "h1", expected: "资金总览" }
      - { element: 累计充值卡片, selector: "[data-testid='fund-topup']", expected: visible }
      - { element: 累计消耗卡片, selector: "[data-testid='fund-spend']", expected: visible }
      - { element: 当前余额卡片, selector: "[data-testid='fund-balance']", expected: visible }
      - { element: 应收款卡片, selector: "[data-testid='fund-receivable']", expected: visible }
      - { element: 资金占用卡片, selector: "[data-testid='fund-occupied']", expected: visible }
      - { element: 流水表格, selector: "[data-testid='fund-table']", expected: visible }

  # ===== CP-A2-003: 数据状态测试 =====
  - id: CP-A2-003
    category: data
    description: 数据加载状态
    spec_ref: "§2 数据需求"
    cases:
      - { scenario: loading, expected: 骨架屏 }
      - { scenario: empty, expected: "暂无资金记录" }
      - { scenario: error, expected: 错误提示 }
      - { scenario: success, expected: 资金数据 }

  # ===== CP-A2-004: 功能操作测试 =====
  - id: CP-A2-004
    category: function
    description: 核心功能操作
    spec_ref: "§5 API 接口"
    cases:
      - { action: 日期筛选, expected: 数据更新 }
      - { action: 账户筛选, expected: 数据过滤 }
      - { action: 导出, role: finance, expected: 下载Excel }

  # ===== CP-A2-005: Phase 1 规则测试 =====
  - id: CP-A2-005
    category: phase1
    description: Phase 1 不阻断规则
    spec_ref: "MASTER.md §3.1"
    cases:
      - { scenario: 负余额, expected: 红色显示+不阻断 }
      - { scenario: 资金占用高, expected: 警告高亮+可操作 }

summary:
  total_checkpoints: 5
  permission_cases: 7
  ui_cases: 7
  data_cases: 4
  function_cases: 3
  phase1_cases: 2
  total_cases: 23
```

### 4.2 测试代码

```typescript
// __tests__/e2e/a2-fund-overview/fund-overview.spec.ts

import { test, expect } from '@playwright/test';
import { loginAs } from '../../utils/auth';
import { TestRole } from '../../fixtures/test-accounts';

/**
 * A2 资金总览测试
 *
 * @spec docs/10.module-specs/A2-fund-overview.md
 * @checkpoint checkpoints/A2-fund-overview.yaml
 */

// ============================================================
// CP-A2-001: 权限测试
// ============================================================
test.describe('CP-A2-001: 权限测试', () => {
  const allowedRoles: TestRole[] = ['ceo', 'finance', 'project_owner', 'account_manager'];
  const deniedRoles: TestRole[] = ['supervisor', 'pitcher', 'admin'];

  for (const role of allowedRoles) {
    test(`${role} 可以访问资金总览`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto('/fund');

      await expect(page).toHaveURL('/fund');
      await expect(page.locator('h1')).toHaveText('资金总览');
    });
  }

  for (const role of deniedRoles) {
    test(`${role} 不能访问资金总览`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto('/fund');

      await expect(page).toHaveURL('/unauthorized');
    });
  }

  test('finance 有导出权限', async ({ page }) => {
    await loginAs(page, 'finance');
    await page.goto('/fund');

    await expect(page.locator('[data-testid="export-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="export-button"]')).toBeEnabled();
  });

  test('project_owner 只见项目关联账户', async ({ page }) => {
    await loginAs(page, 'project_owner');
    await page.goto('/fund');

    await expect(page.locator('[data-testid="data-scope-project"]')).toBeVisible();
  });
});

// ============================================================
// CP-A2-002: 页面渲染测试
// ============================================================
test.describe('CP-A2-002: 页面渲染', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'ceo');
    await page.goto('/fund');
  });

  test('显示页面标题', async ({ page }) => {
    await expect(page.locator('h1')).toHaveText('资金总览');
  });

  test('显示 5 个资金卡片', async ({ page }) => {
    await expect(page.locator('[data-testid="fund-topup"]')).toBeVisible();
    await expect(page.locator('[data-testid="fund-spend"]')).toBeVisible();
    await expect(page.locator('[data-testid="fund-balance"]')).toBeVisible();
    await expect(page.locator('[data-testid="fund-receivable"]')).toBeVisible();
    await expect(page.locator('[data-testid="fund-occupied"]')).toBeVisible();
  });

  test('显示资金流水表格', async ({ page }) => {
    await expect(page.locator('[data-testid="fund-table"]')).toBeVisible();

    // 验证表头
    const headers = page.locator('[data-testid="fund-table"] th');
    await expect(headers.nth(0)).toHaveText('时间');
    await expect(headers.nth(1)).toHaveText('类型');
    await expect(headers.nth(2)).toHaveText('金额');
  });
});

// ============================================================
// CP-A2-003: 数据状态测试
// ============================================================
test.describe('CP-A2-003: 数据状态', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'ceo');
  });

  test('加载中显示骨架屏', async ({ page }) => {
    await page.route('/api/v1/fund*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.continue();
    });

    await page.goto('/fund');
    await expect(page.locator('[data-testid="loading-skeleton"]')).toBeVisible();
  });

  test('空数据显示提示', async ({ page }) => {
    await page.route('/api/v1/fund*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          summary: { topup: 0, spend: 0, balance: 0 },
          transactions: []
        }),
      });
    });

    await page.goto('/fund');
    await expect(page.locator('[data-testid="empty-state"]')).toBeVisible();
  });

  test('错误时显示错误提示', async ({ page }) => {
    await page.route('/api/v1/fund*', (route) => {
      route.fulfill({ status: 500 });
    });

    await page.goto('/fund');
    await expect(page.locator('[data-testid="error-state"]')).toBeVisible();
  });

  test('成功加载显示数据', async ({ page }) => {
    await page.goto('/fund');
    await page.waitForSelector('[data-testid="fund-balance"]');

    await expect(page.locator('[data-testid="fund-balance"]')).toContainText('¥');
  });
});

// ============================================================
// CP-A2-004: 功能操作测试
// ============================================================
test.describe('CP-A2-004: 功能操作', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'finance');
    await page.goto('/fund');
    await page.waitForSelector('[data-testid="fund-table"]');
  });

  test('日期筛选更新数据', async ({ page }) => {
    const requestPromise = page.waitForRequest(req =>
      req.url().includes('/api/v1/fund') && req.url().includes('start_date')
    );

    await page.click('[data-testid="date-filter"]');
    await page.fill('[data-testid="date-start"]', '2024-01-01');
    await page.fill('[data-testid="date-end"]', '2024-01-31');
    await page.click('[data-testid="date-apply"]');

    await requestPromise;
  });

  test('账户筛选过滤数据', async ({ page }) => {
    const requestPromise = page.waitForRequest(req =>
      req.url().includes('/api/v1/fund') && req.url().includes('account_id')
    );

    await page.click('[data-testid="account-filter"]');
    await page.click('[data-testid="account-option-1"]');

    await requestPromise;
  });

  test('导出下载 Excel', async ({ page }) => {
    const downloadPromise = page.waitForEvent('download');

    await page.click('[data-testid="export-button"]');

    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/\.xlsx$/);
  });
});

// ============================================================
// CP-A2-005: Phase 1 规则测试
// ============================================================
test.describe('CP-A2-005: Phase 1 不阻断规则', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'ceo');
  });

  test('负余额红色显示但不阻断', async ({ page }) => {
    await page.route('/api/v1/fund*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          summary: {
            topup: 100000,
            spend: 150000,
            balance: -50000,  // 负余额
          },
          transactions: [],
        }),
      });
    });

    await page.goto('/fund');

    // 验证负余额红色显示
    const balanceCard = page.locator('[data-testid="fund-balance"]');
    await expect(balanceCard).toHaveClass(/text-red|negative/);
    await expect(balanceCard).toContainText('-¥');

    // 验证导航不阻断
    await page.click('[data-testid="nav-projects"]');
    await expect(page).toHaveURL('/projects');
  });
});
```

### 4.3 覆盖率报告

```markdown
## 测试覆盖率报告: A2 资金总览

### 1. 检查点覆盖

| 检查点 | 描述 | 用例数 | 状态 |
|--------|------|--------|------|
| CP-A2-001 | 权限测试 | 9 | ✅ |
| CP-A2-002 | 页面渲染 | 3 | ✅ |
| CP-A2-003 | 数据状态 | 4 | ✅ |
| CP-A2-004 | 功能操作 | 3 | ✅ |
| CP-A2-005 | Phase 1 | 1 | ✅ |

### 2. 角色权限覆盖

| 角色 | 预期 | 测试 |
|------|------|------|
| ceo | allowed | ✅ |
| finance | allowed | ✅ |
| supervisor | denied | ✅ |
| pitcher | denied | ✅ |
| project_owner | allowed | ✅ |
| account_manager | allowed | ✅ |
| admin | denied | ✅ |

### 3. 总计

- 测试文件: 1 (fund-overview.spec.ts)
- 测试用例: 20
- 覆盖率: 100%
```

---

## 5. A3 项目盈亏

**规格书**: [A3-project-pnl.md](./A3-project-pnl.md)
**页面路径**: `/projects/pnl`
**模块优先级**: P0

### 5.1 检查点清单

```yaml
# checkpoints/A3-project-pnl.yaml

module: "A3-project-pnl"
spec_file: "docs/10.module-specs/A3-project-pnl.md"
page_path: "/projects/pnl"

checkpoints:
  - id: CP-A3-001
    category: permission
    description: 项目盈亏页访问权限
    cases:
      - { role: ceo, expected: allowed, scope: "全公司" }
      - { role: finance, expected: allowed, scope: "财务视图" }
      - { role: supervisor, expected: denied }
      - { role: pitcher, expected: denied }
      - { role: project_owner, expected: allowed, scope: "自己项目" }
      - { role: account_manager, expected: denied }
      - { role: admin, expected: denied }

  - id: CP-A3-002
    category: ui
    description: 页面元素渲染
    cases:
      - { element: 页面标题, expected: "项目盈亏" }
      - { element: 利润卡片, selector: "[data-testid='pnl-profit']" }
      - { element: 盈亏表格, selector: "[data-testid='pnl-table']" }
      - { element: 趋势图, selector: "[data-testid='pnl-chart']" }

  - id: CP-A3-003
    category: data
    description: 数据加载状态
    cases:
      - { scenario: loading, expected: 骨架屏 }
      - { scenario: empty, expected: "暂无项目数据" }
      - { scenario: error, expected: 错误提示 }
      - { scenario: success, expected: 盈亏数据 }

  - id: CP-A3-004
    category: function
    description: 核心功能操作
    cases:
      - { action: 维度切换, expected: 表格视图切换 }
      - { action: 排序, expected: 按列排序 }
      - { action: 日期筛选, expected: 数据更新 }
      - { action: 点击项目行, expected: 跳转详情 }

  - id: CP-A3-005
    category: phase1
    description: Phase 1 不阻断规则
    cases:
      - { scenario: 亏损项目, expected: 红色显示+可操作 }
      - { scenario: CPL超标, expected: 黄色警告+可操作 }

summary:
  total_checkpoints: 5
  total_cases: 21
```

### 5.2 测试代码 (摘要)

```typescript
// __tests__/e2e/a3-project-pnl/project-pnl.spec.ts

import { test, expect } from '@playwright/test';
import { loginAs } from '../../utils/auth';
import { TestRole } from '../../fixtures/test-accounts';

/**
 * A3 项目盈亏测试
 */

test.describe('CP-A3-001: 权限测试', () => {
  const allowedRoles: TestRole[] = ['ceo', 'finance', 'project_owner'];
  const deniedRoles: TestRole[] = ['supervisor', 'pitcher', 'account_manager', 'admin'];

  for (const role of allowedRoles) {
    test(`${role} 可以访问`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto('/projects/pnl');
      await expect(page).toHaveURL('/projects/pnl');
    });
  }

  for (const role of deniedRoles) {
    test(`${role} 不能访问`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto('/projects/pnl');
      await expect(page).toHaveURL('/unauthorized');
    });
  }
});

test.describe('CP-A3-005: Phase 1 不阻断规则', () => {
  test('亏损项目红色显示但可操作', async ({ page }) => {
    await loginAs(page, 'ceo');

    await page.route('/api/v1/projects/pnl*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{
            id: 'proj-loss',
            name: '亏损项目',
            spend: 100000,
            revenue: 50000,
            profit: -50000,  // 亏损
          }],
        }),
      });
    });

    await page.goto('/projects/pnl');

    // 验证亏损红色显示
    const profitCell = page.locator('[data-testid="profit-cell-proj-loss"]');
    await expect(profitCell).toHaveClass(/text-red|negative/);

    // 验证可点击
    await page.click('[data-testid="row-proj-loss"]');
    await expect(page).toHaveURL(/\/projects\/proj-loss/);
  });
});
```

---

## 6. B1 充值审批

**规格书**: [B1-topup-approval.md](./B1-topup-approval.md)
**页面路径**: `/topups`
**模块优先级**: P1

### 6.1 检查点清单

```yaml
# checkpoints/B1-topup-approval.yaml

module: "B1-topup-approval"
spec_file: "docs/10.module-specs/B1-topup-approval.md"
page_path: "/topups"

checkpoints:
  - id: CP-B1-001
    category: permission
    description: 充值审批页访问权限
    cases:
      - { role: ceo, expected: allowed, action: "审批" }
      - { role: finance, expected: allowed, action: "审批" }
      - { role: supervisor, expected: allowed, action: "确认数据" }
      - { role: pitcher, expected: denied }
      - { role: project_owner, expected: allowed, action: "创建+查看" }
      - { role: account_manager, expected: denied }
      - { role: admin, expected: denied }

  - id: CP-B1-002
    category: ui
    description: 页面元素渲染
    cases:
      - { element: 页面标题, expected: "充值审批" }
      - { element: 充值列表, selector: "[data-testid='topup-table']" }
      - { element: 新建按钮, selector: "[data-testid='create-topup-btn']" }
      - { element: 状态筛选, selector: "[data-testid='status-filter']" }

  - id: CP-B1-003
    category: data
    description: 数据加载状态
    cases:
      - { scenario: loading, expected: 骨架屏 }
      - { scenario: empty, expected: "暂无充值记录" }
      - { scenario: error, expected: 错误提示 }
      - { scenario: success, expected: 充值列表 }

  - id: CP-B1-004
    category: function
    description: 状态机操作 (7 状态)
    cases:
      - { transition: "draft→pending_review", actor: project_owner }
      - { transition: "pending_review→finance_approve", actor: supervisor }
      - { transition: "finance_approve→paid", actor: finance }
      - { transition: "paid→completed", actor: finance }
      - { transition: "pending_review→rejected", actor: supervisor }
      - { transition: "pending_review→voided", actor: project_owner }
      - { illegal: "draft→paid", expected: "400 ST-001" }
      - { illegal: "completed→paid", expected: "400 ST-002" }

  - id: CP-B1-005
    category: phase1
    description: Phase 1 不阻断规则
    cases:
      - { scenario: 大额充值, expected: 警告高亮+可审批 }

summary:
  total_checkpoints: 5
  total_cases: 24
```

### 6.2 测试代码 (状态机重点)

```typescript
// __tests__/e2e/b1-topup-approval/topup-approval.spec.ts

import { test, expect } from '@playwright/test';
import { loginAs } from '../../utils/auth';

/**
 * B1 充值审批测试
 */

// ============================================================
// CP-B1-004: 状态机操作测试
// ============================================================
test.describe('CP-B1-004: 状态机操作', () => {

  test('draft→pending_review (project_owner)', async ({ page }) => {
    await loginAs(page, 'project_owner');
    await page.goto('/topups');

    // 找到 draft 状态记录并提交
    await page.click('[data-testid="submit-btn-draft-1"]');

    await expect(page.locator('[data-testid="toast-success"]')).toContainText('已提交审核');
    await expect(page.locator('[data-testid="status-draft-1"]')).toHaveText('pending_review');
  });

  test('pending_review→finance_approve (supervisor)', async ({ page }) => {
    await loginAs(page, 'supervisor');
    await page.goto('/topups');

    await page.click('[data-testid="confirm-btn-pending-1"]');

    await expect(page.locator('[data-testid="toast-success"]')).toContainText('已确认');
  });

  test('finance_approve→paid (finance)', async ({ page }) => {
    await loginAs(page, 'finance');
    await page.goto('/topups');

    await page.click('[data-testid="approve-btn-finance-1"]');

    await expect(page.locator('[data-testid="toast-success"]')).toContainText('审批通过');
  });

  test('非法转换: draft→paid 返回 400', async ({ page }) => {
    await loginAs(page, 'finance');

    // 直接调用 API 尝试非法转换
    const response = await page.request.post('/api/v1/topups/draft-1/transition', {
      data: { to_status: 'paid' }
    });

    expect(response.status()).toBe(400);
    const body = await response.json();
    expect(body.code).toBe('ST-001');
  });

  test('非法转换: completed→paid 返回 400', async ({ page }) => {
    await loginAs(page, 'admin');

    const response = await page.request.post('/api/v1/topups/completed-1/transition', {
      data: { to_status: 'paid' }
    });

    expect(response.status()).toBe(400);
    const body = await response.json();
    expect(body.code).toBe('ST-002');
  });

  test('终态 completed 按钮禁用', async ({ page }) => {
    await loginAs(page, 'ceo');
    await page.goto('/topups');

    // completed 状态的记录应该没有操作按钮
    await expect(page.locator('[data-testid="action-btn-completed-1"]')).not.toBeVisible();
  });
});
```

---

## 7. B2 日报审核

**规格书**: [B2-daily-report-review.md](./B2-daily-report-review.md)
**页面路径**: `/daily-reports`
**模块优先级**: P1

### 7.1 检查点清单

```yaml
# checkpoints/B2-daily-report-review.yaml

module: "B2-daily-report-review"
spec_file: "docs/10.module-specs/B2-daily-report-review.md"
page_path: "/daily-reports"

checkpoints:
  - id: CP-B2-001
    category: permission
    description: 日报审核页访问权限
    cases:
      - { role: ceo, expected: allowed, scope: "全公司" }
      - { role: finance, expected: allowed, action: "终审" }
      - { role: supervisor, expected: allowed, action: "趋势审核" }
      - { role: pitcher, expected: allowed, scope: "个人日报" }
      - { role: project_owner, expected: allowed, scope: "项目日报" }
      - { role: account_manager, expected: denied }
      - { role: admin, expected: denied }

  - id: CP-B2-002
    category: ui
    description: 页面元素渲染
    cases:
      - { element: 页面标题, expected: "日报管理" }
      - { element: 日报表格, selector: "[data-testid='daily-reports-table']" }
      - { element: 状态Tab, selector: "[data-testid='status-tabs']" }
      - { element: 表格列, columns: [日期, 项目, 投手, 进粉数, 消耗, CPL, 状态, 操作] }

  - id: CP-B2-003
    category: data
    description: 数据加载状态
    cases:
      - { scenario: loading, expected: 骨架屏 }
      - { scenario: empty, expected: "暂无日报" }
      - { scenario: error, expected: 错误提示 }
      - { scenario: success, expected: 日报列表 }

  - id: CP-B2-004
    category: function
    description: 状态机操作 (8 状态)
    cases:
      - { transition: "raw_submitted→trend_pending", auto: true }
      - { transition: "trend_pending→trend_ok", actor: supervisor }
      - { transition: "trend_pending→trend_flagged", actor: supervisor }
      - { transition: "trend_flagged→trend_resolved", actor: supervisor }
      - { transition: "trend_ok→final_pending", actor: supervisor }
      - { transition: "final_pending→final_confirmed", actor: finance }
      - { transition: "final_confirmed→final_locked", auto: true }
      - { illegal: "raw_submitted→final_confirmed", expected: "400 ST-001" }
      - { illegal: "final_locked→final_confirmed", expected: "400 ST-002" }

  - id: CP-B2-005
    category: phase1
    description: Phase 1 不阻断规则
    cases:
      - { scenario: CPL超标, expected: 红色高亮+审核按钮可用 }
      - { scenario: 趋势异常, expected: 黄色警告+可继续审核 }

summary:
  total_checkpoints: 5
  total_cases: 28
```

### 7.2 测试代码 (摘要)

```typescript
// __tests__/e2e/b2-daily-report-review/daily-report-review.spec.ts

import { test, expect } from '@playwright/test';
import { loginAs } from '../../utils/auth';

/**
 * B2 日报审核测试
 */

test.describe('CP-B2-001: 权限测试', () => {
  const allowedRoles = ['ceo', 'finance', 'supervisor', 'pitcher', 'project_owner'];
  const deniedRoles = ['account_manager', 'admin'];

  for (const role of allowedRoles) {
    test(`${role} 可以访问日报页`, async ({ page }) => {
      await loginAs(page, role as any);
      await page.goto('/daily-reports');
      await expect(page).toHaveURL('/daily-reports');
    });
  }

  for (const role of deniedRoles) {
    test(`${role} 不能访问日报页`, async ({ page }) => {
      await loginAs(page, role as any);
      await page.goto('/daily-reports');
      await expect(page).toHaveURL('/unauthorized');
    });
  }
});

test.describe('CP-B2-004: 状态机操作', () => {
  test('trend_pending→trend_ok (supervisor)', async ({ page }) => {
    await loginAs(page, 'supervisor');
    await page.goto('/daily-reports');

    await page.click('[data-testid="approve-trend-btn"]');

    await expect(page.locator('[data-testid="toast-success"]')).toContainText('趋势通过');
  });

  test('trend_pending→trend_flagged (supervisor)', async ({ page }) => {
    await loginAs(page, 'supervisor');
    await page.goto('/daily-reports');

    await page.click('[data-testid="flag-trend-btn"]');
    await page.fill('[data-testid="flag-reason"]', 'CPL 异常');
    await page.click('[data-testid="flag-confirm"]');

    await expect(page.locator('[data-testid="toast-success"]')).toContainText('已标记异常');
  });

  test('非法转换: raw_submitted→final_confirmed', async ({ page }) => {
    await loginAs(page, 'finance');

    const response = await page.request.post('/api/v1/daily-reports/raw-1/transition', {
      data: { to_status: 'final_confirmed' }
    });

    expect(response.status()).toBe(400);
  });

  test('终态 final_locked 不可修改', async ({ page }) => {
    await loginAs(page, 'ceo');
    await page.goto('/daily-reports');

    // final_locked 状态记录的编辑按钮应该禁用
    await expect(page.locator('[data-testid="edit-btn-locked-1"]')).toBeDisabled();
  });
});

test.describe('CP-B2-005: Phase 1 不阻断规则', () => {
  test('CPL 超标高亮但审核按钮可用', async ({ page }) => {
    await loginAs(page, 'supervisor');

    await page.route('/api/v1/daily-reports*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{
            id: 'dr-abnormal-1',
            cpl: 1000,
            target_cpl: 100,
            status: 'trend_pending',
          }],
        }),
      });
    });

    await page.goto('/daily-reports');

    // 验证高亮
    const cplCell = page.locator('[data-testid="cpl-cell-dr-abnormal-1"]');
    await expect(cplCell).toHaveClass(/bg-red-50|text-red/);

    // 验证审核按钮可用
    const approveBtn = page.locator('[data-testid="approve-trend-btn-dr-abnormal-1"]');
    await expect(approveBtn).toBeEnabled();
  });
});
```

---

## 8. B3 周度简报

**规格书**: [B3-weekly-brief.md](./B3-weekly-brief.md)
**页面路径**: `/weekly-briefs`
**模块优先级**: P2

### 8.1 检查点清单

```yaml
# checkpoints/B3-weekly-brief.yaml

module: "B3-weekly-brief"
spec_file: "docs/10.module-specs/B3-weekly-brief.md"
page_path: "/weekly-briefs"

checkpoints:
  - id: CP-B3-001
    category: permission
    cases:
      - { role: ceo, expected: allowed, scope: "全公司" }
      - { role: finance, expected: allowed, scope: "只读" }
      - { role: supervisor, expected: allowed, scope: "团队" }
      - { role: pitcher, expected: denied }
      - { role: project_owner, expected: allowed, action: "创建+编辑" }
      - { role: account_manager, expected: denied }
      - { role: admin, expected: denied }

  - id: CP-B3-002
    category: ui
    cases:
      - { element: 页面标题, expected: "周度简报" }
      - { element: 周报列表, selector: "[data-testid='weekly-briefs-table']" }
      - { element: 周次选择器, selector: "[data-testid='week-picker']" }

  - id: CP-B3-003
    category: data
    cases:
      - { scenario: loading, expected: 骨架屏 }
      - { scenario: empty, expected: "暂无周报" }
      - { scenario: error, expected: 错误提示 }
      - { scenario: success, expected: 周报列表 }

  - id: CP-B3-004
    category: function
    cases:
      - { action: 创建周报, expected: 状态draft }
      - { action: 编辑草稿, expected: 保存成功 }
      - { action: 提交周报, expected: 状态submitted }
      - { action: 重复创建, expected: 拒绝+提示 }

  - id: CP-B3-005
    category: phase1
    cases:
      - { scenario: 数据缺失, expected: 警告+可提交 }

summary:
  total_cases: 18
```

---

## 9. C1 项目管理

**规格书**: [C1-project-mgmt.md](./C1-project-mgmt.md)
**页面路径**: `/projects`
**模块优先级**: P0

### 9.1 检查点清单

```yaml
# checkpoints/C1-project-mgmt.yaml

module: "C1-project-mgmt"
spec_file: "docs/10.module-specs/C1-project-mgmt.md"
page_path: "/projects"

checkpoints:
  - id: CP-C1-001
    category: permission
    cases:
      - { role: ceo, expected: allowed, action: "全部CRUD" }
      - { role: finance, expected: allowed, scope: "只读" }
      - { role: supervisor, expected: allowed, scope: "团队项目" }
      - { role: pitcher, expected: allowed, scope: "只读个人" }
      - { role: project_owner, expected: allowed, action: "创建+编辑自己" }
      - { role: account_manager, expected: allowed, scope: "只读" }
      - { role: admin, expected: allowed, action: "全部CRUD" }

  - id: CP-C1-002
    category: ui
    cases:
      - { element: 页面标题, expected: "项目管理" }
      - { element: 项目表格, selector: "[data-testid='projects-table']" }
      - { element: 新建按钮, selector: "[data-testid='create-project-btn']" }
      - { element: 状态筛选, selector: "[data-testid='status-filter']" }

  - id: CP-C1-003
    category: data
    cases:
      - { scenario: loading, expected: 骨架屏 }
      - { scenario: empty, expected: "暂无项目" }
      - { scenario: error, expected: 错误提示 }
      - { scenario: success, expected: 项目列表 }

  - id: CP-C1-004
    category: function
    description: 状态机操作 (5 状态)
    cases:
      - { transition: "planning→active", action: "启动" }
      - { transition: "active→paused", action: "暂停" }
      - { transition: "paused→active", action: "恢复" }
      - { transition: "active→completed", action: "完成" }
      - { transition: "planning→cancelled", action: "取消" }
      - { illegal: "completed→active", expected: "400 ST-002" }
      - { illegal: "cancelled→active", expected: "400 ST-001" }

  - id: CP-C1-005
    category: phase1
    cases:
      - { scenario: 预算超支, expected: 红色高亮+可操作 }

summary:
  total_cases: 23
```

---

## 10. C2 投手管理

**规格书**: [C2-pitcher-mgmt.md](./C2-pitcher-mgmt.md)
**页面路径**: `/users?role=pitcher`
**模块优先级**: P2

### 10.1 检查点清单

```yaml
# checkpoints/C2-pitcher-mgmt.yaml

module: "C2-pitcher-mgmt"
spec_file: "docs/10.module-specs/C2-pitcher-mgmt.md"
page_path: "/users?role=pitcher"

checkpoints:
  - id: CP-C2-001
    category: permission
    cases:
      - { role: ceo, expected: allowed, scope: "全公司" }
      - { role: finance, expected: denied }
      - { role: supervisor, expected: allowed, scope: "团队" }
      - { role: pitcher, expected: allowed, scope: "只看自己" }
      - { role: project_owner, expected: denied }
      - { role: account_manager, expected: denied }
      - { role: admin, expected: allowed, action: "创建+编辑" }

  - id: CP-C2-002
    category: ui
    cases:
      - { element: 投手列表, selector: "[data-testid='pitchers-table']" }
      - { element: 表格列, columns: [姓名, 用户名, 团队, 主管, 负责账户, 状态] }

  - id: CP-C2-003
    category: data
    cases:
      - { scenario: loading, expected: 骨架屏 }
      - { scenario: empty, expected: "暂无投手" }
      - { scenario: error, expected: 错误提示 }
      - { scenario: success, expected: 投手列表 }

  - id: CP-C2-004
    category: function
    cases:
      - { action: 创建投手, role: admin }
      - { action: 编辑投手, role: admin }
      - { action: 停用投手, expected: is_active=false }
      - { action: 启用投手, expected: is_active=true }
      - { action: 分配账户, role: supervisor }

  - id: CP-C2-005
    category: phase1
    cases:
      - { scenario: 账户为空, expected: 警告+可保存 }

summary:
  total_cases: 19
```

---

## 11. C3 消耗明细

**规格书**: [C3-spend-detail.md](./C3-spend-detail.md)
**页面路径**: `/spend`
**模块优先级**: P1

### 11.1 检查点清单

```yaml
# checkpoints/C3-spend-detail.yaml

module: "C3-spend-detail"
spec_file: "docs/10.module-specs/C3-spend-detail.md"
page_path: "/spend"

checkpoints:
  - id: CP-C3-001
    category: permission
    cases:
      - { role: ceo, expected: allowed, scope: "全公司" }
      - { role: finance, expected: allowed, action: "导出" }
      - { role: supervisor, expected: allowed, scope: "团队" }
      - { role: pitcher, expected: allowed, scope: "个人账户" }
      - { role: project_owner, expected: allowed, scope: "项目" }
      - { role: account_manager, expected: allowed, scope: "管理账户" }
      - { role: admin, expected: allowed, action: "导入" }

  - id: CP-C3-002
    category: ui
    cases:
      - { element: 页面标题, expected: "消耗明细" }
      - { element: 消耗表格, selector: "[data-testid='spend-table']" }
      - { element: 表格列, columns: [账户, 项目, 渠道, 日期, 消耗, 曝光, 点击, 粉数, CPA] }

  - id: CP-C3-003
    category: data
    cases:
      - { scenario: loading, expected: 骨架屏 }
      - { scenario: empty, expected: "暂无消耗数据" }
      - { scenario: error, expected: 错误提示 }
      - { scenario: success, expected: 消耗列表 }

  - id: CP-C3-004
    category: function
    cases:
      - { action: 日期筛选, expected: 数据更新 }
      - { action: 项目筛选, expected: 数据过滤 }
      - { action: 渠道筛选, expected: 数据过滤 }
      - { action: 导出, role: finance, expected: Excel下载 }
      - { action: 导入, role: admin, expected: 数据写入 }

  - id: CP-C3-005
    category: phase1
    cases:
      - { scenario: CPA异常高, expected: 红色高亮+可查看 }

summary:
  total_cases: 20
```

---

## 12. D1 月度结算

**规格书**: [D1-monthly-settlement.md](./D1-monthly-settlement.md)
**页面路径**: `/settlements`
**模块优先级**: P2

### 12.1 检查点清单

```yaml
# checkpoints/D1-monthly-settlement.yaml

module: "D1-monthly-settlement"
spec_file: "docs/10.module-specs/D1-monthly-settlement.md"
page_path: "/settlements"

checkpoints:
  - id: CP-D1-001
    category: permission
    cases:
      - { role: ceo, expected: allowed, action: "锁定" }
      - { role: finance, expected: allowed, action: "生成+确认" }
      - { role: supervisor, expected: denied }
      - { role: pitcher, expected: denied }
      - { role: project_owner, expected: allowed, scope: "只读自己项目" }
      - { role: account_manager, expected: denied }
      - { role: admin, expected: allowed, action: "解锁" }

  - id: CP-D1-002
    category: ui
    cases:
      - { element: 页面标题, expected: "月度结算" }
      - { element: 结算表格, selector: "[data-testid='settlement-table']" }
      - { element: 月份选择, selector: "[data-testid='month-picker']" }

  - id: CP-D1-003
    category: data
    cases:
      - { scenario: loading, expected: 骨架屏 }
      - { scenario: empty, expected: "暂无结算数据" }
      - { scenario: error, expected: 错误提示 }
      - { scenario: success, expected: 结算列表 }

  - id: CP-D1-004
    category: function
    description: 状态机操作 (4 状态)
    cases:
      - { transition: "pending→draft", action: "生成结算" }
      - { transition: "draft→confirmed", action: "确认" }
      - { transition: "confirmed→locked", action: "锁定" }
      - { transition: "locked→confirmed", action: "解锁", role: admin }
      - { illegal: "pending→locked", expected: "400 ST-001" }

  - id: CP-D1-005
    category: phase1
    cases:
      - { scenario: 负毛利, expected: 红色高亮+可锁定 }

summary:
  total_cases: 20
```

---

## 13. 跨模块集成测试

**检查点**: CP-INT-001 ~ CP-INT-006

```yaml
# checkpoints/integration.yaml

module: "integration"

checkpoints:
  - id: CP-INT-001
    description: 充值→消耗→结算完整流程
    modules: [B1, C3, D1]
    steps:
      - 创建并完成充值 (B1)
      - 导入消耗数据 (C3)
      - 生成月度结算 (D1)
    expected: 数据一致

  - id: CP-INT-002
    description: 日报→周报数据联动
    modules: [B2, B3]
    expected: 周报自动汇总日报

  - id: CP-INT-003
    description: 项目状态影响其他模块
    modules: [C1, B1, B2]
    expected: paused 项目限制充值

  - id: CP-INT-004
    description: 驾驶舱数据来源验证
    modules: [A1, B2, C3]
    expected: 数据一致

  - id: CP-INT-005
    description: 跨项目数据隔离
    modules: [C1, B2, A3]
    role: project_owner
    expected: 只见自己项目

  - id: CP-INT-006
    description: 角色权限全局一致
    modules: [ALL]
    role: pitcher
    expected: 所有模块权限一致
```

---

## 14. 覆盖率汇总

### 14.1 检查点统计

| 模块 | 权限 | UI | 数据 | 功能 | Phase1 | 合计 |
|------|------|-----|------|------|--------|------|
| A1 驾驶舱 | 9 | 5 | 4 | 5 | 2 | 25 |
| A2 资金总览 | 9 | 3 | 4 | 3 | 1 | 20 |
| A3 项目盈亏 | 7 | 4 | 4 | 4 | 2 | 21 |
| B1 充值审批 | 7 | 4 | 4 | 8 | 1 | 24 |
| B2 日报审核 | 7 | 4 | 4 | 11 | 2 | 28 |
| B3 周度简报 | 7 | 3 | 4 | 4 | 1 | 19 |
| C1 项目管理 | 7 | 4 | 4 | 7 | 1 | 23 |
| C2 投手管理 | 7 | 2 | 4 | 5 | 1 | 19 |
| C3 消耗明细 | 7 | 3 | 4 | 5 | 1 | 20 |
| D1 月度结算 | 7 | 3 | 4 | 5 | 1 | 20 |
| 跨模块集成 | 2 | - | 2 | 4 | - | 8 |
| **合计** | **76** | **35** | **42** | **61** | **13** | **227** |

### 14.2 角色权限覆盖矩阵

| 模块 | ceo | finance | supervisor | pitcher | project_owner | account_manager | admin |
|------|-----|---------|------------|---------|---------------|-----------------|-------|
| A1 | ✅全 | ✅财务 | ✅团队 | ✅个人 | ✅项目 | ✅账户 | ✅系统 |
| A2 | ✅全 | ✅导出 | ❌ | ❌ | ✅项目 | ✅账户 | ❌ |
| A3 | ✅全 | ✅财务 | ❌ | ❌ | ✅项目 | ❌ | ❌ |
| B1 | ✅审批 | ✅审批 | ✅确认 | ❌ | ✅创建 | ❌ | ❌ |
| B2 | ✅全 | ✅终审 | ✅趋势 | ✅个人 | ✅项目 | ❌ | ❌ |
| B3 | ✅全 | ✅只读 | ✅团队 | ❌ | ✅创建 | ❌ | ❌ |
| C1 | ✅CRUD | ✅只读 | ✅团队 | ✅只读 | ✅编辑 | ✅只读 | ✅CRUD |
| C2 | ✅全 | ❌ | ✅团队 | ✅自己 | ❌ | ❌ | ✅创建 |
| C3 | ✅全 | ✅导出 | ✅团队 | ✅个人 | ✅项目 | ✅账户 | ✅导入 |
| D1 | ✅锁定 | ✅生成 | ❌ | ❌ | ✅只读 | ❌ | ✅解锁 |

### 14.3 测试文件清单

```
__tests__/e2e/
├── a1-dashboard/dashboard.spec.ts          (25 tests)
├── a2-fund-overview/fund-overview.spec.ts  (20 tests)
├── a3-project-pnl/project-pnl.spec.ts      (21 tests)
├── b1-topup-approval/topup-approval.spec.ts (24 tests)
├── b2-daily-report-review/daily-report-review.spec.ts (28 tests)
├── b3-weekly-brief/weekly-brief.spec.ts    (19 tests)
├── c1-project-mgmt/project-mgmt.spec.ts    (23 tests)
├── c2-pitcher-mgmt/pitcher-mgmt.spec.ts    (19 tests)
├── c3-spend-detail/spend-detail.spec.ts    (20 tests)
├── d1-monthly-settlement/monthly-settlement.spec.ts (20 tests)
└── integration/cross-module.spec.ts        (8 tests)

Total: 227 tests
```

---

## 附录

### A. data-testid 命名规范

```typescript
// 页面级
data-testid="{module}-page"
data-testid="page-title"

// 表格
data-testid="{module}-table"
data-testid="{column}-cell-{rowId}"

// 状态
data-testid="loading-skeleton"
data-testid="empty-state"
data-testid="error-state"

// 表单
data-testid="{field}-input"
data-testid="{field}-select"
data-testid="{field}-error"

// 按钮
data-testid="submit-button"
data-testid="{action}-btn-{rowId}"

// 弹窗
data-testid="{action}-dialog"
data-testid="{action}-confirm"
data-testid="{action}-cancel"

// 提示
data-testid="toast-success"
data-testid="toast-error"

// 筛选
data-testid="{field}-filter"
data-testid="pagination-next"
data-testid="pagination-prev"
```

### B. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v3.0 | 2025-12-23 | 基于 AI_TEST_GUIDE_v2.1.md 全面重构：检查点清单格式、5类测试覆盖、7角色全覆盖、Playwright代码规范 |
| v2.0 | 2025-12-23 | 添加集成测试、状态机测试、Phase 1 规则 |
| v1.0 | 2025-12-23 | 初始版本 |

---

**维护者**: AI 广告代投系统开发团队
**关联文档**:
- AI_TEST_GUIDE_v2.1.md (测试编写指南)
- docs/10.module-specs/ (模块规格书)
