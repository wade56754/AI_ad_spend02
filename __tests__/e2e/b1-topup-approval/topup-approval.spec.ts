/**
 * B1 充值审批 E2E 测试
 *
 * @spec docs/10.module-specs/B1-topup-approval.md
 * @checkpoint __tests__/checkpoints/B1-topup-approval.yaml
 *
 * 状态机: 7 状态
 * draft → pending_review → finance_approve → paid → completed
 *              ↓                 ↓
 *          rejected           voided
 */

import { test, expect } from '@playwright/test';
import { loginAs, expectAccessDenied } from '../../utils/auth';
import { TestRole, MODULE_PERMISSIONS } from '../../fixtures/test-accounts';
import { mockTopupData } from '../../fixtures/mock-data';
import {
  expectPageTitle,
  expectLoadingState,
  expectEmptyState,
  expectErrorState,
  expectSuccessToast,
  expectVisible,
  expectTableVisible,
  expectIllegalTransitionRejected,
} from '../../utils/assertions';

const MODULE = 'B1-topup-approval';
const PAGE_PATH = '/topups';
const PAGE_TITLE = '充值审批';

// ============================================================
// CP-B1-001: 权限测试
// ============================================================
test.describe('CP-B1-001: 权限测试', () => {
  const { allowed, denied } = MODULE_PERMISSIONS[MODULE];

  for (const role of allowed) {
    test(`${role} 可以访问充值审批页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto(PAGE_PATH);

      await expect(page).toHaveURL(PAGE_PATH);
      await expect(page.locator('h1')).toHaveText(PAGE_TITLE);
    });
  }

  for (const role of denied) {
    test(`${role} 不能访问充值审批页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto(PAGE_PATH);

      await expectAccessDenied(page);
    });
  }

  test('project_owner 可以创建充值申请', async ({ page }) => {
    await loginAs(page, 'project_owner');
    await page.goto(PAGE_PATH);

    await expectVisible(page, 'create-topup-btn');
    await expect(page.locator('[data-testid="create-topup-btn"]')).toBeEnabled();
  });

  test('finance 可以审批', async ({ page }) => {
    await loginAs(page, 'finance');
    await page.route('/api/v1/topups*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTopupData.success),
      });
    });
    await page.goto(PAGE_PATH);

    // finance 应该能看到审批按钮
    await page.waitForSelector('[data-testid="topup-table"]');
  });
});

// ============================================================
// CP-B1-002: 页面渲染测试
// ============================================================
test.describe('CP-B1-002: 页面渲染', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'ceo');
    await page.route('/api/v1/topups*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTopupData.success),
      });
    });
    await page.goto(PAGE_PATH);
  });

  test('显示页面标题', async ({ page }) => {
    await expectPageTitle(page, PAGE_TITLE);
  });

  test('显示充值列表表格', async ({ page }) => {
    await expectTableVisible(page, 'topup-table');
  });

  test('显示新建按钮', async ({ page }) => {
    await expectVisible(page, 'create-topup-btn');
  });

  test('显示状态筛选器', async ({ page }) => {
    await expectVisible(page, 'status-filter');
  });
});

// ============================================================
// CP-B1-003: 数据状态测试
// ============================================================
test.describe('CP-B1-003: 数据状态', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'ceo');
  });

  test('加载中显示骨架屏', async ({ page }) => {
    await page.route('/api/v1/topups*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTopupData.success),
      });
    });

    await page.goto(PAGE_PATH);
    await expectLoadingState(page);
  });

  test('空数据显示提示', async ({ page }) => {
    await page.route('/api/v1/topups*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTopupData.empty),
      });
    });

    await page.goto(PAGE_PATH);
    await expectEmptyState(page, '暂无充值记录');
  });

  test('错误时显示错误提示', async ({ page }) => {
    await page.route('/api/v1/topups*', (route) => {
      route.fulfill({ status: 500 });
    });

    await page.goto(PAGE_PATH);
    await expectErrorState(page);
  });

  test('成功加载显示数据', async ({ page }) => {
    await page.route('/api/v1/topups*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTopupData.success),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="topup-table"] tbody tr');

    const rows = page.locator('[data-testid="topup-table"] tbody tr');
    await expect(rows).toHaveCount(4);
  });
});

