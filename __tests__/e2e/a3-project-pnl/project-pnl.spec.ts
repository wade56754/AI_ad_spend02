/**
 * A3 项目盈亏 E2E 测试
 *
 * @spec docs/10.module-specs/A3-project-pnl.md
 * @checkpoint __tests__/checkpoints/A3-project-pnl.yaml
 */

import { test, expect } from '@playwright/test';
import { loginAs, expectAccessDenied } from '../../utils/auth';
import { TestRole, MODULE_PERMISSIONS } from '../../fixtures/test-accounts';
import {
  expectPageTitle,
  expectLoadingState,
  expectEmptyState,
  expectErrorState,
  expectVisible,
  expectTableVisible,
} from '../../utils/assertions';

const MODULE = 'A3-project-pnl';
const PAGE_PATH = '/project-pnl';
const PAGE_TITLE = '项目盈亏';

// Mock 数据
const mockPnlData = {
  success: {
    items: [
      { id: 'proj-1', name: '项目A', revenue: 150000, cost: 100000, profit: 50000, margin: 33.3 },
      { id: 'proj-2', name: '项目B', revenue: 80000, cost: 60000, profit: 20000, margin: 25.0 },
    ],
    total: 2,
    summary: { total_revenue: 230000, total_cost: 160000, total_profit: 70000 },
  },
  empty: { items: [], total: 0, summary: { total_revenue: 0, total_cost: 0, total_profit: 0 } },
  negative_profit: {
    items: [
      { id: 'proj-loss-1', name: '亏损项目', revenue: 50000, cost: 80000, profit: -30000, margin: -60.0 },
    ],
    total: 1,
    summary: { total_revenue: 50000, total_cost: 80000, total_profit: -30000 },
  },
};

// ============================================================
// CP-A3-001: 权限测试
// ============================================================
test.describe('CP-A3-001: 权限测试', () => {
  const { allowed, denied } = MODULE_PERMISSIONS[MODULE];

  for (const role of allowed) {
    test(`${role} 可以访问项目盈亏页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto(PAGE_PATH);

      await expect(page).toHaveURL(PAGE_PATH);
      await expect(page.locator('h1')).toHaveText(PAGE_TITLE);
    });
  }

  for (const role of denied) {
    test(`${role} 不能访问项目盈亏页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto(PAGE_PATH);

      await expectAccessDenied(page);
    });
  }

  test('project_owner 只能看到自己负责的项目', async ({ page }) => {
    await loginAs(page, 'project_owner');
    await page.route('/api/v1/project-pnl*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{ id: 'proj-1', name: '我的项目', profit: 50000 }],
          total: 1,
        }),
      });
    });
    await page.goto(PAGE_PATH);

    await page.waitForSelector('[data-testid="pnl-table"]');
    const rows = page.locator('[data-testid="pnl-table"] tbody tr');
    await expect(rows).toHaveCount(1);
  });
});

// ============================================================
// CP-A3-002: 页面渲染测试
// ============================================================
test.describe('CP-A3-002: 页面渲染', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'ceo');
    await page.route('/api/v1/project-pnl*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPnlData.success),
      });
    });
    await page.goto(PAGE_PATH);
  });

  test('显示页面标题', async ({ page }) => {
    await expectPageTitle(page, PAGE_TITLE);
  });

  test('显示盈亏汇总', async ({ page }) => {
    await expectVisible(page, 'pnl-summary');
  });

  test('显示盈亏表格', async ({ page }) => {
    await expectTableVisible(page, 'pnl-table');
  });

  test('显示时间筛选器', async ({ page }) => {
    await expectVisible(page, 'time-filter');
  });

  test('表格包含必要列', async ({ page }) => {
    const headers = ['项目', '收入', '成本', '毛利', '利润率'];
    for (const header of headers) {
      await expect(page.locator('[data-testid="pnl-table"] th').filter({ hasText: header })).toBeVisible();
    }
  });
});

