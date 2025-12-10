/**
 * UI 交互测试脚本
 * 使用 Chrome DevTools Protocol 检测页面交互、点击响应、性能等
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// 测试配置
const BASE_URL = 'http://localhost:3000';
const REPORT_DIR = path.join(__dirname, 'ui-test-reports');

// 确保报告目录存在
if (!fs.existsSync(REPORT_DIR)) {
  fs.mkdirSync(REPORT_DIR, { recursive: true });
}

// 测试页面列表
const TEST_PAGES = [
  { name: '仪表盘', url: '/', selectors: {
    sidebar: 'nav',
    header: 'header',
    mainContent: 'main',
    statCards: '[class*="stat"]',
    charts: 'canvas, svg',
  }},
  { name: '项目管理', url: '/projects', selectors: {
    sidebar: 'nav',
    table: 'table',
    buttons: 'button',
    searchInput: 'input[type="search"], input[placeholder*="搜索"]',
  }},
];

// 颜色输出
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

/**
 * 检测页面可访问性问题
 */
async function checkAccessibility(page) {
  const issues = [];

  // 检查是否有 alt 属性的图片
  const imagesWithoutAlt = await page.$$eval('img:not([alt])', imgs => imgs.length);
  if (imagesWithoutAlt > 0) {
    issues.push({
      severity: 'medium',
      type: 'accessibility',
      message: `发现 ${imagesWithoutAlt} 个图片缺少 alt 属性`,
      recommendation: '为所有图片添加描述性的 alt 属性',
    });
  }

  // 检查按钮是否有文本或 aria-label
  const buttonsWithoutLabel = await page.$$eval(
    'button:not([aria-label]):not(:has(*))',
    btns => btns.filter(btn => !btn.textContent.trim()).length
  );
  if (buttonsWithoutLabel > 0) {
    issues.push({
      severity: 'high',
      type: 'accessibility',
      message: `发现 ${buttonsWithoutLabel} 个按钮缺少文本或 aria-label`,
      recommendation: '为所有按钮添加可读的文本或 aria-label',
    });
  }

  // 检查表单输入是否有 label
  const inputsWithoutLabel = await page.$$eval(
    'input:not([aria-label]):not([id])',
    inputs => inputs.length
  );
  if (inputsWithoutLabel > 0) {
    issues.push({
      severity: 'medium',
      type: 'accessibility',
      message: `发现 ${inputsWithoutLabel} 个输入框可能缺少关联的 label`,
      recommendation: '使用 <label> 标签或 aria-label 属性',
    });
  }

  return issues;
}

/**
 * 检测响应式设计
 */
async function checkResponsiveness(page, url) {
  const viewports = [
    { name: '手机', width: 375, height: 667 },
    { name: '平板', width: 768, height: 1024 },
    { name: '桌面', width: 1920, height: 1080 },
  ];

  const results = [];

  for (const viewport of viewports) {
    await page.setViewport(viewport);
    await page.goto(url, { waitUntil: 'networkidle2' });

    // 检查水平滚动条
    const hasHorizontalScroll = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });

    // 检查元素溢出
    const overflowElements = await page.evaluate(() => {
      const elements = document.querySelectorAll('*');
      const overflowing = [];
      elements.forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.right > window.innerWidth || rect.left < 0) {
          overflowing.push({
            tag: el.tagName,
            classes: el.className,
            width: rect.width,
          });
        }
      });
      return overflowing.slice(0, 5); // 只返回前5个
    });

    results.push({
      viewport: viewport.name,
      width: viewport.width,
      hasHorizontalScroll,
      overflowCount: overflowElements.length,
      overflowElements: overflowElements,
    });
  }

  return results;
}

/**
 * 检测交互响应性
 */
