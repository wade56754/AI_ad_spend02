/**
 * C1 项目管理 E2E 测试
 *
 * @spec docs/10.module-specs/C1-project-mgmt.md
 * @checkpoint __tests__/checkpoints/C1-project-mgmt.yaml
 *
 * 状态机: 5 状态
 * planning → active → paused → completed → archived
 */

import { test, expect } from '@playwright/test';
import { loginAs, expectAccessDenied } from '../../utils/auth';
import { TestRole, MODULE_PERMISSIONS } from '../../fixtures/test-accounts';
import { mockProjectData } from '../../fixtures/mock-data';
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

const MODULE = 'C1-project-mgmt';
const PAGE_PATH = '/projects';
const PAGE_TITLE = '项目管理';

// ============================================================
// CP-C1-001: 权限测试
// ============================================================
test.describe('CP-C1-001: 权限测试', () => {
  const { allowed, denied } = MODULE_PERMISSIONS[MODULE];

  for (const role of allowed) {
    test(`${role} 可以访问项目管理页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto(PAGE_PATH);

      await expect(page).toHaveURL(PAGE_PATH);
      await expect(page.locator('h1')).toHaveText(PAGE_TITLE);
    });
  }

  for (const role of denied) {
    test(`${role} 不能访问项目管理页`, async ({ page }) => {
      await loginAs(page, role);
      await page.goto(PAGE_PATH);

      await expectAccessDenied(page);
    });
  }

  test('ceo 可以创建项目', async ({ page }) => {
    await loginAs(page, 'ceo');
    await page.goto(PAGE_PATH);

    await expectVisible(page, 'create-project-btn');
    await expect(page.locator('[data-testid="create-project-btn"]')).toBeEnabled();
  });

  test('project_owner 可以管理自己的项目', async ({ page }) => {
    await loginAs(page, 'project_owner');
    await page.route('/api/v1/projects*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{ id: 'proj-1', name: '我的项目', owner_id: 'project_owner_id', status: 'active' }],
          total: 1,
        }),
      });
    });
    await page.goto(PAGE_PATH);

    await page.waitForSelector('[data-testid="project-table"]');
    // 应该能看到编辑按钮
    await expectVisible(page, 'edit-btn-proj-1');
  });

  test('pitcher 只能查看项目（不能编辑）', async ({ page }) => {
    await loginAs(page, 'pitcher');
    await page.route('/api/v1/projects*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockProjectData.success),
      });
    });
    await page.goto(PAGE_PATH);

    await page.waitForSelector('[data-testid="project-table"]');
    // pitcher 不应该看到编辑按钮
    const editBtn = page.locator('[data-testid="edit-btn-proj-1"]');
    await expect(editBtn).not.toBeVisible();
  });
});

// ============================================================
// CP-C1-002: 页面渲染测试
// ============================================================
test.describe('CP-C1-002: 页面渲染', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'ceo');
    await page.route('/api/v1/projects*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockProjectData.success),
      });
    });
    await page.goto(PAGE_PATH);
  });

  test('显示页面标题', async ({ page }) => {
    await expectPageTitle(page, PAGE_TITLE);
  });

  test('显示项目列表表格', async ({ page }) => {
    await expectTableVisible(page, 'project-table');
  });

  test('显示新建按钮', async ({ page }) => {
    await expectVisible(page, 'create-project-btn');
  });

  test('显示状态筛选器', async ({ page }) => {
    await expectVisible(page, 'status-filter');
  });

  test('显示搜索框', async ({ page }) => {
    await expectVisible(page, 'search-input');
  });

  test('表格包含必要列', async ({ page }) => {
    const headers = ['项目名称', '负责人', '状态', '预算', '消耗', '操作'];
    for (const header of headers) {
      await expect(page.locator('[data-testid="project-table"] th').filter({ hasText: header })).toBeVisible();
    }
  });
});

// ============================================================
// CP-C1-003: 数据状态测试
// ============================================================
test.describe('CP-C1-003: 数据状态', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'ceo');
  });

  test('加载中显示骨架屏', async ({ page }) => {
    await page.route('/api/v1/projects*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockProjectData.success),
      });
    });

    await page.goto(PAGE_PATH);
    await expectLoadingState(page);
  });

  test('空数据显示提示', async ({ page }) => {
    await page.route('/api/v1/projects*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockProjectData.empty),
      });
    });

    await page.goto(PAGE_PATH);
    await expectEmptyState(page, '暂无项目');
  });

  test('错误时显示错误提示', async ({ page }) => {
    await page.route('/api/v1/projects*', (route) => {
      route.fulfill({ status: 500 });
    });

    await page.goto(PAGE_PATH);
    await expectErrorState(page);
  });

  test('成功加载显示数据', async ({ page }) => {
    await page.route('/api/v1/projects*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockProjectData.success),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="project-table"] tbody tr');

    const rows = page.locator('[data-testid="project-table"] tbody tr');
    await expect(rows).toHaveCount(3);
  });
});

// ============================================================
// CP-C1-004: 状态机操作测试 (5 状态)
// ============================================================
test.describe('CP-C1-004: 状态机操作', () => {

  // ----- 合法状态转换 -----

  test('planning → active (ceo 启动项目)', async ({ page }) => {
    await loginAs(page, 'ceo');

    await page.route('/api/v1/projects*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'proj-plan-1', name: '测试项目', status: 'planning', budget: 100000 }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.route('/api/v1/projects/proj-plan-1/activate', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'proj-plan-1', status: 'active' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="project-table"]');

    await page.click('[data-testid="activate-btn-proj-plan-1"]');

    await expectSuccessToast(page, '项目已启动');
  });

  test('active → paused (project_owner 暂停)', async ({ page }) => {
    await loginAs(page, 'project_owner');

    await page.route('/api/v1/projects*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'proj-active-1', name: '运行中项目', status: 'active' }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.route('/api/v1/projects/proj-active-1/pause', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'proj-active-1', status: 'paused' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="project-table"]');

    await page.click('[data-testid="pause-btn-proj-active-1"]');

    await expectSuccessToast(page, '项目已暂停');
  });

  test('paused → active (恢复项目)', async ({ page }) => {
    await loginAs(page, 'project_owner');

    await page.route('/api/v1/projects*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'proj-paused-1', name: '暂停项目', status: 'paused' }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.route('/api/v1/projects/proj-paused-1/resume', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'proj-paused-1', status: 'active' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="project-table"]');

    await page.click('[data-testid="resume-btn-proj-paused-1"]');

    await expectSuccessToast(page, '项目已恢复');
  });

  test('active → completed (ceo 完成项目)', async ({ page }) => {
    await loginAs(page, 'ceo');

    await page.route('/api/v1/projects*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'proj-complete-1', name: '待完成项目', status: 'active' }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.route('/api/v1/projects/proj-complete-1/complete', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'proj-complete-1', status: 'completed' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="project-table"]');

    await page.click('[data-testid="complete-btn-proj-complete-1"]');

    // 确认对话框
    await page.click('[data-testid="confirm-complete"]');

    await expectSuccessToast(page, '项目已完成');
  });

  test('completed → archived (admin 归档)', async ({ page }) => {
    await loginAs(page, 'admin');

    await page.route('/api/v1/projects*', (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'proj-archive-1', name: '已完成项目', status: 'completed' }],
            total: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.route('/api/v1/projects/proj-archive-1/archive', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'proj-archive-1', status: 'archived' }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="project-table"]');

    await page.click('[data-testid="archive-btn-proj-archive-1"]');

    await expectSuccessToast(page, '项目已归档');
  });

  test('终态 archived 按钮不可操作', async ({ page }) => {
    await loginAs(page, 'ceo');

    await page.route('/api/v1/projects*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{ id: 'proj-archived-1', name: '归档项目', status: 'archived' }],
          total: 1,
        }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="project-table"]');

    // archived 状态的记录不应该有状态操作按钮
    const actionBtn = page.locator('[data-testid*="btn-proj-archived-1"]').filter({ hasNotText: '查看' });
    const count = await actionBtn.count();
    expect(count).toBe(0);
  });

  // ----- 非法状态转换 -----

  test('非法转换: planning → completed 返回 400 ST-001', async ({ page }) => {
    await loginAs(page, 'ceo');

    const response = await page.request.post('/api/v1/projects/proj-plan-1/transition', {
      data: { to_status: 'completed' },
    });

    await expectIllegalTransitionRejected(response, 'ST-001');
  });

  test('非法转换: archived → active 返回 400 ST-002', async ({ page }) => {
    await loginAs(page, 'admin');

    const response = await page.request.post('/api/v1/projects/proj-archived-1/transition', {
      data: { to_status: 'active' },
    });

    await expectIllegalTransitionRejected(response, 'ST-002');
  });
});

// ============================================================
// CP-C1-005: Phase 1 规则测试
// ============================================================
test.describe('CP-C1-005: Phase 1 不阻断规则', () => {
  test('超支项目高亮但可继续操作', async ({ page }) => {
    await loginAs(page, 'ceo');

    await page.route('/api/v1/projects*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockProjectData.over_budget),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="project-table"]');

    // 1. 验证超支高亮
    const row = page.locator('[data-testid="row-proj-over-1"]');
    await expect(row).toHaveClass(/bg-red|bg-amber|warning/);

    // 2. 验证消耗列显示负值高亮
    const spentCell = page.locator('[data-testid="spent-cell-proj-over-1"]');
    await expect(spentCell).toHaveClass(/text-red|negative/);

    // 3. 验证仍可操作 (Phase 1 不阻断)
    const pauseBtn = page.locator('[data-testid="pause-btn-proj-over-1"]');
    await expect(pauseBtn).toBeEnabled();
  });

  test('项目预警但可正常跳转详情', async ({ page }) => {
    await loginAs(page, 'project_owner');

    await page.route('/api/v1/projects*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{
            id: 'proj-warn-1',
            name: '预警项目',
            status: 'active',
            budget: 100000,
            spent: 95000,
            is_warning: true,
          }],
          total: 1,
        }),
      });
    });

    await page.goto(PAGE_PATH);
    await page.waitForSelector('[data-testid="project-table"]');

    // 验证预警图标
    const warningIcon = page.locator('[data-testid="warning-icon-proj-warn-1"]');
    await expect(warningIcon).toBeVisible();

    // 验证可点击跳转详情
    await page.click('[data-testid="row-proj-warn-1"]');
    await expect(page).toHaveURL(/\/projects\/proj-warn-1/);
  });
});

// ============================================================
// CP-C1-006: 创建/编辑项目表单测试
// ============================================================
test.describe('CP-C1-006: 项目表单', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'ceo');
    await page.route('/api/v1/projects*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockProjectData.success),
      });
    });
    await page.goto(PAGE_PATH);
  });

  test('点击新建按钮打开表单', async ({ page }) => {
    await page.click('[data-testid="create-project-btn"]');

    await expect(page.locator('[data-testid="project-form-modal"]')).toBeVisible();
    await expect(page.locator('[data-testid="project-form-title"]')).toHaveText('新建项目');
  });

  test('表单必填字段验证', async ({ page }) => {
    await page.click('[data-testid="create-project-btn"]');

    // 不填写直接提交
    await page.click('[data-testid="submit-project-btn"]');

    // 应该显示错误提示
    await expect(page.locator('[data-testid="error-name"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-owner"]')).toBeVisible();
  });

  test('成功创建项目', async ({ page }) => {
    await page.route('/api/v1/projects', (route) => {
      if (route.request().method() === 'POST') {
        route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({ id: 'proj-new-1', name: '新项目', status: 'planning' }),
        });
      } else {
        route.continue();
      }
    });

    await page.click('[data-testid="create-project-btn"]');

    await page.fill('[data-testid="input-name"]', '新项目');
    await page.selectOption('[data-testid="select-owner"]', 'owner-1');
    await page.fill('[data-testid="input-budget"]', '100000');

    await page.click('[data-testid="submit-project-btn"]');

    await expectSuccessToast(page, '项目创建成功');
  });
});
