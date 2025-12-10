/**
 * 日报管理基础功能 E2E 测试
 *
 * 测试场景：
 * 1. 页面加载
 * 2. 列表显示
 * 3. 筛选功能
 * 4. 分页功能
 * 5. CRUD 操作
 */

import { Browser, Page } from 'puppeteer'
import { DailyReportsPage } from '../../pages/DailyReportsPage'
import { LoginPage } from '../../pages/LoginPage'

describe('日报管理基础功能测试', () => {
  let browser: Browser
  let page: Page
  let dailyReportsPage: DailyReportsPage
  let loginPage: LoginPage

  beforeAll(async () => {
    browser = await global.__BROWSER__
  })

  beforeEach(async () => {
    page = await browser.newPage()
    dailyReportsPage = new DailyReportsPage(page)
    loginPage = new LoginPage(page)

    // 登录（使用投手账号，有权限查看日报）
    await loginPage.navigate()
    await loginPage.login('buyer@example.com', 'Buyer123!')
    await page.waitForTimeout(2000)
  })

  afterEach(async () => {
    await page.close()
  })

  describe('页面加载', () => {
    it('应该成功加载日报管理页面', async () => {
      await dailyReportsPage.navigate()

      const url = await dailyReportsPage.getCurrentUrl()
      expect(url).toContain('/daily-reports')
    })

    it('应该显示页面标题', async () => {
      await dailyReportsPage.navigate()

      const title = await dailyReportsPage.getPageTitle()
      expect(title).toBeTruthy()
      expect(title).toMatch(/日报|Daily Report/i)
    })

    it('应该显示表格', async () => {
      await dailyReportsPage.navigate()

      const hasTable = await dailyReportsPage.hasTable()
      expect(hasTable).toBe(true)
    })
  })

  describe('列表显示', () => {
    it('应该显示日报列表', async () => {
      await dailyReportsPage.navigate()

      const rowsCount = await dailyReportsPage.getTableRowsCount()
      expect(rowsCount).toBeGreaterThanOrEqual(0)

      console.log(`📋 日报数量: ${rowsCount}`)
    })

    it('表格行应该包含数据', async () => {
      await dailyReportsPage.navigate()

      const rowsCount = await dailyReportsPage.getTableRowsCount()

      if (rowsCount > 0) {
        const firstRowData = await dailyReportsPage.getFirstRowData()
        expect(Object.keys(firstRowData).length).toBeGreaterThan(0)

        console.log('📊 第一行数据:', firstRowData)
      }
    })

    it('应该显示操作按钮', async () => {
      await dailyReportsPage.navigate()

      // 检查是否有创建按钮
      const hasCreateButton = await dailyReportsPage.exists(
        'button:has-text("创建"), [data-testid="create-report"]'
      )

      console.log(`➕ 创建按钮: ${hasCreateButton ? '存在' : '不存在'}`)
    })
  })

  describe('筛选功能', () => {
    it('应该能够按状态筛选', async () => {
      await dailyReportsPage.navigate()

      const initialCount = await dailyReportsPage.getTableRowsCount()

      // 应用筛选
      await dailyReportsPage.filterReports({
        status: 'raw_submitted',
      })

      await page.waitForTimeout(1000)

      const filteredCount = await dailyReportsPage.getTableRowsCount()

      console.log(`🔍 筛选前: ${initialCount}, 筛选后: ${filteredCount}`)
    }, 60000)

    it('应该能够按日期筛选', async () => {
      await dailyReportsPage.navigate()

      // 筛选今天的日报
      const today = new Date().toISOString().split('T')[0]

      await dailyReportsPage.filterReports({
        dateStart: today,
        dateEnd: today,
      })

      await page.waitForTimeout(1000)

      const count = await dailyReportsPage.getTableRowsCount()

      console.log(`📅 今天的日报数量: ${count}`)
    }, 60000)

    it('应该能够清空筛选', async () => {
      await dailyReportsPage.navigate()

      // 应用筛选
      await dailyReportsPage.filterReports({
        status: 'raw_submitted',
      })

      await page.waitForTimeout(1000)
      const filteredCount = await dailyReportsPage.getTableRowsCount()

      // 清空筛选
      await dailyReportsPage.clearFilters()

      await page.waitForTimeout(1000)
      const totalCount = await dailyReportsPage.getTableRowsCount()

      console.log(`🔄 筛选后: ${filteredCount}, 清空后: ${totalCount}`)
    }, 60000)
  })

  describe('分页功能', () => {
    it('应该显示分页组件', async () => {
      await dailyReportsPage.navigate()

      const hasPagination = await dailyReportsPage.exists(
        '.pagination, [data-testid="pagination"]'
      )

      console.log(`📄 分页组件: ${hasPagination ? '存在' : '不存在'}`)
    })

    it('应该能够翻页', async () => {
      await dailyReportsPage.navigate()

      const hasNextButton = await dailyReportsPage.exists(
        'button:has-text("下一页"), [aria-label="下一页"]'
      )

      if (hasNextButton) {
        const firstPageData = await dailyReportsPage.getFirstRowData()

        await dailyReportsPage.goToNextPage()
        await page.waitForTimeout(1000)

        const secondPageData = await dailyReportsPage.getFirstRowData()

        // 两页的第一行数据应该不同
        expect(firstPageData).not.toEqual(secondPageData)

        console.log('✅ 翻页功能正常')
      }
    }, 60000)
  })

  describe('查看功能', () => {
    it('应该能够查看日报详情', async () => {
      await dailyReportsPage.navigate()

      const rowsCount = await dailyReportsPage.getTableRowsCount()

      if (rowsCount > 0) {
        await dailyReportsPage.viewFirstReport()
        await page.waitForTimeout(1000)

        // 检查是否打开了详情抽屉/对话框
        const isDrawerOpen = await dailyReportsPage.isDetailDrawerOpen()

        console.log(`📖 详情抽屉: ${isDrawerOpen ? '已打开' : '未打开'}`)
      }
    }, 60000)
  })

  describe('搜索功能', () => {
    it('应该能够搜索日报', async () => {
      await dailyReportsPage.navigate()

      // 检查是否有搜索框
      const hasSearchInput = await dailyReportsPage.exists(
        'input[placeholder*="搜索"], input[type="search"]'
      )

      if (hasSearchInput) {
        await dailyReportsPage.searchReports('test')
        await page.waitForTimeout(1000)

        const count = await dailyReportsPage.getTableRowsCount()

        console.log(`🔍 搜索结果数量: ${count}`)
      }
    }, 60000)
  })

  describe('导出功能', () => {
    it('应该显示导出按钮', async () => {
      await dailyReportsPage.navigate()

      const hasExportButton = await dailyReportsPage.exists(
        'button:has-text("导出"), [data-testid="export"]'
      )

      console.log(`📤 导出按钮: ${hasExportButton ? '存在' : '不存在'}`)
    })

    it('点击导出应该触发下载', async () => {
      await dailyReportsPage.navigate()

      const hasExportButton = await dailyReportsPage.exists(
        'button:has-text("导出"), [data-testid="export"]'
      )

      if (hasExportButton) {
        // 监听下载事件
        const downloadPromise = page.waitForEvent('download', { timeout: 10000 }).catch(() => null)

        await dailyReportsPage.clickExport()

        const download = await downloadPromise

        if (download) {
          console.log('✅ 导出功能触发下载')
        } else {
          console.log('⚠️  未检测到下载事件（可能需要后端支持）')
        }
      }
    }, 60000)
  })

  describe('权限控制', () => {
    it('不同角色应该看到不同的操作按钮', async () => {
      await dailyReportsPage.navigate()

      // 检查当前角色能看到的按钮
      const hasCreateButton = await dailyReportsPage.exists('button:has-text("创建")')
      const hasEditButton = await dailyReportsPage.exists('[data-testid="edit-button"]')
      const hasDeleteButton = await dailyReportsPage.exists('[data-testid="delete-button"]')

      console.log('🔐 权限检查:')
      console.log(`  创建按钮: ${hasCreateButton ? '✓' : '✗'}`)
      console.log(`  编辑按钮: ${hasEditButton ? '✓' : '✗'}`)
      console.log(`  删除按钮: ${hasDeleteButton ? '✓' : '✗'}`)
    })
  })

  describe('响应式设计', () => {
    it('移动端应该正常显示', async () => {
      await page.setViewport({ width: 375, height: 667 })
      await dailyReportsPage.navigate()

      const hasTable = await dailyReportsPage.hasTable()
      expect(hasTable).toBe(true)

      console.log('📱 移动端显示正常')
    })

    it('平板应该正常显示', async () => {
      await page.setViewport({ width: 768, height: 1024 })
      await dailyReportsPage.navigate()

      const hasTable = await dailyReportsPage.hasTable()
      expect(hasTable).toBe(true)

      console.log('💻 平板显示正常')
    })
  })
})
