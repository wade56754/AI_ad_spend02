/**
 * 日报管理页面对象
 * 封装日报管理页面的所有交互逻辑
 */

import { BasePage } from './BasePage'

export class DailyReportsPage extends BasePage {
  // 选择器定义
  private selectors = {
    // 页面标识
    pageTitle: 'h1, [data-testid="page-title"]',

    // 筛选器
    filterDateStart: 'input[name="dateStart"], #dateStart',
    filterDateEnd: 'input[name="dateEnd"], #dateEnd',
    filterStatus: 'select[name="status"], #status',
    filterAccount: 'select[name="account"], #account',
    applyFilterButton: 'button:has-text("筛选"), [data-testid="apply-filter"]',
    clearFilterButton: 'button:has-text("清空"), [data-testid="clear-filter"]',

    // 表格
    reportsTable: 'table, [data-testid="reports-table"]',
    tableRows: 'tbody tr',
    firstRow: 'tbody tr:first-child',

    // 操作按钮
    createButton: 'button:has-text("创建"), [data-testid="create-report"]',
    exportButton: 'button:has-text("导出"), [data-testid="export"]',
    batchImportButton: 'button:has-text("批量导入"), [data-testid="batch-import"]',

    // 行操作
    viewButton: '[data-testid="view-button"], button:has-text("查看")',
    editButton: '[data-testid="edit-button"], button:has-text("编辑")',
    deleteButton: '[data-testid="delete-button"], button:has-text("删除")',

    // 分页
    pagination: '.pagination, [data-testid="pagination"]',
    nextPageButton: 'button:has-text("下一页"), [aria-label="下一页"]',
    prevPageButton: 'button:has-text("上一页"), [aria-label="上一页"]',
    pageNumber: '.page-number, [data-testid="page-number"]',

    // 对话框/抽屉
    detailDrawer: '[role="dialog"], .drawer',
    confirmDialog: '[role="alertdialog"], .confirm-dialog',
    confirmYesButton: 'button:has-text("确定"), button:has-text("是")',
    confirmNoButton: 'button:has-text("取消"), button:has-text("否")',
  }

  /**
   * 导航到日报管理页面
   */
  async navigate() {
    await this.goto('/daily-reports')
    await this.waitForLoadingToFinish()
  }

  /**
   * 获取页面标题
   */
  async getPageTitle(): Promise<string> {
    return this.getText(this.selectors.pageTitle)
  }

  /**
   * 检查表格是否显示
   */
  async hasTable(): Promise<boolean> {
    return this.isVisible(this.selectors.reportsTable)
  }

  /**
   * 获取表格行数
   */
  async getTableRowsCount(): Promise<number> {
    const rows = await this.page.$$(this.selectors.tableRows)
    return rows.length
  }

  /**
   * 筛选日报
   */
  async filterReports(filters: {
    dateStart?: string
    dateEnd?: string
    status?: string
    account?: string
  }) {
    if (filters.dateStart) {
      await this.fill(this.selectors.filterDateStart, filters.dateStart)
    }

    if (filters.dateEnd) {
      await this.fill(this.selectors.filterDateEnd, filters.dateEnd)
    }

    if (filters.status) {
      await this.page.select(this.selectors.filterStatus, filters.status)
    }

    if (filters.account) {
      await this.page.select(this.selectors.filterAccount, filters.account)
    }

    await this.click(this.selectors.applyFilterButton)
    await this.waitForLoadingToFinish()
  }

  /**
   * 清空筛选
   */
  async clearFilters() {
    await this.click(this.selectors.clearFilterButton)
    await this.waitForLoadingToFinish()
  }

  /**
   * 点击创建按钮
   */
  async clickCreate() {
    await this.click(this.selectors.createButton)
    await this.waitForLoadingToFinish()
  }

  /**
   * 点击导出按钮
   */
  async clickExport() {
    await this.click(this.selectors.exportButton)
  }

  /**
   * 点击批量导入按钮
   */
  async clickBatchImport() {
    await this.click(this.selectors.batchImportButton)
  }

  /**
   * 查看第一条日报
   */
  async viewFirstReport() {
    // 点击第一行的查看按钮
    const firstRow = await this.page.$(this.selectors.firstRow)
    if (firstRow) {
      const viewButton = await firstRow.$(this.selectors.viewButton)
      if (viewButton) {
        await viewButton.click()
        await this.waitForLoadingToFinish()
      }
    }
  }

  /**
   * 编辑第一条日报
   */
  async editFirstReport() {
    const firstRow = await this.page.$(this.selectors.firstRow)
    if (firstRow) {
      const editButton = await firstRow.$(this.selectors.editButton)
      if (editButton) {
        await editButton.click()
        await this.waitForLoadingToFinish()
      }
    }
  }

  /**
   * 删除第一条日报
   */
  async deleteFirstReport() {
    const firstRow = await this.page.$(this.selectors.firstRow)
    if (firstRow) {
      const deleteButton = await firstRow.$(this.selectors.deleteButton)
      if (deleteButton) {
        await deleteButton.click()
        await this.page.waitForTimeout(500)

        // 确认删除
        if (await this.exists(this.selectors.confirmYesButton)) {
          await this.click(this.selectors.confirmYesButton)
          await this.waitForLoadingToFinish()
        }
      }
    }
  }

  /**
   * 翻页
   */
  async goToNextPage() {
    await this.click(this.selectors.nextPageButton)
    await this.waitForLoadingToFinish()
  }

  /**
   * 上一页
   */
  async goToPrevPage() {
    await this.click(this.selectors.prevPageButton)
    await this.waitForLoadingToFinish()
  }

  /**
   * 检查详情抽屉是否打开
   */
  async isDetailDrawerOpen(): Promise<boolean> {
    return this.isVisible(this.selectors.detailDrawer)
  }

  /**
   * 检查确认对话框是否打开
   */
  async isConfirmDialogOpen(): Promise<boolean> {
    return this.isVisible(this.selectors.confirmDialog)
  }

  /**
   * 获取第一行的数据
   */
  async getFirstRowData(): Promise<Record<string, string>> {
    const firstRow = await this.page.$(this.selectors.firstRow)
    if (!firstRow) {
      return {}
    }

    const data = await this.page.evaluate((row) => {
      const cells = row.querySelectorAll('td')
      const result: Record<string, string> = {}

      cells.forEach((cell, index) => {
        result[`col${index}`] = cell.textContent?.trim() || ''
      })

      return result
    }, firstRow)

    return data
  }

  /**
   * 搜索日报
   */
  async searchReports(keyword: string) {
    const searchInput = 'input[placeholder*="搜索"], input[type="search"]'

    if (await this.exists(searchInput)) {
      await this.fill(searchInput, keyword)
      await this.page.keyboard.press('Enter')
      await this.waitForLoadingToFinish()
    }
  }
}
