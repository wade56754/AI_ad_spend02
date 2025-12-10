/**
 * Dashboard 全面测试脚本
 *
 * 在浏览器 Console 中运行，测试所有关键功能点
 */

(function() {
  console.clear();
  console.log('%c=== Dashboard 全面测试 ===', 'color: blue; font-size: 16px; font-weight: bold');
  console.log('');

  const results = {
    pass: [],
    fail: [],
    warning: []
  };

  function test(name, condition, details = '') {
    if (condition) {
      results.pass.push(name);
      console.log(`%c✅ ${name}`, 'color: green', details);
    } else {
      results.fail.push(name);
      console.log(`%c❌ ${name}`, 'color: red', details);
    }
  }

  function warn(name, message) {
    results.warning.push(name);
    console.log(`%c⚠️  ${name}`, 'color: orange', message);
  }

  // ===== 1. 布局与导航 =====
  console.log('\n%c【1. 布局与导航测试】', 'color: blue; font-weight: bold');

  const sidebar = document.querySelector('aside');
  test('侧边栏存在', !!sidebar, sidebar ? `宽度: ${window.getComputedStyle(sidebar).width}` : '');

  if (sidebar) {
    const sidebarStyle = window.getComputedStyle(sidebar);
    test('侧边栏可见', sidebarStyle.display !== 'none' && sidebarStyle.visibility !== 'hidden');

    const menuItems = sidebar.querySelectorAll('[role="button"], a, button');
    test('菜单项数量 > 5', menuItems.length > 5, `找到 ${menuItems.length} 个菜单项`);
  }

  const mainContent = document.querySelector('main');
  test('主内容区域存在', !!mainContent);

  const appLayout = document.querySelector('div.flex.h-screen');
  test('AppLayout 容器存在', !!appLayout);

  // ===== 2. 页头与筛选器 =====
  console.log('\n%c【2. 页头与筛选器测试】', 'color: blue; font-weight: bold');

  const welcomeTitle = document.querySelector('[data-testid="dashboard-welcome-title"]') ||
                       document.querySelector('h1');
  test('欢迎标题存在', !!welcomeTitle, welcomeTitle?.textContent);

  // 检查筛选器 - 可能是 GlobalDateFilter 或 GlobalFilters
  const dateFilter = document.querySelector('[role="combobox"]') ||
                     document.querySelectorAll('button[role="combobox"]')[0];
  test('日期筛选器存在', !!dateFilter);

  const filterButtons = document.querySelectorAll('button[role="combobox"]');
  if (filterButtons.length >= 2) {
    test('多维度筛选器 (≥2个)', true, `找到 ${filterButtons.length} 个筛选器`);
  } else {
    warn('多维度筛选', '只找到 1 个筛选器，可能尚未升级为 GlobalFilters');
  }

  // ===== 3. 告警提示条 =====
  console.log('\n%c【3. 告警提示条测试】', 'color: blue; font-weight: bold');

  const alerts = document.querySelectorAll('[class*="alert"], [class*="banner"]');
  if (alerts.length > 0) {
    test('告警提示条存在', true, `找到 ${alerts.length} 个告警`);

    // 检查是否有中文文案
    const alertText = Array.from(alerts).map(a => a.textContent).join(' ');
    test('告警文案为中文', /[\u4e00-\u9fa5]/.test(alertText));

    // 检查严重等级标识
    const hasEmoji = /[🔴🟠🟡]/.test(alertText);
    test('告警有等级标识', hasEmoji || alertText.includes('紧急') || alertText.includes('需关注'));
  } else {
    warn('告警提示条', '当前无告警显示（可能是正常状态）');
  }

  // ===== 4. KPI 卡片 =====
  console.log('\n%c【4. KPI 卡片测试】', 'color: blue; font-weight: bold');

  const statCards = document.querySelectorAll('[data-testid^="dashboard-stat-card"]') ||
                    document.querySelectorAll('[class*="StatCard"], [class*="stat-card"]');
  test('KPI 卡片数量 = 4', statCards.length === 4, `找到 ${statCards.length} 个卡片`);

  if (statCards.length > 0) {
    // 检查第一个卡片的结构
    const firstCard = statCards[0];
    const hasIcon = firstCard.querySelector('svg') || firstCard.querySelector('[class*="icon"]');
    test('卡片包含图标', !!hasIcon);

    const hasValue = /¥|[\d,]+/.test(firstCard.textContent);
    test('卡片包含数值', hasValue);

    const hasChange = /[+-]?\d+\.?\d*%/.test(firstCard.textContent);
    test('卡片包含变化百分比', hasChange);

    const has7dAvg = firstCard.textContent.includes('7日均值') ||
                     firstCard.textContent.includes('7天均值');
    test('卡片包含 7日均值', has7dAvg);

    // 检查是否有目标/预算信息 (新功能)
    const hasTarget = firstCard.textContent.includes('预算') ||
                      firstCard.textContent.includes('目标') ||
                      firstCard.textContent.includes('ROAS');
    if (hasTarget) {
      test('卡片包含目标/预算 (新)', true);
    } else {
      warn('目标/预算', 'KPI 卡片尚未显示目标/预算信息');
    }

    // 检查卡片交互性
    const isClickable = firstCard.style.cursor === 'pointer' ||
                        firstCard.onclick !== null ||
                        window.getComputedStyle(firstCard).cursor === 'pointer';
    test('KPI 卡片可点击', isClickable);
  }

  // ===== 5. 趋势图 =====
  console.log('\n%c【5. 趋势图测试】', 'color: blue; font-weight: bold');

  const trendChart = document.querySelector('[id*="trend"]') ||
                     document.querySelector('.recharts-wrapper') ||
                     document.querySelector('svg');
  test('趋势图存在', !!trendChart);

  if (trendChart) {
    // 检查 Tab 切换
    const tabs = document.querySelectorAll('[role="tab"], [class*="tab"]');
    test('趋势图有 Tab 切换', tabs.length >= 3, `找到 ${tabs.length} 个 Tab`);

    // 检查是否有数据解读文案
    const summary = document.querySelector('[class*="summary"]') ||
                    Array.from(document.querySelectorAll('p, div')).find(
                      el => el.textContent.includes('日均') || el.textContent.includes('较')
                    );
    test('趋势图有数据解读', !!summary, summary?.textContent.substring(0, 50));

    // 检查 Tab 是否显示聚合数值 (新功能)
    const tabText = Array.from(tabs).map(t => t.textContent).join(' ');
    const hasTabValue = /¥[\d,]+/.test(tabText) || /\d+k/.test(tabText);
    if (hasTabValue) {
      test('Tab 显示聚合数值 (新)', true);
    } else {
      warn('Tab 聚合数值', 'Tab 尚未显示当前数值');
    }
  }

  // ===== 6. 待办事项 =====
  console.log('\n%c【6. 待办事项测试】', 'color: blue; font-weight: bold');

  const pendingSection = document.querySelector('[id*="pending"]') ||
                         document.querySelector('[class*="pending"]') ||
                         Array.from(document.querySelectorAll('h2, h3')).find(
                           el => el.textContent.includes('待处理') || el.textContent.includes('待办')
                         )?.closest('section, div');

  test('待办事项区域存在', !!pendingSection);

  if (pendingSection) {
    const taskItems = pendingSection.querySelectorAll('[class*="task"], li, [role="listitem"]');
    test('待办项目 > 0', taskItems.length > 0, `找到 ${taskItems.length} 个待办项`);

    // 检查优先级标识
    const taskText = pendingSection.textContent;
    const hasPriority = taskText.includes('高') || taskText.includes('中') ||
                        taskText.includes('低') || /🔴|🟠|🟡/.test(taskText);
    test('待办有优先级标识', hasPriority);
  }

  // ===== 7. Top 列表 (新功能) =====
  console.log('\n%c【7. Top 列表测试 (新)】', 'color: blue; font-weight: bold');

  const tables = document.querySelectorAll('table');
  if (tables.length >= 2) {
    test('Top 列表区域存在', true, `找到 ${tables.length} 个表格`);

    const firstTable = tables[0];
    const headers = firstTable.querySelectorAll('th');
    test('表格有列头', headers.length >= 5, `${headers.length} 列`);

    const rows = firstTable.querySelectorAll('tbody tr');
    test('表格有数据行', rows.length > 0, `${rows.length} 行`);

    // 检查是否有 ROAS 列
    const headerText = Array.from(headers).map(h => h.textContent).join(' ');
    test('表格包含 ROAS 列', headerText.includes('ROAS'));
  } else if (tables.length === 1) {
    warn('Top 列表', '只找到 1 个表格，可能 Top 列表尚未集成');
  } else {
    warn('Top 列表', 'Top 列表区域不存在（尚未集成）');
  }

  // ===== 8. 金额格式 =====
  console.log('\n%c【8. 金额格式测试】', 'color: blue; font-weight: bold');

  const bodyText = document.body.textContent;

  // 检查是否有不规范的单位
  const hasW = /¥\d+(\.\d+)?w/i.test(bodyText);
  test('无不规范单位 (¥XXw)', !hasW, hasW ? '发现 ¥XXw 格式' : '');

  // 检查标准格式
  const hasStandardFormat = /¥[\d,]+/.test(bodyText);
  test('使用标准千分位格式', hasStandardFormat);

  const hasWanFormat = /¥?[\d.]+\s*万/.test(bodyText);
  if (hasWanFormat) {
    test('使用"万"单位', true);
  }

  // ===== 9. 响应式布局 =====
  console.log('\n%c【9. 响应式布局测试】', 'color: blue; font-weight: bold');

  const viewport = {
    width: window.innerWidth,
    height: window.innerHeight
  };
  test('视口尺寸', true, `${viewport.width}x${viewport.height}`);

  const isMobile = viewport.width < 768;
  const isTablet = viewport.width >= 768 && viewport.width < 1024;
  const isDesktop = viewport.width >= 1024;

  console.log(`  当前设备: ${isMobile ? '手机' : isTablet ? '平板' : '桌面'}`);

  if (statCards.length > 0) {
    const cardGrid = statCards[0].closest('[class*="grid"]');
    if (cardGrid) {
      const gridStyle = window.getComputedStyle(cardGrid);
      test('卡片使用 Grid 布局', gridStyle.display === 'grid');
    }
  }

  // ===== 10. 性能检查 =====
  console.log('\n%c【10. 性能检查】', 'color: blue; font-weight: bold');

  const imageCount = document.querySelectorAll('img').length;
  const svgCount = document.querySelectorAll('svg').length;

  console.log(`  图片数量: ${imageCount}`);
  console.log(`  SVG 数量: ${svgCount}`);

  if (performance && performance.timing) {
    const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
    test('页面加载时间 < 3s', loadTime < 3000, `${loadTime}ms`);
  }

  // ===== 总结 =====
  console.log('\n%c=== 测试总结 ===', 'color: blue; font-size: 16px; font-weight: bold');
  console.log(`%c✅ 通过: ${results.pass.length}`, 'color: green; font-weight: bold');
  console.log(`%c❌ 失败: ${results.fail.length}`, 'color: red; font-weight: bold');
  console.log(`%c⚠️  警告: ${results.warning.length}`, 'color: orange; font-weight: bold');

  if (results.fail.length > 0) {
    console.log('\n%c失败项目:', 'color: red; font-weight: bold');
    results.fail.forEach(item => console.log(`  - ${item}`));
  }

  if (results.warning.length > 0) {
    console.log('\n%c警告项目:', 'color: orange; font-weight: bold');
    results.warning.forEach(item => console.log(`  - ${item}`));
  }

  // 导出结果供进一步分析
  window.dashboardTestResults = results;
  console.log('\n结果已保存到 window.dashboardTestResults');

  return results;
})();
