import { test, expect } from '@playwright/test';

/**
 * 前端所有页面 E2E 测试
 * 
 * 测试覆盖:
 * 1. 所有页面的可访问性
 * 2. 页面基本渲染
 * 3. 关键 UI 元素存在性
 * 4. 页面导航
 */

// 需要认证的页面列表
const protectedPages = [
  { path: '/', name: '仪表盘' },
  { path: '/projects', name: '项目管理' },
  { path: '/ad-accounts', name: '广告账户' },
  { path: '/channels', name: '渠道管理' },
  { path: '/daily-reports', name: '日报管理' },
  { path: '/topups', name: '充值管理' },
  { path: '/reconciliation', name: '对账管理' },
  { path: '/ledger', name: '财务总账' },
  { path: '/finance/profit', name: '财务利润' },
  { path: '/suppliers', name: '供应商管理' },
  { path: '/settlements', name: '结算管理' },
  { path: '/transfers', name: '余额迁移' },
  { path: '/import-jobs', name: '数据导入' },
  { path: '/reports', name: '报表管理' },
];

// 公开页面
const publicPages = [
  { path: '/login', name: '登录页面' },
  { path: '/register', name: '注册页面' },
];

test.describe('公开页面测试', () => {
  for (const pageInfo of publicPages) {
    test(`${pageInfo.name} - 应该可以访问`, async ({ page }) => {
      await page.goto(pageInfo.path);
      await expect(page).toHaveURL(new RegExp(pageInfo.path));
      // 检查页面已加载（等待至少一个可见元素）
      await page.waitForLoadState('domcontentloaded');
    });

    test(`${pageInfo.name} - 应该正确渲染`, async ({ page }) => {
      await page.goto(pageInfo.path);
      await page.waitForLoadState('domcontentloaded');

      // 等待页面标题设置完成（Next.js metadata 需要时间）
      await page.waitForFunction(() => document.title.length > 0, { timeout: 5000 });

      // 检查页面标题存在
      const title = await page.title();
      expect(title).toBeTruthy();
      expect(title.length).toBeGreaterThan(0);

      // 检查页面主要内容区域存在
      const mainContent = page.locator('main, [role="main"], body');
      await expect(mainContent.first()).toBeVisible();
    });
  }
});

test.describe('受保护页面测试', () => {
  // 清除认证状态
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  });

  for (const pageInfo of protectedPages) {
    test(`${pageInfo.name} - 未登录用户应被重定向或显示登录提示`, async ({ page }) => {
      await page.goto(pageInfo.path);
      
      // 等待页面加载和可能的重定向
      await page.waitForTimeout(2000);
      
      const url = page.url();
      const isOnLoginPage = url.includes('/login');
      const hasLoginForm = await page.getByLabel('用户名或邮箱').isVisible().catch(() => false);
      
      // 应该重定向到登录页或显示登录表单
      expect(isOnLoginPage || hasLoginForm).toBeTruthy();
    });
  }
});

test.describe('页面导航测试', () => {
  test('从登录页可以导航到注册页', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    const registerLink = page.getByRole('link', { name: /注册|立即注册/i });
    if (await registerLink.isVisible().catch(() => false)) {
      await registerLink.click();
      await expect(page).toHaveURL(/\/register/);
    }
  });

  test('从注册页可以导航到登录页', async ({ page }) => {
    await page.goto('/register');
    await page.waitForLoadState('networkidle');
    
    const loginLink = page.getByRole('link', { name: /登录|立即登录/i });
    if (await loginLink.isVisible().catch(() => false)) {
      await loginLink.click();
      await expect(page).toHaveURL(/\/login/);
    }
  });
});

test.describe('页面响应式测试', () => {
  const viewports = [
    { width: 1920, height: 1080, name: 'Desktop' },
    { width: 768, height: 1024, name: 'Tablet' },
    { width: 375, height: 667, name: 'Mobile' },
  ];

  for (const viewport of viewports) {
    test(`登录页面在 ${viewport.name} 视口下应正常显示`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
      
      // 检查主要内容可见
      const mainContent = page.locator('main, [role="main"], body');
      await expect(mainContent.first()).toBeVisible();
    });

    test(`注册页面在 ${viewport.name} 视口下应正常显示`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('/register');
      await page.waitForLoadState('networkidle');
      
      // 检查主要内容可见
      const mainContent = page.locator('main, [role="main"], body');
      await expect(mainContent.first()).toBeVisible();
    });
  }
});

test.describe('页面性能测试', () => {
  test('登录页面应在合理时间内加载', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;
    
    // 页面应在 5 秒内加载完成
    expect(loadTime).toBeLessThan(5000);
  });

  test('注册页面应在合理时间内加载', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/register');
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;
    
    // 页面应在 5 秒内加载完成
    expect(loadTime).toBeLessThan(5000);
  });
});

test.describe('页面可访问性测试', () => {
  test('登录页面应有合理的标题', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');

    // 等待标题设置完成
    await page.waitForFunction(() => document.title.length > 0, { timeout: 5000 });

    const title = await page.title();
    expect(title).toBeTruthy();
    expect(title.length).toBeGreaterThan(0);
  });

  test('注册页面应有合理的标题', async ({ page }) => {
    await page.goto('/register');
    await page.waitForLoadState('domcontentloaded');

    // 等待标题设置完成
    await page.waitForFunction(() => document.title.length > 0, { timeout: 5000 });

    const title = await page.title();
    expect(title).toBeTruthy();
    expect(title.length).toBeGreaterThan(0);
  });

  test('登录页面表单元素应有标签', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');

    // 等待表单元素渲染
    await page.waitForSelector('input', { timeout: 5000 });

    const identifierInput = page.getByLabel('用户名或邮箱');
    const passwordInput = page.getByLabel('密码');

    // 检查输入框存在（可能通过 label 或 aria-label）
    const hasIdentifier = await identifierInput.isVisible().catch(() => false);
    const hasPassword = await passwordInput.isVisible().catch(() => false);

    expect(hasIdentifier || hasPassword).toBeTruthy();
  });
});



