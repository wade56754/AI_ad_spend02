const puppeteer = require('puppeteer');

(async () => {
  console.log('启动浏览器...');
  const browser = await puppeteer.launch({
    headless: false,
    devtools: true,
  });

  const page = await browser.newPage();

  // 监听控制台消息
  page.on('console', (msg) => {
    const type = msg.type();
    const text = msg.text();
    console.log(`[Console ${type}]:`, text);
  });

  // 监听页面错误
  page.on('pageerror', (error) => {
    console.log('[Page Error]:', error.message);
  });

  // 监听请求失败
  page.on('requestfailed', (request) => {
    console.log('[Request Failed]:', request.url(), request.failure().errorText);
  });

  // 监听响应
  page.on('response', (response) => {
    const status = response.status();
    const url = response.url();
    if (status >= 400) {
      console.log(`[HTTP ${status}]:`, url);
    }
  });

  console.log('导航到 http://localhost:3000');
  await page.goto('http://localhost:3000', {
    waitUntil: 'networkidle0',
    timeout: 30000,
  });

  // 等待页面渲染
  await page.waitForTimeout(3000);

  // 检查 DOM 结构
  console.log('\n=== DOM 结构检查 ===');
  const domInfo = await page.evaluate(() => {
    // 检查侧边栏
    const sidebar = document.querySelector('aside');
    const sidebarStyles = sidebar ? window.getComputedStyle(sidebar) : null;

    // 检查主内容区域
    const main = document.querySelector('main');

    // 检查 AppLayout
    const appLayout = document.querySelector('div.flex.h-screen');

    // 检查用户信息
    const welcomeText = document.querySelector('[data-testid="dashboard-welcome-title"]');

    return {
      hasSidebar: !!sidebar,
      sidebarVisible: sidebarStyles ? sidebarStyles.display !== 'none' : false,
      sidebarWidth: sidebarStyles ? sidebarStyles.width : null,
      sidebarPosition: sidebarStyles ? {
        display: sidebarStyles.display,
        position: sidebarStyles.position,
        visibility: sidebarStyles.visibility,
      } : null,
      hasMain: !!main,
      hasAppLayout: !!appLayout,
      welcomeText: welcomeText ? welcomeText.textContent : null,
      bodyChildren: document.body.children.length,
      bodyFirstChild: document.body.children[0]?.tagName,
    };
  });

  console.log('DOM 信息:', JSON.stringify(domInfo, null, 2));

  // 检查本地存储
  console.log('\n=== 本地存储检查 ===');
  const storage = await page.evaluate(() => {
    return {
      authToken: localStorage.getItem('auth_token'),
      authUser: localStorage.getItem('auth_user'),
      allKeys: Object.keys(localStorage),
    };
  });
  console.log('LocalStorage:', JSON.stringify(storage, null, 2));

  // 截图
  console.log('\n=== 截图 ===');
  await page.screenshot({
    path: 'd:\\git\\1108\\frontend\\debug-screenshot.png',
    fullPage: true,
  });
  console.log('截图已保存到: d:\\git\\1108\\frontend\\debug-screenshot.png');

  // 获取网络请求统计
  console.log('\n=== 等待用户检查（浏览器将保持打开）===');
  console.log('按 Ctrl+C 退出');

  // 保持浏览器打开
  await new Promise(() => {});
})();
