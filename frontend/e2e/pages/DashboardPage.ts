/**
 * 仪表盘页面对象
 * 封装仪表盘页面的所有交互逻辑
 */

import { BasePage } from './BasePage'

export class DashboardPage extends BasePage {
  // 选择器定义
  private selectors = {
    // 页面标识
    pageTitle: 'h1, [data-testid="page-title"]',

    // 统计卡片
    statsCards: '[data-testid="stats-card"], .stats-card',

    // 趋势图表
    trendChart: '[data-testid="trend-chart"], .trend-chart',

    // 异常账户表格
    abnormalAccountsTable: '[data-testid="abnormal-accounts-table"], .abnormal-accounts-table',

    // 今日任务卡片
    todayTasksCard: '[data-testid="today-tasks-card"], .today-tasks-card',

    // 用户菜单
    userMenu: '[data-testid="user-menu"], .user-menu',
    logoutButton: '[data-testid="logout-button"], button:has-text("退出")',

    // 侧边栏导航
    sidebar: '[data-testid="sidebar"], nav',
    dailyReportsLink: 'a[href*="/daily-reports"]',
    topupLink: 'a[href*="/topup"]',
    reconciliationLink: 'a[href*="/reconciliation"]',
  }

  /**
   * 导航到仪表盘页面
   */
  async navigate() {
    await this.goto('/')
    await this.waitForLoadingToFinish()
  }

  /**
   * 检查是否在仪表盘页面
   */
  async isOnDashboard(): Promise<boolean> {
    const url = await this.getCurrentUrl()
    return url.endsWith('/') || url.includes('/dashboard')
  }

  /**
   * 获取页面标题
   */
  async getPageTitle(): Promise<string> {
    return this.getText(this.selectors.pageTitle)
  }

  /**
   * 检查统计卡片是否显示
   */
  async hasStatsCards(): Promise<boolean> {
    return this.isVisible(this.selectors.statsCards)
  }

  /**
   * 获取统计卡片数量
   */
  async getStatsCardsCount(): Promise<number> {
    const elements = await this.page.$$(this.selectors.statsCards)
    return elements.length
  }

  /**
   * 检查趋势图表是否显示
   */
  async hasTrendChart(): Promise<boolean> {
    return this.isVisible(this.selectors.trendChart)
  }

  /**
   * 检查异常账户表格是否显示
   */
  async hasAbnormalAccountsTable(): Promise<boolean> {
    return this.isVisible(this.selectors.abnormalAccountsTable)
  }

  /**
   * 检查今日任务卡片是否显示
   */
  async hasTodayTasksCard(): Promise<boolean> {
    return this.isVisible(this.selectors.todayTasksCard)
  }

  /**
   * 点击用户菜单
   */
  async clickUserMenu() {
    await this.click(this.selectors.userMenu)
  }

  /**
   * 执行退出登录
   */
  async logout() {
    await this.clickUserMenu()
    await this.click(this.selectors.logoutButton)
    await this.waitForLoadingToFinish()
  }

  /**
   * 导航到日报管理页面
   */
  async goToDailyReports() {
    await this.click(this.selectors.dailyReportsLink)
    await this.waitForLoadingToFinish()
  }

  /**
   * 导航到充值管理页面
   */
  async goToTopup() {
    await this.click(this.selectors.topupLink)
    await this.waitForLoadingToFinish()
  }

  /**
   * 导航到对账管理页面
   */
  async goToReconciliation() {
    await this.click(this.selectors.reconciliationLink)
    await this.waitForLoadingToFinish()
  }

  /**
   * 检查侧边栏是否显示
   */
  async hasSidebar(): Promise<boolean> {
    return this.isVisible(this.selectors.sidebar)
  }
}