async function checkInteractivity(page, selectors) {
  const interactions = [];

  // 测试按钮点击
  try {
    const buttons = await page.$$('button:not([disabled])');
    log(`找到 ${buttons.length} 个可点击按钮`, 'cyan');

    for (let i = 0; i < Math.min(buttons.length, 5); i++) {
      const button = buttons[i];
      const buttonText = await button.evaluate(el => el.textContent?.trim() || el.getAttribute('aria-label') || '未命名按钮');

      try {
        const startTime = Date.now();
        await button.click();
        await page.waitForTimeout(500); // 等待响应
        const responseTime = Date.now() - startTime;

        // 检查是否有视觉反馈
        const hasActiveState = await button.evaluate(el => {
          const styles = window.getComputedStyle(el);
          return styles.cursor === 'pointer';
        });

        interactions.push({
          type: 'button',
          element: buttonText,
          responseTime,
          hasActiveState,
          status: 'success',
        });
      } catch (err) {
        interactions.push({
          type: 'button',
          element: buttonText,
          status: 'error',
          error: err.message,
        });
      }
    }
  } catch (err) {
    log(`按钮测试失败: ${err.message}`, 'red');
  }

  // 测试链接
  try {
    const links = await page.$$('a[href]');
    log(`找到 ${links.length} 个链接`, 'cyan');

    for (let i = 0; i < Math.min(links.length, 5); i++) {
      const link = links[i];
      const linkText = await link.evaluate(el => el.textContent?.trim() || el.href);
      const href = await link.evaluate(el => el.getAttribute('href'));

      // 检查链接样式
      const hasHoverStyle = await link.evaluate(el => {
        const styles = window.getComputedStyle(el);
        return styles.cursor === 'pointer' || styles.textDecoration.includes('underline');
      });

      interactions.push({
        type: 'link',
        element: linkText,
        href,
        hasHoverStyle,
        status: 'success',
      });
    }
  } catch (err) {
    log(`链接测试失败: ${err.message}`, 'red');
  }

  // 测试表单输入
  try {
    const inputs = await page.$$('input:not([type="hidden"])');
    log(`找到 ${inputs.length} 个输入框`, 'cyan');

    for (let i = 0; i < Math.min(inputs.length, 3); i++) {
      const input = inputs[i];
      const inputType = await input.evaluate(el => el.type);
      const placeholder = await input.evaluate(el => el.placeholder);

      try {
        await input.click();
        await input.type('测试输入');
        await page.waitForTimeout(100);
        const value = await input.evaluate(el => el.value);

        interactions.push({
          type: 'input',
          inputType,
          placeholder,
          canType: value.includes('测试输入'),
          status: 'success',
        });

        await input.evaluate(el => el.value = ''); // 清空
      } catch (err) {
        interactions.push({
          type: 'input',
          inputType,
          status: 'error',
          error: err.message,
        });
      }
    }
  } catch (err) {
    log(`输入框测试失败: ${err.message}`, 'red');
  }

  return interactions;
}

/**
 * 检测性能指标
 */
async function checkPerformance(page) {
  const metrics = await page.metrics();
  const performance = await page.evaluate(() => {
    const perf = window.performance;
    const timing = perf.timing;

    return {
      domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
      loadComplete: timing.loadEventEnd - timing.navigationStart,
      firstPaint: perf.getEntriesByType('paint')[0]?.startTime || 0,
      domNodes: document.querySelectorAll('*').length,
      scripts: document.querySelectorAll('script').length,
      stylesheets: document.querySelectorAll('link[rel="stylesheet"]').length,
    };
  });

  return {
    ...performance,
    jsHeapSize: Math.round(metrics.JSHeapUsedSize / 1024 / 1024 * 100) / 100, // MB
    layoutDuration: Math.round(metrics.LayoutDuration * 100) / 100,
    recalcStyleDuration: Math.round(metrics.RecalcStyleDuration * 100) / 100,
  };
}

/**
 * 检测控制台错误和警告
 */
