/**
 * 充值管理页面对象
 */

import { Page } from 'puppeteer'
import { BasePage } from './BasePage'

export class TopupPage extends BasePage {
  private selectors = {
    // 列表相关
    table: 'table, [role="table"]',
    tableRow: 'tr[data-testid="topup-row"], tbody tr',
    emptyState: '[data-testid="empty-state"], .empty-state',

    // 按钮
    createButton: 'button:has-text("创建"), button:has-text("新建"), [data-testid="create-topup"]',
    submitButton: 'button[type="submit"]',
    cancelButton: 'button:has-text("取消"), button:has-text("Cancel")',
    reviewButton: '[data-testid="review-button"], button:has-text("审核")',
    approveButton: '[data-testid="approve-button"], button:has-text("通过")',
    rejectButton: '[data-testid="reject-button"], button:has-text("驳回")',
    exportButton: 'button:has-text("导出"), [data-testid="export"]',

    // 表单字段
    accountSelect: 'select[name="account"], [data-testid="account-select"]',
    amountInput: 'input[name="amount"], [data-testid="amount-input"]',
    proofUpload: 'input[type="file"], [data-testid="proof-upload"]',
    remarksInput: 'textarea[name="remarks"], [data-testid="remarks-input"]',

    // 筛选相关
    statusFilter: 'select[name="status"], [data-testid="status-filter"]',
    accountFilter: 'select[name="account_filter"], [data-testid="account-filter"]',
    dateStartInput: 'input[name="date_start"], [data-testid="date-start"]',
    dateEndInput: 'input[name="date_end"], [data-testid="date-end"]',
    filterButton: 'button:has-text("筛选"), button:has-text("Filter")',
    clearFilterButton: 'button:has-text("清空"), button:has-text("Clear")',

    // 搜索
    searchInput: 'input[placeholder*="搜索"], input[type="search"]',

    // 分页
    pagination: '.pagination, [data-testid="pagination"]',
    nextPageButton: 'button:has-text("下一页"), [aria-label="下一页"]',
    prevPageButton: 'button:has-text("上一页"), [aria-label="上一页"]',

    // 详情/抽屉
    detailDrawer: '[role="dialog"], .drawer, [data-testid="detail-drawer"]',
    closeDrawerButton: 'button[aria-label="关闭"], button:has-text("关闭")',

    // 审核表单
    reviewModal: '[role="dialog"][aria-label*="审核"], [data-testid="review-modal"]',
    reviewReasonInput: 'textarea[name="review_reason"], [data-testid="review-reason"]',

    // 状态徽章
    statusBadge: '[data-testid="status-badge"], .status-badge',

    // 凭证预览
    proofPreview: '[data-testid="proof-preview"], .proof-preview',
    proofModal: '[role="dialog"][aria-label*="凭证"], [data-testid="proof-modal"]',
  }

  async navigate() {
    await this.goto('/topup')
  }

  // ===== 列表操作 =====

  async getTableRowsCount(): Promise<number> {
    await this.waitForElement(this.selectors.table)
    const rows = await this.page.$$(this.selectors.tableRow)
    return rows.length
  }

  async hasTable(): Promise<boolean> {
    return this.exists(this.selectors.table)
  }

  async getFirstRowData(): Promise<Record<string, string>> {
    await this.waitForElement(this.selectors.tableRow)

    return this.page.evaluate(() => {
      const row = document.querySelector('tbody tr')
      if (!row) return {}

      const cells = row.querySelectorAll('td')
      const data: Record<string, string> = {}

      cells.forEach((cell, index) => {
        data[`col_${index}`] = cell.textContent?.trim() || ''
      })

      return data
    })
  }

  // ===== 创建充值 =====

  async clickCreate() {
    await this.click(this.selectors.createButton)
    await this.page.waitForTimeout(500)
  }

  async selectAccount(accountName: string) {
    await this.waitForElement(this.selectors.accountSelect)
    await this.page.select(this.selectors.accountSelect, accountName)
  }

  async fillAmount(amount: string) {
    await this.fill(this.selectors.amountInput, amount)
  }

  async uploadProof(filePath: string) {
    const input = await this.page.$(this.selectors.proofUpload)
    if (input) {
      await input.uploadFile(filePath)
    }
  }

  async fillRemarks(remarks: string) {
    await this.fill(this.selectors.remarksInput, remarks)
  }

  async submitForm() {
    await this.click(this.selectors.submitButton)
    await this.page.waitForTimeout(1000)
  }

  async createTopup(data: {
    account: string
    amount: string
    proofPath?: string
    remarks?: string
  }) {
    await this.clickCreate()
    await this.selectAccount(data.account)
    await this.fillAmount(data.amount)

    if (data.proofPath) {
      await this.uploadProof(data.proofPath)
    }

    if (data.remarks) {
      await this.fillRemarks(data.remarks)
    }

    await this.submitForm()
  }

  // ===== 筛选操作 =====

  async filterByStatus(status: string) {
    await this.waitForElement(this.selectors.statusFilter)
    await this.page.select(this.selectors.statusFilter, status)
    await this.page.waitForTimeout(500)
  }

  async filterByAccount(accountId: string) {
    await this.waitForElement(this.selectors.accountFilter)
    await this.page.select(this.selectors.accountFilter, accountId)
    await this.page.waitForTimeout(500)
  }

  async filterByDateRange(startDate: string, endDate: string) {
    await this.fill(this.selectors.dateStartInput, startDate)
    await this.fill(this.selectors.dateEndInput, endDate)

    if (await this.exists(this.selectors.filterButton)) {
      await this.click(this.selectors.filterButton)
    }

    await this.page.waitForTimeout(500)
  }

