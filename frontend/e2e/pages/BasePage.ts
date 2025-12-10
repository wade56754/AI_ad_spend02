/**
 * 基础页面类
 * 所有页面对象继承此类
 */

import { Page } from 'puppeteer'
import * as helpers from '../utils/helpers'

export class BasePage {
  protected page: Page
  protected baseUrl: string

  constructor(page: Page) {
    this.page = page
    this.baseUrl = global.BASE_URL || 'http://localhost:3000'
  }

  /**
   * 导航到指定路径
   */
  async goto(path: string) {
    const url = `${this.baseUrl}${path}`
    await this.page.goto(url, {
      waitUntil: ['domcontentloaded', 'networkidle0'],
      timeout: 30000,
    })
  }

  /**
   * 获取当前 URL
   */
  async getCurrentUrl(): Promise<string> {
    return this.page.url()
  }

  /**
   * 获取页面标题
   */
  async getTitle(): Promise<string> {
    return this.page.title()
  }

  /**
   * 等待元素出现
   */
  async waitForElement(selector: string, timeout = 10000) {
    return helpers.waitForElement(this.page, selector, timeout)
  }

  /**
   * 等待文本出现
   */
  async waitForText(text: string, timeout = 10000) {
    return helpers.waitForText(this.page, text, timeout)
  }

  /**
   * 点击元素
   */
  async click(selector: string) {
    await this.waitForElement(selector)
    await this.page.click(selector)
  }

  /**
   * 填写输入框
   */
  async fill(selector: string, value: string) {
    return helpers.fillInput(this.page, selector, value)
  }

  /**
   * 获取文本内容
   */
  async getText(selector: string): Promise<string> {
    return helpers.getText(this.page, selector)
  }

  /**
   * 检查元素是否存在
   */
  async exists(selector: string): Promise<boolean> {
    return helpers.elementExists(this.page, selector)
  }

  /**
   * 检查元素是否可见
   */
  async isVisible(selector: string): Promise<boolean> {
    return helpers.isElementVisible(this.page, selector)
  }

  /**
   * 截图
   */
  async screenshot(name: string) {
    return helpers.takeScreenshot(this.page, name)
  }

  /**
   * 等待导航完成
   */
  async waitForNavigation(timeout = 30000) {
    return helpers.waitForNavigation(this.page, timeout)
  }

  /**
   * 等待加载完成
   */
  async waitForLoadingToFinish(timeout = 30000) {
    return helpers.waitForLoadingToFinish(this.page, timeout)
  }

  /**
   * 清除浏览器存储
   */
  async clearStorage() {
    return helpers.clearBrowserStorage(this.page)
  }

  /**
   * 设置 LocalStorage
   */
  async setLocalStorage(key: string, value: string) {
    return helpers.setLocalStorage(this.page, key, value)
  }

  /**
   * 获取 LocalStorage
   */
  async getLocalStorage(key: string): Promise<string | null> {
    return helpers.getLocalStorage(this.page, key)
  }
}
