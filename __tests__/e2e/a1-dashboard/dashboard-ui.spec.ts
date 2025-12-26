/**
 * Dashboard UI 测试 - 验证 data-testid 属性
 *
 * 不需要登录，直接测试 UI 元素
 * 注：完整功能测试见 dashboard.spec.ts（需要后端服务）
 */

import { test, expect } from '@playwright/test';

const DASHBOARD_PATH = '/';

test.describe('Dashboard UI data-testid 验证', () => {
  test.beforeEach(async ({ page }) => {
    // 直接访问首页，可能会被重定向到登录页
    // 或者如果有 mock 数据，可以看到仪表盘
    await page.goto(DASHBOARD_PATH);
  });

  test('页面加载不报错', async ({ page }) => {
    // 等待页面加载完成
    await page.waitForLoadState('domcontentloaded');

    // 检查页面是否正常（可能是登录页或仪表盘）
    const pageTitle = await page.title();
    expect(pageTitle).toBeTruthy();
  });

  test('如果在登录页，验证登录表单 testId', async ({ page }) => {
    const loginButton = page.locator('[data-testid="login-button"]');
    const isLoginPage = await loginButton.isVisible().catch(() => false);

    if (isLoginPage) {
      // 验证登录页面的 data-testid
      await expect(page.locator('[data-testid="email-input"]')).toBeVisible();
      await expect(page.locator('[data-testid="password-input"]')).toBeVisible();
      await expect(loginButton).toBeVisible();
    } else {
      // 如果不在登录页，跳过此测试
      test.skip();
    }
  });

  test('导航侧边栏 testId 可用', async ({ page }) => {
    // 尝试查找侧边栏导航
    const navDashboard = page.locator('[data-testid="nav-dashboard"]');
    const isVisible = await navDashboard.isVisible().catch(() => false);

    if (isVisible) {
      await expect(navDashboard).toBeVisible();
      await expect(page.locator('[data-testid="nav-projects"]')).toBeVisible();
      await expect(page.locator('[data-testid="nav-ad-accounts"]')).toBeVisible();
    } else {
      // 可能被重定向到登录页，跳过
      test.skip();
    }
  });
});
