const { chromium } = require('playwright');

async function testCEODashboard() {
  console.log('启动浏览器...');
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  // 收集控制台消息
  const consoleMessages = [];
  page.on('console', msg => {
    const type = msg.type();
    if (type === 'error' || type === 'warning') {
      consoleMessages.push(`[${type}] ${msg.text()}`);
    }
  });

  // 收集失败的网络请求
  const failedRequests = [];
  page.on('requestfailed', request => {
    failedRequests.push(`${request.method()} ${request.url()} - ${request.failure()?.errorText}`);
  });
  page.on('response', response => {
    if (response.status() >= 400) {
      failedRequests.push(`${response.status()} ${response.url()}`);
      console.log(`[HTTP ${response.status()}] ${response.url()}`);
    }
  });

  // 收集页面错误
  page.on('pageerror', error => {
    consoleMessages.push(`[PAGE ERROR] ${error.message}`);
  });

  try {
    // 1. 登录页面
    console.log('1. 导航到登录页...');
    await page.goto('http://localhost:3000/login');
    await page.waitForLoadState('networkidle');

    // 2. 填写登录表单
    console.log('2. 填写登录信息...');
    await page.fill('#identifier', 'admin@test.com');
    await page.fill('#password', 'admin123');

    // 3. 点击登录按钮
    console.log('3. 点击登录...');
    await page.click('[data-testid="login-button"]');

    // 4. 等待跳转到仪表盘
    console.log('4. 等待跳转...');
    await page.waitForURL('**/dashboard**', { timeout: 10000 }).catch(() => {
      console.log('   未跳转到 dashboard，检查当前 URL...');
    });
    console.log('   当前 URL:', page.url());

    // 5. 等待页面加载 (登录后自动跳转到首页即 CEO 驾驶舱)
    console.log('5. 等待 CEO 驾驶舱加载...');
    await page.waitForLoadState('networkidle');

    // 等待 CEO 驾驶舱内容出现 - 等待实际内容而非页面标题
    console.log('   等待数据加载...');
    try {
      // 等待"公司现金状况"这个实际内容出现
      await page.waitForSelector('text=公司现金状况', { timeout: 30000 });
      console.log('   ✅ 找到公司现金状况');
    } catch (e) {
      console.log('   ⚠️ 未找到公司现金状况，等待更长时间...');
      await page.waitForTimeout(10000);

      // 尝试截取中间状态
      await page.screenshot({ path: 'ceo-dashboard-loading.png' });
      console.log('   📸 保存了加载状态截图: ceo-dashboard-loading.png');
    }

    // 再等待一下确保所有内容加载
    await page.waitForTimeout(3000);

    // 6. 检查页面内容
    console.log('6. 检查页面内容...');
    const pageTitle = await page.title();
    console.log('   页面标题:', pageTitle);

    // 检查主内容区域
    const mainContent = await page.$('main');
    if (mainContent) {
      const mainText = await mainContent.textContent();
      console.log('   main 区域文本长度:', mainText?.length || 0);
      if (mainText && mainText.length < 500) {
        console.log('   main 区域内容:', mainText.substring(0, 200));
      }
    } else {
      console.log('   ⚠️ 未找到 main 元素');
    }

    // 检查是否有 loading 状态
    const loadingElements = await page.$$('[class*="skeleton"], [class*="loading"], [class*="spinner"]');
    console.log('   Loading 元素数量:', loadingElements.length);

    const bodyText = await page.textContent('body');

    // 检查中文文本
    const checks = [
      { text: 'CEO 驾驶舱', name: '标题' },
      { text: '公司现金状况', name: '现金状况' },
      { text: '盈利概览', name: '盈利概览' },
      { text: '项目余额', name: '项目余额' },
      { text: '毛利', name: '毛利' },
    ];

    console.log('\n   中文检查:');
    for (const check of checks) {
      const found = bodyText.includes(check.text);
      console.log(`   ${found ? '✅' : '❌'} ${check.name}: "${check.text}"`);
    }

    // 7. 截图
    console.log('\n7. 保存截图...');
    await page.screenshot({
      path: 'ceo-dashboard-test-result.png',
      fullPage: true
    });
    console.log('   截图已保存: ceo-dashboard-test-result.png');

    // 8. 打印控制台错误和失败请求
    if (consoleMessages.length > 0) {
      console.log('\n浏览器控制台消息:');
      consoleMessages.forEach(msg => console.log('  ', msg));
    }
    if (failedRequests.length > 0) {
      console.log('\n失败的网络请求:');
      failedRequests.forEach(req => console.log('  ', req));
    }

    // 9. 检查是否有错误
    const hasError = bodyText.includes('加载仪表盘失败');
    const allChecksPass = checks.every(c => bodyText.includes(c.text));

    if (hasError) {
      console.log('\n❌ CEO 驾驶舱测试失败!');
      console.log('   原因: 页面显示加载错误');
    } else if (!allChecksPass) {
      console.log('\n❌ CEO 驾驶舱测试失败!');
      console.log('   原因: 部分中文文本未找到');
    } else {
      console.log('\n✅ CEO 驾驶舱测试通过!');
      console.log('   所有中文文本正确显示');
    }

  } catch (error) {
    console.error('测试失败:', error.message);
    await page.screenshot({ path: 'ceo-dashboard-error.png' });
  } finally {
    await browser.close();
    console.log('\n浏览器已关闭');
  }
}

testCEODashboard();
