# AI 测试用例编写指南 v2.1

> **文档定位**: 指导 AI 编写完整、准确的前端测试用例
> **核心原则**: 规格书驱动 + 确定性断言 + 完整覆盖
> **技术栈**: Playwright + TypeScript

---

## 第一章 快速入门

### 1.1 AI 编写测试的标准流程

```
┌─────────────────────────────────────────────────────────────────┐
│                 AI 编写测试用例流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1          Step 2          Step 3          Step 4        │
│  ┌───────┐      ┌───────┐      ┌───────┐      ┌───────┐       │
│  │读规格书│ ──→ │生成检查│ ──→ │编写测试│ ──→ │ 自检  │       │
│  │       │      │点清单  │      │代码    │      │       │       │
│  └───────┘      └───────┘      └───────┘      └───────┘       │
│      │              │              │              │            │
│      ↓              ↓              ↓              ↓            │
│  提取测试点     YAML 格式      .spec.ts       检查清单        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 一个完整示例

**输入**: 规格书 `B2-daily-report-review.md`

**Step 1: 提取测试点**
```yaml
模块: 日报审核
路径: /daily-reports/review
权限: supervisor, ceo
核心功能: 查看待审核日报、通过/驳回
```

**Step 2: 生成检查点清单**
```yaml
checkpoints:
  - id: CP-001
    name: 权限测试
    cases: 7 个角色
  - id: CP-002
    name: 页面渲染
    cases: 标题、表格、筛选器
  - id: CP-003
    name: 审核操作
    cases: 通过、驳回
```

**Step 3: 编写测试代码**
```typescript
// daily-report-review.spec.ts
test('supervisor 可以访问日报审核页', async ({ page }) => {
  await loginAs(page, 'supervisor');
  await page.goto('/daily-reports/review');
  await expect(page).toHaveURL('/daily-reports/review');
  await expect(page.locator('h1')).toHaveText('日报审核');
});
```

**Step 4: 自检**
```
✅ 7 角色权限全覆盖
✅ 所有断言都是确定性的
✅ 使用 data-testid 选择器
```

---

## 第二章 检查点清单规范

### 2.1 检查点清单格式

每个模块必须生成一个检查点清单，覆盖 5 类测试：

```yaml
# checkpoints/{module-name}.yaml

module: "{模块名}"
spec_file: "docs/10.module-specs/{规格书}.md"
page_path: "/{页面路径}"

checkpoints:
  # ===== 1. 权限测试（必须）=====
  - id: CP-{MODULE}-001
    category: permission
    description: 页面访问权限
    spec_ref: "§1.2 用户角色"
    cases:
      - { role: ceo, expected: allowed }
      - { role: finance, expected: denied }
      - { role: supervisor, expected: allowed }
      - { role: pitcher, expected: denied }
      - { role: project_owner, expected: denied }
      - { role: account_manager, expected: denied }
      - { role: admin, expected: denied }

  # ===== 2. 页面渲染测试（必须）=====
  - id: CP-{MODULE}-002
    category: ui
    description: 页面元素渲染
    spec_ref: "§3 UI 规范"
    cases:
      - { element: 页面标题, selector: "h1", expected: "{标题文本}" }
      - { element: 数据表格, selector: "[data-testid='xxx-table']", expected: visible }
      - { element: 操作按钮, selector: "[data-testid='xxx-btn']", expected: visible }

  # ===== 3. 数据状态测试（必须）=====
  - id: CP-{MODULE}-003
    category: data
    description: 数据加载状态
    spec_ref: "§2 数据需求"
    cases:
      - { scenario: loading, expected: 显示加载状态 }
      - { scenario: empty, expected: 显示空状态提示 }
      - { scenario: error, expected: 显示错误提示 }
      - { scenario: success, expected: 显示数据列表 }

  # ===== 4. 功能操作测试（按需）=====
  - id: CP-{MODULE}-004
    category: function
    description: 核心功能操作
    spec_ref: "§5 API 接口"
    cases:
      - { action: 创建, expected: 成功提示 + 列表刷新 }
      - { action: 编辑, expected: 成功提示 + 数据更新 }
      - { action: 删除, expected: 确认弹窗 + 成功提示 }

  # ===== 5. Phase 1 规则测试（必须）=====
  - id: CP-{MODULE}-005
    category: phase1
    description: Phase 1 不阻断规则
    spec_ref: "MASTER.md §3.1"
    cases:
      - { scenario: 异常数据, expected: 高亮显示但按钮可点击 }
      - { scenario: 缺失数据, expected: 警告提示但可提交 }

