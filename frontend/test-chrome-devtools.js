/**
 * Chrome DevTools 前端测试脚本
 * 使用 Puppeteer 和 Chrome DevTools Protocol 进行页面测试
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// 测试配置
const BASE_URL = 'http://localhost:3000';
const TEST_PAGES = [
  { name: '首页', path: '/' },
  { name: '登录页', path: '/login' },
  { name: '仪表盘', path: '/projects' },
];

// 测试报告数据结构
const testReport = {
  timestamp: new Date().toISOString(),
  summary: {
    total: 0,
    passed: 0,
    failed: 0,
    warnings: 0,
  },
  pages: [],
  performance: [],
  errors: [],
  warnings: [],
};

/**
 * 测试单个页面
 */
async function testPage(browser, pageConfig) {
  const page = await browser.newPage();
  const pageResult = {
    name: pageConfig.name,
    path: pageConfig.path,
    status: 'pending',
    loadTime: 0,
    errors: [],
    warnings: [],
    consoleErrors: [],
    networkErrors: [],
    performance: {},
  };

  try {
    // 监听控制台错误
    page.on('console', (msg) => {
      const type = msg.type();
      if (type === 'error') {
        pageResult.consoleErrors.push({
          text: msg.text(),
          location: msg.location(),
        });
      } else if (type === 'warning') {
        pageResult.warnings.push(msg.text());
      }
    });

    // 监听页面错误
    page.on('pageerror', (error) => {
      pageResult.errors.push({
        message: error.message,
        stack: error.stack,
      });
    });

    // 监听网络请求失败
    page.on('requestfailed', (request) => {
      pageResult.networkErrors.push({
        url: request.url(),
        failure: request.failure()?.errorText,
      });
    });

    // 启用性能监控
    await page.setCacheEnabled(false);
    const client = await page.target().createCDPSession();
    await client.send('Performance.enable');
    await client.send('Network.enable');

    // 记录开始时间
    const startTime = Date.now();

    // 导航到页面
    const response = await page.goto(`${BASE_URL}${pageConfig.path}`, {
      waitUntil: 'networkidle2',
      timeout: 30000,
    });

    // 记录加载时间
    pageResult.loadTime = Date.now() - startTime;

    // 检查响应状态
    if (!response || response.status() >= 400) {
      pageResult.status = 'failed';
      pageResult.errors.push({
        message: `HTTP ${response?.status() || 'Unknown'} 错误`,
        url: `${BASE_URL}${pageConfig.path}`,
      });
      testReport.summary.failed++;
      return pageResult;
    }

    // 获取性能指标
    try {
      const performanceMetrics = await page.metrics();
      const performanceTiming = JSON.parse(
        await page.evaluate(() => JSON.stringify(window.performance.timing))
      );

      pageResult.performance = {
        metrics: performanceMetrics,
        timing: {
          domContentLoaded: performanceTiming.domContentLoadedEventEnd - performanceTiming.navigationStart,
          loadComplete: performanceTiming.loadEventEnd - performanceTiming.navigationStart,
          firstPaint: performanceTiming.responseEnd - performanceTiming.navigationStart,
        },
      };

      // 使用 Chrome DevTools Protocol 获取更详细的性能数据
      const perfEntries = await client.send('Performance.getMetrics');
      if (perfEntries && perfEntries.metrics) {
        const metricsMap = {};
        perfEntries.metrics.forEach((metric) => {
          metricsMap[metric.name] = metric.value;
        });
        pageResult.performance.cdpMetrics = metricsMap;
      }
    } catch (perfError) {
      pageResult.warnings.push(`性能指标收集失败: ${perfError.message}`);
    }

    // 检查页面基本元素
    const title = await page.title();
    const url = page.url();

    // 检查是否有明显错误
    const hasErrors = pageResult.errors.length > 0 || pageResult.consoleErrors.length > 0;

    if (hasErrors) {
      pageResult.status = 'warning';
      testReport.summary.warnings++;
    } else {
      pageResult.status = 'passed';
      testReport.summary.passed++;
    }

    pageResult.title = title;
    pageResult.finalUrl = url;

    // 等待页面完全加载
    await new Promise(resolve => setTimeout(resolve, 1000));

    // 截图（可选）
    const screenshotPath = path.join(
      __dirname,
      'test-reports',
      'screenshots',
      `${pageConfig.name.replace(/\s+/g, '-')}-${Date.now()}.png`
    );
    await page.screenshot({ path: screenshotPath, fullPage: true });
    pageResult.screenshot = screenshotPath;

  } catch (error) {
    pageResult.status = 'failed';
    pageResult.errors.push({
      message: error.message,
      stack: error.stack,
    });
    testReport.summary.failed++;
  } finally {
    await page.close();
  }

  return pageResult;
}

