/**
 * D1 月度结算 E2E 测试
 *
 * @spec docs/10.module-specs/D1-monthly-settlement.md
 * @checkpoint __tests__/checkpoints/D1-monthly-settlement.yaml
 *
 * 状态机: 4 状态
 * draft → pending_confirm → confirmed → locked
 */

import { test, expect } from '@playwright/test';
import { loginAs, expectAccessDenied } from '../../utils/auth';
import { TestRole, MODULE_PERMISSIONS } from '../../fixtures/test-accounts';
import { mockSettlementData } from '../../fixtures/mock-data';
import {
  expectPageTitle,
  expectLoadingState,
  expectEmptyState,
  expectErrorState,
  expectVisible,
  expectTableVisible,
  expectSuccessToast,
  expectIllegalTransitionRejected,
} from '../../utils/assertions';

const MODULE = 'D1-monthly-settlement';
const PAGE_PATH = '/settlements';
const PAGE_TITLE = '月度结算';

// ============================================================
// CP-D1-001: 权限测试
// ============================================================
test.describe('CP-D1-001: 权限测试', () => {
  const { allowed, denied } = MODULE_PERMISSIONS[MODULE];

  for (const role of allowed) {
    test(`${role} 可以访问月度结算页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto(PAGE_PATH);

      await expect(page).toHaveURL(PAGE_PATH);
      await expect(page.locator('h1')).toHaveText(PAGE_TITLE);
    });
  }

  for (const role of denied) {
    test(`${role} 不能访问月度结算页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto(PAGE_PATH);

      await expectAccessDenied(page);
    });
  }

  test('finance 可以生成结算单', async ({ page }) => {
    await loginAs(page, 'finance');
    await page.goto(PAGE_PATH);

    await expectVisible(page, 'generate-settlement-btn');
    await expect(page.locator('[data-testid="generate-settlement-btn"]')).toBeEnabled();
  });

  test('ceo 可以锁定结算单', async ({ page }) => {
    await loginAs(page, 'ceo');
    await page.route('/api/v1/settlements*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{ id: 'settle-1', status: 'confirmed' }],
          total: 1,
        }),
      });
    });
    await page.goto(PAGE_PATH);

    await page.waitForSelector('[data-testid="settlement-table"]');
    await expectVisible(page, 'lock-btn-settle-1');
  });
});

// ============================================================
// CP-D1-002: 页面渲染测试
// ============================================================
test.describe('CP-D1-002: 页面渲染', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'finance');
    await page.route('/api/v1/settlements*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSettlementData.success),
      });
    });
    await page.goto(PAGE_PATH);
  });

  test('显示页面标题', async ({ page }) => {
    await expectPageTitle(page, PAGE_TITLE);
  });

  test('显示结算表格', async ({ page }) => {
    await expectTableVisible(page, 'settlement-table');
  });

  test('显示月份筛选器', async ({ page }) => {
    await expectVisible(page, 'month-filter');
  });

  test('显示生成结算按钮', async ({ page }) => {
    await expectVisible(page, 'generate-settlement-btn');
  });

  test('表格包含必要列', async ({ page }) => {
    const headers = ['月份', '项目', '消耗', '进粉', '收入', '毛利', '状态', '操作'];
    for (const header of headers) {
      await expect(page.locator('[data-testid="settlement-table"] th').filter({ hasText: header })).toBeVisible();
    }
  });
});

// ============================================================
// CP-D1-003: 数据状态测试
// ============================================================
test.describe('CP-D1-003: 数据状态', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'finance');
  });

  test('加载中显示骨架屏', async ({ page }) => {
    await page.route('/api/v1/settlements*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSettlementData.success),
      });
    });

    await page.goto(PAGE_PATH);
    await expectLoadingState(page);
  });

  test('空数据显示提示', async ({ page }) => {
    await page.route('/api/v1/settlements*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSettlementData.empty),
      });
    });

    await page.goto(PAGE_PATH);
    await expectEmptyState(page, '暂无结算记录');
  });

  test('错误时显示错误提示', async ({ page }) => {
    await page.route('/api/v1/settlements*', (route) => {
      route.fulfill({ status: 500 });
    });

    await page.goto(PAGE_PATH);
    await expectErrorState(page);
  });

  test('成功加载显示数据', async ({ page }) => {
    await page.route('/api/v1/settlements*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSettlementData.success),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="settlement-table"] tbody tr');

    const rows = page.locator('[data-testid="settlement-table"] tbody tr');
    await expect(rows).toHaveCount(2);
  });
});

