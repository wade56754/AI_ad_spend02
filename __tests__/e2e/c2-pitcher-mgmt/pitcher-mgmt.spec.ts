/**
 * C2 投手管理 E2E 测试
 *
 * @spec docs/10.module-specs/C2-pitcher-mgmt.md
 * @checkpoint __tests__/checkpoints/C2-pitcher-mgmt.yaml
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

const MODULE = 'C2-pitcher-mgmt';
const PAGE_PATH = '/pitchers';
const PAGE_TITLE = '投手管理';

// Mock 数据
const mockPitcherData = {
  success: {
    items: [
      {
        id: 'pitcher-1',
        name: '投手小王',
        email: 'wang@test.com',
        status: 'active',
        supervisor_name: '主管A',
        projects: ['项目A', '项目B'],
      },
      {
        id: 'pitcher-2',
        name: '投手小李',
        email: 'li@test.com',
        status: 'active',
        supervisor_name: '主管B',
        projects: ['项目C'],
      },
    ],
    total: 2,
  },
  empty: { items: [], total: 0 },
};

// ============================================================
// CP-C2-001: 权限测试
// ============================================================
test.describe('CP-C2-001: 权限测试', () => {
  const { allowed, denied } = MODULE_PERMISSIONS[MODULE];

  for (const role of allowed) {
    test(`${role} 可以访问投手管理页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto(PAGE_PATH);

      await expect(page).toHaveURL(PAGE_PATH);
      await expect(page.locator('h1')).toHaveText(PAGE_TITLE);
    });
  }

  for (const role of denied) {
    test(`${role} 不能访问投手管理页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto(PAGE_PATH);

      await expectAccessDenied(page);
    });
  }

  test('supervisor 可以管理自己团队的投手', async ({ page }) => {
    await loginAs(page, 'supervisor');
    await page.route('/api/v1/pitchers*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{ id: 'pitcher-1', name: '我的投手', supervisor_id: 'supervisor_id' }],
          total: 1,
        }),
      });
    });
    await page.goto(PAGE_PATH);

    await page.waitForSelector('[data-testid="pitcher-table"]');
    // 应该能看到编辑按钮
    await expectVisible(page, 'edit-btn-pitcher-1');
  });

  test('admin 可以创建新投手', async ({ page }) => {
    await loginAs(page, 'admin');
    await page.goto(PAGE_PATH);

    await expectVisible(page, 'create-pitcher-btn');
    await expect(page.locator('[data-testid="create-pitcher-btn"]')).toBeEnabled();
  });
});

// ============================================================
// CP-C2-002: 页面渲染测试
// ============================================================
test.describe('CP-C2-002: 页面渲染', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'supervisor');
    await page.route('/api/v1/pitchers*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPitcherData.success),
      });
    });
    await page.goto(PAGE_PATH);
  });

  test('显示页面标题', async ({ page }) => {
    await expectPageTitle(page, PAGE_TITLE);
  });

  test('显示投手列表表格', async ({ page }) => {
    await expectTableVisible(page, 'pitcher-table');
  });

  test('显示搜索框', async ({ page }) => {
    await expectVisible(page, 'search-input');
  });

  test('显示状态筛选器', async ({ page }) => {
    await expectVisible(page, 'status-filter');
  });

  test('表格包含必要列', async ({ page }) => {
    const headers = ['姓名', '邮箱', '状态', '主管', '负责项目', '操作'];
    for (const header of headers) {
      await expect(page.locator('[data-testid="pitcher-table"] th').filter({ hasText: header })).toBeVisible();
    }
  });
});

// ============================================================
// CP-C2-003: 数据状态测试
// ============================================================
test.describe('CP-C2-003: 数据状态', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'supervisor');
  });

  test('加载中显示骨架屏', async ({ page }) => {
    await page.route('/api/v1/pitchers*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPitcherData.success),
      });
    });

    await page.goto(PAGE_PATH);
    await expectLoadingState(page);
  });

  test('空数据显示提示', async ({ page }) => {
    await page.route('/api/v1/pitchers*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPitcherData.empty),
      });
    });

    await page.goto(PAGE_PATH);
    await expectEmptyState(page, '暂无投手');
  });

  test('错误时显示错误提示', async ({ page }) => {
    await page.route('/api/v1/pitchers*', (route) => {
      route.fulfill({ status: 500 });
    });

    await page.goto(PAGE_PATH);
    await expectErrorState(page);
  });

  test('成功加载显示数据', async ({ page }) => {
    await page.route('/api/v1/pitchers*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPitcherData.success),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="pitcher-table"] tbody tr');

    const rows = page.locator('[data-testid="pitcher-table"] tbody tr');
    await expect(rows).toHaveCount(2);
  });
});

// ============================================================
// CP-C2-004: 功能操作测试
// ============================================================
test.describe('CP-C2-004: 功能操作', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'supervisor');
    await page.route('/api/v1/pitchers*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockPitcherData.success),
        });
      } else {
        route.continue();
      }
    });
    await page.goto(PAGE_PATH);
  });

  test('搜索投手', async ({ page }) => {
    const requestPromise = page.waitForRequest(req =>
      req.url().includes('/api/v1/pitchers') && req.url().includes('search=小王')
    );

    await page.fill('[data-testid="search-input"]', '小王');
    await page.click('[data-testid="search-btn"]');

    await requestPromise;
  });

  test('编辑投手信息', async ({ page }) => {
    await page.waitForSelector('[data-testid="pitcher-table"]');
    await page.click('[data-testid="edit-btn-pitcher-1"]');

    await expect(page.locator('[data-testid="pitcher-form-modal"]')).toBeVisible();
  });

  test('分配项目给投手', async ({ page }) => {
    await page.route('/api/v1/pitchers/pitcher-1/assign-project', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true }),
      });
    });

    await page.waitForSelector('[data-testid="pitcher-table"]');
    await page.click('[data-testid="assign-btn-pitcher-1"]');

    await page.selectOption('[data-testid="project-select"]', 'proj-1');
    await page.click('[data-testid="assign-confirm"]');

    await expectSuccessToast(page, '分配成功');
  });

  test('查看投手绩效', async ({ page }) => {
    await page.waitForSelector('[data-testid="pitcher-table"]');
    await page.click('[data-testid="performance-btn-pitcher-1"]');

    await expect(page.locator('[data-testid="performance-modal"]')).toBeVisible();
  });
});

// ============================================================
// CP-C2-005: Phase 1 规则测试
// ============================================================
test.describe('CP-C2-005: Phase 1 不阻断规则', () => {
  test('绩效异常投手高亮但可正常操作', async ({ page }) => {
    await loginAs(page, 'supervisor');

    await page.route('/api/v1/pitchers*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{
            id: 'pitcher-abnormal-1',
            name: '异常投手',
            status: 'active',
            avg_cpl: 500,
            target_cpl: 100,
            is_abnormal: true,
          }],
          total: 1,
        }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="pitcher-table"]');

    // 1. 验证行高亮
    const row = page.locator('[data-testid="row-pitcher-abnormal-1"]');
    await expect(row).toHaveClass(/bg-amber|bg-yellow|warning/);

    // 2. 验证操作按钮仍可用 (Phase 1 不阻断)
    const editBtn = page.locator('[data-testid="edit-btn-pitcher-abnormal-1"]');
    await expect(editBtn).toBeEnabled();
  });
});
