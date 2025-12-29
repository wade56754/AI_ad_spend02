/**
 * C3 消耗明细 E2E 测试
 *
 * @spec docs/10.module-specs/C3-spend-detail.md
 * @checkpoint __tests__/checkpoints/C3-spend-detail.yaml
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

const MODULE = 'C3-spend-detail';
const PAGE_PATH = '/spend-detail';
const PAGE_TITLE = '消耗明细';

// Mock 数据
const mockSpendData = {
  success: {
    items: [
      {
        id: 'spend-1',
        date: '2024-12-23',
        project_name: '项目A',
        ad_account: '账户001',
        spend: 5000,
        conversions: 50,
        cpl: 100,
      },
      {
        id: 'spend-2',
        date: '2024-12-22',
        project_name: '项目B',
        ad_account: '账户002',
        spend: 8000,
        conversions: 80,
        cpl: 100,
      },
    ],
    total: 2,
    summary: { total_spend: 13000, total_conversions: 130 },
  },
  empty: { items: [], total: 0, summary: { total_spend: 0, total_conversions: 0 } },
};

// ============================================================
// CP-C3-001: 权限测试
// ============================================================
test.describe('CP-C3-001: 权限测试', () => {
  const { allowed, denied } = MODULE_PERMISSIONS[MODULE];

  for (const role of allowed) {
    test(`${role} 可以访问消耗明细页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto(PAGE_PATH);

      await expect(page).toHaveURL(PAGE_PATH);
      await expect(page.locator('h1')).toHaveText(PAGE_TITLE);
    });
  }

  for (const role of denied) {
    test(`${role} 不能访问消耗明细页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto(PAGE_PATH);

      await expectAccessDenied(page);
    });
  }

  test('pitcher 只能看到自己的消耗数据', async ({ page }) => {
    await loginAs(page, 'pitcher');
    await page.route('/api/v1/spend-detail*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{ id: 'spend-1', pitcher_id: 'pitcher-1', spend: 5000 }],
          total: 1,
        }),
      });
    });
    await page.goto(PAGE_PATH);

    await page.waitForSelector('[data-testid="spend-table"]');
    const rows = page.locator('[data-testid="spend-table"] tbody tr');
    await expect(rows).toHaveCount(1);
  });
});

// ============================================================
// CP-C3-002: 页面渲染测试
// ============================================================
test.describe('CP-C3-002: 页面渲染', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'finance');
    await page.route('/api/v1/spend-detail*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSpendData.success),
      });
    });
    await page.goto(PAGE_PATH);
  });

  test('显示页面标题', async ({ page }) => {
    await expectPageTitle(page, PAGE_TITLE);
  });

  test('显示消耗汇总', async ({ page }) => {
    await expectVisible(page, 'spend-summary');
  });

  test('显示消耗明细表格', async ({ page }) => {
    await expectTableVisible(page, 'spend-table');
  });

  test('显示日期范围筛选', async ({ page }) => {
    await expectVisible(page, 'date-range-filter');
  });

  test('显示项目筛选', async ({ page }) => {
    await expectVisible(page, 'project-filter');
  });

  test('显示账户筛选', async ({ page }) => {
    await expectVisible(page, 'account-filter');
  });

  test('表格包含必要列', async ({ page }) => {
    const headers = ['日期', '项目', '账户', '消耗', '进粉', 'CPL'];
    for (const header of headers) {
      await expect(page.locator('[data-testid="spend-table"] th').filter({ hasText: header })).toBeVisible();
    }
  });
});

// ============================================================
// CP-C3-003: 数据状态测试
// ============================================================
test.describe('CP-C3-003: 数据状态', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'finance');
  });

  test('加载中显示骨架屏', async ({ page }) => {
    await page.route('/api/v1/spend-detail*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSpendData.success),
      });
    });

    await page.goto(PAGE_PATH);
    await expectLoadingState(page);
  });

  test('空数据显示提示', async ({ page }) => {
    await page.route('/api/v1/spend-detail*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSpendData.empty),
      });
    });

    await page.goto(PAGE_PATH);
    await expectEmptyState(page, '暂无消耗记录');
  });

  test('错误时显示错误提示', async ({ page }) => {
    await page.route('/api/v1/spend-detail*', (route) => {
      route.fulfill({ status: 500 });
    });

    await page.goto(PAGE_PATH);
    await expectErrorState(page);
  });

  test('成功加载显示数据', async ({ page }) => {
    await page.route('/api/v1/spend-detail*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSpendData.success),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="spend-table"] tbody tr');

    const rows = page.locator('[data-testid="spend-table"] tbody tr');
    await expect(rows).toHaveCount(2);
  });
});

// ============================================================
// CP-C3-004: 功能操作测试
// ============================================================
test.describe('CP-C3-004: 功能操作', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'finance');
    await page.route('/api/v1/spend-detail*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSpendData.success),
      });
    });
    await page.goto(PAGE_PATH);
  });

  test('日期范围筛选刷新数据', async ({ page }) => {
    const requestPromise = page.waitForRequest(req =>
      req.url().includes('/api/v1/spend-detail') && req.url().includes('start_date')
    );

    await page.click('[data-testid="date-range-filter"]');
    await page.click('[data-testid="date-preset-last7days"]');

    await requestPromise;
  });

  test('项目筛选', async ({ page }) => {
    await page.click('[data-testid="project-filter"]');
    await page.click('[data-testid="project-option-proj-1"]');

    await page.waitForSelector('[data-testid="spend-table"]');
  });

  test('账户筛选', async ({ page }) => {
    await page.click('[data-testid="account-filter"]');
    await page.click('[data-testid="account-option-1"]');

    await page.waitForSelector('[data-testid="spend-table"]');
  });

  test('导出明细', async ({ page }) => {
    const downloadPromise = page.waitForEvent('download');

    await page.click('[data-testid="export-btn"]');

    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('spend');
  });

  test('排序功能', async ({ page }) => {
    await page.click('[data-testid="sort-spend"]');

    const requestPromise = page.waitForRequest(req =>
      req.url().includes('sort=spend')
    );
    await page.click('[data-testid="sort-spend"]');
    await requestPromise;
  });

  test('分页功能', async ({ page }) => {
    await page.route('/api/v1/spend-detail*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...mockSpendData.success,
          total: 100,
        }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="pagination"]');

    await page.click('[data-testid="page-next"]');

    const requestPromise = page.waitForRequest(req =>
      req.url().includes('page=2')
    );
    await requestPromise;
  });
});

// ============================================================
// CP-C3-005: Phase 1 规则测试
// ============================================================
test.describe('CP-C3-005: Phase 1 不阻断规则', () => {
  test('高消耗记录高亮但可正常查看', async ({ page }) => {
    await loginAs(page, 'finance');

    await page.route('/api/v1/spend-detail*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{
            id: 'spend-high-1',
            date: '2024-12-23',
            spend: 100000,
            is_high_spend: true,
          }],
          total: 1,
        }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="spend-table"]');

    // 1. 验证高消耗高亮
    const row = page.locator('[data-testid="row-spend-high-1"]');
    await expect(row).toHaveClass(/bg-amber|bg-yellow|warning/);

    // 2. 验证导出功能仍可用
    await expect(page.locator('[data-testid="export-btn"]')).toBeEnabled();
  });

  test('CPL 异常高亮但不影响筛选功能', async ({ page }) => {
    await loginAs(page, 'supervisor');

    await page.route('/api/v1/spend-detail*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{
            id: 'spend-abnormal-1',
            spend: 10000,
            conversions: 10,
            cpl: 1000,
            target_cpl: 100,
            is_abnormal: true,
          }],
          total: 1,
        }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="spend-table"]');

    // CPL 高亮
    const cplCell = page.locator('[data-testid="cpl-cell-spend-abnormal-1"]');
    await expect(cplCell).toHaveClass(/text-red|negative/);

    // 筛选功能正常
    await expect(page.locator('[data-testid="project-filter"]')).toBeEnabled();
    await expect(page.locator('[data-testid="date-range-filter"]')).toBeEnabled();
  });
});