# ===== 覆盖统计 =====
summary:
  total_checkpoints: 5
  permission_cases: 7
  ui_cases: X
  data_cases: 4
  function_cases: X
  phase1_cases: 2
```

### 2.2 必须覆盖的 7 个角色

每个页面的权限测试必须覆盖全部 7 个角色：

| 角色 | 前端名称 | 后端名称 | 说明 |
|------|----------|----------|------|
| ceo | ceo | ceo | 老板 |
| finance | finance | finance | 财务 |
| supervisor | supervisor | data_operator | 主管 |
| pitcher | pitcher | media_buyer | 投手 |
| project_owner | project_owner | project_owner | 项目负责人 |
| account_manager | account_manager | account_manager | 户管 |
| admin | admin | admin | 管理员 |

---

## 第三章 测试代码规范

### 3.1 文件结构

```
__tests__/
├── e2e/
│   ├── auth/
│   │   └── login.spec.ts
│   ├── daily-reports/
│   │   ├── list.spec.ts
│   │   └── review.spec.ts
│   ├── projects/
│   │   └── list.spec.ts
│   └── topups/
│       ├── request.spec.ts
│       └── approve.spec.ts
│
├── fixtures/
│   ├── test-accounts.ts      # 测试账号
│   └── test-data.ts          # 测试数据
│
└── utils/
    ├── auth.ts               # 登录辅助函数
    └── assertions.ts         # 通用断言
```

### 3.2 测试账号配置

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

### 3.3 登录辅助函数

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

### 3.4 测试文件模板

```typescript
// __tests__/e2e/{module}/{feature}.spec.ts

import { test, expect } from '@playwright/test';
import { loginAs } from '../../utils/auth';
import { TEST_ACCOUNTS, TestRole } from '../../fixtures/test-accounts';

/**
 * {模块名} - {功能名} 测试
 * 
 * @spec docs/10.module-specs/{规格书}.md
 * @checkpoint checkpoints/{module}.yaml
 */

// ============================================================
// CP-001: 权限测试
// ============================================================
test.describe('权限测试', () => {
  const allowedRoles: TestRole[] = ['ceo', 'supervisor'];
  const deniedRoles: TestRole[] = ['finance', 'pitcher', 'project_owner', 'account_manager', 'admin'];

  for (const role of allowedRoles) {
    test(`${role} 可以访问`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto('/{path}');
      
      await expect(page).toHaveURL('/{path}');
      await expect(page.locator('h1')).toBeVisible();
    });
  }

  for (const role of deniedRoles) {
    test(`${role} 不能访问`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto('/{path}');
      
      // 应该被重定向到无权限页面
      await expect(page).toHaveURL('/unauthorized');
    });
  }
});

// ============================================================
// CP-002: 页面渲染测试
// ============================================================
test.describe('页面渲染', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'supervisor');
    await page.goto('/{path}');
  });

  test('显示页面标题', async ({ page }) => {
    await expect(page.locator('h1')).toHaveText('{标题}');
  });

  test('显示数据表格', async ({ page }) => {
    await expect(page.locator('[data-testid="{module}-table"]')).toBeVisible();
  });

  test('表格包含必要列', async ({ page }) => {
    const headers = page.locator('[data-testid="{module}-table"] th');
    await expect(headers).toHaveCount({N});
    
    // 验证列标题
    await expect(headers.nth(0)).toHaveText('日期');
    await expect(headers.nth(1)).toHaveText('项目');
    // ...
  });
});

