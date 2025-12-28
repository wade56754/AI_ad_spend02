/**
 * 认证辅助函数
 *
 * 基于: AI_TEST_GUIDE_v2.1.md §3.3
 */

import { Page, expect } from '@playwright/test';
import { TEST_ACCOUNTS, TestRole } from '../fixtures/test-accounts';

/**
 * 以指定角色登录
 */
export async function loginAs(page: Page, role: TestRole): Promise<void> {
  const account = TEST_ACCOUNTS[role];

  await page.goto('/login');

  // 等待登录页面加载
  await page.waitForSelector('[data-testid="email-input"]');

  // 填写登录表单
  await page.fill('[data-testid="email-input"]', account.email);
  await page.fill('[data-testid="password-input"]', account.password);
  await page.click('[data-testid="login-button"]');

  // 等待登录完成（离开登录页面）
  await page.waitForURL(/^(?!.*\/login).*$/);
}

/**
 * 退出登录
 */
export async function logout(page: Page): Promise<void> {
  await page.click('[data-testid="user-menu"]');
  await page.click('[data-testid="logout-button"]');
  await page.waitForURL('/login');
}

/**
 * 检查当前是否已登录
 */
export async function isLoggedIn(page: Page): Promise<boolean> {
  const url = page.url();
  return !url.includes('/login');
}

/**
 * 确保已登录指定角色
 * 如果已登录其他角色，先退出再登录
 */
export async function ensureLoggedInAs(page: Page, role: TestRole): Promise<void> {
  const currentUrl = page.url();

  if (currentUrl.includes('/login')) {
    await loginAs(page, role);
  } else {
    // 检查当前角色是否匹配（通过 API 或 localStorage）
    // 简化处理：直接退出再登录
    await logout(page);
    await loginAs(page, role);
  }
}

/**
 * 验证用户被拒绝访问（重定向到 unauthorized 页面）
 */
export async function expectAccessDenied(page: Page): Promise<void> {
  await expect(page).toHaveURL(/\/(unauthorized|403|login)/);
}

/**
 * 验证用户可以访问页面
 */
export async function expectAccessAllowed(page: Page, expectedPath: string): Promise<void> {
  await expect(page).toHaveURL(new RegExp(expectedPath));
}
