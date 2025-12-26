/**
 * B2 日报审核 E2E 测试
 *
 * @spec docs/10.module-specs/B2-daily-report-review.md
 * @checkpoint __tests__/checkpoints/B2-daily-report-review.yaml
 *
 * 状态机: 8 状态
 * raw_submitted → trend_pending → trend_ok/trend_flagged
 *                                      ↓
 *                               trend_resolved → final_pending → final_confirmed → final_locked
 */

import { test, expect } from '@playwright/test';
import { loginAs, expectAccessDenied } from '../../utils/auth';
import { TestRole, MODULE_PERMISSIONS } from '../../fixtures/test-accounts';
import { mockDailyReportData } from '../../fixtures/mock-data';
import {
  expectPageTitle,
  expectLoadingState,
  expectEmptyState,
  expectErrorState,
  expectSuccessToast,
  expectVisible,
  expectTableVisible,
  expectIllegalTransitionRejected,
  expectHighlightedButEnabled,
} from '../../utils/assertions';

const MODULE = 'B2-daily-report-review';
const PAGE_PATH = '/daily-reports';
const PAGE_TITLE = '日报审核';

// ============================================================
// CP-B2-001: 权限测试
// ============================================================
test.describe('CP-B2-001: 权限测试', () => {
  const { allowed, denied } = MODULE_PERMISSIONS[MODULE];

  for (const role of allowed) {
    test(`${role} 可以访问日报审核页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto(PAGE_PATH);

      await expect(page).toHaveURL(PAGE_PATH);
      await expect(page.locator('h1')).toHaveText(PAGE_TITLE);
    });
  }

  for (const role of denied) {
    test(`${role} 不能访问日报审核页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto(PAGE_PATH);

      await expectAccessDenied(page);
    });
  }

  test('pitcher 只能看到自己的日报', async ({ page }) => {
    await loginAs(page, 'pitcher');
    await page.route('/api/v1/daily-reports*', (route) => {
      // API 应该只返回当前投手的日报
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{ id: 'dr-1', pitcher_id: 'pitcher-1', pitcher_name: '当前投手' }],
          total: 1,
        }),
      });
    });
    await page.goto(PAGE_PATH);

    await page.waitForSelector('[data-testid="daily-report-table"]');
    const rows = page.locator('[data-testid="daily-report-table"] tbody tr');
    await expect(rows).toHaveCount(1);
  });

  test('supervisor 可以审核团队日报', async ({ page }) => {
    await loginAs(page, 'supervisor');
    await page.route('/api/v1/daily-reports*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockDailyReportData.success),
      });
    });
    await page.goto(PAGE_PATH);

    await page.waitForSelector('[data-testid="daily-report-table"]');
    // supervisor 应该能看到审核按钮
    await expectVisible(page, 'review-actions');
  });
});

// ============================================================
// CP-B2-002: 页面渲染测试
// ============================================================
test.describe('CP-B2-002: 页面渲染', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'supervisor');
    await page.route('/api/v1/daily-reports*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockDailyReportData.success),
      });
    });
    await page.goto(PAGE_PATH);
  });

  test('显示页面标题', async ({ page }) => {
    await expectPageTitle(page, PAGE_TITLE);
  });

  test('显示日报列表表格', async ({ page }) => {
    await expectTableVisible(page, 'daily-report-table');
  });

  test('显示日期筛选器', async ({ page }) => {
    await expectVisible(page, 'date-filter');
  });

  test('显示状态筛选器', async ({ page }) => {
    await expectVisible(page, 'status-filter');
  });

  test('显示项目筛选器', async ({ page }) => {
    await expectVisible(page, 'project-filter');
  });

  test('表格包含必要列', async ({ page }) => {
    const headers = ['日期', '项目', '投手', '进粉', '消耗', 'CPL', '状态', '操作'];
    for (const header of headers) {
      await expect(page.locator('[data-testid="daily-report-table"] th').filter({ hasText: header })).toBeVisible();
    }
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
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockDailyReportData.success),
      });
    });

    await page.goto(PAGE_PATH);
    await expectLoadingState(page);
  });

  test('空数据显示提示', async ({ page }) => {
    await page.route('/api/v1/daily-reports*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockDailyReportData.empty),
      });
    });

    await page.goto(PAGE_PATH);
    await expectEmptyState(page, '暂无日报');
  });

  test('错误时显示错误提示', async ({ page }) => {
    await page.route('/api/v1/daily-reports*', (route) => {
      route.fulfill({ status: 500 });
    });

    await page.goto(PAGE_PATH);
    await expectErrorState(page);
  });

  test('成功加载显示数据', async ({ page }) => {
    await page.route('/api/v1/daily-reports*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockDailyReportData.success),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="daily-report-table"] tbody tr');

    const rows = page.locator('[data-testid="daily-report-table"] tbody tr');
    await expect(rows).toHaveCount(2);
  });
});

