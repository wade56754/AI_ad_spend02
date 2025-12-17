// Check page layout structure
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();

  await page.goto('http://localhost:3000', { waitUntil: 'networkidle0' });

  // Wait a bit for React to render
  await page.waitForTimeout(2000);

  // Check DOM structure
  const structure = await page.evaluate(() => {
    const body = document.body;
    const html = document.documentElement;

    // Find layout elements
    const sidebar = document.querySelector('aside');
    const mainContent = document.querySelector('main');
    const appLayout = document.querySelector('div.flex.h-screen');

    return {
      bodyClasses: body.className,
      htmlClasses: html.className,
      hasSidebar: !!sidebar,
      sidebarDisplay: sidebar ? window.getComputedStyle(sidebar).display : 'not found',
      sidebarWidth: sidebar ? window.getComputedStyle(sidebar).width : 'not found',
      sidebarClasses: sidebar ? sidebar.className : 'not found',
      hasMain: !!mainContent,
      hasAppLayout: !!appLayout,
      appLayoutClasses: appLayout ? appLayout.className : 'not found',
      bodyHTML: body.innerHTML.substring(0, 500),
      childrenCount: body.children.length,
      firstChildTag: body.children[0]?.tagName,
      firstChildClasses: body.children[0]?.className,
    };
  });

  console.log('DOM Structure Analysis:');
  console.log(JSON.stringify(structure, null, 2));

  // Take a screenshot
  await page.screenshot({ path: 'd:\\git\\1108\\frontend\\layout-check.png', fullPage: true });

  await browser.close();
})();
