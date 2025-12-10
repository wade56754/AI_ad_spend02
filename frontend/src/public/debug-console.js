// 在浏览器控制台运行此脚本以诊断问题
// 复制整个文件内容，粘贴到 Chrome DevTools Console 中执行

console.log('=== 开始诊断 ===\n');

// 1. 检查侧边栏
console.log('1. 侧边栏检查:');
const sidebar = document.querySelector('aside');
if (sidebar) {
  const styles = window.getComputedStyle(sidebar);
  console.log('  ✓ 侧边栏元素存在');
  console.log('  - display:', styles.display);
  console.log('  - width:', styles.width);
  console.log('  - visibility:', styles.visibility);
  console.log('  - position:', styles.position);
  console.log('  - z-index:', styles.zIndex);
  console.log('  - background:', styles.background);
  console.log('  - className:', sidebar.className);
} else {
  console.log('  ✗ 侧边栏元素不存在！');
}

// 2. 检查 AppLayout
console.log('\n2. AppLayout 检查:');
const appLayout = document.querySelector('div.flex.h-screen');
if (appLayout) {
  const styles = window.getComputedStyle(appLayout);
  console.log('  ✓ AppLayout 存在');
  console.log('  - display:', styles.display);
  console.log('  - flex-direction:', styles.flexDirection);
  console.log('  - children count:', appLayout.children.length);
  Array.from(appLayout.children).forEach((child, i) => {
    console.log(`  - child ${i}:`, child.tagName, child.className);
  });
} else {
  console.log('  ✗ AppLayout 不存在！');
}

// 3. 检查主内容区域
console.log('\n3. 主内容区域检查:');
const main = document.querySelector('main');
if (main) {
  console.log('  ✓ main 元素存在');
  console.log('  - className:', main.className);
} else {
  console.log('  ✗ main 元素不存在！');
}

// 4. 检查用户信息
console.log('\n4. 用户信息检查:');
const welcomeTitle = document.querySelector('[data-testid="dashboard-welcome-title"]');
if (welcomeTitle) {
  console.log('  ✓ 欢迎标题存在');
  console.log('  - 内容:', welcomeTitle.textContent);
} else {
  console.log('  ✗ 欢迎标题不存在');
}

// 5. 检查 LocalStorage
console.log('\n5. LocalStorage 检查:');
console.log('  - auth_token:', localStorage.getItem('auth_token') ? '存在' : '不存在');
console.log('  - auth_user:', localStorage.getItem('auth_user') ? '存在' : '不存在');

// 6. 检查 React 错误
console.log('\n6. React 挂载检查:');
const root = document.getElementById('__next');
if (root) {
  console.log('  ✓ Next.js root 存在');
  console.log('  - children count:', root.children.length);
} else {
  console.log('  ✗ Next.js root 不存在！');
}

// 7. 检查所有 aside 元素（可能有多个）
console.log('\n7. 所有 aside 元素:');
const allAsides = document.querySelectorAll('aside');
console.log('  - 找到', allAsides.length, '个 aside 元素');
allAsides.forEach((aside, i) => {
  const styles = window.getComputedStyle(aside);
  console.log(`  aside ${i}:`, {
    display: styles.display,
    width: styles.width,
    className: aside.className,
  });
});

// 8. 检查 body 结构
console.log('\n8. Body 结构:');
console.log('  - body children:', document.body.children.length);
Array.from(document.body.children).forEach((child, i) => {
  console.log(`  child ${i}:`, child.tagName, child.id, child.className.substring(0, 50));
});

console.log('\n=== 诊断完成 ===');
console.log('\n如果侧边栏元素存在但不可见，请检查 CSS 样式问题');
console.log('如果侧边栏元素不存在，说明 AppLayout 没有正确渲染');