// ============================================================
// CP-003: 数据状态测试
// ============================================================
test.describe('数据状态', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'supervisor');
  });

  test('加载中显示骨架屏', async ({ page }) => {
    // 拦截 API 延迟响应
    await page.route('/api/v1/{endpoint}', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.continue();
    });
    
    await page.goto('/{path}');
    await expect(page.locator('[data-testid="loading-skeleton"]')).toBeVisible();
  });

  test('空数据显示提示', async ({ page }) => {
    // Mock 空数据响应
    await page.route('/api/v1/{endpoint}', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({ items: [], total: 0 }),
      });
    });
    
    await page.goto('/{path}');
    await expect(page.locator('[data-testid="empty-state"]')).toBeVisible();
    await expect(page.locator('[data-testid="empty-state"]')).toContainText('暂无数据');
  });

  test('错误时显示错误提示', async ({ page }) => {
    // Mock 错误响应
    await page.route('/api/v1/{endpoint}', async (route) => {
      await route.fulfill({ status: 500 });
    });
    
    await page.goto('/{path}');
    await expect(page.locator('[data-testid="error-state"]')).toBeVisible();
  });

  test('成功加载显示数据', async ({ page }) => {
    await page.goto('/{path}');
    await expect(page.locator('[data-testid="{module}-table"] tbody tr')).toHaveCount.greaterThan(0);
  });
});

// ============================================================
// CP-004: 功能操作测试
// ============================================================
test.describe('功能操作', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'supervisor');
    await page.goto('/{path}');
  });

  test('操作成功显示提示', async ({ page }) => {
    await page.click('[data-testid="action-button"]');
    
    // 验证成功提示
    await expect(page.locator('[data-testid="toast-success"]')).toBeVisible();
    await expect(page.locator('[data-testid="toast-success"]')).toContainText('操作成功');
  });
});

// ============================================================
// CP-005: Phase 1 规则测试
// ============================================================
test.describe('Phase 1 规则', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'supervisor');
  });

  test('异常数据高亮但不阻断操作', async ({ page }) => {
    // Mock 包含异常数据的响应
    await page.route('/api/v1/{endpoint}', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          items: [{
            id: 'test-1',
            // 异常数据：CPL 超标
            conversions: 10,
            spend: 10000,
          }],
          total: 1,
        }),
      });
    });
    
    await page.goto('/{path}');
    
    // 1. 验证数据高亮
    const abnormalCell = page.locator('[data-testid="cpl-cell-test-1"]');
    await expect(abnormalCell).toHaveClass(/bg-red-50|text-red/);
    
    // 2. 验证按钮仍可点击（Phase 1 不阻断）
    const actionButton = page.locator('[data-testid="action-btn-test-1"]');
    await expect(actionButton).toBeEnabled();
    await expect(actionButton).not.toBeDisabled();
  });
});
```

---

## 第四章 断言规范

### 4.1 确定性断言（必须使用）

AI 编写的断言必须是**确定性的**，即 AI 能明确判断通过/失败：

```typescript
// ✅ 确定性断言

// URL 精确匹配
await expect(page).toHaveURL('/daily-reports/review');

// 文本精确匹配
await expect(page.locator('h1')).toHaveText('日报审核');

// 元素可见性
await expect(page.locator('[data-testid="table"]')).toBeVisible();

// 元素启用状态
await expect(page.locator('button')).toBeEnabled();
await expect(page.locator('button')).toBeDisabled();

// 元素数量
await expect(page.locator('tr')).toHaveCount(10);

// CSS 类（用于高亮检测）
await expect(page.locator('.cell')).toHaveClass(/bg-red-50/);

// 属性值
await expect(page.locator('input')).toHaveAttribute('disabled', '');
await expect(page.locator('input')).toHaveValue('test@test.com');
```

### 4.2 禁止使用的断言

```typescript
// ❌ 禁止：模糊断言

// 禁止包含判断（可能误判）
expect(text).toContain('日报');

// 禁止正则匹配（不确定）
expect(text).toMatch(/日报.*/);

// 禁止主观判断
expect(element).toBeLargeEnough();

// 禁止硬编码等待
await page.waitForTimeout(3000);
```

### 4.3 选择器优先级

```typescript
// 优先级从高到低

// 1️⃣ data-testid（最推荐）
page.locator('[data-testid="daily-reports-table"]')

// 2️⃣ 语义化属性
page.locator('[role="button"][aria-label="提交"]')