/**
 * 生成测试报告
 */
function generateReport() {
  const reportDir = path.join(__dirname, 'test-reports');
  if (!fs.existsSync(reportDir)) {
    fs.mkdirSync(reportDir, { recursive: true });
  }
  if (!fs.existsSync(path.join(reportDir, 'screenshots'))) {
    fs.mkdirSync(path.join(reportDir, 'screenshots'), { recursive: true });
  }

  // 生成 Markdown 报告
  const markdownReport = generateMarkdownReport();
  const reportPath = path.join(
    reportDir,
    `test-report-${new Date().toISOString().replace(/[:.]/g, '-')}.md`
  );
  fs.writeFileSync(reportPath, markdownReport, 'utf-8');

  // 生成 JSON 报告
  const jsonPath = path.join(
    reportDir,
    `test-report-${new Date().toISOString().replace(/[:.]/g, '-')}.json`
  );
  fs.writeFileSync(jsonPath, JSON.stringify(testReport, null, 2), 'utf-8');

  console.log(`\n✅ 测试报告已生成:`);
  console.log(`   - Markdown: ${reportPath}`);
  console.log(`   - JSON: ${jsonPath}\n`);

  return { markdownPath: reportPath, jsonPath };
}

/**
 * 生成 Markdown 格式的测试报告
 */
function generateMarkdownReport() {
  const { summary, pages, timestamp } = testReport;
  const passRate = summary.total > 0 ? ((summary.passed / summary.total) * 100).toFixed(2) : 0;

  let report = `# 前端页面测试报告\n\n`;
  report += `**生成时间**: ${new Date(timestamp).toLocaleString('zh-CN')}\n\n`;
  report += `---\n\n`;

  // 测试摘要
  report += `## 📊 测试摘要\n\n`;
  report += `| 指标 | 数量 |\n`;
  report += `|------|------|\n`;
  report += `| 总测试数 | ${summary.total} |\n`;
  report += `| ✅ 通过 | ${summary.passed} |\n`;
  report += `| ❌ 失败 | ${summary.failed} |\n`;
  report += `| ⚠️ 警告 | ${summary.warnings} |\n`;
  report += `| 通过率 | ${passRate}% |\n\n`;

  // 页面测试详情
  report += `## 📄 页面测试详情\n\n`;
  pages.forEach((page) => {
    const statusIcon = page.status === 'passed' ? '✅' : page.status === 'failed' ? '❌' : '⚠️';
    report += `### ${statusIcon} ${page.name}\n\n`;
    report += `- **路径**: ${page.path}\n`;
    report += `- **状态**: ${page.status}\n`;
    report += `- **加载时间**: ${page.loadTime}ms\n`;
    if (page.title) {
      report += `- **页面标题**: ${page.title}\n`;
    }
    if (page.finalUrl) {
      report += `- **最终URL**: ${page.finalUrl}\n`;
    }

    // 性能指标
    if (page.performance && page.performance.timing) {
      report += `\n#### 性能指标\n\n`;
      report += `| 指标 | 值 |\n`;
      report += `|------|------|\n`;
      report += `| DOM 内容加载 | ${page.performance.timing.domContentLoaded}ms |\n`;
      report += `| 页面完全加载 | ${page.performance.timing.loadComplete}ms |\n`;
      report += `| 首次绘制 | ${page.performance.timing.firstPaint}ms |\n`;
    }

    // 错误信息
    if (page.errors.length > 0) {
      report += `\n#### ❌ 错误 (${page.errors.length}个)\n\n`;
      page.errors.forEach((error, index) => {
        report += `${index + 1}. **${error.message}**\n`;
        if (error.stack) {
          report += `   \`\`\`\n   ${error.stack}\n   \`\`\`\n`;
        }
      });
    }

    // 控制台错误
    if (page.consoleErrors.length > 0) {
      report += `\n#### 🖥️ 控制台错误 (${page.consoleErrors.length}个)\n\n`;
      page.consoleErrors.forEach((error, index) => {
        report += `${index + 1}. ${error.text}\n`;
      });
    }

    // 网络错误
    if (page.networkErrors.length > 0) {
      report += `\n#### 🌐 网络错误 (${page.networkErrors.length}个)\n\n`;
      page.networkErrors.forEach((error, index) => {
        report += `${index + 1}. ${error.url} - ${error.failure}\n`;
      });
    }

    // 警告
    if (page.warnings.length > 0) {
      report += `\n#### ⚠️ 警告 (${page.warnings.length}个)\n\n`;
      page.warnings.forEach((warning, index) => {
        report += `${index + 1}. ${warning}\n`;
      });
    }

    report += `\n---\n\n`;
  });

  // 总结
  report += `## 📝 测试总结\n\n`;
  if (summary.failed === 0 && summary.warnings === 0) {
    report += `✅ **所有测试通过！** 前端页面运行正常，未发现错误。\n\n`;
  } else if (summary.failed === 0) {
    report += `⚠️ **测试通过，但有警告** 建议检查警告信息并优化。\n\n`;
  } else {
    report += `❌ **测试失败** 发现 ${summary.failed} 个失败项，需要修复。\n\n`;
  }

  report += `---\n\n`;
  report += `**测试工具**: Puppeteer + Chrome DevTools Protocol\n`;
  report += `**测试环境**: ${BASE_URL}\n`;

  return report;
}

