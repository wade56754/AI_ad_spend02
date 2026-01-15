import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E 测试配置
 *
 * 基于: AI_TEST_GUIDE_v2.1.md
 *
 * 运行方式:
 *   1. 先启动前端: cd frontend && pnpm run dev
 *   2. 再运行测试: npx playwright test
 *
 * 或使用 webServer 自动启动 (需要在 frontend 目录下运行):
 *   npx playwright test --config=../playwright.config.ts
 */

export default defineConfig({
  // 测试目录
  testDir: './__tests__/e2e',

  // 测试文件匹配模式
  testMatch: '**/*.spec.ts',

  // 完全并行运行测试
  fullyParallel: true,

  // 失败时不重试（CI 中可以设置重试）
  retries: process.env.CI ? 2 : 0,

  // 并行工作进程数
  workers: process.env.CI ? 1 : undefined,

  // 报告器
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
  ],

  // 全局设置
  use: {
    // 基础 URL
    baseURL: process.env.BASE_URL || 'http://localhost:3000',

    // 截图设置
    screenshot: 'only-on-failure',

    // 视频录制（仅失败时）
    video: 'retain-on-failure',

    // 追踪设置
    trace: 'retain-on-failure',

    // 默认超时
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },

  // 全局超时
  timeout: 60000,

  // 预期超时
  expect: {
    timeout: 10000,
  },

  // 项目配置（浏览器）
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // 可以添加更多浏览器
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // 开发服务器（可选，运行测试前启动）
  // 注意: 在开发时建议手动启动 dev server，CI 环境会自动启动
  webServer: process.env.CI ? {
    command: 'cd frontend && pnpm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: false,
    timeout: 120000,
  } : undefined,
});
