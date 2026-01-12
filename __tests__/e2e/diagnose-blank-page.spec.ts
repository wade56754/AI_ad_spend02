/**
 * 页面空白问题诊断测试
 */

import { test, expect } from '@playwright/test';

const FRONTEND_URL = process.env.NEXT_PUBLIC_FRONTEND_URL || 'http://localhost:3000';
const ADMIN_EMAIL = 'admin@test.local';
const ADMIN_PASSWORD = 'admin123456';

test.describe('页面空白问题诊断', () => {
  test('检查仪表盘页面加载状态', async ({ page }) => {
    // 监听所有网络请求
    const requests: Array<{ url: string; status: number; method: string }> = [];
    const failedRequests: Array<{ url: string; status: number; error: string }> = [];

    page.on('response', (response) => {
      const url = response.url();
      const status = response.status();
      const method = response.request().method();
      
      requests.push({ url, status, method });
      
      if (status >= 400) {
        failedRequests.push({
          url,
          status,
          error: `${status} ${response.statusText()}`,
        });
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

    console.log('📝 Step 2: 登录');
    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[name="password"]').first();
    const loginButton = page.locator('button[type="submit"], button:has-text("登录")').first();

    await emailInput.fill(ADMIN_EMAIL);
    await passwordInput.fill(ADMIN_PASSWORD);
    await loginButton.click();

    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    const token = await page.evaluate(() => localStorage.getItem('auth-token'));
    console.log(`🔑 Token: ${token ? '已获取' : '未获取'}`);

    console.log('📝 Step 3: 访问仪表盘页面');
    await page.goto(`${FRONTEND_URL}/dashboard`);
    
    // 等待页面加载
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000); // 等待更长时间，确保所有内容加载

    // 检查页面内容
    const pageContent = await page.content();
    const bodyText = await page.locator('body').textContent().catch(() => '');
    const hasContent = bodyText && bodyText.trim().length > 0;
    const hasError = pageContent.includes('错误') || 
                     pageContent.includes('Error') ||
                     pageContent.includes('失败') ||
                     pageContent.includes('空白');

    console.log('\n📊 诊断结果:');
    console.log('='.repeat(60));

    // 1. 检查页面内容
    console.log('\n1. 页面内容检查:');
    console.log(`   页面 URL: ${page.url()}`);
    console.log(`   页面标题: ${await page.title()}`);
    console.log(`   页面是否有内容: ${hasContent ? '✅ 是' : '❌ 否'}`);
    console.log(`   页面文本长度: ${bodyText?.length || 0} 字符`);
    
    if (!hasContent) {
      console.log('   ⚠️  页面内容为空！');
    }

    // 2. 检查页面元素
    console.log('\n2. 页面元素检查:');
    const mainContent = page.locator('main, [role="main"], .main-content, #main').first();
    const hasMain = await mainContent.isVisible().catch(() => false);
    console.log(`   Main 元素可见: ${hasMain ? '✅' : '❌'}`);

    const dashboard = page.locator('[data-testid="dashboard"], .dashboard, #dashboard').first();
    const hasDashboard = await dashboard.isVisible().catch(() => false);
    console.log(`   Dashboard 元素可见: ${hasDashboard ? '✅' : '❌'}`);

    // 3. 检查网络请求
    console.log('\n3. 网络请求状态:');
    console.log(`   总请求数: ${requests.length}`);
    console.log(`   失败请求数: ${failedRequests.length}`);
    
    if (failedRequests.length > 0) {
      console.log('   失败的请求:');
      failedRequests.forEach((req, index) => {
        console.log(`     ${index + 1}. [${req.status}] ${req.url}`);
      });
    }

    // 4. 检查控制台错误
    if (consoleErrors.length > 0) {
      console.log('\n4. 控制台错误:');
      consoleErrors.forEach((err, index) => {
        console.log(`   ${index + 1}. ${err}`);
      });
    }

    // 5. 检查页面错误
    if (pageErrors.length > 0) {
      console.log('\n5. 页面错误:');
      pageErrors.forEach((err, index) => {
        console.log(`   ${index + 1}. ${err}`);
      });
    }

    // 6. 检查加载状态
    console.log('\n6. 加载状态检查:');
    const loadingElements = page.locator('.loading, [data-loading], .spinner, .skeleton').first();
    const isLoading = await loadingElements.isVisible().catch(() => false);
    console.log(`   是否仍在加载: ${isLoading ? '⚠️  是' : '✅ 否'}`);

    // 7. 检查 React 错误边界
    console.log('\n7. React 错误边界检查:');
    const errorBoundary = page.locator('.error-boundary, [data-error-boundary]').first();
    const hasErrorBoundary = await errorBoundary.isVisible().catch(() => false);
    if (hasErrorBoundary) {
      const errorText = await errorBoundary.textContent().catch(() => '');
      console.log(`   ⚠️  发现错误边界: ${errorText}`);
    } else {
      console.log('   ✅ 未发现错误边界');
    }

    // 8. 截图保存
    await page.screenshot({ path: 'blank-page-diagnosis.png', fullPage: true });
    console.log('\n📸 已保存截图: blank-page-diagnosis.png');

    console.log('\n' + '='.repeat(60));

    // 生成诊断报告
    const diagnosis = {
      url: page.url(),
      hasContent,
      contentLength: bodyText?.length || 0,
      hasMainElement: hasMain,
      hasDashboardElement: hasDashboard,
      totalRequests: requests.length,
      failedRequests: failedRequests.length,
      consoleErrors: consoleErrors.length,
      pageErrors: pageErrors.length,
      isLoading,
      hasErrorBoundary,
    };

    console.log('\n📋 诊断摘要:');
    console.log(JSON.stringify(diagnosis, null, 2));

    // 如果页面空白，输出详细信息
    if (!hasContent || bodyText?.trim().length === 0) {
      console.log('\n⚠️  页面空白问题诊断:');
      console.log('   可能的原因:');
      console.log('   1. 前端构建错误');
      console.log('   2. React 组件渲染失败');
      console.log('   3. API 请求全部失败');
      console.log('   4. 路由配置错误');
      console.log('   5. 权限检查导致重定向');
      
      // 检查是否有重定向
      const finalUrl = page.url();
      if (finalUrl.includes('/login')) {
        console.log('\n   ⚠️  页面被重定向到登录页，可能是权限问题');
      }
    }
  });

  test('检查前端构建状态', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/dashboard`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // 检查是否有构建错误
    const pageContent = await page.content();
    const hasBuildError = pageContent.includes('Build Error') || 
                          pageContent.includes('Module not found') ||
                          pageContent.includes('Cannot find module');

    if (hasBuildError) {
      console.log('❌ 发现构建错误');
      const errorText = await page.locator('body').textContent();
      console.log('错误内容:', errorText);
    } else {
      console.log('✅ 未发现构建错误');
    }
  });
});

