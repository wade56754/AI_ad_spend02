const puppeteer = require('puppeteer');

(async () => {
  console.log('🚀 启动浏览器检查...\n');

  const browser = await puppeteer.launch({
    headless: false, // 显示浏览器窗口
    devtools: true,  // 自动打开DevTools
    args: ['--window-size=1920,1080']
  });

  const page = await browser.newPage();

  // 设置视口
  await page.setViewport({ width: 1920, height: 1080 });

  // 收集控制台消息
  const consoleMessages = [];
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    consoleMessages.push({ type, text, timestamp: new Date().toISOString() });
    console.log(`[CONSOLE ${type.toUpperCase()}] ${text}`);
  });

  // 收集网络请求
  const networkRequests = [];
  page.on('request', request => {
    networkRequests.push({
      url: request.url(),
      method: request.method(),
      resourceType: request.resourceType(),
      headers: request.headers(),
      timestamp: new Date().toISOString()
    });
  });

  // 收集网络响应
  const networkResponses = [];
  page.on('response', response => {
    networkResponses.push({
      url: response.url(),
      status: response.status(),
      statusText: response.statusText(),
      headers: response.headers(),
      timestamp: new Date().toISOString()
    });
  });

  // 收集网络错误
  const networkErrors = [];
  page.on('requestfailed', request => {
    const failure = request.failure();
    networkErrors.push({
      url: request.url(),
      method: request.method(),
      errorText: failure ? failure.errorText : 'Unknown error',
      timestamp: new Date().toISOString()
    });
    console.log(`❌ [NETWORK ERROR] ${request.url()}`);
    console.log(`   Method: ${request.method()}`);
    console.log(`   Error: ${failure ? failure.errorText : 'Unknown'}\n`);
  });

  // 收集页面错误
  const pageErrors = [];
  page.on('pageerror', error => {
    pageErrors.push({
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    });
    console.log(`🔴 [PAGE ERROR] ${error.message}`);
    if (error.stack) {
      console.log(`   Stack: ${error.stack}\n`);
    }
  });

  try {
    console.log('📱 正在访问 http://localhost:3000\n');

    // 访问页面，等待网络空闲
    await page.goto('http://localhost:3000', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    // 等待额外的网络请求
    await page.waitForTimeout(5000);

    console.log('\n' + '='.repeat(80));
    console.log('📊 检查结果汇总');
    console.log('='.repeat(80) + '\n');

    // 输出控制台消息统计
    console.log(`\n📝 控制台消息总数: ${consoleMessages.length}`);
    const errorLogs = consoleMessages.filter(m => m.type === 'error');
    const warningLogs = consoleMessages.filter(m => m.type === 'warning');
    console.log(`   - 错误 (error): ${errorLogs.length}`);
    console.log(`   - 警告 (warning): ${warningLogs.length}`);

    if (errorLogs.length > 0) {
      console.log('\n🔴 控制台错误详情:');
      errorLogs.forEach((log, i) => {
        console.log(`\n${i + 1}. [${log.timestamp}]`);
        console.log(`   ${log.text}`);
      });
    }

    // 输出网络请求统计
    console.log(`\n\n🌐 网络请求总数: ${networkRequests.length}`);
    console.log(`   - 成功响应: ${networkResponses.filter(r => r.status >= 200 && r.status < 400).length}`);
    console.log(`   - 失败响应: ${networkResponses.filter(r => r.status >= 400).length}`);
    console.log(`   - 网络错误: ${networkErrors.length}`);

    if (networkErrors.length > 0) {
      console.log('\n❌ 网络错误详情:');
      networkErrors.forEach((error, i) => {
        console.log(`\n${i + 1}. [${error.timestamp}]`);
        console.log(`   URL: ${error.url}`);
        console.log(`   Method: ${error.method}`);
        console.log(`   Error: ${error.errorText}`);
      });
    }

    // 输出失败的HTTP请求
    const failedResponses = networkResponses.filter(r => r.status >= 400);
    if (failedResponses.length > 0) {
      console.log('\n⚠️  失败的HTTP请求:');
      failedResponses.forEach((response, i) => {
        console.log(`\n${i + 1}. [${response.timestamp}]`);
        console.log(`   URL: ${response.url}`);
        console.log(`   Status: ${response.status} ${response.statusText}`);
      });
    }

    // 输出页面错误
    if (pageErrors.length > 0) {
      console.log('\n\n🔴 页面JavaScript错误:');
      pageErrors.forEach((error, i) => {
        console.log(`\n${i + 1}. [${error.timestamp}]`);
        console.log(`   ${error.message}`);
        if (error.stack) {
          console.log(`   Stack:\n${error.stack}`);
        }
      });
    }

    // 保存详细报告到JSON文件
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        consoleMessages: consoleMessages.length,
        consoleErrors: errorLogs.length,
        consoleWarnings: warningLogs.length,
        networkRequests: networkRequests.length,
        networkErrors: networkErrors.length,
        httpErrors: failedResponses.length,
        pageErrors: pageErrors.length
      },
      consoleMessages,
      networkRequests,
      networkResponses,
      networkErrors,
      pageErrors
    };

    const fs = require('fs');
    fs.writeFileSync(
      'd:/git/1108/frontend/browser-debug-report.json',
      JSON.stringify(report, null, 2)
    );

    console.log('\n\n✅ 详细报告已保存到: browser-debug-report.json');
    console.log('\n⏸️  浏览器将保持打开30秒供您手动检查...');

    // 保持浏览器打开30秒
    await page.waitForTimeout(30000);

  } catch (error) {
    console.error('\n💥 发生错误:', error.message);
    console.error(error.stack);
  } finally {
    await browser.close();
    console.log('\n👋 浏览器已关闭');
  }
})();
