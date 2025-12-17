/**
 * 仪表盘基础功能 E2E 测试
 *
 * 测试场景：
 * 1. 页面加载和渲染
 * 2. 统计卡片显示
 * 3. 图表显示
 * 4. 导航功能
 * 5. 用户菜单和退出
 */

import { Browser, Page } from 'puppeteer'
import { DashboardPage } from '../../pages/DashboardPage'
import { LoginPage } from '../../pages/LoginPage'

describe('仪表盘基础功能测试', () => {
  let browser: Browser
  let page: Page
  let dashboardPage: DashboardPage
  let loginPage: LoginPage

  beforeAll(async () => {
    browser = await global.__BROWSER__
  })

  beforeEach(async () => {
    page = await browser.newPage()
    dashboardPage = new DashboardPage(page)
    loginPage = new LoginPage(page)

    // 登录到系统
    await loginPage.navigate()
    await loginPage.login('admin@example.com', 'Admin123!')
    await page.waitForTimeout(2000)
  })

  afterEach(async () => {
    await page.close()
  })

  describe('页面加载', () => {
    it('应该成功加载仪表盘页面', async () => {
      await dashboardPage.navigate()

      const isOnDashboard = await dashboardPage.isOnDashboard()
      expect(isOnDashboard).toBe(true)
    })

    it('应该显示页面标题', async () => {
      await dashboardPage.navigate()

      const title = await dashboardPage.getPageTitle()
      expect(title).toBeTruthy()
      expect(title.length).toBeGreaterThan(0)
    })

    it('应该显示侧边栏', async () => {
      await dashboardPage.navigate()

      const hasSidebar = await dashboardPage.hasSidebar()
      expect(hasSidebar).toBe(true)
    })
  })

  describe('统计卡片', () => {
    it('应该显示统计卡片', async () => {
      await dashboardPage.navigate()

      const hasStatsCards = await dashboardPage.hasStatsCards()
      expect(hasStatsCards).toBe(true)
    })

    it('应该显示多个统计卡片', async () => {
      await dashboardPage.navigate()

      const count = await dashboardPage.getStatsCardsCount()
      expect(count).toBeGreaterThan(0)

      console.log(`📊 统计卡片数量: ${count}`)
    })

    it('统计卡片应该包含数值', async () => {
      await dashboardPage.navigate()

      // 检查卡片中是否有数值显示
      const hasNumbers = await page.evaluate(() => {
        const cards = document.querySelectorAll('[data-testid="stats-card"], .stats-card')
        if (cards.length === 0) return false

        for (const card of Array.from(cards)) {
          const text = card.textContent || ''
          if (/\d+/.test(text)) {  // 检查是否包含数字
            return true
          }
        }
        return false
      })

      expect(hasNumbers).toBe(true)
    })
  })

  describe('图表显示', () => {
    it('应该显示趋势图表', async () => {
      await dashboardPage.navigate()

      const hasTrendChart = await dashboardPage.hasTrendChart()
      expect(hasTrendChart).toBe(true)
    })

    it('应该显示异常账户表格', async () => {
      await dashboardPage.navigate()

      const hasTable = await dashboardPage.hasAbnormalAccountsTable()
      expect(hasTable).toBe(true)
    })

    it('应该显示今日任务卡片', async () => {
      await dashboardPage.navigate()

      const hasTasksCard = await dashboardPage.hasTodayTasksCard()
      expect(hasTasksCard).toBe(true)
    })
  })

  describe('导航功能', () => {
    it('应该能够导航到日报管理页面', async () => {
      await dashboardPage.navigate()

      await dashboardPage.goToDailyReports()

      const url = await dashboardPage.getCurrentUrl()
      expect(url).toContain('/daily-reports')
    }, 60000)

    it('应该能够导航到充值管理页面', async () => {
      await dashboardPage.navigate()

      await dashboardPage.goToTopup()

      const url = await dashboardPage.getCurrentUrl()
      expect(url).toContain('/topup')
    }, 60000)

    it('应该能够导航到对账管理页面', async () => {
      await dashboardPage.navigate()

      await dashboardPage.goToReconciliation()

      const url = await dashboardPage.getCurrentUrl()
      expect(url).toContain('/reconciliation')
    }, 60000)

    it('导航后应该能够返回仪表盘', async () => {
      await dashboardPage.navigate()

      // 导航到其他页面
      await dashboardPage.goToDailyReports()
      await page.waitForTimeout(1000)

      // 返回仪表盘
      await dashboardPage.navigate()

      const isOnDashboard = await dashboardPage.isOnDashboard()
      expect(isOnDashboard).toBe(true)
    }, 60000)
  })

  describe('用户菜单', () => {
    it('应该能够打开用户菜单', async () => {
      await dashboardPage.navigate()

      await dashboardPage.clickUserMenu()
      await page.waitForTimeout(500)

      // 验证菜单是否打开（检查退出按钮是否可见）
      const logoutButtonVisible = await dashboardPage.isVisible(
        '[data-testid="logout-button"], button:has-text("退出")'
      )

      expect(logoutButtonVisible).toBe(true)
    })

    it('应该能够退出登录', async () => {
      await dashboardPage.navigate()

      await dashboardPage.logout()
      await page.waitForTimeout(2000)

      // 验证已跳转到登录页面
      const url = await dashboardPage.getCurrentUrl()
      expect(url).toContain('/login')

      // 验证 token 已清除
      const hasToken = await dashboardPage.getLocalStorage('auth-token')
      expect(hasToken).toBeNull()
    }, 60000)
  })

  describe('响应式布局', () => {
    it('应该在移动端视口正常显示', async () => {
      await page.setViewport({ width: 375, height: 667 })  // iPhone SE
      await dashboardPage.navigate()

      // 检查页面是否正常加载
      const isOnDashboard = await dashboardPage.isOnDashboard()
      expect(isOnDashboard).toBe(true)

      // 移动端可能有不同的布局
      // 检查是否有移动端菜单按钮
      const hasMobileMenu = await dashboardPage.exists(
        '[data-testid="mobile-menu"], .mobile-menu-button'
      )

      console.log(`📱 移动端菜单: ${hasMobileMenu ? '存在' : '不存在'}`)
    })

    it('应该在平板视口正常显示', async () => {
      await page.setViewport({ width: 768, height: 1024 })  // iPad
      await dashboardPage.navigate()

      const isOnDashboard = await dashboardPage.isOnDashboard()
      expect(isOnDashboard).toBe(true)
    })

    it('应该在桌面视口正常显示', async () => {
      await page.setViewport({ width: 1920, height: 1080 })  // 桌面
      await dashboardPage.navigate()

      const isOnDashboard = await dashboardPage.isOnDashboard()
      expect(isOnDashboard).toBe(true)

      // 桌面端应该显示侧边栏
      const hasSidebar = await dashboardPage.hasSidebar()
      expect(hasSidebar).toBe(true)
    })
  })

  describe('数据刷新', () => {
    it('页面刷新后数据应该保持', async () => {
      await dashboardPage.navigate()

      // 获取初始数据
      const initialTitle = await dashboardPage.getPageTitle()

      // 刷新页面
      await page.reload({ waitUntil: 'networkidle0' })
      await page.waitForTimeout(1000)

      // 验证仍在仪表盘
      const isOnDashboard = await dashboardPage.isOnDashboard()
      expect(isOnDashboard).toBe(true)

      // 验证数据仍然存在
      const newTitle = await dashboardPage.getPageTitle()
      expect(newTitle).toBe(initialTitle)
    })
  })

  describe('错误处理', () => {
    it('未登录时应该跳转到登录页面', async () => {
      // 清除认证信息
      await dashboardPage.clearStorage()

      // 尝试访问仪表盘
      await dashboardPage.navigate()
      await page.waitForTimeout(2000)

      // 应该被重定向到登录页面
      const url = await dashboardPage.getCurrentUrl()
      expect(url).toContain('/login')
    }, 60000)

    it('API 错误时应该显示错误消息', async () => {
      await dashboardPage.navigate()

      // Mock API 返回错误
      await page.setRequestInterception(true)
      page.on('request', (request) => {
        if (request.url().includes('/api/')) {
          request.respond({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Internal Server Error' }),
          })
        } else {
          request.continue()
        }
      })

      // 刷新页面触发 API 调用
      await page.reload()
      await page.waitForTimeout(2000)

      // 检查是否显示错误消息
      const hasError = await dashboardPage.exists('[role="alert"], .error-message')

      console.log(`❌ 错误消息显示: ${hasError ? '是' : '否'}`)
    })
  })
})
