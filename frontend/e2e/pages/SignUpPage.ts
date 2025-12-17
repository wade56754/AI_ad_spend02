/**
 * 注册页面对象
 * 封装注册页面的所有交互逻辑
 */

import { BasePage } from './BasePage'

export class SignUpPage extends BasePage {
  // 选择器定义
  private selectors = {
    usernameInput: 'input[name="username"], #username',
    emailInput: 'input[type="email"], input[name="email"], #email',
    passwordInput: 'input[name="password"], #password',
    confirmPasswordInput: 'input[name="confirmPassword"], #confirmPassword',
    roleSelect: 'select[name="role"], #role',
    submitButton: 'button[type="submit"]',
    errorMessage: '[role="alert"], .error-message, .alert-error',
    successMessage: '.success-message, .alert-success',
    loginLink: 'a[href*="/login"]',
    termsCheckbox: 'input[type="checkbox"][name="terms"]',
  }

  /**
   * 导航到注册页面
   */
  async navigate() {
    await this.goto('/sign-up')
    await this.waitForLoadingToFinish()
  }

  /**
   * 填写用户名
   */
  async fillUsername(username: string) {
    await this.fill(this.selectors.usernameInput, username)
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
   * 填写确认密码
   */
  async fillConfirmPassword(password: string) {
    await this.fill(this.selectors.confirmPasswordInput, password)
  }

  /**
   * 选择角色
   */
  async selectRole(role: string) {
    const element = await this.waitForElement(this.selectors.roleSelect)
    await this.page.select(this.selectors.roleSelect, role)
  }

  /**
   * 勾选条款
   */
  async acceptTerms() {
    if (await this.exists(this.selectors.termsCheckbox)) {
      const isChecked = await this.page.$eval(
        this.selectors.termsCheckbox,
        (el: any) => el.checked
      )
      if (!isChecked) {
        await this.click(this.selectors.termsCheckbox)
      }
    }
  }

  /**
   * 点击提交按钮
   */
  async clickSubmit() {
    await this.click(this.selectors.submitButton)
  }

  /**
   * 执行完整注册流程
   */
  async signUp(userData: {
    username: string
    email: string
    password: string
    confirmPassword?: string
    role?: string
    acceptTerms?: boolean
  }) {
    await this.fillUsername(userData.username)
    await this.fillEmail(userData.email)
    await this.fillPassword(userData.password)

    if (userData.confirmPassword) {
      await this.fillConfirmPassword(userData.confirmPassword)
    }

    if (userData.role) {
      await this.selectRole(userData.role)
    }

    if (userData.acceptTerms !== false) {
      await this.acceptTerms()
    }

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
   * 检查是否显示成功消息
   */
  async hasSuccessMessage(): Promise<boolean> {
    return this.isVisible(this.selectors.successMessage)
  }

  /**
   * 获取成功消息文本
   */
  async getSuccessMessage(): Promise<string> {
    if (await this.hasSuccessMessage()) {
      return this.getText(this.selectors.successMessage)
    }
    return ''
  }

  /**
   * 点击登录链接
   */
  async clickLoginLink() {
    await this.click(this.selectors.loginLink)
  }

  /**
   * 检查是否注册成功（通过 URL 变化）
   */
  async isSignUpSuccessful(): Promise<boolean> {
    try {
      // 等待 URL 变化（通常注册成功会跳转）
      await this.page.waitForFunction(
        () => !window.location.pathname.includes('/sign-up'),
        { timeout: 10000 }
      )
      return true
    } catch {
      return false
    }
  }
}