// ============================================================
// CP-B2-004: 8 状态机操作测试
// ============================================================
test.describe('CP-B2-004: 状态机操作', () => {

  // ----- 合法状态转换 -----

  test('raw_submitted → trend_pending (系统自动)', async ({ page }) => {
    await loginAs(page, 'pitcher');

    await page.route('/api/v1/daily-reports*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'dr-raw-1', status: 'raw_submitted', conversions: 100, spend: 10000 }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.route('/api/v1/daily-reports/dr-raw-1/submit', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'dr-raw-1', status: 'trend_pending' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="daily-report-table"]');

    await page.click('[data-testid="submit-btn-dr-raw-1"]');

    await expectSuccessToast(page, '已提交');
  });

  test('trend_pending → trend_ok (supervisor 确认正常)', async ({ page }) => {
    await loginAs(page, 'supervisor');

    await page.route('/api/v1/daily-reports*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'dr-trend-1', status: 'trend_pending', conversions: 100, spend: 10000 }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.route('/api/v1/daily-reports/dr-trend-1/approve-trend', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'dr-trend-1', status: 'trend_ok' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="daily-report-table"]');

    await page.click('[data-testid="approve-trend-btn-dr-trend-1"]');

    await expectSuccessToast(page, '趋势确认');
  });

  test('trend_pending → trend_flagged (supervisor 标记异常)', async ({ page }) => {
    await loginAs(page, 'supervisor');

    await page.route('/api/v1/daily-reports*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'dr-flag-1', status: 'trend_pending', conversions: 10, spend: 10000, cpl: 1000 }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.route('/api/v1/daily-reports/dr-flag-1/flag-trend', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'dr-flag-1', status: 'trend_flagged' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="daily-report-table"]');

    await page.click('[data-testid="flag-trend-btn-dr-flag-1"]');

    // 填写标记原因
    await page.fill('[data-testid="flag-reason"]', 'CPL 过高');
    await page.click('[data-testid="flag-confirm"]');

    await expectSuccessToast(page, '已标记异常');
  });

  test('trend_flagged → trend_resolved (pitcher 解释后 supervisor 确认)', async ({ page }) => {
    await loginAs(page, 'supervisor');

    await page.route('/api/v1/daily-reports*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{
              id: 'dr-flagged-1',
              status: 'trend_flagged',
              flag_reason: 'CPL 过高',
              pitcher_explanation: '今天有新渠道测试',
            }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.route('/api/v1/daily-reports/dr-flagged-1/resolve-trend', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'dr-flagged-1', status: 'trend_resolved' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="daily-report-table"]');

    await page.click('[data-testid="resolve-btn-dr-flagged-1"]');

    await expectSuccessToast(page, '已解决');
  });

  test('trend_ok → final_pending (进入终稿流程)', async ({ page }) => {
    await loginAs(page, 'pitcher');

    await page.route('/api/v1/daily-reports*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'dr-ok-1', status: 'trend_ok' }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.route('/api/v1/daily-reports/dr-ok-1/submit-final', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'dr-ok-1', status: 'final_pending' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="daily-report-table"]');

    await page.click('[data-testid="submit-final-btn-dr-ok-1"]');

    await expectSuccessToast(page, '已提交终稿');
  });

  test('final_pending → final_confirmed (supervisor 确认终稿)', async ({ page }) => {
    await loginAs(page, 'supervisor');

    await page.route('/api/v1/daily-reports*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'dr-final-1', status: 'final_pending' }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.route('/api/v1/daily-reports/dr-final-1/confirm-final', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'dr-final-1', status: 'final_confirmed' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="daily-report-table"]');

    await page.click('[data-testid="confirm-final-btn-dr-final-1"]');

    await expectSuccessToast(page, '终稿已确认');
  });

  test('final_confirmed → final_locked (project_owner 锁定)', async ({ page }) => {
    await loginAs(page, 'project_owner');

    await page.route('/api/v1/daily-reports*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'dr-confirmed-1', status: 'final_confirmed' }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.route('/api/v1/daily-reports/dr-confirmed-1/lock', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'dr-confirmed-1', status: 'final_locked' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="daily-report-table"]');

    await page.click('[data-testid="lock-btn-dr-confirmed-1"]');

    await expectSuccessToast(page, '已锁定');
  });

  test('终态 final_locked 按钮不可操作', async ({ page }) => {
    await loginAs(page, 'ceo');

    await page.route('/api/v1/daily-reports*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{ id: 'dr-locked-1', status: 'final_locked' }],
          total: 1,
        }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="daily-report-table"]');

    // final_locked 状态的记录不应该有操作按钮
    const actionBtn = page.locator('[data-testid*="btn-dr-locked-1"]');
    const count = await actionBtn.count();
    expect(count).toBe(0);
  });

  // ----- 非法状态转换 -----

  test('非法转换: raw_submitted → final_locked 返回 400 ST-001', async ({ page }) => {
    await loginAs(page, 'supervisor');

    const response = await page.request.post('/api/v1/daily-reports/dr-raw-1/transition', {
      data: { to_status: 'final_locked' },
    });

    await expectIllegalTransitionRejected(response, 'ST-001');
  });

  test('非法转换: final_locked → trend_pending 返回 400 ST-002', async ({ page }) => {
    await loginAs(page, 'admin');

    const response = await page.request.post('/api/v1/daily-reports/dr-locked-1/transition', {
      data: { to_status: 'trend_pending' },
    });

    await expectIllegalTransitionRejected(response, 'ST-002');
  });

  test('非法转换: trend_ok → trend_flagged 返回 400', async ({ page }) => {
    await loginAs(page, 'supervisor');

    const response = await page.request.post('/api/v1/daily-reports/dr-ok-1/transition', {
      data: { to_status: 'trend_flagged' },
    });

    expect(response.status()).toBe(400);
  });
});