  async filterTopups(filters: {
    status?: string
    account?: string
    dateStart?: string
    dateEnd?: string
  }) {
    if (filters.status) {
      await this.filterByStatus(filters.status)
    }

    if (filters.account) {
      await this.filterByAccount(filters.account)
    }

    if (filters.dateStart && filters.dateEnd) {
      await this.filterByDateRange(filters.dateStart, filters.dateEnd)
    }
  }

  async clearFilters() {
    if (await this.exists(this.selectors.clearFilterButton)) {
      await this.click(this.selectors.clearFilterButton)
      await this.page.waitForTimeout(500)
    }
  }

  // ===== 搜索操作 =====

  async searchTopups(keyword: string) {
    await this.fill(this.selectors.searchInput, keyword)
    await this.page.keyboard.press('Enter')
    await this.page.waitForTimeout(500)
  }

  // ===== 分页操作 =====

  async goToNextPage() {
    await this.click(this.selectors.nextPageButton)
    await this.page.waitForTimeout(1000)
  }

  async goToPreviousPage() {
    await this.click(this.selectors.prevPageButton)
    await this.page.waitForTimeout(1000)
  }

  // ===== 查看详情 =====

  async viewFirstTopup() {
    const viewButton = await this.page.$(
      '[data-testid="view-button"]:first-of-type, button[title*="查看"]:first-of-type'
    )

    if (viewButton) {
      await viewButton.click()
      await this.page.waitForTimeout(500)
    }
  }

  async isDetailDrawerOpen(): Promise<boolean> {
    return this.isVisible(this.selectors.detailDrawer)
  }

  async closeDetailDrawer() {
    if (await this.isDetailDrawerOpen()) {
      await this.click(this.selectors.closeDrawerButton)
      await this.page.waitForTimeout(500)
    }
  }

  async getDetailData(): Promise<Record<string, string>> {
    await this.waitForElement(this.selectors.detailDrawer)

    return this.page.evaluate(() => {
      const drawer = document.querySelector('[role="dialog"], .drawer')
      if (!drawer) return {}

      const data: Record<string, string> = {}
      const labels = drawer.querySelectorAll('.detail-label, [data-testid*="label"]')
      const values = drawer.querySelectorAll('.detail-value, [data-testid*="value"]')

      labels.forEach((label, index) => {
        const key = label.textContent?.trim() || `field_${index}`
        const value = values[index]?.textContent?.trim() || ''
        data[key] = value
      })

      return data
    })
  }

  // ===== 审核操作 =====

  async clickReview() {
    await this.click(this.selectors.reviewButton)
    await this.page.waitForTimeout(500)
  }

  async isReviewModalOpen(): Promise<boolean> {
    return this.isVisible(this.selectors.reviewModal)
  }

  async approveTopup(reason?: string) {
    await this.clickReview()

    if (reason) {
      await this.fill(this.selectors.reviewReasonInput, reason)
    }

    await this.click(this.selectors.approveButton)
    await this.page.waitForTimeout(1000)
  }

  async rejectTopup(reason: string) {
    await this.clickReview()
    await this.fill(this.selectors.reviewReasonInput, reason)
    await this.click(this.selectors.rejectButton)
    await this.page.waitForTimeout(1000)
  }

  // ===== 凭证查看 =====

  async viewProof() {
    const proofPreview = await this.page.$(this.selectors.proofPreview)

    if (proofPreview) {
      await proofPreview.click()
      await this.page.waitForTimeout(500)
    }
  }

  async isProofModalOpen(): Promise<boolean> {
    return this.isVisible(this.selectors.proofModal)
  }

  async closeProofModal() {
    if (await this.isProofModalOpen()) {
      const closeButton = await this.page.$(`${this.selectors.proofModal} button[aria-label="关闭"]`)
      if (closeButton) {
        await closeButton.click()
        await this.page.waitForTimeout(500)
      }
    }
  }

  // ===== 导出操作 =====

  async clickExport() {
    await this.click(this.selectors.exportButton)
    await this.page.waitForTimeout(500)
  }

  // ===== 状态检查 =====

  async getStatusBadges(): Promise<string[]> {
    await this.waitForElement(this.selectors.statusBadge)

    return this.page.evaluate((selector) => {
      const badges = document.querySelectorAll(selector)
      return Array.from(badges).map(badge => badge.textContent?.trim() || '')
    }, this.selectors.statusBadge)
  }

  async hasTopupWithStatus(status: string): Promise<boolean> {
    const badges = await this.getStatusBadges()
    return badges.some(badge => badge.includes(status))
  }

  // ===== 错误/成功消息 =====

  async hasSuccessMessage(): Promise<boolean> {
    return this.exists('[role="alert"].success, .success-message, [data-testid="success"]')
  }

  async getSuccessMessage(): Promise<string> {
    const selector = '[role="alert"].success, .success-message, [data-testid="success"]'
    return this.getText(selector)
  }

  async hasErrorMessage(): Promise<boolean> {
    return this.exists('[role="alert"].error, .error-message, [data-testid="error"]')
  }

  async getErrorMessage(): Promise<string> {
    const selector = '[role="alert"].error, .error-message, [data-testid="error"]'
    return this.getText(selector)
  }

  // ===== 页面状态 =====

  async getPageTitle(): Promise<string> {
    return this.getText('h1, [data-testid="page-title"]')
  }

  async isLoading(): Promise<boolean> {
    return this.exists('.loading, [data-testid="loading"], .spinner')
  }
}