// ============================================================
// CP-B1-004: 状态机操作测试 (7 状态)
// ============================================================
test.describe('CP-B1-004: 状态机操作', () => {

  // ----- 合法状态转换 -----

  test('draft → pending_review (project_owner 提交)', async ({ page }) => {
    await loginAs(page, 'project_owner');

    // Mock 列表数据
    await page.route('/api/v1/topups*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'topup-draft-1', amount: 50000, status: 'draft', project: '项目A' }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    // Mock 状态转换 API
    await page.route('/api/v1/topups/topup-draft-1/submit', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'topup-draft-1', status: 'pending_review' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="topup-table"]');

    // 点击提交按钮
    await page.click('[data-testid="submit-btn-topup-draft-1"]');

    await expectSuccessToast(page, '已提交');
  });

  test('pending_review → finance_approve (supervisor 确认)', async ({ page }) => {
    await loginAs(page, 'supervisor');

    await page.route('/api/v1/topups*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'topup-pending-1', amount: 50000, status: 'pending_review' }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.route('/api/v1/topups/topup-pending-1/confirm', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'topup-pending-1', status: 'finance_approve' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="topup-table"]');

    await page.click('[data-testid="confirm-btn-topup-pending-1"]');

    await expectSuccessToast(page, '已确认');
  });

  test('finance_approve → paid (finance 审批通过)', async ({ page }) => {
    await loginAs(page, 'finance');

    await page.route('/api/v1/topups*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'topup-fa-1', amount: 50000, status: 'finance_approve' }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.route('/api/v1/topups/topup-fa-1/approve', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'topup-fa-1', status: 'paid' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="topup-table"]');

    await page.click('[data-testid="approve-btn-topup-fa-1"]');

    await expectSuccessToast(page, '审批通过');
  });

  test('pending_review → rejected (supervisor 拒绝)', async ({ page }) => {
    await loginAs(page, 'supervisor');

    await page.route('/api/v1/topups*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'topup-reject-1', amount: 50000, status: 'pending_review' }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.route('/api/v1/topups/topup-reject-1/reject', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'topup-reject-1', status: 'rejected' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="topup-table"]');

    await page.click('[data-testid="reject-btn-topup-reject-1"]');

    // 填写拒绝原因
    await page.fill('[data-testid="reject-reason"]', '金额过大');
    await page.click('[data-testid="reject-confirm"]');

    await expectSuccessToast(page, '已拒绝');
  });

  test('终态 completed 按钮不可操作', async ({ page }) => {
    await loginAs(page, 'ceo');

    await page.route('/api/v1/topups*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{ id: 'topup-completed-1', amount: 50000, status: 'completed' }],
          total: 1,
        }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="topup-table"]');

    // completed 状态的记录不应该有操作按钮
    const actionBtn = page.locator('[data-testid*="btn-topup-completed-1"]');
    const count = await actionBtn.count();
    expect(count).toBe(0);
  });

  // ----- 非法状态转换 -----

  test('非法转换: draft → paid 返回 400 ST-001', async ({ page }) => {
    await loginAs(page, 'finance');

    // 直接调用 API 尝试非法转换
    const response = await page.request.post('/api/v1/topups/topup-draft-1/transition', {
      data: { to_status: 'paid' },
    });

    await expectIllegalTransitionRejected(response, 'ST-001');
  });

  test('非法转换: completed → paid 返回 400 ST-002', async ({ page }) => {
    await loginAs(page, 'admin');

    const response = await page.request.post('/api/v1/topups/topup-completed-1/transition', {
      data: { to_status: 'paid' },
    });

    await expectIllegalTransitionRejected(response, 'ST-002');
  });

  test('非法转换: rejected → finance_approve 返回 400', async ({ page }) => {
    await loginAs(page, 'ceo');

    const response = await page.request.post('/api/v1/topups/topup-rejected-1/transition', {
      data: { to_status: 'finance_approve' },
    });

    expect(response.status()).toBe(400);
  });
});

// ============================================================
// CP-B1-005: Phase 1 规则测试
// ============================================================
test.describe('CP-B1-005: Phase 1 不阻断规则', () => {
  test('大额充值警告高亮但可审批', async ({ page }) => {
    await loginAs(page, 'finance');

    await page.route('/api/v1/topups*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{
            id: 'topup-large-1',
            amount: 1000000,  // 大额
            status: 'finance_approve',
            is_large_amount: true,
            warnings: ['金额超过 50 万，请谨慎审批'],
          }],
          total: 1,
        }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="topup-table"]');

    // 1. 验证警告高亮
    const row = page.locator('[data-testid="row-topup-large-1"]');
    await expect(row).toHaveClass(/bg-amber|bg-yellow|warning/);

    // 2. 验证审批按钮仍可用 (Phase 1 不阻断)
    const approveBtn = page.locator('[data-testid="approve-btn-topup-large-1"]');
    await expect(approveBtn).toBeEnabled();
    await expect(approveBtn).not.toHaveAttribute('disabled');
  });
});