// ============================================================
// CP-A3-003: 数据状态测试
// ============================================================
test.describe('CP-A3-003: 数据状态', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'ceo');
  });

  test('加载中显示骨架屏', async ({ page }) => {
    await page.route('/api/v1/project-pnl*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPnlData.success),
      });
    });

    await page.goto(PAGE_PATH);
    await expectLoadingState(page);
  });

  test('空数据显示提示', async ({ page }) => {
    await page.route('/api/v1/project-pnl*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPnlData.empty),
      });
    });

    await page.goto(PAGE_PATH);
    await expectEmptyState(page, '暂无盈亏数据');
  });

  test('错误时显示错误提示', async ({ page }) => {
    await page.route('/api/v1/project-pnl*', (route) => {
      route.fulfill({ status: 500 });
    });

    await page.goto(PAGE_PATH);
    await expectErrorState(page);
  });

  test('成功加载显示数据', async ({ page }) => {
    await page.route('/api/v1/project-pnl*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPnlData.success),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="pnl-table"] tbody tr');

    const rows = page.locator('[data-testid="pnl-table"] tbody tr');
    await expect(rows).toHaveCount(2);
  });
});

// ============================================================
// CP-A3-004: 功能操作测试
// ============================================================
test.describe('CP-A3-004: 功能操作', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'ceo');
    await page.route('/api/v1/project-pnl*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPnlData.success),
      });
    });
    await page.goto(PAGE_PATH);
  });

  test('月份切换刷新数据', async ({ page }) => {
    const requestPromise = page.waitForRequest(req =>
      req.url().includes('/api/v1/project-pnl') && req.url().includes('month=2024-11')
    );

    await page.click('[data-testid="month-picker"]');
    await page.click('[data-testid="month-option-2024-11"]');

    await requestPromise;
  });

  test('点击项目跳转详情', async ({ page }) => {
    await page.waitForSelector('[data-testid="pnl-table"]');
    await page.click('[data-testid="row-proj-1"]');

    await expect(page).toHaveURL(/\/projects\/proj-1/);
  });

  test('导出报表功能', async ({ page }) => {
    const downloadPromise = page.waitForEvent('download');

    await page.click('[data-testid="export-btn"]');

    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('pnl');
  });

  test('排序功能', async ({ page }) => {
    await page.click('[data-testid="sort-profit"]');

    // 验证 API 请求包含排序参数
    const requestPromise = page.waitForRequest(req =>
      req.url().includes('sort=profit')
    );
    await page.click('[data-testid="sort-profit"]');
    await requestPromise;
  });
});

// ============================================================
// CP-A3-005: Phase 1 规则测试
// ============================================================
test.describe('CP-A3-005: Phase 1 不阻断规则', () => {
  test('亏损项目高亮但可正常操作', async ({ page }) => {
    await loginAs(page, 'ceo');

    await page.route('/api/v1/project-pnl*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPnlData.negative_profit),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="pnl-table"]');

    // 1. 验证亏损高亮
    const profitCell = page.locator('[data-testid="profit-cell-proj-loss-1"]');
    await expect(profitCell).toHaveClass(/text-red|negative/);

    // 2. 验证利润率高亮
    const marginCell = page.locator('[data-testid="margin-cell-proj-loss-1"]');
    await expect(marginCell).toHaveClass(/text-red|negative/);

    // 3. 验证仍可点击查看详情
    const row = page.locator('[data-testid="row-proj-loss-1"]');
    await row.click();
    await expect(page).toHaveURL(/\/projects\/proj-loss-1/);
  });

  test('汇总亏损高亮但导出功能正常', async ({ page }) => {
    await loginAs(page, 'ceo');

    await page.route('/api/v1/project-pnl*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPnlData.negative_profit),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="pnl-summary"]');

    // 验证汇总卡片高亮
    const summaryProfit = page.locator('[data-testid="summary-total-profit"]');
    await expect(summaryProfit).toHaveClass(/text-red|negative/);

    // 验证导出按钮可用
    await expect(page.locator('[data-testid="export-btn"]')).toBeEnabled();
  });
});
