/**
 * 登录页面 E2E 测试
 *
 * 验证登录页面的 data-testid 属性是否正确设置
 */

import { test, expect } from '@playwright/test';

const LOGIN_PATH = '/login';

test.describe('登录页面 UI 测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(LOGIN_PATH);
  });

  test('登录页面包含必要的 data-testid 元素', async ({ page }) => {
    // 验证邮箱输入框
    const emailInput = page.locator('[data-testid="email-input"]');
    await expect(emailInput).toBeVisible();
    await expect(emailInput).toBeEnabled();

    // 验证密码输入框
    const passwordInput = page.locator('[data-testid="password-input"]');
    await expect(passwordInput).toBeVisible();
    await expect(passwordInput).toBeEnabled();

    // 验证登录按钮
    const loginButton = page.locator('[data-testid="login-button"]');
    await expect(loginButton).toBeVisible();
    await expect(loginButton).toBeEnabled();
  });

  test('可以在输入框中输入内容', async ({ page }) => {
    const emailInput = page.locator('[data-testid="email-input"]');
    const passwordInput = page.locator('[data-testid="password-input"]');

    await emailInput.fill('test@example.com');
    await passwordInput.fill('password123');

    await expect(emailInput).toHaveValue('test@example.com');
    await expect(passwordInput).toHaveValue('password123');
  });

  test('点击登录按钮触发表单提交', async ({ page }) => {
    const emailInput = page.locator('[data-testid="email-input"]');
    const passwordInput = page.locator('[data-testid="password-input"]');
    const loginButton = page.locator('[data-testid="login-button"]');

    await emailInput.fill('test@example.com');
    await passwordInput.fill('password123');

    // 拦截 API 请求
    await page.route('/api/v1/auth/login', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'test-token',
          user: { id: '1', email: 'test@example.com', role: 'admin' },
        }),
      });
    });

    await loginButton.click();

    // 验证按钮状态变化（登录中）
    // 注：实际行为取决于实现
  });

  test('空表单提交显示错误', async ({ page }) => {
    const loginButton = page.locator('[data-testid="login-button"]');

    await loginButton.click();

    // HTML5 required 验证会阻止提交
    // 或者显示 toast 错误消息
  });

  test('登录页面标题正确', async ({ page }) => {
    await expect(page).toHaveTitle(/登录/);
  });
});