// ============================================================
// CP-B2-005: Phase 1 规则测试
// ============================================================
test.describe('CP-B2-005: Phase 1 不阻断规则', () => {
  test('CPL 超标日报高亮但可审核', async ({ page }) => {
    await loginAs(page, 'supervisor');

    await page.route('/api/v1/daily-reports*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockDailyReportData.abnormal_cpl),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="daily-report-table"]');

    // 1. 验证 CPL 列高亮
    const cplCell = page.locator('[data-testid="cpl-cell-dr-abnormal-1"]');
    await expect(cplCell).toHaveClass(/text-red|bg-red|negative/);

    // 2. 验证审核按钮仍可用 (Phase 1 不阻断)
    const approveBtn = page.locator('[data-testid="approve-trend-btn-dr-abnormal-1"]');
    await expect(approveBtn).toBeEnabled();
    await expect(approveBtn).not.toHaveAttribute('disabled');
  });

  test('异常日报有警告提示但不阻断操作', async ({ page }) => {
    await loginAs(page, 'supervisor');

    await page.route('/api/v1/daily-reports*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockDailyReportData.abnormal_cpl),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="daily-report-table"]');

    // 验证警告图标或提示存在
    const warningIcon = page.locator('[data-testid="warning-icon-dr-abnormal-1"]');
    await expect(warningIcon).toBeVisible();

    // 验证行可点击查看详情
    const row = page.locator('[data-testid="row-dr-abnormal-1"]');
    await row.click();

    // 应该能打开详情
    await expect(page.locator('[data-testid="report-detail-modal"]')).toBeVisible();
  });

  test('批量审核时异常项目仍可被选中', async ({ page }) => {
    await loginAs(page, 'supervisor');

    await page.route('/api/v1/daily-reports*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            { id: 'dr-normal-1', status: 'trend_pending', cpl: 100, is_abnormal: false },
            { id: 'dr-abnormal-1', status: 'trend_pending', cpl: 1000, is_abnormal: true },
          ],
          total: 2,
        }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="daily-report-table"]');

    // 异常日报的复选框应该可选
    const abnormalCheckbox = page.locator('[data-testid="checkbox-dr-abnormal-1"]');
    await expect(abnormalCheckbox).toBeEnabled();

    // 选中后批量审核按钮仍可用
    await abnormalCheckbox.click();
    const batchApproveBtn = page.locator('[data-testid="batch-approve-btn"]');
    await expect(batchApproveBtn).toBeEnabled();
  });
});
