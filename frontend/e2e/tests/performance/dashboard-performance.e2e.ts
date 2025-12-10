/**
 * 仪表盘性能测试
 * 使用 Chrome DevTools Protocol 测试页面性能
 */

import { Browser, Page } from 'puppeteer'
import { DashboardPage } from '../../pages/DashboardPage'
import { LoginPage } from '../../pages/LoginPage'
import { PerformanceTester } from '../../utils/performance'

describe('仪表盘页面性能测试', () => {
  let browser: Browser
  let page: Page
  let dashboardPage: DashboardPage
  let loginPage: LoginPage
  let perfTester: PerformanceTester

  beforeAll(async () => {
    browser = await global.__BROWSER__
  })

  beforeEach(async () => {
    page = await browser.newPage()
    dashboardPage = new DashboardPage(page)
    loginPage = new LoginPage(page)
    perfTester = new PerformanceTester(page)

    // 登录（性能测试需要已登录状态）
    await loginPage.navigate()
    await loginPage.login('admin@example.com', 'Admin123!')
    await page.waitForTimeout(2000)
  })

  afterEach(async () => {
    await perfTester.stopPerformanceMonitoring()
    await page.close()
  })

  describe('页面加载性能', () => {
    it('应该在合理时间内完成首次内容渲染 (FCP)', async () => {
      await perfTester.startPerformanceMonitoring()

      // 导航到仪表盘
      await dashboardPage.navigate()

      // 收集性能指标
      const metrics = await perfTester.collectPerformanceMetrics()

      // 验证 FCP < 1800ms (Core Web Vitals 优秀标准)
      expect(metrics.FCP).toBeLessThan(1800)

      console.log(`📊 FCP: ${metrics.FCP.toFixed(2)}ms`)

      // 生成报告
      await perfTester.saveReport(metrics, 'dashboard-initial-load')
    }, 60000)

    it('应该在合理时间内完成最大内容渲染 (LCP)', async () => {
      await perfTester.startPerformanceMonitoring()

      await dashboardPage.navigate()

      const metrics = await perfTester.collectPerformanceMetrics()

      // 验证 LCP < 2500ms (Core Web Vitals 优秀标准)
      expect(metrics.LCP).toBeLessThan(2500)

      console.log(`📊 LCP: ${metrics.LCP.toFixed(2)}ms`)
    }, 60000)

    it('应该有较低的累积布局偏移 (CLS)', async () => {
      await perfTester.startPerformanceMonitoring()

      await dashboardPage.navigate()

      const metrics = await perfTester.collectPerformanceMetrics()

      // 验证 CLS < 0.1 (Core Web Vitals 优秀标准)
      expect(metrics.CLS).toBeLessThan(0.1)

      console.log(`📊 CLS: ${metrics.CLS.toFixed(4)}`)
    }, 60000)

    it('应该在合理时间内完成 DOM 加载', async () => {
      await perfTester.startPerformanceMonitoring()

      await dashboardPage.navigate()

      const metrics = await perfTester.collectPerformanceMetrics()

      // DOM Content Loaded 应该 < 3000ms
      expect(metrics.domContentLoaded).toBeLessThan(3000)

      console.log(`📊 DOM Content Loaded: ${metrics.domContentLoaded.toFixed(2)}ms`)
    }, 60000)
  })

  describe('资源加载性能', () => {
    it('应该限制资源请求数量', async () => {
      await perfTester.startPerformanceMonitoring()

      await dashboardPage.navigate()

      const metrics = await perfTester.collectPerformanceMetrics()

      // 验证总请求数 < 100
      expect(metrics.resourceStats.totalRequests).toBeLessThan(100)

      console.log(`📊 总请求数: ${metrics.resourceStats.totalRequests}`)
      console.log(`📊 总大小: ${(metrics.resourceStats.totalSize / 1024 / 1024).toFixed(2)} MB`)
    }, 60000)

    it('应该限制总资源大小', async () => {
      await perfTester.startPerformanceMonitoring()

      await dashboardPage.navigate()

      const metrics = await perfTester.collectPerformanceMetrics()

      // 验证总大小 < 5MB
      const totalSizeMB = metrics.resourceStats.totalSize / 1024 / 1024
      expect(totalSizeMB).toBeLessThan(5)

      console.log(`📊 总资源大小: ${totalSizeMB.toFixed(2)} MB`)
    }, 60000)

    it('应该优化脚本和样式表加载', async () => {
      await perfTester.startPerformanceMonitoring()

      await dashboardPage.navigate()

      const metrics = await perfTester.collectPerformanceMetrics()

      // 检查 JS 和 CSS 资源
      const jsStats = metrics.resourceStats.byType['script'] || { count: 0, size: 0 }
      const cssStats = metrics.resourceStats.byType['stylesheet'] || { count: 0, size: 0 }

      console.log(`📊 JS 文件: ${jsStats.count} 个, ${(jsStats.size / 1024).toFixed(2)} KB`)
      console.log(`📊 CSS 文件: ${cssStats.count} 个, ${(cssStats.size / 1024).toFixed(2)} KB`)

      // JS 文件总大小应该 < 1MB
      expect(jsStats.size).toBeLessThan(1024 * 1024)

      // CSS 文件总大小应该 < 500KB
      expect(cssStats.size).toBeLessThan(500 * 1024)
    }, 60000)
  })

  describe('交互性能', () => {
    it('应该快速响应用户交互', async () => {
      await dashboardPage.navigate()

      // 测量点击统计卡片的响应时间
      const startTime = Date.now()

      // 模拟用户交互（如果有可点击元素）
      if (await dashboardPage.hasStatsCards()) {
        await dashboardPage.click('[data-testid="stats-card"]:first-child')
      }

      const endTime = Date.now()
      const interactionTime = endTime - startTime

      // 交互响应时间应该 < 100ms
      expect(interactionTime).toBeLessThan(100)

      console.log(`📊 交互响应时间: ${interactionTime}ms`)
    }, 60000)
  })

  describe('导航性能', () => {
    it('应该快速导航到不同页面', async () => {
      await dashboardPage.navigate()

      // 测量导航到日报页面的时间
      const startTime = Date.now()
      await dashboardPage.goToDailyReports()
      const endTime = Date.now()

      const navigationTime = endTime - startTime

      // 导航时间应该 < 2000ms
      expect(navigationTime).toBeLessThan(2000)

      console.log(`📊 导航耗时: ${navigationTime}ms`)
    }, 60000)
  })

  describe('完整性能报告', () => {
    it('应该生成完整的性能报告', async () => {
      await perfTester.startPerformanceMonitoring()

      await dashboardPage.navigate()

      const metrics = await perfTester.collectPerformanceMetrics()

      // 生成详细报告
      const reportPath = await perfTester.saveReport(metrics, 'dashboard-full-report')

      expect(reportPath).toBeTruthy()

      // 打印关键指标
      console.log('\n📊 === 性能测试报告 ===')
      console.log(`FCP: ${metrics.FCP.toFixed(2)}ms`)
      console.log(`LCP: ${metrics.LCP.toFixed(2)}ms`)
      console.log(`CLS: ${metrics.CLS.toFixed(4)}`)
      console.log(`TTI: ${metrics.TTI.toFixed(2)}ms`)
      console.log(`DOM Content Loaded: ${metrics.domContentLoaded.toFixed(2)}ms`)
      console.log(`Load Complete: ${metrics.loadComplete.toFixed(2)}ms`)
      console.log(`总请求数: ${metrics.resourceStats.totalRequests}`)
      console.log(`总大小: ${(metrics.resourceStats.totalSize / 1024 / 1024).toFixed(2)} MB`)
      console.log(`报告已保存: ${reportPath}`)
      console.log('=========================\n')
    }, 60000)
  })
})
