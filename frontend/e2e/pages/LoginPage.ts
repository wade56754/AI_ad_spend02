/**
 * 登录页面对象
 * 封装登录页面的所有交互逻辑
 */

import { BasePage } from './BasePage'

export class LoginPage extends BasePage {
  // 选择器定义
  private selectors = {
    emailInput: 'input[type="email"], input[name="email"], #email',
    passwordInput: 'input[type="password"], input[name="password"], #password',
    submitButton: 'button[type="submit"]',
    errorMessage: '[role="alert"], .error-message, .alert-error',
    loadingIndicator: '.loading, .spinner, [data-loading="true"]',
    forgotPasswordLink: 'a[href*="forgot-password"]',
    signUpLink: 'a[href*="sign-up"]',
  }

  /**
   * 导航到登录页面
   */
  async navigate() {
    await this.goto('/login')
    await this.waitForLoadingToFinish()
  }

  /**
   * 填写邮箱
   */
  async fillEmail(email: string) {
    await this.fill(this.selectors.emailInput, email)
  }

  /**
   * 填写密码
   */
  async fillPassword(password: string) {
    await this.fill(this.selectors.passwordInput, password)
  }

  /**
   * 点击提交按钮
   */
  async clickSubmit() {
    await this.click(this.selectors.submitButton)
  }

  /**
   * 执行登录操作
   */
  async login(email: string, password: string) {
    await this.fillEmail(email)
    await this.fillPassword(password)
    await this.clickSubmit()
    await this.waitForLoadingToFinish()
  }

  /**
   * 检查是否显示错误消息
   */
  async hasErrorMessage(): Promise<boolean> {
    return this.isVisible(this.selectors.errorMessage)
  }

  /**
   * 获取错误消息文本
   */
  async getErrorMessage(): Promise<string> {
    if (await this.hasErrorMessage()) {
      return this.getText(this.selectors.errorMessage)
    }
    return ''
  }

  /**
   * 检查是否正在加载
   */
  async isLoading(): Promise<boolean> {
    return this.isVisible(this.selectors.loadingIndicator)
  }

  /**
   * 点击忘记密码链接
   */
  async clickForgotPassword() {
    await this.click(this.selectors.forgotPasswordLink)
  }

  /**
   * 点击注册链接
   */
  async clickSignUp() {
    await this.click(this.selectors.signUpLink)
  }

  /**
   * 检查是否登录成功（通过 URL 变化）
   */
  async isLoginSuccessful(): Promise<boolean> {
    try {
      // 等待 URL 变化（通常登录成功会跳转到首页或仪表盘）
      await this.page.waitForFunction(
        () => !window.location.pathname.includes('/login'),
        { timeout: 10000 }
      )
      return true
    } catch {
      return false
    }
  }

  /**
   * 检查是否有 auth token 存储
   */
  async hasAuthToken(): Promise<boolean> {
    const token = await this.getLocalStorage('auth-token')
    return token !== null && token.length > 0
  }
}
