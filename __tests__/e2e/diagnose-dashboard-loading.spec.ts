/**
 * 仪表盘加载失败诊断测试
 * 
 * 使用 admin 账号登录，检查仪表盘加载问题
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const FRONTEND_URL = process.env.NEXT_PUBLIC_FRONTEND_URL || 'http://localhost:3000';

// Admin 账号信息
const ADMIN_EMAIL = 'admin@test.local';
const ADMIN_PASSWORD = 'admin123456';

test.describe('仪表盘加载失败诊断', () => {
  test('使用 admin 账号登录并访问仪表盘', async ({ page }) => {
    // 监听所有网络请求
    const apiRequests: Array<{ url: string; status: number; response?: any }> = [];
    const apiErrors: Array<{ url: string; error: string }> = [];

    page.on('response', async (response) => {
      const url = response.url();
      if (url.includes('/api/v1/dashboards')) {
        const status = response.status();
        let responseBody = null;
        try {
          responseBody = await response.json();
        } catch {
          // 忽略 JSON 解析错误
        }
        apiRequests.push({ url, status, response: responseBody });
        
        if (status >= 400) {
          apiErrors.push({
            url,
            error: responseBody?.message || responseBody?.error?.message || `HTTP ${status}`,
          });
        }
      }
    });

    // 监听控制台错误
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // 监听页面错误
    const pageErrors: string[] = [];
    page.on('pageerror', (error) => {
      pageErrors.push(error.message);
    });

    console.log('📝 Step 1: 访问登录页面');
    await page.goto(`${FRONTEND_URL}/login`);
    await page.waitForLoadState('networkidle');

    // 检查登录页面是否正常加载
    const loginForm = page.locator('form, [data-testid="login-form"]').first();
    await expect(loginForm).toBeVisible({ timeout: 5000 });

    console.log('📝 Step 2: 输入 admin 账号信息');
    // 查找邮箱输入框（支持多种选择器）
    const emailInput = page.locator('input[type="email"], input[name="email"], [data-testid="email-input"]').first();
    await emailInput.fill(ADMIN_EMAIL);

    // 查找密码输入框
    const passwordInput = page.locator('input[type="password"], input[name="password"], [data-testid="password-input"]').first();
    await passwordInput.fill(ADMIN_PASSWORD);

    console.log('📝 Step 3: 点击登录按钮');
    const loginButton = page.locator('button[type="submit"], button:has-text("登录"), [data-testid="login-button"]').first();
    await loginButton.click();

    // 等待登录完成（重定向或页面变化）
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // 检查是否登录成功
    const currentUrl = page.url();
    console.log(`📍 当前 URL: ${currentUrl}`);

    // 检查 localStorage 中的 token
    const token = await page.evaluate(() => localStorage.getItem('auth-token'));
    console.log(`🔑 Token: ${token ? token.substring(0, 20) + '...' : '未找到'}`);

    if (!token) {
      console.error('❌ 登录失败：未找到 auth-token');
      // 检查是否有错误消息
      const errorMessage = await page.locator('.error, [role="alert"], .text-red-500').first().textContent().catch(() => null);
      if (errorMessage) {
        console.error(`❌ 错误信息: ${errorMessage}`);
      }
      test.fail('登录失败：未找到 auth-token');
    }

    // 检查用户信息
    const userInfo = await page.evaluate(() => {
      const userStr = localStorage.getItem('auth-user');
      return userStr ? JSON.parse(userStr) : null;
    });
    console.log(`👤 用户信息:`, userInfo);

    if (userInfo) {
      console.log(`   角色: ${userInfo.role}`);
      console.log(`   邮箱: ${userInfo.email}`);
    }

    console.log('📝 Step 4: 访问仪表盘页面');
    await page.goto(`${FRONTEND_URL}/dashboard`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000); // 等待 API 请求完成

    // 检查页面内容
    const pageContent = await page.content();
    const hasError = pageContent.includes('加载仪表盘失败') || 
                     pageContent.includes('Build Error') ||
                     pageContent.includes('TECH_TO_BUSINESS');

    console.log('\n📊 诊断结果:');
    console.log('='.repeat(60));

    // 1. 检查 API 请求
    console.log('\n1. API 请求状态:');
    if (apiRequests.length === 0) {
      console.log('   ⚠️  未发现 API 请求');
    } else {
      apiRequests.forEach((req, index) => {
        const statusIcon = req.status >= 400 ? '❌' : '✅';
        console.log(`   ${statusIcon} [${req.status}] ${req.url}`);
        if (req.status >= 400 && req.response) {
          console.log(`      错误: ${JSON.stringify(req.response, null, 2)}`);
        }
      });
    }

    // 2. 检查 API 错误
    if (apiErrors.length > 0) {
      console.log('\n2. API 错误详情:');
      apiErrors.forEach((err, index) => {
        console.log(`   ${index + 1}. ${err.url}`);
        console.log(`      错误: ${err.error}`);
      });
    }

    // 3. 检查控制台错误
    if (consoleErrors.length > 0) {
      console.log('\n3. 控制台错误:');
      consoleErrors.forEach((err, index) => {
        console.log(`   ${index + 1}. ${err}`);
      });
    }

    // 4. 检查页面错误
    if (pageErrors.length > 0) {
      console.log('\n4. 页面错误:');
      pageErrors.forEach((err, index) => {
        console.log(`   ${index + 1}. ${err}`);
      });
    }

    // 5. 检查页面内容
    console.log('\n5. 页面状态:');
    if (hasError) {
      console.log('   ❌ 页面包含错误信息');
      // 尝试查找错误消息
      const errorElement = page.locator('text=/加载仪表盘失败|Build Error|权限|仅限/').first();
      const errorText = await errorElement.textContent().catch(() => null);
      if (errorText) {
        console.log(`   错误文本: ${errorText}`);
      }
    } else {
      console.log('   ✅ 页面未发现明显错误');
    }

    // 6. 检查权限相关
    console.log('\n6. 权限检查:');
    const permissionError = apiErrors.find(err => 
      err.error.includes('权限') || 
      err.error.includes('仅限') ||
      err.error.includes('PERMISSION') ||
      err.error.includes('403')
    );
    if (permissionError) {
      console.log('   ❌ 发现权限错误');
      console.log(`   错误: ${permissionError.error}`);
    } else {
      console.log('   ✅ 未发现权限错误');
    }

    // 7. 检查认证相关
    console.log('\n7. 认证检查:');
    const authError = apiErrors.find(err => 
      err.error.includes('认证') || 
      err.error.includes('AUTH') ||
      err.error.includes('401') ||
      err.error.includes('未提供')
    );
    if (authError) {
      console.log('   ❌ 发现认证错误');
      console.log(`   错误: ${authError.error}`);
    } else {
      console.log('   ✅ 未发现认证错误');
    }

    console.log('\n' + '='.repeat(60));

    // 生成诊断报告
    const diagnosis = {
      loginSuccess: !!token,
      userRole: userInfo?.role,
      apiRequests: apiRequests.length,
      apiErrors: apiErrors.length,
      consoleErrors: consoleErrors.length,
      pageErrors: pageErrors.length,
      hasPageError: hasError,
    };

    console.log('\n📋 诊断摘要:');
    console.log(JSON.stringify(diagnosis, null, 2));

    // 如果发现错误，输出详细信息
    if (apiErrors.length > 0 || consoleErrors.length > 0 || pageErrors.length > 0 || hasError) {
      console.log('\n⚠️  发现问题，请查看上述详细信息');
      
      // 保存截图
      await page.screenshot({ path: 'dashboard-diagnosis-screenshot.png', fullPage: true });
      console.log('📸 已保存截图: dashboard-diagnosis-screenshot.png');
    } else {
      console.log('\n✅ 未发现明显问题');
    }
  });

  test('直接测试 CEO Dashboard API', async ({ page }) => {
    console.log('📝 测试 CEO Dashboard API 端点');

    // 先登录获取 token
    await page.goto(`${FRONTEND_URL}/login`);
    await page.waitForLoadState('networkidle');

    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[name="password"]').first();
    const loginButton = page.locator('button[type="submit"], button:has-text("登录")').first();

    await emailInput.fill(ADMIN_EMAIL);
    await passwordInput.fill(ADMIN_PASSWORD);
    await loginButton.click();

    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // 获取 token
    const token = await page.evaluate(() => localStorage.getItem('auth-token'));
    
    if (!token) {
      test.fail('无法获取认证令牌');
    }

    console.log(`🔑 Token: ${token.substring(0, 20)}...`);

    // 直接调用 API
    const response = await page.evaluate(async (token) => {
      const res = await fetch(`${BASE_URL}/api/v1/dashboards/ceo/v3/overview`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      return {
        status: res.status,
        statusText: res.statusText,
        body: await res.json(),
      };
    }, token);

    console.log('\n📊 API 响应:');
    console.log(`   状态码: ${response.status}`);
    console.log(`   状态文本: ${response.statusText}`);
    console.log(`   响应体:`, JSON.stringify(response.body, null, 2));

    if (response.status === 200) {
      console.log('✅ API 调用成功');
      expect(response.body.success).toBe(true);
    } else {
      console.log(`❌ API 调用失败: ${response.status}`);
      console.log(`   错误信息: ${response.body.message || response.body.error?.message || '未知错误'}`);
    }
  });
});

