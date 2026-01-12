/**
 * 页面空白问题诊断测试 V2
 * 直接访问根路径并检查
 */

import { test, expect } from '@playwright/test';

const FRONTEND_URL = process.env.NEXT_PUBLIC_FRONTEND_URL || 'http://localhost:3000';
const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const ADMIN_EMAIL = 'admin@test.local';
const ADMIN_PASSWORD = 'admin123456';

test.describe('页面空白问题诊断 V2', () => {
  test('完整诊断流程', async ({ page }) => {
    // 监听所有网络请求和响应
    const apiCalls: Array<{ url: string; status: number; method: string; response?: any }> = [];
    const consoleMessages: Array<{ type: string; text: string }> = [];
    const pageErrors: string[] = [];

    page.on('response', async (response) => {
      const url = response.url();
      if (url.includes('/api/') || url.includes(BASE_URL)) {
        const status = response.status();
        const method = response.request().method();
        let responseBody = null;
        try {
          responseBody = await response.json();
        } catch {
          // 忽略 JSON 解析错误
        }
        apiCalls.push({ url, status, method, response: responseBody });
      }
    });

    page.on('console', (msg) => {
      consoleMessages.push({ type: msg.type(), text: msg.text() });
    });

    page.on('pageerror', (error) => {
      pageErrors.push(error.message);
    });

    console.log('📝 Step 1: 直接访问根路径');
    await page.goto(`${FRONTEND_URL}/`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    const currentUrl = page.url();
    console.log(`📍 当前 URL: ${currentUrl}`);

    // 检查是否被重定向到登录页
    if (currentUrl.includes('/login')) {
      console.log('⚠️  页面被重定向到登录页');
      
      console.log('📝 Step 2: 执行登录');
      const emailInput = page.locator('input[type="email"], input[name="email"], [data-testid="email-input"]').first();
      const passwordInput = page.locator('input[type="password"], input[name="password"], [data-testid="password-input"]').first();
      const loginButton = page.locator('button[type="submit"], button:has-text("登录"), [data-testid="login-button"]').first();

      // 等待输入框出现
      await emailInput.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {
        console.log('❌ 无法找到登录输入框');
      });

      if (await emailInput.isVisible().catch(() => false)) {
        await emailInput.fill(ADMIN_EMAIL);
        await passwordInput.fill(ADMIN_PASSWORD);
        await loginButton.click();

        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
      }
    }

    // 再次检查 URL
    const finalUrl = page.url();
    console.log(`📍 最终 URL: ${finalUrl}`);

    // 检查 localStorage
    const token = await page.evaluate(() => localStorage.getItem('auth-token'));
    const userInfo = await page.evaluate(() => {
      const userStr = localStorage.getItem('auth-user');
      return userStr ? JSON.parse(userStr) : null;
    });

    console.log(`🔑 Token: ${token ? '已获取' : '未获取'}`);
    if (userInfo) {
      console.log(`👤 用户: ${userInfo.email} (${userInfo.role})`);
    }

    // 如果还在登录页，尝试直接访问仪表盘
    if (finalUrl.includes('/login')) {
      console.log('📝 Step 3: 直接访问仪表盘路径');
      await page.goto(`${FRONTEND_URL}/`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(5000);
    }

    // 检查页面内容
    const bodyText = await page.locator('body').textContent().catch(() => '');
    const pageContent = await page.content();
    const hasContent = bodyText && bodyText.trim().length > 50; // 至少 50 个字符才算有内容

    console.log('\n📊 诊断结果:');
    console.log('='.repeat(60));

    // 1. 页面状态
    console.log('\n1. 页面状态:');
    console.log(`   URL: ${page.url()}`);
    console.log(`   标题: ${await page.title()}`);
    console.log(`   内容长度: ${bodyText?.length || 0} 字符`);
    console.log(`   是否有内容: ${hasContent ? '✅' : '❌'}`);

    // 2. 检查关键元素
    console.log('\n2. 关键元素检查:');
    const checks = [
      { name: 'AppLayout', selector: '[data-testid="app-layout"], .app-layout, main' },
      { name: 'Sidebar', selector: '[data-testid="sidebar"], .sidebar, nav' },
      { name: 'Dashboard Content', selector: '[data-testid="dashboard"], .dashboard, .dashboard-content' },
      { name: 'Loading Spinner', selector: '.loading, .spinner, [data-loading]' },
      { name: 'Error Message', selector: '.error, [role="alert"], .text-red-500' },
    ];

    for (const check of checks) {
      const element = page.locator(check.selector).first();
      const isVisible = await element.isVisible().catch(() => false);
      const text = isVisible ? await element.textContent().catch(() => '') : '';
      console.log(`   ${check.name}: ${isVisible ? '✅' : '❌'} ${text ? `(${text.substring(0, 50)}...)` : ''}`);
    }

    // 3. API 调用
    console.log('\n3. API 调用状态:');
    console.log(`   总 API 调用数: ${apiCalls.length}`);
    
    const failedCalls = apiCalls.filter(call => call.status >= 400);
    if (failedCalls.length > 0) {
      console.log(`   ❌ 失败调用数: ${failedCalls.length}`);
      failedCalls.forEach((call, index) => {
        console.log(`      ${index + 1}. [${call.status}] ${call.method} ${call.url}`);
        if (call.response) {
          console.log(`         错误: ${JSON.stringify(call.response.error || call.response, null, 2)}`);
        }
      });
    } else {
      console.log('   ✅ 所有 API 调用成功');
    }

    // 4. 控制台消息
    const errors = consoleMessages.filter(msg => msg.type === 'error');
    const warnings = consoleMessages.filter(msg => msg.type === 'warning');
    
    if (errors.length > 0) {
      console.log('\n4. 控制台错误:');
      errors.forEach((err, index) => {
        console.log(`   ${index + 1}. ${err.text}`);
      });
    }

    if (warnings.length > 0) {
      console.log('\n5. 控制台警告:');
      warnings.slice(0, 5).forEach((warn, index) => {
        console.log(`   ${index + 1}. ${warn.text}`);
      });
    }

    // 5. 页面错误
    if (pageErrors.length > 0) {
      console.log('\n6. 页面错误:');
      pageErrors.forEach((err, index) => {
        console.log(`   ${index + 1}. ${err}`);
      });
    }

    // 6. 检查是否有构建错误
    const hasBuildError = pageContent.includes('Build Error') || 
                          pageContent.includes('Module not found') ||
                          pageContent.includes('Cannot find module');
    
    if (hasBuildError) {
      console.log('\n7. 构建错误:');
      console.log('   ❌ 发现构建错误');
      const errorMatch = pageContent.match(/Build Error[\s\S]*?<\/div>/);
      if (errorMatch) {
        console.log(`   错误内容: ${errorMatch[0].substring(0, 200)}...`);
      }
    }

    // 7. 截图
    await page.screenshot({ path: 'blank-page-diagnosis-v2.png', fullPage: true });
    console.log('\n📸 已保存截图: blank-page-diagnosis-v2.png');

    console.log('\n' + '='.repeat(60));

    // 生成诊断报告
    const diagnosis = {
      url: page.url(),
      hasContent,
      contentLength: bodyText?.length || 0,
      tokenExists: !!token,
      userExists: !!userInfo,
      apiCallsCount: apiCalls.length,
      failedApiCalls: failedCalls.length,
      consoleErrors: errors.length,
      pageErrors: pageErrors.length,
      hasBuildError,
    };

    console.log('\n📋 诊断摘要:');
    console.log(JSON.stringify(diagnosis, null, 2));

    // 如果页面空白，提供建议
    if (!hasContent || bodyText?.trim().length < 50) {
      console.log('\n⚠️  页面空白问题分析:');
      console.log('   可能的原因:');
      
      if (!token) {
        console.log('   1. ❌ 未登录或 Token 丢失');
      }
      
      if (failedCalls.length > 0) {
        console.log('   2. ❌ API 请求失败');
      }
      
      if (hasBuildError) {
        console.log('   3. ❌ 前端构建错误');
      }
      
      if (pageErrors.length > 0) {
        console.log('   4. ❌ JavaScript 运行时错误');
      }
      
      if (errors.length > 0) {
        console.log('   5. ❌ React 组件渲染错误');
      }
    }
  });
});

