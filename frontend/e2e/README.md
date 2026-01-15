# E2E 测试文档

> **Puppeteer + Chrome DevTools 端到端自动化测试**
>
> 本文档说明如何使用 Puppeteer 进行端到端测试和性能分析。

---

## 📋 目录

- [快速开始](#快速开始)
- [测试框架组成](#测试框架组成)
- [运行测试](#运行测试)
- [编写测试](#编写测试)
- [页面对象模型](#页面对象模型)
- [性能测试](#性能测试)
- [调试测试](#调试测试)
- [最佳实践](#最佳实践)

---

## 快速开始

### 1. 运行 E2E 测试

```bash
# 运行所有 E2E 测试（无头模式）
pnpm run test:e2e

# 显示浏览器窗口运行
pnpm run test:e2e:headed

# 调试模式（显示浏览器、慢放、打开 DevTools）
pnpm run test:e2e:debug

# 只运行性能测试
pnpm run test:performance
```

### 2. 目录结构

```
frontend/e2e/
├── jest.config.js              # E2E Jest 配置
├── setup/                      # 全局设置
│   ├── global-setup.ts         # 启动开发服务器
│   ├── global-teardown.ts      # 清理服务器
│   └── setup.ts                # 环境变量设置
├── utils/                      # 工具函数
│   ├── helpers.ts              # 测试辅助函数
│   └── performance.ts          # 性能测试工具
├── pages/                      # 页面对象模型
│   ├── BasePage.ts             # 基础页面类
│   ├── LoginPage.ts            # 登录页面
│   └── DashboardPage.ts        # 仪表盘页面
└── tests/                      # 测试用例
    ├── auth/                   # 认证测试
    │   └── login.e2e.ts
    └── performance/            # 性能测试
        └── dashboard-performance.e2e.ts
```

---

## 测试框架组成

### 核心技术栈

| 工具                         | 版本     | 用途         |
| ---------------------------- | -------- | ------------ |
| **Puppeteer**                | ^24.32.1 | 浏览器自动化 |
| **Jest**                     | ^29.7.0  | 测试运行器   |
| **Chrome DevTools Protocol** | -        | 性能分析     |

### 关键特性

✅ **无头/有头模式切换**：通过环境变量控制
✅ **页面对象模型 (POM)**：封装页面交互逻辑
✅ **性能监控**：Core Web Vitals 指标收集
✅ **自动截图**：失败时自动保存截图
✅ **Network Mock**：模拟 API 响应
✅ **等待工具**：智能等待元素/导航/API

---

## 运行测试

### 命令详解

```bash
# 基础命令
pnpm run test:e2e                 # 无头模式运行所有 E2E 测试
pnpm run test:e2e:headed          # 显示浏览器窗口
pnpm run test:e2e:debug           # 调试模式（慢放 + DevTools）

# 性能测试
pnpm run test:performance         # 运行性能测试

# 运行特定测试
pnpm run test:e2e -- login.e2e.ts

# 运行所有测试（单元 + E2E）
pnpm run test:all
```

### 环境变量

```bash
# 控制浏览器显示
HEADLESS=false pnpm run test:e2e

# 慢放模式（ms）
SLOWMO=100 pnpm run test:e2e

# 打开 DevTools
DEVTOOLS=true pnpm run test:e2e

# 自定义 BASE_URL
BASE_URL=http://localhost:4000 pnpm run test:e2e
```

---

## 编写测试

### 基础测试结构

```typescript
import { Browser, Page } from 'puppeteer';
import { LoginPage } from '../../pages/LoginPage';

describe('登录测试', () => {
  let browser: Browser;
  let page: Page;
  let loginPage: LoginPage;

  beforeAll(async () => {
    browser = await global.__BROWSER__;
  });

  beforeEach(async () => {
    page = await browser.newPage();
    loginPage = new LoginPage(page);
  });

  afterEach(async () => {
    await page.close();
  });

  it('应该成功登录', async () => {
    await loginPage.navigate();
    await loginPage.login('admin@example.com', 'password123');

    expect(await loginPage.isLoginSuccessful()).toBe(true);
  }, 60000);
});
```

### 使用页面对象

```typescript
// 推荐：使用页面对象封装交互
await loginPage.login('admin@example.com', 'password');

// 不推荐：直接操作页面
await page.type('#email', 'admin@example.com');
await page.type('#password', 'password');
await page.click('button[type="submit"]');
```

---

## 页面对象模型

### BasePage 基础类

所有页面对象继承 `BasePage`，提供通用方法：

```typescript
class MyPage extends BasePage {
  async navigate() {
    await this.goto('/my-page');
  }

  async clickButton() {
    await this.click('[data-testid="my-button"]');
  }

  async getText() {
    return this.getText('[data-testid="my-text"]');
  }
}
```

### 可用方法

- `goto(path)` - 导航到页面
- `click(selector)` - 点击元素
- `fill(selector, value)` - 填写输入框
- `getText(selector)` - 获取文本
- `exists(selector)` - 检查元素是否存在
- `isVisible(selector)` - 检查元素是否可见
- `screenshot(name)` - 截图
- `waitForElement(selector)` - 等待元素出现
- `waitForText(text)` - 等待文本出现
- `clearStorage()` - 清除浏览器存储

### 创建新页面对象

```typescript
// e2e/pages/MyPage.ts
import { BasePage } from './BasePage';

export class MyPage extends BasePage {
  private selectors = {
    title: 'h1',
    button: 'button[data-testid="submit"]',
  };

  async navigate() {
    await this.goto('/my-page');
  }

  async getTitle(): Promise<string> {
    return this.getText(this.selectors.title);
  }

  async clickSubmit() {
    await this.click(this.selectors.button);
  }
}
```

---

## 性能测试

### 使用 PerformanceTester

```typescript
import { PerformanceTester } from '../../utils/performance';

it('应该有良好的加载性能', async () => {
  const perfTester = new PerformanceTester(page);

  await perfTester.startPerformanceMonitoring();
  await dashboardPage.navigate();

  const metrics = await perfTester.collectPerformanceMetrics();

  // 验证 Core Web Vitals
  expect(metrics.FCP).toBeLessThan(1800); // First Contentful Paint
  expect(metrics.LCP).toBeLessThan(2500); // Largest Contentful Paint
  expect(metrics.CLS).toBeLessThan(0.1); // Cumulative Layout Shift

  // 生成报告
  await perfTester.saveReport(metrics, 'dashboard');
}, 60000);
```

### 性能指标说明

| 指标    | 说明         | 优秀标准 |
| ------- | ------------ | -------- |
| **FCP** | 首次内容渲染 | < 1800ms |
| **LCP** | 最大内容渲染 | < 2500ms |
| **CLS** | 累积布局偏移 | < 0.1    |
| **TTI** | 可交互时间   | < 3800ms |
| **TBT** | 总阻塞时间   | < 300ms  |

### 性能报告

性能测试会自动生成 Markdown 报告，保存在 `e2e/reports/` 目录：

```markdown
# 性能测试报告 - dashboard

## Core Web Vitals

| 指标 | 值        | 评分    |
| ---- | --------- | ------- |
| FCP  | 1234.56ms | ✅ 优秀 |
| LCP  | 2100.00ms | ✅ 优秀 |
| CLS  | 0.05      | ✅ 优秀 |

## 资源统计

- 总请求数: 45
- 总大小: 2.34 MB
```

---

## 调试测试

### 1. 使用调试模式

```bash
pnpm run test:e2e:debug
```

此模式会：

- ✅ 显示浏览器窗口
- ✅ 慢放操作（100ms 延迟）
- ✅ 自动打开 Chrome DevTools

### 2. 手动截图

```typescript
await loginPage.screenshot('login-before-submit');
await loginPage.clickSubmit();
await loginPage.screenshot('login-after-submit');
```

截图保存在 `e2e/screenshots/` 目录。

### 3. 查看控制台日志

```typescript
page.on('console', (msg) => {
  console.log('浏览器日志:', msg.text());
});
```

### 4. 暂停执行

```typescript
await page.waitForTimeout(5000); // 暂停 5 秒
```

### 5. 使用 page.evaluate 调试

```typescript
const value = await page.evaluate(() => {
  console.log('当前 URL:', window.location.href);
  console.log('LocalStorage:', localStorage.getItem('auth-token'));
  return document.querySelector('h1')?.textContent;
});
console.log('页面标题:', value);
```

---

## 最佳实践

### ✅ 推荐做法

1. **使用页面对象模型**

   ```typescript
   // ✅ 好
   await loginPage.login('user@example.com', 'password');

   // ❌ 避免
   await page.type('#email', 'user@example.com');
   ```

2. **等待元素就绪**

   ```typescript
   // ✅ 好
   await loginPage.waitForElement('button[type="submit"]');
   await loginPage.click('button[type="submit"]');

   // ❌ 避免（可能失败）
   await loginPage.click('button[type="submit"]');
   ```

3. **每个测试独立**

   ```typescript
   beforeEach(async () => {
     await loginPage.clearStorage(); // 清除状态
   });
   ```

4. **使用描述性选择器**

   ```typescript
   // ✅ 好
   '[data-testid="login-button"]';
   'button[type="submit"]';

   // ❌ 避免
   'button:nth-child(3)';
   '.btn-123abc';
   ```

5. **合理设置超时**
   ```typescript
   it('测试用例', async () => {
     // 测试逻辑
   }, 60000); // 60秒超时
   ```

### ❌ 避免的做法

1. 不要在测试中使用固定延迟（`sleep`）
2. 不要依赖测试执行顺序
3. 不要在测试中修改共享状态
4. 不要测试第三方库的功能
5. 不要忽略失败的测试

---

## 工具函数参考

### helpers.ts

```typescript
import * as helpers from '../utils/helpers';

// 等待导航
await helpers.waitForNavigation(page);

// 等待元素
await helpers.waitForElement(page, 'button');

// 等待文本
await helpers.waitForText(page, '登录成功');

// 填写输入
await helpers.fillInput(page, '#email', 'test@example.com');

// 截图
await helpers.takeScreenshot(page, 'test-screenshot');

// 检查元素存在
const exists = await helpers.elementExists(page, '.error');

// 等待 API 响应
const data = await helpers.waitForApiResponse(page, '/api/login');

// Mock API
await helpers.mockApiResponse(page, '/api/users', { users: [] });

// 清除存储
await helpers.clearBrowserStorage(page);

// 设置 LocalStorage
await helpers.setLocalStorage(page, 'token', 'abc123');
```

---

## 常见问题

### Q: 测试运行很慢怎么办？

A: 尝试以下优化：

```bash
# 1. 并行运行测试
pnpm run test:e2e -- --maxWorkers=4

# 2. 使用无头模式
pnpm run test:e2e  # 默认无头

# 3. 只运行必要的测试
pnpm run test:e2e -- login.e2e.ts
```

### Q: 如何调试失败的测试？

A: 使用调试模式：

```bash
pnpm run test:e2e:debug -- login.e2e.ts
```

或在测试中添加截图：

```typescript
await page.screenshot({ path: 'debug.png', fullPage: true });
```

### Q: 如何测试需要登录的页面？

A: 使用 `beforeEach` 钩子：

```typescript
beforeEach(async () => {
  await loginPage.navigate();
  await loginPage.login('admin@example.com', 'password');
});
```

或直接设置 auth token：

```typescript
await page.evaluate(() => {
  localStorage.setItem('auth-token', 'mock-token');
});
```

### Q: 如何处理弹窗/对话框？

A: 监听 dialog 事件：

```typescript
page.on('dialog', async (dialog) => {
  await dialog.accept(); // 或 dialog.dismiss()
});
```

### Q: 如何测试文件上传？

A: 使用 `uploadFile` 方法：

```typescript
const filePath = path.join(__dirname, 'test-file.jpg');
const input = await page.$('input[type="file"]');
await input.uploadFile(filePath);
```

---

## 参考资源

### 官方文档

- [Puppeteer 文档](https://pptr.dev/)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
- [Web Vitals](https://web.dev/vitals/)

### 内部文档

- [测试模板](../tests/README.md)
- [性能测试工具](./utils/performance.ts)
- [页面对象基类](./pages/BasePage.ts)

---

## 获取帮助

遇到问题时：

1. 查看本文档的常见问题部分
2. 查看示例测试 `e2e/tests/auth/login.e2e.ts`
3. 使用调试模式运行测试
4. 查看截图和日志输出