// ============================================================
// CP-D1-004: 状态机操作测试 (4 状态)
// ============================================================
test.describe('CP-D1-004: 状态机操作', () => {

  // ----- 合法状态转换 -----

  test('draft → pending_confirm (finance 提交)', async ({ page }) => {
    await loginAs(page, 'finance');

    await page.route('/api/v1/settlements*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'settle-draft-1', month: '2024-12', status: 'draft' }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.route('/api/v1/settlements/settle-draft-1/submit', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'settle-draft-1', status: 'pending_confirm' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="settlement-table"]');

    await page.click('[data-testid="submit-btn-settle-draft-1"]');

    await expectSuccessToast(page, '已提交');
  });

  test('pending_confirm → confirmed (project_owner 确认)', async ({ page }) => {
    await loginAs(page, 'project_owner');

    await page.route('/api/v1/settlements*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'settle-pending-1', month: '2024-12', status: 'pending_confirm' }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.route('/api/v1/settlements/settle-pending-1/confirm', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'settle-pending-1', status: 'confirmed' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="settlement-table"]');

    await page.click('[data-testid="confirm-btn-settle-pending-1"]');

    await expectSuccessToast(page, '已确认');
  });

  test('confirmed → locked (ceo 锁定)', async ({ page }) => {
    await loginAs(page, 'ceo');

    await page.route('/api/v1/settlements*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'settle-confirmed-1', month: '2024-12', status: 'confirmed' }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.route('/api/v1/settlements/settle-confirmed-1/lock', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'settle-confirmed-1', status: 'locked' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="settlement-table"]');

    await page.click('[data-testid="lock-btn-settle-confirmed-1"]');

    // 确认对话框
    await page.click('[data-testid="lock-confirm"]');

    await expectSuccessToast(page, '已锁定');
  });

  test('终态 locked 按钮不可操作', async ({ page }) => {
    await loginAs(page, 'ceo');

    await page.route('/api/v1/settlements*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{ id: 'settle-locked-1', month: '2024-11', status: 'locked' }],
          total: 1,
        }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="settlement-table"]');

    // locked 状态的记录不应该有操作按钮
    const actionBtn = page.locator('[data-testid*="btn-settle-locked-1"]').filter({ hasNotText: '查看' });
    const count = await actionBtn.count();
    expect(count).toBe(0);
  });

  // ----- 非法状态转换 -----

  test('非法转换: draft → locked 返回 400 ST-001', async ({ page }) => {
    await loginAs(page, 'ceo');

    const response = await page.request.post('/api/v1/settlements/settle-draft-1/transition', {
      data: { to_status: 'locked' },
    });

    await expectIllegalTransitionRejected(response, 'ST-001');
  });

  test('非法转换: locked → draft 返回 400 ST-002', async ({ page }) => {
    await loginAs(page, 'admin');

    const response = await page.request.post('/api/v1/settlements/settle-locked-1/transition', {
      data: { to_status: 'draft' },
    });

    await expectIllegalTransitionRejected(response, 'ST-002');
  });
});

// ============================================================
// CP-D1-005: Phase 1 规则测试
// ============================================================
test.describe('CP-D1-005: Phase 1 不阻断规则', () => {
  test('负毛利结算单高亮但可确认', async ({ page }) => {
    await loginAs(page, 'project_owner');

    await page.route('/api/v1/settlements*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSettlementData.negative_profit),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="settlement-table"]');

    // 1. 验证负毛利高亮
    const profitCell = page.locator('[data-testid="profit-cell-settle-loss-1"]');
    await expect(profitCell).toHaveClass(/text-red|negative/);

    // 2. 验证确认按钮仍可用 (Phase 1 不阻断)
    // 假设状态是 pending_confirm
    await page.route('/api/v1/settlements*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{
            id: 'settle-loss-1',
            month: '2024-12',
            profit: -50000,
            status: 'pending_confirm',
            is_negative: true,
          }],
          total: 1,
        }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="settlement-table"]');

    const confirmBtn = page.locator('[data-testid="confirm-btn-settle-loss-1"]');
    await expect(confirmBtn).toBeEnabled();
  });

  test('亏损项目警告但锁定功能正常', async ({ page }) => {
    await loginAs(page, 'ceo');

    await page.route('/api/v1/settlements*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{
            id: 'settle-loss-confirmed-1',
            month: '2024-12',
            profit: -30000,
            status: 'confirmed',
            is_negative: true,
            warnings: ['本月亏损'],
          }],
          total: 1,
        }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="settlement-table"]');

    // 验证警告图标
    const warningIcon = page.locator('[data-testid="warning-icon-settle-loss-confirmed-1"]');
    await expect(warningIcon).toBeVisible();

    // 验证锁定按钮可用
    const lockBtn = page.locator('[data-testid="lock-btn-settle-loss-confirmed-1"]');
    await expect(lockBtn).toBeEnabled();
  });
});

// ============================================================
// CP-D1-006: 生成结算功能测试
// ============================================================
test.describe('CP-D1-006: 生成结算', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'finance');
    await page.route('/api/v1/settlements*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSettlementData.success),
      });
    });
    await page.goto(PAGE_PATH);
  });

  test('点击生成按钮打开选择对话框', async ({ page }) => {
    await page.click('[data-testid="generate-settlement-btn"]');

    await expect(page.locator('[data-testid="generate-modal"]')).toBeVisible();
    await expect(page.locator('[data-testid="month-select"]')).toBeVisible();
    await expect(page.locator('[data-testid="project-select"]')).toBeVisible();
  });

  test('成功生成结算单', async ({ page }) => {
    await page.route('/api/v1/settlements/generate', (route) => {
      route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'settle-new-1', status: 'draft' }),
      });
    });

    await page.click('[data-testid="generate-settlement-btn"]');
    await page.selectOption('[data-testid="month-select"]', '2024-12');
    await page.selectOption('[data-testid="project-select"]', 'proj-1');
    await page.click('[data-testid="generate-confirm"]');

    await expectSuccessToast(page, '结算单已生成');
  });

  test('重复生成给出提示', async ({ page }) => {
    await page.route('/api/v1/settlements/generate', (route) => {
      route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ code: 'SETTLE-001', message: '该月结算单已存在' }),
      });
    });

    await page.click('[data-testid="generate-settlement-btn"]');
    await page.selectOption('[data-testid="month-select"]', '2024-11');
    await page.selectOption('[data-testid="project-select"]', 'proj-1');
    await page.click('[data-testid="generate-confirm"]');

    await expect(page.locator('[data-testid="toast-error"]')).toContainText('已存在');
  });
});
