/**
 * A2 资金总览 E2E 测试
 *
 * @spec docs/10.module-specs/A2-fund-overview.md
 * @checkpoint __tests__/checkpoints/A2-fund-overview.yaml
 */

import { test, expect } from '@playwright/test';
import { loginAs, expectAccessDenied } from '../../utils/auth';
import { TestRole, MODULE_PERMISSIONS } from '../../fixtures/test-accounts';
import { mockFundData } from '../../fixtures/mock-data';
import {
  expectPageTitle,
  expectLoadingState,
  expectEmptyState,
  expectErrorState,
  expectVisible,
} from '../../utils/assertions';

const MODULE = 'A2-fund-overview';
const PAGE_PATH = '/fund';
const PAGE_TITLE = '资金总览';

// ============================================================
// CP-A2-001: 权限测试
// ============================================================
test.describe('CP-A2-001: 权限测试', () => {
  const { allowed, denied } = MODULE_PERMISSIONS[MODULE];

  for (const role of allowed) {
    test(`${role} 可以访问资金总览页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto(PAGE_PATH);

      await expect(page).toHaveURL(PAGE_PATH);
      await expect(page.locator('h1')).toHaveText(PAGE_TITLE);
    });
  }

  for (const role of denied) {
    test(`${role} 不能访问资金总览页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto(PAGE_PATH);

      await expectAccessDenied(page);
    });
  }

  test('finance 可以查看所有资金明细', async ({ page }) => {
    await loginAs(page, 'finance');
    await page.route('/api/v1/fund*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockFundData.success),
      });
    });
    await page.goto(PAGE_PATH);

    await page.waitForSelector('[data-testid="fund-summary"]');
    await expectVisible(page, 'fund-transactions');
  });
});

// ============================================================
// CP-A2-002: 页面渲染测试
// ============================================================
test.describe('CP-A2-002: 页面渲染', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'finance');
    await page.route('/api/v1/fund*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockFundData.success),
      });
    });
    await page.goto(PAGE_PATH);
  });

  test('显示页面标题', async ({ page }) => {
    await expectPageTitle(page, PAGE_TITLE);
  });

  test('显示资金汇总卡片', async ({ page }) => {
    await expectVisible(page, 'fund-summary');
  });

  test('显示充值金额', async ({ page }) => {
    await expectVisible(page, 'summary-topup');
  });

  test('显示消耗金额', async ({ page }) => {
    await expectVisible(page, 'summary-spend');
  });

  test('显示余额', async ({ page }) => {
    await expectVisible(page, 'summary-balance');
  });

  test('显示应收账款', async ({ page }) => {
    await expectVisible(page, 'summary-receivable');
  });

  test('显示交易流水表', async ({ page }) => {
    await expectVisible(page, 'fund-transactions');
  });
});

// ============================================================
// CP-A2-003: 数据状态测试
// ============================================================
test.describe('CP-A2-003: 数据状态', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'finance');
  });

  test('加载中显示骨架屏', async ({ page }) => {
    await page.route('/api/v1/fund*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockFundData.success),
      });
    });

    await page.goto(PAGE_PATH);
    await expectLoadingState(page);
  });

  test('空数据显示提示', async ({ page }) => {
    await page.route('/api/v1/fund*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockFundData.empty),
      });
    });

    await page.goto(PAGE_PATH);
    await expectEmptyState(page, '暂无资金记录');
  });

  test('错误时显示错误提示', async ({ page }) => {
    await page.route('/api/v1/fund*', (route) => {
      route.fulfill({ status: 500 });
    });

    await page.goto(PAGE_PATH);
    await expectErrorState(page);
  });

  test('成功加载显示资金数据', async ({ page }) => {
    await page.route('/api/v1/fund*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockFundData.success),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="summary-balance"]');

    const balanceCard = page.locator('[data-testid="summary-balance"]');
    await expect(balanceCard).toContainText('¥');
  });
});

// ============================================================
// CP-A2-004: 功能操作测试
// ============================================================
test.describe('CP-A2-004: 功能操作', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'finance');
    await page.route('/api/v1/fund*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockFundData.success),
      });
    });
    await page.goto(PAGE_PATH);
  });

  test('时间范围筛选刷新数据', async ({ page }) => {
    const requestPromise = page.waitForRequest(req =>
      req.url().includes('/api/v1/fund') && req.url().includes('period=30d')
    );

    await page.click('[data-testid="time-filter"]');
    await page.click('[data-testid="time-option-30d"]');

    await requestPromise;
  });

  test('账户筛选功能', async ({ page }) => {
    await page.click('[data-testid="account-filter"]');
    await page.click('[data-testid="account-option-1"]');

    await page.waitForSelector('[data-testid="fund-transactions"]');
  });

  test('交易类型筛选', async ({ page }) => {
    await page.click('[data-testid="type-filter"]');
    await page.click('[data-testid="type-option-topup"]');

    await page.waitForSelector('[data-testid="fund-transactions"]');
  });

  test('导出功能', async ({ page }) => {
    const downloadPromise = page.waitForEvent('download');

    await page.click('[data-testid="export-btn"]');

    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('fund');
  });
});

// ============================================================
// CP-A2-005: Phase 1 规则测试
// ============================================================
test.describe('CP-A2-005: Phase 1 不阻断规则', () => {
  test('负余额高亮但页面正常显示', async ({ page }) => {
    await loginAs(page, 'finance');

    await page.route('/api/v1/fund*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockFundData.negative_balance),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="summary-balance"]');

    // 1. 验证负余额高亮
    const balanceCard = page.locator('[data-testid="summary-balance"]');
    await expect(balanceCard).toHaveClass(/text-red|bg-red|negative/);

    // 2. 验证页面功能正常
    await expect(page.locator('[data-testid="fund-transactions"]')).toBeVisible();
    await expect(page.locator('[data-testid="export-btn"]')).toBeEnabled();
  });
});
