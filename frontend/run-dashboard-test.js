/**
 * Dashboard 自动化测试运行器
 * 使用 Puppeteer 启动浏览器并运行测试
 */

const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  console.log('🚀 启动 Dashboard 测试...\n');

  let browser;
  try {
    browser = await puppeteer.launch({
      headless: false, // 显示浏览器窗口
      devtools: false,
      defaultViewport: {
        width: 1920,
        height: 1080
      }
    });

    const page = await browser.newPage();

    // 监听控制台输出
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();

      // 过滤掉不重要的日志
      if (text.includes('Download the React DevTools')) return;
      if (text.includes('Webpack')) return;
      if (text.includes('[HMR]')) return;

      // 美化输出
      if (type === 'log') {
        console.log(text);
      } else if (type === 'error') {
        // 跳过 API 错误，我们已经知道后端没运行
        if (!text.includes('Failed to fetch') && !text.includes('Network request failed')) {
          console.error('❌', text);
        }
      } else if (type === 'warning') {
        console.warn('⚠️ ', text);
      }
    });

    // 监听页面错误（但忽略 API 错误）
    page.on('pageerror', error => {
      if (!error.message.includes('fetch') && !error.message.includes('Network')) {
        console.error('💥 页面错误:', error.message);
      }
    });

    console.log('📡 连接到 http://localhost:3000 ...\n');

    // 导航到 Dashboard
    try {
      await page.goto('http://localhost:3000', {
        waitUntil: 'networkidle0',
        timeout: 30000
      });
    } catch (navError) {
      console.log('⚠️  页面加载超时，但继续测试（可能是 API 调用导致）\n');
    }

    // 等待页面基本渲染
    await page.waitForTimeout(3000);

    console.log('🧪 执行测试脚本...\n');

    // 读取测试脚本
    const testScript = fs.readFileSync('d:\\git\\1108\\frontend\\test-dashboard.js', 'utf-8');

    // 在页面中执行测试
    const results = await page.evaluate(testScript);

    // 截图
    const screenshotPath = 'd:\\git\\1108\\frontend\\dashboard-test-screenshot.png';
    await page.screenshot({
      path: screenshotPath,
      fullPage: true
    });
    console.log(`\n📸 截图已保存: ${screenshotPath}`);

    // 额外的 DOM 检查
    console.log('\n📊 DOM 结构分析:');

    const domInfo = await page.evaluate(() => {
      return {
        // 侧边栏
        sidebar: {
          exists: !!document.querySelector('aside'),
          width: document.querySelector('aside')?.offsetWidth || 0,
          menuItems: document.querySelectorAll('aside a, aside button').length
        },
        // KPI 卡片
        statCards: {
          count: document.querySelectorAll('[data-testid^="dashboard-stat-card"]').length,
          hasTarget: Array.from(document.querySelectorAll('[data-testid^="dashboard-stat-card"]'))
            .some(card => card.textContent.includes('预算') || card.textContent.includes('目标'))
        },
        // 趋势图
        chart: {
          exists: !!document.querySelector('.recharts-wrapper, svg'),
          tabs: document.querySelectorAll('[role="tab"]').length,
          tabsHaveValues: Array.from(document.querySelectorAll('[role="tab"]'))
            .some(tab => /¥[\d,]+/.test(tab.textContent))
        },
        // Top 列表
        topLists: {
          tableCount: document.querySelectorAll('table').length,
          firstTableRows: document.querySelector('table tbody')?.querySelectorAll('tr').length || 0
        },
        // 告警
        alerts: {
          count: document.querySelectorAll('[class*="alert"]').length,
          isChinese: /[\u4e00-\u9fa5]/.test(document.body.textContent)
        },
        // 金额格式
        currency: {
          hasWrongFormat: /¥\d+\.?\d*w/i.test(document.body.textContent),
          hasStandardFormat: /¥[\d,]+/.test(document.body.textContent),
          hasWanFormat: /¥?[\d.]+\s*万/.test(document.body.textContent)
        }
      };
    });

    console.log('\n🔍 详细检查结果:');
    console.log('');

    // 侧边栏
    console.log('【侧边栏】');
    console.log(`  存在: ${domInfo.sidebar.exists ? '✅' : '❌'}`);
    console.log(`  宽度: ${domInfo.sidebar.width}px`);
    console.log(`  菜单项: ${domInfo.sidebar.menuItems} 个`);
    console.log('');

    // KPI 卡片
    console.log('【KPI 卡片】');
    console.log(`  数量: ${domInfo.statCards.count} ${domInfo.statCards.count === 4 ? '✅' : '❌'}`);
    console.log(`  包含目标/预算: ${domInfo.statCards.hasTarget ? '✅' : '⚠️  未集成'}`);
    console.log('');

    // 趋势图
    console.log('【趋势图】');
    console.log(`  存在: ${domInfo.chart.exists ? '✅' : '❌'}`);
    console.log(`  Tab 数量: ${domInfo.chart.tabs}`);
    console.log(`  Tab 显示数值: ${domInfo.chart.tabsHaveValues ? '✅' : '⚠️  未集成'}`);
    console.log('');

    // Top 列表
    console.log('【Top 列表】');
    console.log(`  表格数量: ${domInfo.topLists.tableCount}`);
    console.log(`  首个表格行数: ${domInfo.topLists.firstTableRows}`);
    console.log(`  状态: ${domInfo.topLists.tableCount >= 2 ? '✅ 已集成' : '⚠️  待集成'}`);
    console.log('');

    // 告警
    console.log('【告警提示】');
    console.log(`  数量: ${domInfo.alerts.count}`);
    console.log(`  中文文案: ${domInfo.alerts.isChinese ? '✅' : '❌'}`);
    console.log('');

    // 金额格式
    console.log('【金额格式】');
    console.log(`  无错误格式(¥XXw): ${!domInfo.currency.hasWrongFormat ? '✅' : '❌'}`);
    console.log(`  标准千分位: ${domInfo.currency.hasStandardFormat ? '✅' : '❌'}`);
    console.log(`  使用"万"单位: ${domInfo.currency.hasWanFormat ? '✅' : '未使用'}`);
    console.log('');

    // 改进建议
    console.log('\n💡 改进建议:');
    const suggestions = [];

    if (!domInfo.statCards.hasTarget) {
      suggestions.push('• KPI 卡片需要集成 target 属性以显示预算/目标');
    }
    if (!domInfo.chart.tabsHaveValues) {
      suggestions.push('• 趋势图 Tab 需要显示聚合数值（如"消耗 ¥125.7k"）');
    }
    if (domInfo.topLists.tableCount < 2) {
      suggestions.push('• 需要在趋势图下方添加 TopLists 组件（消耗Top5 + ROAS最差Top5）');
    }
    if (domInfo.currency.hasWrongFormat) {
      suggestions.push('• 修正金额格式，使用"万"替代"w"');
    }

    if (suggestions.length === 0) {
      console.log('  🎉 所有改造项都已完成！');
    } else {
      suggestions.forEach(s => console.log(s));
    }

    console.log('\n✨ 测试完成！浏览器窗口将保持打开状态供你检查。');
    console.log('   按 Ctrl+C 退出。\n');

    // 保持浏览器打开
    await new Promise(() => {});

  } catch (error) {
    console.error('\n💥 测试执行失败:', error.message);
    console.error(error.stack);
  } finally {
    // 不关闭浏览器，让用户可以手动检查
    // if (browser) await browser.close();
  }
})();