async function monitorConsole(page) {
  const logs = {
    errors: [],
    warnings: [],
    info: [],
  };

  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();

    if (type === 'error') {
      logs.errors.push(text);
    } else if (type === 'warning') {
      logs.warnings.push(text);
    }
  });

  page.on('pageerror', error => {
    logs.errors.push(`Page Error: ${error.message}`);
  });

  return logs;
}

/**
 * 检测布局问题
 */
async function checkLayout(page) {
  const issues = [];

  // 检查重叠元素
  const overlappingElements = await page.evaluate(() => {
    const elements = Array.from(document.querySelectorAll('*'));
    const overlaps = [];

    for (let i = 0; i < elements.length - 1; i++) {
      const rect1 = elements[i].getBoundingClientRect();
      if (rect1.width === 0 || rect1.height === 0) continue;

      for (let j = i + 1; j < Math.min(i + 10, elements.length); j++) {
        const rect2 = elements[j].getBoundingClientRect();
        if (rect2.width === 0 || rect2.height === 0) continue;

        // 检查是否重叠
        const overlap = !(
          rect1.right < rect2.left ||
          rect1.left > rect2.right ||
          rect1.bottom < rect2.top ||
          rect1.top > rect2.bottom
        );

        if (overlap && window.getComputedStyle(elements[i]).position !== 'absolute') {
          overlaps.push({
            element1: elements[i].tagName + '.' + elements[i].className,
            element2: elements[j].tagName + '.' + elements[j].className,
          });
          break;
        }
      }

      if (overlaps.length >= 5) break;
    }

    return overlaps;
  });

  if (overlappingElements.length > 0) {
    issues.push({
      severity: 'medium',
      type: 'layout',
      message: `发现 ${overlappingElements.length} 对可能重叠的元素`,
      details: overlappingElements,
      recommendation: '检查 CSS 布局，避免元素意外重叠',
    });
  }

  // 检查过小的点击目标
  const tinyTargets = await page.evaluate(() => {
    const clickable = document.querySelectorAll('button, a, input, [onclick]');
    const tiny = [];

    clickable.forEach(el => {
      const rect = el.getBoundingClientRect();
      if ((rect.width > 0 && rect.width < 44) || (rect.height > 0 && rect.height < 44)) {
        tiny.push({
          tag: el.tagName,
          text: el.textContent?.trim().substring(0, 30) || '',
          width: Math.round(rect.width),
          height: Math.round(rect.height),
        });
      }
    });

    return tiny.slice(0, 10);
  });

  if (tinyTargets.length > 0) {
    issues.push({
      severity: 'medium',
      type: 'usability',
      message: `发现 ${tinyTargets.length} 个点击目标过小（建议最小 44x44px）`,
      details: tinyTargets,
      recommendation: '增加可点击元素的尺寸或内边距',
    });
  }

  return issues;
}

/**
 * 生成报告
 */
