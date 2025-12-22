/**
 * 测试认证和页面导航
 * 使用 Playwright 自动化测试登录后能否正常访问其他页面
 */
const { chromium } = require('playwright');

const BASE_URL = 'http://localhost:3000';
const TEST_EMAIL = 'demo@test.com';
const TEST_PASSWORD = 'demo1234';

async function testAuthNavigation() {
  console.log('=== 开始认证和导航测试 ===\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // 监听控制台消息
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`[Console Error] ${msg.text()}`);
    }
  });

  // 监听网络请求失败
  page.on('requestfailed', request => {
    console.log(`[Request Failed] ${request.url()} - ${request.failure()?.errorText}`);
  });

  try {
    // 1. 访问登录页
    console.log('1. 访问登录页...');
    await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' });
    console.log(`   当前 URL: ${page.url()}`);

    // 2. 填写登录表单
    console.log('2. 填写登录表单...');
    await page.fill('input[name="identifier"], input[type="email"]', TEST_EMAIL);
    await page.fill('input[name="password"], input[type="password"]', TEST_PASSWORD);

    // 3. 提交登录
    console.log('3. 提交登录...');
    await page.click('button[type="submit"]');

    // 等待导航完成 - 等待不在 /login 页面
    await page.waitForTimeout(3000); // 等待登录响应
    await page.waitForURL(/^(?!.*\/login)/, { timeout: 10000 }).catch(() => {});
    console.log(`   登录后 URL: ${page.url()}`);

    // 4. 验证 localStorage 中的 token
    const authToken = await page.evaluate(() => localStorage.getItem('auth-token'));
    console.log(`   Token 存储: ${authToken ? '有效 (长度: ' + authToken.length + ')' : '无效'}`);

    if (!authToken || authToken === 'undefined') {
      console.log('   ERROR: Token 未正确存储!');
      return false;
    }

    // 5. 测试访问多个页面
    const pagesToTest = [
      { path: '/projects', name: '项目列表' },
      { path: '/channels', name: '渠道管理' },
      { path: '/ad-accounts', name: '广告账户' },
      { path: '/daily-reports', name: '日报管理' },
      { path: '/topups', name: '充值管理' },
    ];

    console.log('\n4. 测试页面导航...');
    let successCount = 0;
    let failCount = 0;

    for (const { path, name } of pagesToTest) {
      console.log(`\n   测试 ${name} (${path})...`);

      // 监听 API 响应
      let apiError = null;
      const responseHandler = (response) => {
        if (response.url().includes('/api/') && response.status() === 401) {
          apiError = response.url();
        }
      };
      page.on('response', responseHandler);

      try {
        await page.goto(`${BASE_URL}${path}`, { waitUntil: 'networkidle', timeout: 15000 });
        const currentUrl = page.url();

        if (currentUrl.includes('/login')) {
          console.log(`   FAIL: 被重定向到登录页`);
          if (apiError) {
            console.log(`   原因: API 401 - ${apiError}`);
          }
          failCount++;
        } else {
          console.log(`   OK: 当前 URL = ${currentUrl}`);
          successCount++;
        }
      } catch (err) {
        console.log(`   ERROR: ${err.message}`);
        failCount++;
      }

      page.off('response', responseHandler);
    }

    // 6. 输出测试结果
    console.log('\n=== 测试结果 ===');
    console.log(`成功: ${successCount}/${pagesToTest.length}`);
    console.log(`失败: ${failCount}/${pagesToTest.length}`);

    return failCount === 0;

  } catch (error) {
    console.log(`\nERROR: ${error.message}`);
    console.log(error.stack);
    return false;
  } finally {
    await browser.close();
  }
}

testAuthNavigation()
  .then(success => {
    console.log(`\n测试${success ? '通过' : '失败'}`);
    process.exit(success ? 0 : 1);
  })
  .catch(err => {
    console.error(err);
    process.exit(1);
  });
