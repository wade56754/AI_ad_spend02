/**
 * 登录页面完整性验证测试
 *
 * 此测试脚本执行用户要求的所有验证项:
 * 1. 页面基础验证
 * 2. 登录表单验证
 * 3. Network请求验证
 * 4. Console错误检查
 * 5. 模拟登录测试
 * 6. Local Storage验证
 * 7. 问题诊断
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// 配置
const FRONTEND_URL = 'http://localhost:3000';
const BACKEND_URL = 'http://localhost:8000';
const TEST_EMAIL = 'test@example.com';
const TEST_PASSWORD = 'test123';

// 测试结果
const testResults = {
  timestamp: new Date().toISOString(),
  success: [],
  failures: [],
  networkRequests: [],
  consoleErrors: [],
  loginRequest: null,
  localStorage: {},
  screenshots: []
};

/**
 * 等待指定时间
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 记录成功项
 */
function recordSuccess(message) {
  console.log(`✅ ${message}`);
  testResults.success.push(message);
}

/**
 * 记录失败项
 */
function recordFailure(message) {
  console.log(`❌ ${message}`);
  testResults.failures.push(message);
}

/**
 * 主测试函数
 */
async function runLoginVerification() {
  let browser;
  let page;

  try {
    // 启动浏览器
    console.log('🚀 启动Chrome浏览器...\n');
    // 检测是否在 CI 环境或无头模式下运行
    const isCI = process.env.CI === 'true' || process.env.HEADLESS === 'true';

    browser = await puppeteer.launch({
      headless: isCI ? 'new' : false,  // CI 环境使用 headless 模式
      devtools: !isCI,   // 非 CI 环境打开 DevTools
      args: [
        '--window-size=1920,1080',
        '--disable-web-security',
        '--disable-features=IsolateOrigins,site-per-process',
        '--no-sandbox',  // CI 环境需要
        '--disable-setuid-sandbox'  // CI 环境需要
      ]
    });

    page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });

    // ============================================================
    // 1. 监听Console消息
    // ============================================================
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();

      if (type === 'error' || type === 'warning') {
        testResults.consoleErrors.push({
          type,
          message: text,
          timestamp: new Date().toISOString()
        });
      }
    });

    // ============================================================
    // 2. 监听Network请求
    // ============================================================
    await page.setRequestInterception(true);

    page.on('request', request => {
      const url = request.url();

      // 过滤Chrome扩展请求
      if (
        url.includes('chrome-extension://') ||
        url.includes('/general') ||
        url.includes('/tone') ||
        url.includes('/template') ||
        url.includes('googleapis.com')
      ) {
        request.continue();
        return;
      }

      // 只记录项目请求
      if (url.includes('localhost:3000') || url.includes('localhost:8000')) {
        testResults.networkRequests.push({
          method: request.method(),
          url,
          headers: request.headers(),
          postData: request.postData(),
          timestamp: new Date().toISOString()
        });
      }

      request.continue();
    });

    page.on('response', async response => {
      const url = response.url();

      // 只记录登录API响应
      if (url.includes('/api/v1/auth/login')) {
        try {
          const status = response.status();
          const headers = response.headers();
          const body = await response.text();

          testResults.loginRequest = {
            url,
            status,
            headers,
            responseBody: body,
            timestamp: new Date().toISOString()
          };
        } catch (error) {
          console.error('无法读取响应体:', error.message);
        }
      }
    });

    // ============================================================
    // 3. 页面基础验证
    // ============================================================
    console.log('\n📋 步骤1: 页面基础验证\n');

    console.log(`访问 ${FRONTEND_URL}...`);
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle2', timeout: 30000 });

    // 等待页面加载
    await sleep(2000);

    // 检查当前URL
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      recordSuccess('自动跳转到 /login 路径');
    } else {
      recordFailure(`未跳转到登录页,当前URL: ${currentUrl}`);
    }

    // 检查页面标题
    const pageTitle = await page.$eval('h2', el => el.textContent);
    if (pageTitle.includes('AI 广告代投系统')) {
      recordSuccess('页面标题正确: "AI 广告代投系统"');
    } else {
      recordFailure(`页面标题错误: ${pageTitle}`);
    }

    // 检查页面是否正常渲染
    const bodyVisible = await page.$('body');
    if (bodyVisible) {
      recordSuccess('页面正常渲染 (无白屏)');
    } else {
      recordFailure('页面白屏或未渲染');
    }

    // 截图
    const screenshotPath = path.join(__dirname, '../screenshots/login-page.png');
    await page.screenshot({ path: screenshotPath, fullPage: true });
    testResults.screenshots.push(screenshotPath);
    console.log(`📸 截图已保存: ${screenshotPath}\n`);

    // ============================================================
    // 4. 登录表单验证
    // ============================================================
    console.log('📋 步骤2: 登录表单验证\n');

    // 检查邮箱输入框
    const emailInput = await page.$('input[type="email"]#email');
    if (emailInput) {
      const emailName = await page.$eval('input#email', el => el.getAttribute('name'));
      const emailId = await page.$eval('input#email', el => el.id);

      if (emailName === 'email' && emailId === 'email') {
        recordSuccess('<input id="email" name="email" type="email"> 存在且正确');
      } else {
        recordFailure(`邮箱输入框属性不正确: name="${emailName}", id="${emailId}"`);
      }
    } else {
      recordFailure('未找到邮箱输入框');
    }

    // 检查Label
    const emailLabel = await page.$eval('label[for="email"]', el => el.textContent);
    if (emailLabel.includes('邮箱地址')) {
      recordSuccess('Label显示为 "邮箱地址"');
    } else {
      recordFailure(`Label文本错误: ${emailLabel}`);
    }

    // 检查密码输入框
    const passwordInput = await page.$('input[type="password"]');
    if (passwordInput) {
      recordSuccess('<input type="password"> 存在');
    } else {
      recordFailure('未找到密码输入框');
    }

    // 检查记住我checkbox
    const rememberMeCheckbox = await page.$('input[type="checkbox"]#remember_me');
    if (rememberMeCheckbox) {
      recordSuccess('<input type="checkbox" id="remember_me"> 存在');
    } else {
      recordFailure('未找到"记住我"复选框');
    }

    // 检查提交按钮
    const submitButton = await page.$eval('button[type="submit"]', el => el.textContent);
    if (submitButton.includes('登录')) {
      recordSuccess('提交按钮显示 "登录"');
    } else {
      recordFailure(`提交按钮文本错误: ${submitButton}`);
    }

    // ============================================================
    // 5. 模拟登录测试
    // ============================================================
    console.log('\n📋 步骤3: 模拟登录测试\n');

    // 清空之前的网络请求记录
    testResults.networkRequests = [];

    // 输入测试凭证
    await page.type('input#email', TEST_EMAIL);
    recordSuccess(`输入邮箱: ${TEST_EMAIL}`);

    await page.type('input#password', TEST_PASSWORD);
    recordSuccess(`输入密码: ${TEST_PASSWORD}`);

    // 勾选"记住我"
    await page.click('input#remember_me');
    recordSuccess('勾选"记住我"');

    // 等待确保输入完成
    await sleep(1000);

    // 点击登录按钮
    console.log('\n🔄 点击"登录"按钮...\n');
    await Promise.all([
      page.click('button[type="submit"]'),
      page.waitForResponse(
        response => response.url().includes('/api/v1/auth/login'),
        { timeout: 10000 }
      ).catch(() => null)  // 忽略超时错误
    ]);

    // 等待响应
    await sleep(3000);

    // ============================================================
    // 6. 分析登录请求
    // ============================================================
    console.log('📋 步骤4: 分析登录请求\n');

    if (testResults.loginRequest) {
      const { status, url, responseBody } = testResults.loginRequest;

      console.log(`请求URL: ${url}`);
      console.log(`状态码: ${status}`);
      console.log(`响应体:\n${responseBody}\n`);

      // 查找对应的请求
      const loginReq = testResults.networkRequests.find(
        req => req.url.includes('/api/v1/auth/login')
      );

      if (loginReq) {
        console.log('📤 Request Payload:');
        console.log(loginReq.postData || 'No POST data');
        console.log('');

        // 解析payload
        let payload = {};
        try {
          payload = JSON.parse(loginReq.postData || '{}');
        } catch (e) {
          // Ignore
        }

        // 检查字段
        if (payload.email) {
          recordSuccess(`Request使用 "email" 字段: ${payload.email}`);
        } else {
          recordFailure('Request未使用 "email" 字段');
        }

        if (payload.identifier) {
          recordFailure('Request错误地使用了 "identifier" 字段');
        } else {
          recordSuccess('Request未包含错误的 "identifier" 字段');
        }

        if (payload.password) {
          recordSuccess('Request包含 "password" 字段');
        }

        if (payload.remember_me !== undefined) {
          recordSuccess(`Request包含 "remember_me" 字段: ${payload.remember_me}`);
        }
      }

      // 检查响应状态
      if (status === 200) {
        recordSuccess('登录请求成功 (200 OK)');

        try {
          const responseJson = JSON.parse(responseBody);
          if (responseJson.data && responseJson.data.access_token) {
            recordSuccess('响应包含 access_token');
          }
        } catch (e) {
          // Ignore
        }
      } else if (status === 422) {
        recordFailure(`登录请求失败 (422 Unprocessable Entity) - 字段验证错误`);
        console.log('⚠️  这是预期的错误,因为后端使用 "identifier" 字段而非 "email"');
      } else if (status === 401) {
        recordFailure(`登录请求失败 (401 Unauthorized) - 认证失败`);
      } else {
        recordFailure(`登录请求失败 (${status})`);
      }
    } else {
      recordFailure('未捕获到登录请求');
    }

    // ============================================================
    // 7. 检查Local Storage
    // ============================================================
    console.log('\n📋 步骤5: 检查Local Storage\n');

    const localStorage = await page.evaluate(() => {
      const storage = {};
      for (let i = 0; i < window.localStorage.length; i++) {
        const key = window.localStorage.key(i);
        storage[key] = window.localStorage.getItem(key);
      }
      return storage;
    });

    testResults.localStorage = localStorage;

    if (localStorage['auth-token']) {
      recordSuccess('Local Storage包含 "auth-token"');
    } else {
      recordFailure('Local Storage不包含 "auth-token"');
    }

    if (localStorage['refresh-token']) {
      recordSuccess('Local Storage包含 "refresh-token"');
    } else {
      recordFailure('Local Storage不包含 "refresh-token"');
    }

    if (localStorage['token-expiry']) {
      recordSuccess('Local Storage包含 "token-expiry"');
    } else {
      recordFailure('Local Storage不包含 "token-expiry"');
    }

    // ============================================================
    // 8. 检查Console错误
    // ============================================================
    console.log('\n📋 步骤6: 检查Console错误\n');

    if (testResults.consoleErrors.length === 0) {
      recordSuccess('Console无错误信息');
    } else {
      testResults.consoleErrors.forEach(error => {
        recordFailure(`Console ${error.type}: ${error.message}`);
      });
    }

    // ============================================================
    // 9. 截图最终状态
    // ============================================================
    const finalScreenshotPath = path.join(__dirname, '../screenshots/login-final-state.png');
    await page.screenshot({ path: finalScreenshotPath, fullPage: true });
    testResults.screenshots.push(finalScreenshotPath);
    console.log(`📸 最终状态截图: ${finalScreenshotPath}\n`);

  } catch (error) {
    console.error('❌ 测试执行错误:', error);
    testResults.failures.push(`测试执行错误: ${error.message}`);
  } finally {
    // ============================================================
    // 10. 生成测试报告
    // ============================================================
    console.log('\n' + '='.repeat(80));
    console.log('📊 测试报告');
    console.log('='.repeat(80) + '\n');

    console.log(`✅ 成功项: ${testResults.success.length}`);
    testResults.success.forEach(item => console.log(`   - ${item}`));

    console.log(`\n❌ 失败项: ${testResults.failures.length}`);
    testResults.failures.forEach(item => console.log(`   - ${item}`));

    console.log(`\n📡 网络请求: ${testResults.networkRequests.length}`);
    testResults.networkRequests.forEach(req => {
      console.log(`   - ${req.method} ${req.url}`);
    });

    console.log(`\n🐛 Console错误: ${testResults.consoleErrors.length}`);
    testResults.consoleErrors.forEach(err => {
      console.log(`   - [${err.type}] ${err.message}`);
    });

    // 保存详细报告为JSON
    const reportPath = path.join(__dirname, '../reports/login-verification-report.json');
    const reportDir = path.dirname(reportPath);
    if (!fs.existsSync(reportDir)) {
      fs.mkdirSync(reportDir, { recursive: true });
    }
    fs.writeFileSync(reportPath, JSON.stringify(testResults, null, 2), 'utf8');
    console.log(`\n💾 详细报告已保存: ${reportPath}`);

    console.log('\n' + '='.repeat(80) + '\n');

    // 等待5秒后关闭浏览器
    console.log('⏳ 5秒后关闭浏览器...');
    await sleep(5000);

    if (browser) {
      await browser.close();
    }
  }
}

// 执行测试
runLoginVerification()
  .then(() => {
    console.log('✅ 测试执行完成');
    process.exit(testResults.failures.length > 0 ? 1 : 0);
  })
  .catch(error => {
    console.error('❌ 测试执行失败:', error);
    process.exit(1);
  });