function generateReport(results) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const reportPath = path.join(REPORT_DIR, `ui-test-report-${timestamp}.md`);

  let report = `# UI 交互测试报告\n\n`;
  report += `**生成时间**: ${new Date().toLocaleString('zh-CN')}\n\n`;
  report += `---\n\n`;

  results.forEach((result, index) => {
    report += `## ${index + 1}. ${result.pageName}\n\n`;
    report += `**URL**: ${result.url}\n\n`;

    // 性能指标
    report += `### 📊 性能指标\n\n`;
    report += `| 指标 | 数值 | 状态 |\n`;
    report += `|------|------|------|\n`;
    report += `| DOM 加载时间 | ${result.performance.domContentLoaded}ms | ${result.performance.domContentLoaded < 1000 ? '✅' : '⚠️'} |\n`;
    report += `| 页面完全加载 | ${result.performance.loadComplete}ms | ${result.performance.loadComplete < 2000 ? '✅' : '⚠️'} |\n`;
    report += `| 首次绘制 | ${Math.round(result.performance.firstPaint)}ms | ${result.performance.firstPaint < 500 ? '✅' : '⚠️'} |\n`;
    report += `| DOM 节点数 | ${result.performance.domNodes} | ${result.performance.domNodes < 1500 ? '✅' : '⚠️'} |\n`;
    report += `| JS 堆内存 | ${result.performance.jsHeapSize} MB | ${result.performance.jsHeapSize < 50 ? '✅' : '⚠️'} |\n`;
    report += `\n`;

    // 控制台日志
    if (result.console.errors.length > 0 || result.console.warnings.length > 0) {
      report += `### ⚠️ 控制台问题\n\n`;

      if (result.console.errors.length > 0) {
        report += `**错误 (${result.console.errors.length}):**\n\n`;
        result.console.errors.forEach(err => {
          report += `- ❌ ${err}\n`;
        });
        report += `\n`;
      }

      if (result.console.warnings.length > 0) {
        report += `**警告 (${result.console.warnings.length}):**\n\n`;
        result.console.warnings.forEach(warn => {
          report += `- ⚠️ ${warn}\n`;
        });
        report += `\n`;
      }
    }

    // 交互测试
    report += `### 🖱️ 交互测试\n\n`;
    report += `**测试的交互元素**: ${result.interactions.length}\n\n`;

    const successfulInteractions = result.interactions.filter(i => i.status === 'success').length;
    const successRate = result.interactions.length > 0
      ? Math.round(successfulInteractions / result.interactions.length * 100)
      : 0;

    report += `**成功率**: ${successRate}% (${successfulInteractions}/${result.interactions.length})\n\n`;

    if (result.interactions.some(i => i.status === 'error')) {
      report += `**失败的交互:**\n\n`;
      result.interactions
        .filter(i => i.status === 'error')
        .forEach(i => {
          report += `- ❌ ${i.type}: ${i.element || '未知'} - ${i.error}\n`;
        });
      report += `\n`;
    }

    // 响应式测试
    report += `### 📱 响应式设计\n\n`;
    result.responsiveness.forEach(resp => {
      const status = !resp.hasHorizontalScroll && resp.overflowCount === 0 ? '✅' : '⚠️';
      report += `**${resp.viewport} (${resp.width}px)**: ${status}\n`;
      if (resp.hasHorizontalScroll) {
        report += `- ⚠️ 出现水平滚动条\n`;
      }
      if (resp.overflowCount > 0) {
        report += `- ⚠️ ${resp.overflowCount} 个元素溢出视口\n`;
      }
      report += `\n`;
    });

    // 可访问性问题
    if (result.accessibility.length > 0) {
      report += `### ♿ 可访问性问题\n\n`;
      result.accessibility.forEach(issue => {
        const icon = issue.severity === 'high' ? '🔴' : issue.severity === 'medium' ? '🟡' : '🟢';
        report += `${icon} **${issue.type}** (${issue.severity})\n`;
        report += `- 问题: ${issue.message}\n`;
        report += `- 建议: ${issue.recommendation}\n\n`;
      });
    }

    // 布局问题
    if (result.layoutIssues.length > 0) {
      report += `### 📐 布局问题\n\n`;
      result.layoutIssues.forEach(issue => {
        const icon = issue.severity === 'high' ? '🔴' : issue.severity === 'medium' ? '🟡' : '🟢';
        report += `${icon} **${issue.type}** (${issue.severity})\n`;
        report += `- 问题: ${issue.message}\n`;
        report += `- 建议: ${issue.recommendation}\n\n`;
      });
    }

    report += `---\n\n`;
  });

  // 总结和建议
  report += `## 📋 总结和改进建议\n\n`;

  const allIssues = results.flatMap(r => [
    ...r.accessibility.map(i => ({ ...i, page: r.pageName })),
    ...r.layoutIssues.map(i => ({ ...i, page: r.pageName })),
  ]);

  const highPriority = allIssues.filter(i => i.severity === 'high');
  const mediumPriority = allIssues.filter(i => i.severity === 'medium');

  report += `### 🔴 高优先级问题 (${highPriority.length})\n\n`;
  if (highPriority.length > 0) {
    highPriority.forEach(issue => {
      report += `- **[${issue.page}]** ${issue.message}\n`;
      report += `  - 建议: ${issue.recommendation}\n\n`;
    });
  } else {
    report += `✅ 无高优先级问题\n\n`;
  }

  report += `### 🟡 中优先级问题 (${mediumPriority.length})\n\n`;
  if (mediumPriority.length > 0) {
    mediumPriority.forEach(issue => {
      report += `- **[${issue.page}]** ${issue.message}\n`;
      report += `  - 建议: ${issue.recommendation}\n\n`;
    });
  } else {
    report += `✅ 无中优先级问题\n\n`;
  }

  // 性能建议
  report += `### ⚡ 性能优化建议\n\n`;
  const avgLoadTime = results.reduce((sum, r) => sum + r.performance.loadComplete, 0) / results.length;
  const avgDomNodes = results.reduce((sum, r) => sum + r.performance.domNodes, 0) / results.length;

  if (avgLoadTime > 2000) {
    report += `- ⚠️ 平均加载时间 ${Math.round(avgLoadTime)}ms 偏慢，建议优化资源加载\n`;
  }
  if (avgDomNodes > 1500) {
    report += `- ⚠️ 平均 DOM 节点数 ${Math.round(avgDomNodes)} 较多，考虑虚拟滚动或懒加载\n`;
  }

  report += `\n---\n\n`;
  report += `**测试完成时间**: ${new Date().toLocaleString('zh-CN')}\n`;

  fs.writeFileSync(reportPath, report, 'utf8');
  return reportPath;
}