// 3️⃣ 唯一 ID
page.locator('#submit-button')

// 4️⃣ 组合选择器
page.locator('button.btn-primary')

// ❌ 禁止使用
page.locator('text=提交')           // 纯文本，不稳定
page.locator('div > div > button')  // 路径选择器，易变
page.locator('tr:nth-child(3)')     // 索引选择器，易变
```

### 4.4 等待策略

```typescript
// ✅ 正确的等待方式

// 等待 URL 变化
await page.waitForURL('/dashboard');

// 等待元素出现
await page.waitForSelector('[data-testid="table"]');

// 等待网络空闲
await page.waitForLoadState('networkidle');

// 等待 API 响应
await page.waitForResponse(resp => resp.url().includes('/api/v1/reports'));

// 带超时的断言
await expect(page.locator('[data-testid="status"]')).toHaveText('成功', { timeout: 5000 });
```

---

## 第五章 常见场景测试模板

### 5.1 权限测试模板

```typescript
test.describe('权限测试', () => {
  // 定义允许/拒绝的角色
  const allowedRoles: TestRole[] = ['ceo', 'supervisor'];
  const deniedRoles: TestRole[] = ['finance', 'pitcher', 'project_owner', 'account_manager', 'admin'];

  // 批量测试允许访问
  for (const role of allowedRoles) {
    test(`${role} 可以访问`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto('/target-path');
      await expect(page).toHaveURL('/target-path');
    });
  }

  // 批量测试拒绝访问
  for (const role of deniedRoles) {
    test(`${role} 被重定向到无权限页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto('/target-path');
      await expect(page).toHaveURL('/unauthorized');
    });
  }
});
```

### 5.2 表格列表测试模板

```typescript
test.describe('表格列表', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'supervisor');
    await page.goto('/list-path');
  });

  test('表格结构正确', async ({ page }) => {
    const table = page.locator('[data-testid="data-table"]');
    await expect(table).toBeVisible();
    
    // 验证表头
    const headers = table.locator('th');
    await expect(headers).toHaveCount(6);
    await expect(headers.nth(0)).toHaveText('日期');
    await expect(headers.nth(1)).toHaveText('项目');
    // ...
  });

  test('分页正常工作', async ({ page }) => {
    // 点击下一页
    await page.click('[data-testid="pagination-next"]');
    
    // 验证 URL 或数据变化
    await expect(page).toHaveURL(/page=2/);
  });

  test('筛选正常工作', async ({ page }) => {
    // 选择筛选条件
    await page.selectOption('[data-testid="status-filter"]', 'pending');
    
    // 验证数据更新
    await page.waitForResponse(resp => resp.url().includes('status=pending'));
  });
});
```

### 5.3 表单提交测试模板

```typescript
test.describe('表单提交', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'pitcher');
    await page.goto('/form-path');
  });

  test('必填字段验证', async ({ page }) => {
    // 不填任何内容直接提交
    await page.click('[data-testid="submit-button"]');
    
    // 验证错误提示
    await expect(page.locator('[data-testid="error-project"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-date"]')).toBeVisible();
  });

  test('提交成功', async ({ page }) => {
    // 填写表单
    await page.selectOption('[data-testid="project-select"]', 'project-1');
    await page.fill('[data-testid="date-input"]', '2024-12-23');
    await page.fill('[data-testid="amount-input"]', '1000');
    
    // 提交
    await page.click('[data-testid="submit-button"]');
    
    // 验证成功
    await expect(page.locator('[data-testid="toast-success"]')).toBeVisible();
    await expect(page).toHaveURL('/success-path');
  });

  test('提交失败显示错误', async ({ page }) => {
    // Mock API 失败
    await page.route('/api/v1/submit', route => {
      route.fulfill({
        status: 400,
        body: JSON.stringify({ error: '提交失败' }),
      });
    });

    // 填写并提交
    await page.fill('[data-testid="amount-input"]', '1000');
    await page.click('[data-testid="submit-button"]');
    
    // 验证错误提示
    await expect(page.locator('[data-testid="toast-error"]')).toBeVisible();
  });
});
```

### 5.4 弹窗确认测试模板

```typescript
test.describe('删除确认', () => {
  test('点击删除显示确认弹窗', async ({ page }) => {
    await page.click('[data-testid="delete-btn-1"]');
    
    // 验证弹窗出现
    await expect(page.locator('[data-testid="confirm-dialog"]')).toBeVisible();
    await expect(page.locator('[data-testid="confirm-dialog"]')).toContainText('确定要删除吗');
  });

  test('取消关闭弹窗', async ({ page }) => {
    await page.click('[data-testid="delete-btn-1"]');
    await page.click('[data-testid="confirm-cancel"]');
    
    // 验证弹窗关闭
    await expect(page.locator('[data-testid="confirm-dialog"]')).not.toBeVisible();
  });

  test('确认执行删除', async ({ page }) => {
    await page.click('[data-testid="delete-btn-1"]');
    await page.click('[data-testid="confirm-ok"]');
    
    // 验证删除成功
    await expect(page.locator('[data-testid="toast-success"]')).toContainText('删除成功');
    await expect(page.locator('[data-testid="row-1"]')).not.toBeVisible();
  });
});
```

### 5.5 Phase 1 高亮测试模板

```typescript
test.describe('Phase 1 异常高亮', () => {
  test('CPL 超标数据高亮显示', async ({ page }) => {
    // Mock 包含异常数据
    await page.route('/api/v1/reports', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          items: [{
            id: 'abnormal-1',
            cpl: 500,        // 超过阈值
            threshold: 100,
          }],
        }),
      });
    });

    await page.goto('/reports');

    // 验证高亮样式
    const cell = page.locator('[data-testid="cpl-cell-abnormal-1"]');
    await expect(cell).toHaveClass(/bg-red-50/);
    await expect(cell).toHaveClass(/text-red-600/);
  });

  test('异常数据不阻断操作', async ({ page }) => {
    // 同上 mock 数据...
    await page.goto('/reports');

    // 验证按钮可点击
    const button = page.locator('[data-testid="approve-btn-abnormal-1"]');
    await expect(button).toBeEnabled();
    
    // 点击按钮应该成功
    await button.click();
    await expect(page.locator('[data-testid="toast-success"]')).toBeVisible();
  });
});
```

---

## 第六章 AI 自检清单

### 6.1 编写测试前检查

```markdown
□ 已读取模块规格书
□ 已识别页面路径和权限角色
□ 已列出所有需要测试的功能点
□ 已确认前端代码中存在所需的 data-testid
```

### 6.2 编写测试后检查

```markdown
## 覆盖检查
□ 7 个角色权限全部测试
□ 页面主要元素渲染测试
□ 加载/空/错误/成功 4 种数据状态测试
□ 核心功能操作测试
□ Phase 1 不阻断规则测试

## 代码质量检查
□ 所有断言都是确定性的（精确匹配）
□ 使用 data-testid 作为主要选择器
□ 无硬编码等待（waitForTimeout）
□ 测试之间相互独立（无顺序依赖）

## 文档检查
□ 测试文件有 @spec 注释指向规格书
□ 测试分组有清晰的描述
□ 复杂逻辑有注释说明
```

### 6.3 检查点覆盖率报告模板

测试编写完成后，AI 应输出覆盖率报告：

```markdown
## 测试覆盖率报告: {模块名}

### 1. 检查点覆盖

| 检查点 | 描述 | 用例数 | 状态 |
|--------|------|--------|------|
| CP-001 | 权限测试 | 7 | ✅ |
| CP-002 | 页面渲染 | 4 | ✅ |
| CP-003 | 数据状态 | 4 | ✅ |
| CP-004 | 功能操作 | 3 | ✅ |
| CP-005 | Phase 1 | 2 | ✅ |

### 2. 角色权限覆盖

| 角色 | 预期 | 测试 |
|------|------|------|
| ceo | allowed | ✅ |
| finance | denied | ✅ |
| supervisor | allowed | ✅ |
| pitcher | denied | ✅ |
| project_owner | denied | ✅ |
| account_manager | denied | ✅ |
| admin | denied | ✅ |

### 3. 文件清单

- `__tests__/e2e/{module}/list.spec.ts` (25 tests)
- `__tests__/e2e/{module}/detail.spec.ts` (10 tests)

### 4. 追溯

- 规格书: docs/10.module-specs/{规格书}.md
- 检查点: checkpoints/{module}.yaml
```

---

## 第七章 完整示例：日报审核模块

### 7.1 检查点清单

```yaml
# checkpoints/B2-daily-report-review.yaml

module: "B2-daily-report-review"
spec_file: "docs/10.module-specs/B2-daily-report-review.md"
page_path: "/daily-reports/review"

checkpoints:
  - id: CP-B2-001
    category: permission
    description: 日报审核页访问权限
    spec_ref: "§1.2 用户角色"
    cases:
      - { role: ceo, expected: allowed }
      - { role: finance, expected: denied }
      - { role: supervisor, expected: allowed }
      - { role: pitcher, expected: denied }
      - { role: project_owner, expected: denied }
      - { role: account_manager, expected: denied }
      - { role: admin, expected: denied }

  - id: CP-B2-002
    category: ui
    description: 页面元素渲染
    spec_ref: "§3 UI 规范"
    cases:
      - { element: 页面标题, selector: "h1", expected: "日报审核" }
      - { element: 数据表格, selector: "[data-testid='daily-reports-table']", expected: visible }
      - { element: 状态筛选, selector: "[data-testid='status-filter']", expected: visible }
      - { element: 表格列, count: 8, columns: [日期, 项目, 投手, 进粉数, 消耗, CPL, 状态, 操作] }

  - id: CP-B2-003
    category: data
    description: 数据加载状态
    spec_ref: "§2 数据需求"
    cases:
      - { scenario: loading, expected: 骨架屏 }
      - { scenario: empty, expected: "暂无待审核日报" }
      - { scenario: error, expected: 错误提示 }
      - { scenario: success, expected: 日报列表 }

  - id: CP-B2-004
    category: function
    description: 审核操作
    spec_ref: "§5 API 接口"
    cases:
      - { action: 通过, expected: "审核通过", status: trend_ok }
      - { action: 驳回, expected: "已驳回", status: trend_flagged }

  - id: CP-B2-005
    category: phase1
    description: Phase 1 不阻断规则
    spec_ref: "MASTER.md §3.1"
    cases:
      - { scenario: CPL超标, expected: 红色高亮+按钮可用 }
      - { scenario: 数据缺失, expected: 警告图标+按钮可用 }

summary:
  total_checkpoints: 5
  total_cases: 20
```

### 7.2 完整测试代码

```typescript
// __tests__/e2e/daily-reports/review.spec.ts

import { test, expect } from '@playwright/test';
import { loginAs } from '../../utils/auth';
import { TestRole } from '../../fixtures/test-accounts';

/**
 * 日报审核页测试
 * 
 * @spec docs/10.module-specs/B2-daily-report-review.md
 * @checkpoint checkpoints/B2-daily-report-review.yaml
 */

// ============================================================
// CP-B2-001: 权限测试
// ============================================================
test.describe('CP-B2-001: 权限测试', () => {
  const allowedRoles: TestRole[] = ['ceo', 'supervisor'];
  const deniedRoles: TestRole[] = ['finance', 'pitcher', 'project_owner', 'account_manager', 'admin'];

  for (const role of allowedRoles) {
    test(`${role} 可以访问日报审核页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto('/daily-reports/review');
      
      await expect(page).toHaveURL('/daily-reports/review');
      await expect(page.locator('h1')).toHaveText('日报审核');
    });
  }

  for (const role of deniedRoles) {
    test(`${role} 不能访问日报审核页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto('/daily-reports/review');
      
      await expect(page).toHaveURL('/unauthorized');
    });
  }
});

// ============================================================
// CP-B2-002: 页面渲染测试
// ============================================================
test.describe('CP-B2-002: 页面渲染', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'supervisor');
    await page.goto('/daily-reports/review');
  });

  test('显示页面标题', async ({ page }) => {
    await expect(page.locator('h1')).toHaveText('日报审核');
  });

  test('显示数据表格', async ({ page }) => {
    await expect(page.locator('[data-testid="daily-reports-table"]')).toBeVisible();
  });

  test('显示状态筛选器', async ({ page }) => {
    await expect(page.locator('[data-testid="status-filter"]')).toBeVisible();
  });

  test('表格包含 8 列', async ({ page }) => {
    const headers = page.locator('[data-testid="daily-reports-table"] th');
    await expect(headers).toHaveCount(8);
    
    await expect(headers.nth(0)).toHaveText('日期');
    await expect(headers.nth(1)).toHaveText('项目');
    await expect(headers.nth(2)).toHaveText('投手');
    await expect(headers.nth(3)).toHaveText('进粉数');
    await expect(headers.nth(4)).toHaveText('消耗');
    await expect(headers.nth(5)).toHaveText('CPL');
    await expect(headers.nth(6)).toHaveText('状态');
    await expect(headers.nth(7)).toHaveText('操作');
  });
});

// ============================================================
// CP-B2-003: 数据状态测试
// ============================================================
test.describe('CP-B2-003: 数据状态', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'supervisor');
  });

  test('加载中显示骨架屏', async ({ page }) => {
    await page.route('/api/v1/daily-reports*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 3000));
      await route.continue();
    });
    
    await page.goto('/daily-reports/review');
    await expect(page.locator('[data-testid="loading-skeleton"]')).toBeVisible();
  });

  test('空数据显示提示', async ({ page }) => {
    await page.route('/api/v1/daily-reports*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0 }),
      });
    });
    
    await page.goto('/daily-reports/review');
    await expect(page.locator('[data-testid="empty-state"]')).toBeVisible();
    await expect(page.locator('[data-testid="empty-state"]')).toContainText('暂无待审核日报');
  });

  test('错误时显示错误提示', async ({ page }) => {
    await page.route('/api/v1/daily-reports*', (route) => {
      route.fulfill({ status: 500 });
    });
    
    await page.goto('/daily-reports/review');
    await expect(page.locator('[data-testid="error-state"]')).toBeVisible();
  });

  test('成功加载显示数据', async ({ page }) => {
    await page.goto('/daily-reports/review');
    
    // 等待数据加载完成
    await page.waitForSelector('[data-testid="daily-reports-table"] tbody tr');
    
    const rows = page.locator('[data-testid="daily-reports-table"] tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });
});

// ============================================================
// CP-B2-004: 审核操作测试
// ============================================================
test.describe('CP-B2-004: 审核操作', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'supervisor');
    await page.goto('/daily-reports/review');
    await page.waitForSelector('[data-testid="daily-reports-table"] tbody tr');
  });

  test('点击通过按钮审核通过', async ({ page }) => {
    // 点击第一行的通过按钮
    await page.click('[data-testid="approve-btn"]:first-of-type');
    
    // 验证成功提示
    await expect(page.locator('[data-testid="toast-success"]')).toBeVisible();
    await expect(page.locator('[data-testid="toast-success"]')).toContainText('审核通过');
  });

  test('点击驳回按钮显示驳回弹窗', async ({ page }) => {
    // 点击第一行的驳回按钮
    await page.click('[data-testid="reject-btn"]:first-of-type');
    
    // 验证弹窗出现
    await expect(page.locator('[data-testid="reject-dialog"]')).toBeVisible();
  });

  test('确认驳回成功', async ({ page }) => {
    await page.click('[data-testid="reject-btn"]:first-of-type');
    await page.fill('[data-testid="reject-reason"]', '数据有误');
    await page.click('[data-testid="reject-confirm"]');
    
    // 验证成功提示
    await expect(page.locator('[data-testid="toast-success"]')).toContainText('已驳回');
  });
});

// ============================================================
// CP-B2-005: Phase 1 规则测试
// ============================================================
test.describe('CP-B2-005: Phase 1 不阻断规则', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'supervisor');
  });

  test('CPL 超标数据高亮但按钮可用', async ({ page }) => {
    // Mock 包含 CPL 超标的数据
    await page.route('/api/v1/daily-reports*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{
            id: 'dr-abnormal-1',
            date: '2024-12-23',
            project_name: '测试项目',
            pitcher_name: '测试投手',
            conversions: 10,
            spend: 10000,  // CPL = 1000，假设超标
            cpl: 1000,
            status: 'trend_pending',
          }],
          total: 1,
        }),
      });
    });

    await page.goto('/daily-reports/review');
    await page.waitForSelector('[data-testid="daily-reports-table"]');

    // 1. 验证 CPL 单元格高亮
    const cplCell = page.locator('[data-testid="cpl-cell-dr-abnormal-1"]');
    await expect(cplCell).toHaveClass(/bg-red-50|text-red/);

    // 2. 验证审核按钮可点击（Phase 1 不阻断）
    const approveBtn = page.locator('[data-testid="approve-btn-dr-abnormal-1"]');
    await expect(approveBtn).toBeEnabled();
    await expect(approveBtn).not.toHaveAttribute('disabled');
  });

  test('有警告时仍可提交审核', async ({ page }) => {
    // 同上 mock
    await page.route('/api/v1/daily-reports*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{
            id: 'dr-warning-1',
            conversions: 10,
            spend: 10000,
            status: 'trend_pending',
            warnings: ['CPL 超过预警值'],
          }],
          total: 1,
        }),
      });
    });

    await page.goto('/daily-reports/review');
    
    // 点击审核通过
    await page.click('[data-testid="approve-btn-dr-warning-1"]');
    
    // 应该显示成功（Phase 1 不阻断）
    await expect(page.locator('[data-testid="toast-success"]')).toBeVisible();
  });
});
```

### 7.3 覆盖率报告

```markdown
## 测试覆盖率报告: 日报审核 (B2)

### 1. 检查点覆盖

| 检查点 | 描述 | 用例数 | 状态 |
|--------|------|--------|------|
| CP-B2-001 | 权限测试 | 7 | ✅ |
| CP-B2-002 | 页面渲染 | 4 | ✅ |
| CP-B2-003 | 数据状态 | 4 | ✅ |
| CP-B2-004 | 审核操作 | 3 | ✅ |
| CP-B2-005 | Phase 1 | 2 | ✅ |

### 2. 角色权限覆盖

| 角色 | 预期 | 测试 |
|------|------|------|
| ceo | allowed | ✅ |
| finance | denied | ✅ |
| supervisor | allowed | ✅ |
| pitcher | denied | ✅ |
| project_owner | denied | ✅ |
| account_manager | denied | ✅ |
| admin | denied | ✅ |

### 3. 总计

- 测试文件: 1
- 测试用例: 20
- 覆盖率: 100%

### 4. 追溯

- 规格书: docs/10.module-specs/B2-daily-report-review.md
- 检查点: checkpoints/B2-daily-report-review.yaml
```

---

## 附录 A：data-testid 命名规范

前端代码必须添加以下 `data-testid` 以支持测试：

```typescript
// 页面级
data-testid="{module}-page"           // 页面容器
data-testid="page-title"              // 页面标题 (h1)

// 表格
data-testid="{module}-table"          // 数据表格
data-testid="{column}-cell-{rowId}"   // 特定单元格

// 状态
data-testid="loading-skeleton"        // 加载骨架屏
data-testid="empty-state"             // 空状态
data-testid="error-state"             // 错误状态

// 表单
data-testid="{field}-input"           // 输入框
data-testid="{field}-select"          // 下拉框
data-testid="{field}-error"           // 字段错误提示

// 按钮
data-testid="submit-button"           // 提交按钮
data-testid="{action}-btn-{rowId}"    // 行操作按钮

// 弹窗
data-testid="{action}-dialog"         // 弹窗容器
data-testid="{action}-confirm"        // 确认按钮
data-testid="{action}-cancel"         // 取消按钮

// 提示
data-testid="toast-success"           // 成功提示
data-testid="toast-error"             // 错误提示

// 筛选
data-testid="{field}-filter"          // 筛选器
data-testid="pagination-next"         // 下一页
data-testid="pagination-prev"         // 上一页
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.1 | 2025-12-23 | 精简版：专注于指导 AI 编写测试用例 |

---

**文档定位**: AI 测试用例编写指南
**核心目标**: 让 AI 能够编写完整、准确、可维护的测试用例
