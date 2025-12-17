/**
 * Jest Puppeteer 配置
 * 用于 E2E 测试的 Puppeteer 启动选项
 */

module.exports = {
  launch: {
    // 浏览器启动配置
    headless: process.env.HEADLESS !== 'false', // 默认无头模式，可通过 HEADLESS=false 显示浏览器
    slowMo: process.env.SLOWMO ? parseInt(process.env.SLOWMO) : 0, // 慢放模式，方便调试
    devtools: process.env.DEVTOOLS === 'true', // 是否打开 DevTools

    // 浏览器参数
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--disable-gpu',
      '--window-size=1920,1080',
      '--disable-web-security', // 禁用同源策略（仅测试环境）
    ],

    // 超时设置
    timeout: 30000,

    // 默认视口
    defaultViewport: {
      width: 1920,
      height: 1080,
    },
  },

  // 浏览器上下文配置
  browserContext: 'default',

  // 是否在每个测试后退出浏览器
  exitOnPageError: false,
}