/**
 * 主测试函数
 */
async function runTests() {
  log('='.repeat(60), 'cyan');
  log('UI 交互测试开始', 'cyan');
  log('='.repeat(60), 'cyan');

  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: { width: 1920, height: 1080 },
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const results = [];

  for (const testPage of TEST_PAGES) {
    log(`\n测试页面: ${testPage.name}`, 'blue');
    log(`URL: ${testPage.url}`, 'blue');

    const page = await browser.newPage();
    const consoleLogs = await monitorConsole(page);

    try {
      const url = `${BASE_URL}${testPage.url}`;

      log('  [1/6] 加载页面...', 'yellow');
      await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
      await page.waitForTimeout(1000);

      log('  [2/6] 检测性能指标...', 'yellow');
      const performance = await checkPerformance(page);

      log('  [3/6] 测试交互响应...', 'yellow');
      const interactions = await checkInteractivity(page, testPage.selectors);

      log('  [4/6] 检测响应式设计...', 'yellow');
      const responsiveness = await checkResponsiveness(page, url);

      log('  [5/6] 检测可访问性...', 'yellow');
      const accessibility = await checkAccessibility(page);

      log('  [6/6] 检测布局问题...', 'yellow');
      const layoutIssues = await checkLayout(page);

      results.push({
        pageName: testPage.name,
        url: testPage.url,
        performance,
        interactions,
        responsiveness,
        accessibility,
        layoutIssues,
        console: consoleLogs,
      });

      log(`  ✅ ${testPage.name} 测试完成`, 'green');

    } catch (error) {
      log(`  ❌ ${testPage.name} 测试失败: ${error.message}`, 'red');
      results.push({
        pageName: testPage.name,
        url: testPage.url,
        error: error.message,
        performance: {},
        interactions: [],
        responsiveness: [],
        accessibility: [],
        layoutIssues: [],
        console: consoleLogs,
      });
    } finally {
      await page.close();
    }
  }

  await browser.close();

  log('\n' + '='.repeat(60), 'cyan');
  log('生成测试报告...', 'cyan');
  const reportPath = generateReport(results);
  log(`报告已生成: ${reportPath}`, 'green');
  log('='.repeat(60), 'cyan');
}

// 运行测试
runTests().catch(console.error);
