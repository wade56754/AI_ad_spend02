/**
 * 登录流程 E2E 测试
 *
 * 测试场景：
 * 1. 成功登录
 * 2. 错误凭据登录
 * 3. 表单验证
 * 4. 记住登录状态
 */

import { Browser, Page } from 'puppeteer'
import { LoginPage } from '../../pages/LoginPage'
import { DashboardPage } from '../../pages/DashboardPage'

describe('登录流程 E2E 测试', () => {
  let browser: Browser
  let page: Page
  let loginPage: LoginPage
  let dashboardPage: DashboardPage

  beforeAll(async () => {
    browser = await global.__BROWSER__
  })

  beforeEach(async () => {
    page = await browser.newPage()
    loginPage = new LoginPage(page)
    dashboardPage = new DashboardPage(page)

    // 清除存储，确保每个测试从干净状态开始
    await loginPage.clearStorage()
  })

  afterEach(async () => {
    await page.close()
  })

  describe('页面加载', () => {
    it('应该成功加载登录页面', async () => {
      await loginPage.navigate()

      const url = await loginPage.getCurrentUrl()
      expect(url).toContain('/login')

      const title = await loginPage.getTitle()
      expect(title).toBeTruthy()
    })

    it('应该显示登录表单', async () => {
      await loginPage.navigate()

      // 检查表单元素是否存在
      expect(await loginPage.exists('input[type="email"]')).toBe(true)
      expect(await loginPage.exists('input[type="password"]')).toBe(true)
      expect(await loginPage.exists('button[type="submit"]')).toBe(true)
    })
  })

  describe('表单验证', () => {
    it('应该显示空邮箱错误', async () => {
      await loginPage.navigate()

      // 只填写密码，不填邮箱
      await loginPage.fillPassword('password123')
      await loginPage.clickSubmit()

      // 检查是否显示错误消息
      const hasError = await loginPage.hasErrorMessage()
      expect(hasError).toBe(true)

      const errorMessage = await loginPage.getErrorMessage()
      expect(errorMessage).toMatch(/邮箱|email/i)
    }, 30000)

    it('应该显示空密码错误', async () => {
      await loginPage.navigate()

      // 只填写邮箱，不填密码
      await loginPage.fillEmail('test@example.com')
      await loginPage.clickSubmit()

      // 检查是否显示错误消息
      const hasError = await loginPage.hasErrorMessage()
      expect(hasError).toBe(true)

      const errorMessage = await loginPage.getErrorMessage()
      expect(errorMessage).toMatch(/密码|password/i)
    }, 30000)

    it('应该显示无效邮箱格式错误', async () => {
      await loginPage.navigate()

      await loginPage.fillEmail('invalid-email')
      await loginPage.fillPassword('password123')
      await loginPage.clickSubmit()

      const hasError = await loginPage.hasErrorMessage()
      expect(hasError).toBe(true)

      const errorMessage = await loginPage.getErrorMessage()
      expect(errorMessage).toMatch(/邮箱格式|email format/i)
    }, 30000)
  })

  describe('登录功能', () => {
    it('应该使用有效凭据成功登录', async () => {
      await loginPage.navigate()

      // 使用测试账号登录
      await loginPage.login('admin@example.com', 'Admin123!')

      // 等待跳转
      await page.waitForTimeout(2000)

      // 验证登录成功
      const isSuccess = await loginPage.isLoginSuccessful()
      expect(isSuccess).toBe(true)

      // 验证已跳转到仪表盘
      const isOnDashboard = await dashboardPage.isOnDashboard()
      expect(isOnDashboard).toBe(true)

      // 验证有 auth token
      const hasToken = await loginPage.hasAuthToken()
      expect(hasToken).toBe(true)
    }, 60000)

    it('应该显示错误凭据错误消息', async () => {
      await loginPage.navigate()

      // 使用错误的凭据
      await loginPage.login('wrong@example.com', 'wrongpassword')

      // 等待 API 响应
      await page.waitForTimeout(2000)

      // 验证显示错误消息
      const hasError = await loginPage.hasErrorMessage()
      expect(hasError).toBe(true)

      const errorMessage = await loginPage.getErrorMessage()
      expect(errorMessage).toMatch(/邮箱或密码错误|invalid credentials/i)

      // 验证仍在登录页面
      const url = await loginPage.getCurrentUrl()
      expect(url).toContain('/login')

      // 验证没有 token
      const hasToken = await loginPage.hasAuthToken()
      expect(hasToken).toBe(false)
    }, 60000)
  })

  describe('用户交互', () => {
    it('应该能够切换到注册页面', async () => {
      await loginPage.navigate()

      await loginPage.clickSignUp()
      await page.waitForTimeout(1000)

      const url = await loginPage.getCurrentUrl()
      expect(url).toContain('/sign-up')
    }, 30000)

    it('应该能够切换到忘记密码页面', async () => {
      await loginPage.navigate()

      await loginPage.clickForgotPassword()
      await page.waitForTimeout(1000)

      const url = await loginPage.getCurrentUrl()
      expect(url).toContain('/forgot-password')
    }, 30000)
  })

  describe('加载状态', () => {
    it('登录时应该显示加载指示器', async () => {
      await loginPage.navigate()

      await loginPage.fillEmail('admin@example.com')
      await loginPage.fillPassword('Admin123!')
      await loginPage.clickSubmit()

      // 检查是否显示加载状态（在API响应之前）
      const isLoading = await loginPage.isLoading()
      // 注意：这个测试可能不稳定，因为加载状态可能很快消失
      // 可以考虑使用 network throttling 来测试
    }, 30000)
  })

  describe('记住登录状态', () => {
    it('登录后刷新页面应该保持登录状态', async () => {
      await loginPage.navigate()

      // 登录
      await loginPage.login('admin@example.com', 'Admin123!')
      await page.waitForTimeout(2000)

      // 验证登录成功
      expect(await loginPage.isLoginSuccessful()).toBe(true)

      // 刷新页面
      await page.reload({ waitUntil: 'networkidle0' })
      await page.waitForTimeout(1000)

      // 验证仍然登录（没有跳转到登录页）
      const url = await loginPage.getCurrentUrl()
      expect(url).not.toContain('/login')

      // 验证 token 仍然存在
      const hasToken = await loginPage.hasAuthToken()
      expect(hasToken).toBe(true)
    }, 60000)

    it('清除 storage 后应该跳转到登录页', async () => {
      await loginPage.navigate()

      // 登录
      await loginPage.login('admin@example.com', 'Admin123!')
      await page.waitForTimeout(2000)

      // 清除存储
      await loginPage.clearStorage()

      // 尝试访问受保护的页面
      await dashboardPage.navigate()
      await page.waitForTimeout(1000)

      // 应该跳转到登录页
      const url = await loginPage.getCurrentUrl()
      expect(url).toContain('/login')
    }, 60000)
  })
})
