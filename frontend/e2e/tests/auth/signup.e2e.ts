/**
 * 注册流程 E2E 测试
 *
 * 测试场景：
 * 1. 成功注册
 * 2. 表单验证（邮箱、密码、确认密码）
 * 3. 重复邮箱检测
 * 4. 密码强度验证
 * 5. 页面跳转
 */

import { Browser, Page } from 'puppeteer'
import { SignUpPage } from '../../pages/SignUpPage'
import { LoginPage } from '../../pages/LoginPage'

describe('注册流程 E2E 测试', () => {
  let browser: Browser
  let page: Page
  let signUpPage: SignUpPage
  let loginPage: LoginPage

  // 测试数据
  const validUserData = {
    username: 'testuser_' + Date.now(),
    email: `test_${Date.now()}@example.com`,
    password: 'Test@1234',
    confirmPassword: 'Test@1234',
    role: 'media_buyer',
  }

  beforeAll(async () => {
    browser = await global.__BROWSER__
  })

  beforeEach(async () => {
    page = await browser.newPage()
    signUpPage = new SignUpPage(page)
    loginPage = new LoginPage(page)

    // 清除存储
    await signUpPage.clearStorage()
  })

  afterEach(async () => {
    await page.close()
  })

  describe('页面加载', () => {
    it('应该成功加载注册页面', async () => {
      await signUpPage.navigate()

      const url = await signUpPage.getCurrentUrl()
      expect(url).toContain('/sign-up')

      const title = await signUpPage.getTitle()
      expect(title).toBeTruthy()
    })

    it('应该显示注册表单的所有字段', async () => {
      await signUpPage.navigate()

      // 检查表单元素是否存在
      expect(await signUpPage.exists('input[name="username"]')).toBe(true)
      expect(await signUpPage.exists('input[type="email"]')).toBe(true)
      expect(await signUpPage.exists('input[name="password"]')).toBe(true)
      expect(await signUpPage.exists('button[type="submit"]')).toBe(true)
    })
  })

  describe('表单验证', () => {
    it('应该显示空用户名错误', async () => {
      await signUpPage.navigate()

      // 不填写用户名，填写其他字段
      await signUpPage.fillEmail(validUserData.email)
      await signUpPage.fillPassword(validUserData.password)
      await signUpPage.clickSubmit()

      await page.waitForTimeout(1000)

      const hasError = await signUpPage.hasErrorMessage()
      expect(hasError).toBe(true)

      const errorMessage = await signUpPage.getErrorMessage()
      expect(errorMessage).toMatch(/用户名|username/i)
    }, 30000)

    it('应该显示空邮箱错误', async () => {
      await signUpPage.navigate()

      await signUpPage.fillUsername(validUserData.username)
      await signUpPage.fillPassword(validUserData.password)
      await signUpPage.clickSubmit()

      await page.waitForTimeout(1000)

      const hasError = await signUpPage.hasErrorMessage()
      expect(hasError).toBe(true)

      const errorMessage = await signUpPage.getErrorMessage()
      expect(errorMessage).toMatch(/邮箱|email/i)
    }, 30000)

    it('应该显示无效邮箱格式错误', async () => {
      await signUpPage.navigate()

      await signUpPage.signUp({
        username: validUserData.username,
        email: 'invalid-email',
        password: validUserData.password,
        confirmPassword: validUserData.confirmPassword,
      })

      await page.waitForTimeout(1000)

      const hasError = await signUpPage.hasErrorMessage()
      expect(hasError).toBe(true)

      const errorMessage = await signUpPage.getErrorMessage()
      expect(errorMessage).toMatch(/邮箱格式|email format/i)
    }, 30000)

    it('应该显示空密码错误', async () => {
      await signUpPage.navigate()

      await signUpPage.fillUsername(validUserData.username)
      await signUpPage.fillEmail(validUserData.email)
      await signUpPage.clickSubmit()

      await page.waitForTimeout(1000)

      const hasError = await signUpPage.hasErrorMessage()
      expect(hasError).toBe(true)

      const errorMessage = await signUpPage.getErrorMessage()
      expect(errorMessage).toMatch(/密码|password/i)
    }, 30000)

    it('应该显示密码不匹配错误', async () => {
      await signUpPage.navigate()

      await signUpPage.signUp({
        username: validUserData.username,
        email: validUserData.email,
        password: 'Test@1234',
        confirmPassword: 'Different@1234',
      })

      await page.waitForTimeout(1000)

      const hasError = await signUpPage.hasErrorMessage()
      expect(hasError).toBe(true)

      const errorMessage = await signUpPage.getErrorMessage()
      expect(errorMessage).toMatch(/密码不匹配|passwords do not match/i)
    }, 30000)

    it('应该显示密码强度不足错误', async () => {
      await signUpPage.navigate()

      await signUpPage.signUp({
        username: validUserData.username,
        email: validUserData.email,
        password: '123',  // 弱密码
        confirmPassword: '123',
      })

      await page.waitForTimeout(1000)

      const hasError = await signUpPage.hasErrorMessage()
      expect(hasError).toBe(true)

      const errorMessage = await signUpPage.getErrorMessage()
      expect(errorMessage).toMatch(/密码强度|password strength|至少|at least/i)
    }, 30000)
  })

  describe('注册功能', () => {
    it('应该使用有效数据成功注册', async () => {
      await signUpPage.navigate()

      await signUpPage.signUp(validUserData)

      // 等待响应
      await page.waitForTimeout(2000)

      // 验证注册成功
      const isSuccess = await signUpPage.isSignUpSuccessful()
      expect(isSuccess).toBe(true)

      // 可能跳转到成功页面或登录页面
      const url = await signUpPage.getCurrentUrl()
      expect(url).toMatch(/success|login|dashboard/i)
    }, 60000)

    it('应该显示重复邮箱错误', async () => {
      await signUpPage.navigate()

      // 使用已存在的邮箱
      await signUpPage.signUp({
        username: 'anotheruser',
        email: 'admin@example.com',  // 假设这个邮箱已存在
        password: 'Test@1234',
        confirmPassword: 'Test@1234',
      })

      await page.waitForTimeout(2000)

      const hasError = await signUpPage.hasErrorMessage()
      expect(hasError).toBe(true)

      const errorMessage = await signUpPage.getErrorMessage()
      expect(errorMessage).toMatch(/已存在|already exists|已注册|already registered/i)
    }, 60000)
  })

  describe('用户交互', () => {
    it('应该能够切换到登录页面', async () => {
      await signUpPage.navigate()

      await signUpPage.clickLoginLink()
      await page.waitForTimeout(1000)

      const url = await signUpPage.getCurrentUrl()
      expect(url).toContain('/login')
    }, 30000)

    it('应该能够选择用户角色', async () => {
      await signUpPage.navigate()

      // 如果有角色选择器
      if (await signUpPage.exists('select[name="role"]')) {
        await signUpPage.selectRole('media_buyer')

        const selectedValue = await page.$eval(
          'select[name="role"]',
          (el: any) => el.value
        )

        expect(selectedValue).toBe('media_buyer')
      }
    }, 30000)

    it('应该能够勾选服务条款', async () => {
      await signUpPage.navigate()

      // 如果有条款复选框
      if (await signUpPage.exists('input[name="terms"]')) {
        await signUpPage.acceptTerms()

        const isChecked = await page.$eval(
          'input[name="terms"]',
          (el: any) => el.checked
        )

        expect(isChecked).toBe(true)
      }
    }, 30000)
  })

  describe('密码强度指示器', () => {
    it('应该显示密码强度指示器', async () => {
      await signUpPage.navigate()

      await signUpPage.fillPassword('weak')
      await page.waitForTimeout(500)

      // 检查是否有密码强度指示器
      const hasStrengthIndicator = await signUpPage.exists('.password-strength, [data-testid="password-strength"]')

      // 如果有强度指示器，验证它
      if (hasStrengthIndicator) {
        const strengthText = await signUpPage.getText('.password-strength')
        expect(strengthText).toBeTruthy()
      }
    }, 30000)
  })

  describe('注册流程完整性', () => {
    it('注册成功后应该能够登录', async () => {
      // 1. 注册新用户
      await signUpPage.navigate()

      const newUser = {
        username: 'fulltest_' + Date.now(),
        email: `fulltest_${Date.now()}@example.com`,
        password: 'FullTest@1234',
        confirmPassword: 'FullTest@1234',
      }

      await signUpPage.signUp(newUser)
      await page.waitForTimeout(2000)

      // 验证注册成功
      expect(await signUpPage.isSignUpSuccessful()).toBe(true)

      // 2. 导航到登录页面
      await loginPage.navigate()

      // 3. 使用新注册的账号登录
      await loginPage.login(newUser.email, newUser.password)
      await page.waitForTimeout(2000)

      // 4. 验证登录成功
      const isLoginSuccess = await loginPage.isLoginSuccessful()
      expect(isLoginSuccess).toBe(true)
    }, 90000)
  })
})
