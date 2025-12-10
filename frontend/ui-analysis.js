/**
 * 简化版 UI 分析脚本
 * 使用 Puppeteer 检测 UI 页面、交互和性能
 */

const puppeteer = require('puppeteer');
const fs = require('fs');

const BASE_URL = 'http://localhost:3000';

async function analyzeUI() {
  console.log('启动浏览器...');
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: { width: 1920, height: 1080 },
  });

  const page = await browser.newPage();

  // 监控控制台
  const consoleLogs = { errors: [], warnings: [] };
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    if (type === 'error') consoleLogs.errors.push(text);
    if (type === 'warning') consoleLogs.warnings.push(text);
  });

  console.log('访问仪表盘页面...');
  await page.goto(BASE_URL, { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForTimeout(2000);

  console.log('收集页面信息...');

  // 1. 基本页面结构
  const pageStructure = await page.evaluate(() => {
    return {
      title: document.title,
      url: location.href,
      hasSidebar: !!document.querySelector('nav'),
      hasHeader: !!document.querySelector('header'),
      hasMain: !!document.querySelector('main'),
      domNodes: document.querySelectorAll('*').length,
    };
  });

  // 2. 性能指标
  const performance = await page.evaluate(() => {
    const perf = window.performance;
    const timing = perf.timing;
    const paintEntries = perf.getEntriesByType('paint');

    return {
      domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
      loadComplete: timing.loadEventEnd - timing.navigationStart,
      firstPaint: paintEntries[0]?.startTime || 0,
      firstContentfulPaint: paintEntries[1]?.startTime || 0,
    };
  });

  // 3. 交互元素统计
  const interactiveElements = await page.evaluate(() => {
    const buttons = document.querySelectorAll('button');
    const links = document.querySelectorAll('a');
    const inputs = document.querySelectorAll('input');

    return {
      buttons: buttons.length,
      links: links.length,
      inputs: inputs.length,
      buttonsWithText: Array.from(buttons).filter(b => b.textContent.trim()).length,
      linksWithText: Array.from(links).filter(a => a.textContent.trim()).length,
    };
  });

  // 4. 侧边栏菜单项
  const sidebarMenu = await page.evaluate(() => {
    const menuItems = document.querySelectorAll('nav a');
    return Array.from(menuItems).map(item => ({
      text: item.textContent.trim(),
      href: item.getAttribute('href'),
      isActive: item.classList.contains('bg-blue') || item.className.includes('blue'),
    }));
  });

  // 5. 测试仪表盘统计卡片
  const statCards = await page.evaluate(() => {
    const cards = document.querySelectorAll('[class*="stat"], [class*="card"]');
    return {
      count: cards.length,
      visible: Array.from(cards).filter(c => {
        const rect = c.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      }).length,
    };
  });

  // 6. 响应式测试
  console.log('测试响应式布局...');
  const responsiveTest = [];

  for (const viewport of [
    { name: '手机', width: 375, height: 667 },
    { name: '平板', width: 768, height: 1024 },
    { name: '桌面', width: 1920, height: 1080 },
  ]) {
    await page.setViewport(viewport);
    await page.waitForTimeout(500);

    const hasScroll = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });

    responsiveTest.push({
      ...viewport,
      hasHorizontalScroll: hasScroll,
    });
  }

  // 恢复桌面视口
  await page.setViewport({ width: 1920, height: 1080 });
  await page.goto(BASE_URL, { waitUntil: 'networkidle2' });
  await page.waitForTimeout(1000);

  // 7. 测试侧边栏菜单点击
  console.log('测试侧边栏导航...');
  const navigationTest = [];

  const menuLinks = await page.$$('nav a[href]');
  for (let i = 0; i < Math.min(menuLinks.length, 3); i++) {
    const link = menuLinks[i];
    const text = await link.evaluate(el => el.textContent.trim());
    const href = await link.evaluate(el => el.getAttribute('href'));

    try {
      await link.click();
      await page.waitForTimeout(1000);

      const newUrl = await page.url();
      navigationTest.push({
        menuItem: text,
        expectedHref: href,
        actualUrl: newUrl,
        success: newUrl.includes(href) || (href === '/' && newUrl === BASE_URL + '/'),
      });

      // 返回首页
      if (i < menuLinks.length - 1) {
        await page.goto(BASE_URL, { waitUntil: 'networkidle2' });
        await page.waitForTimeout(500);
      }
    } catch (err) {
      navigationTest.push({
        menuItem: text,
        expectedHref: href,
        error: err.message,
        success: false,
      });
    }
  }

  // 8. UI 问题检测
  const uiIssues = await page.evaluate(() => {
    const issues = [];

    // 检查过小的点击目标
    const clickables = document.querySelectorAll('button, a');
    let tinyButtons = 0;
    clickables.forEach(el => {
      const rect = el.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0 && (rect.width < 44 || rect.height < 44)) {
        tinyButtons++;
      }
    });
    if (tinyButtons > 0) {
      issues.push({
        type: 'usability',
        severity: 'medium',
        message: `${tinyButtons} 个按钮/链接小于推荐尺寸 44x44px`,
      });
    }

    // 检查缺少 alt 的图片
    const imgsWithoutAlt = document.querySelectorAll('img:not([alt])').length;
    if (imgsWithoutAlt > 0) {
      issues.push({
        type: 'accessibility',
        severity: 'medium',
        message: `${imgsWithoutAlt} 张图片缺少 alt 属性`,
      });
    }

    // 检查对比度
    const darkText = Array.from(document.querySelectorAll('*')).filter(el => {
      const style = window.getComputedStyle(el);
      const color = style.color;
      const bg = style.backgroundColor;
      return color && bg && color.includes('128, 128, 128'); // 灰色文本
    });
    if (darkText.length > 10) {
      issues.push({
        type: 'accessibility',
        severity: 'low',
        message: '部分文本可能对比度不足',
      });
    }

    return issues;
  });

  await browser.close();

  // 生成报告
  const report = {
    timestamp: new Date().toISOString(),
    pageStructure,
    performance,
    interactiveElements,
    sidebarMenu,
    statCards,
    responsiveTest,
    navigationTest,
    uiIssues,
    console: consoleLogs,
  };

  // 生成 Markdown 报告
  let markdown = `# UI 分析报告\n\n`;
  markdown += `**生成时间**: ${new Date().toLocaleString('zh-CN')}\n\n`;
  markdown += `---\n\n`;

  markdown += `## 📄 页面基本信息\n\n`;
  markdown += `- **标题**: ${pageStructure.title}\n`;
  markdown += `- **URL**: ${pageStructure.url}\n`;
  markdown += `- **侧边栏**: ${pageStructure.hasSidebar ? '✅ 存在' : '❌ 缺失'}\n`;
  markdown += `- **顶部栏**: ${pageStructure.hasHeader ? '✅ 存在' : '❌ 缺失'}\n`;
  markdown += `- **主内容区**: ${pageStructure.hasMain ? '✅ 存在' : '❌ 缺失'}\n`;
  markdown += `- **DOM 节点数**: ${pageStructure.domNodes}\n\n`;

  markdown += `## ⚡ 性能指标\n\n`;
  markdown += `| 指标 | 数值 | 评估 |\n`;
  markdown += `|------|------|------|\n`;
  markdown += `| DOM 加载时间 | ${performance.domContentLoaded}ms | ${performance.domContentLoaded < 1000 ? '✅ 优秀' : performance.domContentLoaded < 2000 ? '⚠️ 良好' : '❌ 需优化'} |\n`;
  markdown += `| 页面完全加载 | ${performance.loadComplete}ms | ${performance.loadComplete < 2000 ? '✅ 优秀' : performance.loadComplete < 3000 ? '⚠️ 良好' : '❌ 需优化'} |\n`;
  markdown += `| 首次绘制 | ${Math.round(performance.firstPaint)}ms | ${performance.firstPaint < 500 ? '✅ 优秀' : performance.firstPaint < 1000 ? '⚠️ 良好' : '❌ 需优化'} |\n`;
  markdown += `| 首次内容绘制 | ${Math.round(performance.firstContentfulPaint)}ms | ${performance.firstContentfulPaint < 1000 ? '✅ 优秀' : performance.firstContentfulPaint < 2000 ? '⚠️ 良好' : '❌ 需优化'} |\n\n`;

  markdown += `## 🖱️ 交互元素统计\n\n`;
  markdown += `- **按钮**: ${interactiveElements.buttons} 个 (${interactiveElements.buttonsWithText} 个有文本)\n`;
  markdown += `- **链接**: ${interactiveElements.links} 个 (${interactiveElements.linksWithText} 个有文本)\n`;
  markdown += `- **输入框**: ${interactiveElements.inputs} 个\n\n`;

  if (interactiveElements.buttons - interactiveElements.buttonsWithText > 0) {
    markdown += `⚠️ **注意**: ${interactiveElements.buttons - interactiveElements.buttonsWithText} 个按钮没有可见文本，建议添加 aria-label\n\n`;
  }

  markdown += `## 📊 仪表盘内容\n\n`;
  markdown += `- **统计卡片**: ${statCards.count} 个\n`;
  markdown += `- **可见卡片**: ${statCards.visible} 个\n\n`;

  markdown += `## 🧭 侧边栏导航菜单\n\n`;
  if (sidebarMenu.length > 0) {
    markdown += `共 ${sidebarMenu.length} 个菜单项:\n\n`;
    sidebarMenu.forEach((item, i) => {
      const activeIcon = item.isActive ? '🔵' : '⚪';
      markdown += `${i + 1}. ${activeIcon} **${item.text}** → \`${item.href}\`\n`;
    });
    markdown += `\n`;
  } else {
    markdown += `❌ 未检测到侧边栏菜单项\n\n`;
  }

  markdown += `## 📱 响应式测试\n\n`;
  responsiveTest.forEach(test => {
    const status = test.hasHorizontalScroll ? '❌ 出现水平滚动' : '✅ 正常';
    markdown += `- **${test.name}** (${test.width}x${test.height}): ${status}\n`;
  });
  markdown += `\n`;

  markdown += `## 🔗 导航测试\n\n`;
  navigationTest.forEach((test, i) => {
    const icon = test.success ? '✅' : '❌';
    markdown += `${i + 1}. ${icon} **${test.menuItem}**\n`;
    markdown += `   - 预期路径: \`${test.expectedHref}\`\n`;
    if (test.error) {
      markdown += `   - 错误: ${test.error}\n`;
    } else {
      markdown += `   - 实际 URL: \`${test.actualUrl}\`\n`;
    }
    markdown += `\n`;
  });

  markdown += `## ⚠️ UI 问题\n\n`;
  if (uiIssues.length > 0) {
    uiIssues.forEach(issue => {
      const icon = issue.severity === 'high' ? '🔴' : issue.severity === 'medium' ? '🟡' : '🟢';
      markdown += `${icon} **${issue.type}** (${issue.severity})\n`;
      markdown += `- ${issue.message}\n\n`;
    });
  } else {
    markdown += `✅ 未发现明显 UI 问题\n\n`;
  }

  markdown += `## 📋 控制台日志\n\n`;
  if (consoleLogs.errors.length > 0) {
    markdown += `### ❌ 错误 (${consoleLogs.errors.length})\n\n`;
    consoleLogs.errors.forEach(err => {
      markdown += `- ${err}\n`;
    });
    markdown += `\n`;
  }
  if (consoleLogs.warnings.length > 0) {
    markdown += `### ⚠️ 警告 (${consoleLogs.warnings.length})\n\n`;
    consoleLogs.warnings.forEach(warn => {
      markdown += `- ${warn}\n`;
    });
    markdown += `\n`;
  }
  if (consoleLogs.errors.length === 0 && consoleLogs.warnings.length === 0) {
    markdown += `✅ 无控制台错误或警告\n\n`;
  }

  markdown += `---\n\n`;
  markdown += `## 🎯 改进建议\n\n`;

  const suggestions = [];

  if (performance.loadComplete > 3000) {
    suggestions.push('🔴 **高优先级**: 页面加载时间超过 3 秒，建议优化资源加载、启用代码分割');
  }

  if (responsiveTest.some(t => t.hasHorizontalScroll)) {
    suggestions.push('🟡 **中优先级**: 部分视口出现水平滚动，检查 CSS 布局和容器宽度');
  }

  if (uiIssues.some(i => i.type === 'accessibility')) {
    suggestions.push('🟡 **中优先级**: 存在可访问性问题，建议添加适当的 ARIA 标签和 alt 属性');
  }

  if (interactiveElements.buttons - interactiveElements.buttonsWithText > 5) {
    suggestions.push('🟡 **中优先级**: 多个按钮缺少可见文本，影响可用性');
  }

  if (pageStructure.domNodes > 2000) {
    suggestions.push('🟢 **低优先级**: DOM 节点数较多，考虑使用虚拟滚动优化长列表');
  }

  if (suggestions.length > 0) {
    suggestions.forEach(s => markdown += `${s}\n\n`);
  } else {
    markdown += `✅ 当前页面质量良好，暂无重要改进建议\n\n`;
  }

  markdown += `---\n\n`;
  markdown += `**报告生成完成**: ${new Date().toLocaleString('zh-CN')}\n`;

  // 保存报告
  const reportFile = `ui-analysis-report-${Date.now()}.md`;
  fs.writeFileSync(reportFile, markdown, 'utf8');

  console.log('\n' + '='.repeat(60));
  console.log(`✅ UI 分析完成！`);
  console.log(`📄 报告已保存: ${reportFile}`);
  console.log('='.repeat(60));

  // 同时保存 JSON
  fs.writeFileSync(reportFile.replace('.md', '.json'), JSON.stringify(report, null, 2), 'utf8');
}

analyzeUI().catch(err => {
  console.error('❌ 分析失败:', err);
  process.exit(1);
});
