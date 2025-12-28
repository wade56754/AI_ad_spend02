/**
 * B3 周简报 E2E 测试
 *
 * @spec docs/10.module-specs/B3-weekly-brief.md
 * @checkpoint __tests__/checkpoints/B3-weekly-brief.yaml
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
  expectSuccessToast,
} from '../../utils/assertions';

const MODULE = 'B3-weekly-brief';
const PAGE_PATH = '/weekly-briefs';
const PAGE_TITLE = '周简报';

// Mock 数据
const mockWeeklyBriefData = {
  success: {
    items: [
      {
        id: 'wb-1',
        week: '2024-W51',
        project_name: '项目A',
        pitcher_name: '投手小王',
        conversions: 500,
        spend: 50000,
        cpl: 100,
        status: 'pending',
      },
      {
        id: 'wb-2',
        week: '2024-W50',
        project_name: '项目B',
        pitcher_name: '投手小李',
        conversions: 400,
        spend: 40000,
        cpl: 100,
        status: 'confirmed',
      },
    ],
    total: 2,
  },
  empty: { items: [], total: 0 },
};

// ============================================================
// CP-B3-001: 权限测试
// ============================================================
test.describe('CP-B3-001: 权限测试', () => {
  const { allowed, denied } = MODULE_PERMISSIONS[MODULE];

  for (const role of allowed) {
    test(`${role} 可以访问周简报页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto(PAGE_PATH);

      await expect(page).toHaveURL(PAGE_PATH);
      await expect(page.locator('h1')).toHaveText(PAGE_TITLE);
    });
  }

  for (const role of denied) {
    test(`${role} 不能访问周简报页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto(PAGE_PATH);

      await expectAccessDenied(page);
    });
  }

  test('project_owner 可以查看并确认周简报', async ({ page }) => {
    await loginAs(page, 'project_owner');
    await page.route('/api/v1/weekly-briefs*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWeeklyBriefData.success),
      });
    });
    await page.goto(PAGE_PATH);

    await page.waitForSelector('[data-testid="weekly-brief-table"]');
    await expectVisible(page, 'confirm-btn-wb-1');
  });
});

// ============================================================
// CP-B3-002: 页面渲染测试
// ============================================================
test.describe('CP-B3-002: 页面渲染', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'project_owner');
    await page.route('/api/v1/weekly-briefs*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWeeklyBriefData.success),
      });
    });
    await page.goto(PAGE_PATH);
  });

  test('显示页面标题', async ({ page }) => {
    await expectPageTitle(page, PAGE_TITLE);
  });

  test('显示周简报表格', async ({ page }) => {
    await expectTableVisible(page, 'weekly-brief-table');
  });

  test('显示周次筛选器', async ({ page }) => {
    await expectVisible(page, 'week-filter');
  });

  test('显示项目筛选器', async ({ page }) => {
    await expectVisible(page, 'project-filter');
  });

  test('表格包含必要列', async ({ page }) => {
    const headers = ['周次', '项目', '投手', '进粉', '消耗', 'CPL', '状态', '操作'];
    for (const header of headers) {
      await expect(page.locator('[data-testid="weekly-brief-table"] th').filter({ hasText: header })).toBeVisible();
    }
  });
});

// ============================================================
// CP-B3-003: 数据状态测试
// ============================================================
test.describe('CP-B3-003: 数据状态', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'project_owner');
  });

  test('加载中显示骨架屏', async ({ page }) => {
    await page.route('/api/v1/weekly-briefs*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWeeklyBriefData.success),
      });
    });

    await page.goto(PAGE_PATH);
    await expectLoadingState(page);
  });

  test('空数据显示提示', async ({ page }) => {
    await page.route('/api/v1/weekly-briefs*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWeeklyBriefData.empty),
      });
    });

    await page.goto(PAGE_PATH);
    await expectEmptyState(page, '暂无周简报');
  });

  test('错误时显示错误提示', async ({ page }) => {
    await page.route('/api/v1/weekly-briefs*', (route) => {
      route.fulfill({ status: 500 });
    });

    await page.goto(PAGE_PATH);
    await expectErrorState(page);
  });

  test('成功加载显示数据', async ({ page }) => {
    await page.route('/api/v1/weekly-briefs*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWeeklyBriefData.success),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="weekly-brief-table"] tbody tr');

    const rows = page.locator('[data-testid="weekly-brief-table"] tbody tr');
    await expect(rows).toHaveCount(2);
  });
});

// ============================================================
// CP-B3-004: 功能操作测试
// ============================================================
test.describe('CP-B3-004: 功能操作', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'project_owner');
    await page.route('/api/v1/weekly-briefs*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockWeeklyBriefData.success),
        });
      } else {
        route.continue();
      }
    });
    await page.goto(PAGE_PATH);
  });

  test('确认周简报', async ({ page }) => {
    await page.route('/api/v1/weekly-briefs/wb-1/confirm', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'wb-1', status: 'confirmed' }),
      });
    });

    await page.waitForSelector('[data-testid="weekly-brief-table"]');
    await page.click('[data-testid="confirm-btn-wb-1"]');

    await expectSuccessToast(page, '已确认');
  });

  test('周次筛选刷新数据', async ({ page }) => {
    const requestPromise = page.waitForRequest(req =>
      req.url().includes('/api/v1/weekly-briefs') && req.url().includes('week=2024-W50')
    );

    await page.click('[data-testid="week-filter"]');
    await page.click('[data-testid="week-option-2024-W50"]');

    await requestPromise;
  });

  test('点击查看详情', async ({ page }) => {
    await page.waitForSelector('[data-testid="weekly-brief-table"]');
    await page.click('[data-testid="view-btn-wb-1"]');

    await expect(page.locator('[data-testid="brief-detail-modal"]')).toBeVisible();
  });

  test('导出周简报', async ({ page }) => {
    const downloadPromise = page.waitForEvent('download');

    await page.click('[data-testid="export-btn"]');

    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('weekly');
  });
});

// ============================================================
// CP-B3-005: Phase 1 规则测试
// ============================================================
test.describe('CP-B3-005: Phase 1 不阻断规则', () => {
  test('CPL 超标周简报高亮但可确认', async ({ page }) => {
    await loginAs(page, 'project_owner');

    await page.route('/api/v1/weekly-briefs*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{
            id: 'wb-abnormal-1',
            week: '2024-W51',
            project_name: '测试项目',
            conversions: 50,
            spend: 50000,
            cpl: 1000,
            target_cpl: 100,
            status: 'pending',
            is_abnormal: true,
          }],
          total: 1,
        }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="weekly-brief-table"]');

    // 1. 验证 CPL 高亮
    const cplCell = page.locator('[data-testid="cpl-cell-wb-abnormal-1"]');
    await expect(cplCell).toHaveClass(/text-red|negative/);

    // 2. 验证确认按钮仍可用 (Phase 1 不阻断)
    const confirmBtn = page.locator('[data-testid="confirm-btn-wb-abnormal-1"]');
    await expect(confirmBtn).toBeEnabled();
  });
});