/**
 * 主函数
 */
async function main() {
  console.log('🚀 开始前端页面测试...\n');
  console.log(`测试目标: ${BASE_URL}\n`);

  // 检查服务器是否运行（使用 Puppeteer）
  const testBrowser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  try {
    const testPage = await testBrowser.newPage();
    try {
      await testPage.goto(BASE_URL, { waitUntil: 'networkidle2', timeout: 5000 });
      console.log('✅ 服务器连接正常\n');
    } catch (error) {
      console.error(`❌ 无法连接到 ${BASE_URL}`);
      console.error(`请确保开发服务器正在运行: pnpm run dev\n`);
      await testBrowser.close();
      process.exit(1);
    }
    await testPage.close();
  } finally {
    await testBrowser.close();
  }

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  try {
    testReport.summary.total = TEST_PAGES.length;

    // 测试每个页面
    for (const pageConfig of TEST_PAGES) {
      console.log(`测试页面: ${pageConfig.name} (${pageConfig.path})...`);
      const result = await testPage(browser, pageConfig);
      testReport.pages.push(result);

      const statusIcon = result.status === 'passed' ? '✅' : result.status === 'failed' ? '❌' : '⚠️';
      console.log(`  ${statusIcon} ${result.status} (${result.loadTime}ms)`);
      if (result.errors.length > 0) {
        console.log(`  ❌ ${result.errors.length} 个错误`);
      }
      if (result.consoleErrors.length > 0) {
        console.log(`  🖥️ ${result.consoleErrors.length} 个控制台错误`);
      }
    }

    // 生成报告
    const reportPaths = generateReport();

    // 输出摘要
    console.log('\n📊 测试摘要:');
    console.log(`  总测试数: ${testReport.summary.total}`);
    console.log(`  ✅ 通过: ${testReport.summary.passed}`);
    console.log(`  ❌ 失败: ${testReport.summary.failed}`);
    console.log(`  ⚠️ 警告: ${testReport.summary.warnings}`);

    // 返回退出码
    process.exit(testReport.summary.failed > 0 ? 1 : 0);

  } catch (error) {
    console.error('❌ 测试执行失败:', error);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

// 运行测试
if (require.main === module) {
  main().catch((error) => {
    console.error('❌ 未处理的错误:', error);
    process.exit(1);
  });
}

module.exports = { testPage, generateReport };

