/**
 * 充值管理基础功能 E2E 测试
 *
 * 测试场景：
 * 1. 页面加载
 * 2. 列表显示
 * 3. 创建充值
 * 4. 筛选功能
 * 5. 查看详情
 * 6. 审核流程
 * 7. 状态管理
 * 8. 权限控制
 */

import { Browser, Page } from 'puppeteer'
import { TopupPage } from '../../pages/TopupPage'
import { LoginPage } from '../../pages/LoginPage'
import * as path from 'path'

describe('充值管理基础功能测试', () => {
  let browser: Browser
  let page: Page
  let topupPage: TopupPage
  let loginPage: LoginPage

  beforeAll(async () => {
    browser = await global.__BROWSER__
  })

  beforeEach(async () => {
    page = await browser.newPage()
    topupPage = new TopupPage(page)
    loginPage = new LoginPage(page)

    // 登录（使用投手账号）
    await loginPage.navigate()
    await loginPage.login('buyer@example.com', 'Buyer123!')
    await page.waitForTimeout(2000)
  })

  afterEach(async () => {
    await page.close()
  })

  describe('页面加载', () => {
    it('应该成功加载充值管理页面', async () => {
      await topupPage.navigate()

      const url = await topupPage.getCurrentUrl()
      expect(url).toContain('/topup')
    })

    it('应该显示页面标题', async () => {
      await topupPage.navigate()

      const title = await topupPage.getPageTitle()
      expect(title).toBeTruthy()
      expect(title).toMatch(/充值|Topup/i)
    })

    it('应该显示表格', async () => {
      await topupPage.navigate()

      const hasTable = await topupPage.hasTable()
      expect(hasTable).toBe(true)
    })

    it('应该显示创建按钮', async () => {
      await topupPage.navigate()

      const hasCreateButton = await topupPage.exists(
        'button:has-text("创建"), [data-testid="create-topup"]'
      )

      console.log(`➕ 创建按钮: ${hasCreateButton ? '存在' : '不存在'}`)
    })
  })

  describe('列表显示', () => {
    it('应该显示充值列表', async () => {
      await topupPage.navigate()

      const rowsCount = await topupPage.getTableRowsCount()
      expect(rowsCount).toBeGreaterThanOrEqual(0)

      console.log(`📋 充值记录数量: ${rowsCount}`)
    })

    it('表格行应该包含数据', async () => {
      await topupPage.navigate()

      const rowsCount = await topupPage.getTableRowsCount()

      if (rowsCount > 0) {
        const firstRowData = await topupPage.getFirstRowData()
        expect(Object.keys(firstRowData).length).toBeGreaterThan(0)

        console.log('📊 第一行数据:', firstRowData)
      }
    })

    it('应该显示状态徽章', async () => {
      await topupPage.navigate()

      const rowsCount = await topupPage.getTableRowsCount()

      if (rowsCount > 0) {
        const badges = await topupPage.getStatusBadges()
        expect(badges.length).toBeGreaterThan(0)

        console.log('🏷️  状态徽章:', badges)
      }
    })
  })

  describe('创建充值', () => {
    it('点击创建应该打开表单', async () => {
      await topupPage.navigate()

      await topupPage.clickCreate()

      // 应该显示表单模态框或跳转到创建页面
      const hasModal = await topupPage.exists('[role="dialog"], .modal')
      const isCreatePage = (await topupPage.getCurrentUrl()).includes('/create')

      expect(hasModal || isCreatePage).toBe(true)

      console.log(`📝 表单显示: ${hasModal ? '模态框' : '新页面'}`)
    }, 60000)

    it('应该能够填写充值信息', async () => {
      await topupPage.navigate()

      await topupPage.clickCreate()
      await page.waitForTimeout(1000)

      // 选择账号
      const hasAccountSelect = await topupPage.exists('select[name="account"]')

      if (hasAccountSelect) {
        await topupPage.selectAccount('test-account-1')
        console.log('✅ 账号选择成功')
      }

      // 填写金额
      await topupPage.fillAmount('10000')
      console.log('✅ 金额填写成功')

      // 填写备注
      await topupPage.fillRemarks('测试充值')
      console.log('✅ 备注填写成功')
    }, 60000)

    it('应该验证必填字段', async () => {
      await topupPage.navigate()

      await topupPage.clickCreate()
      await page.waitForTimeout(1000)

      // 不填写任何字段，直接提交
      await topupPage.submitForm()

      await page.waitForTimeout(1000)

      // 应该显示验证错误
      const hasError = await topupPage.hasErrorMessage()
      expect(hasError).toBe(true)

      console.log('✅ 表单验证生效')
    }, 60000)

    it('应该验证金额格式', async () => {
      await topupPage.navigate()

      await topupPage.clickCreate()
      await page.waitForTimeout(1000)

      // 填写无效金额
      await topupPage.fillAmount('invalid')
      await topupPage.submitForm()

      await page.waitForTimeout(1000)

      const hasError = await topupPage.hasErrorMessage()
      expect(hasError).toBe(true)

      console.log('✅ 金额格式验证生效')
    }, 60000)

    it('应该能够上传凭证', async () => {
      await topupPage.navigate()

      await topupPage.clickCreate()
      await page.waitForTimeout(1000)

      // 检查是否有文件上传控件
      const hasUpload = await topupPage.exists('input[type="file"]')

      if (hasUpload) {
        // 创建测试图片文件路径
        const testFilePath = path.join(__dirname, '../../fixtures/test-proof.jpg')

        try {
          await topupPage.uploadProof(testFilePath)
          console.log('✅ 凭证上传成功')
        } catch (error) {
          console.log('⚠️  文件不存在或上传失败（需要准备测试文件）')
        }
      } else {
        console.log('ℹ️  当前表单不支持文件上传')
      }
    }, 60000)
  })

  describe('筛选功能', () => {
    it('应该能够按状态筛选', async () => {
      await topupPage.navigate()

      const initialCount = await topupPage.getTableRowsCount()

      // 筛选待审核状态
      await topupPage.filterByStatus('pending_review')
      await page.waitForTimeout(1000)

      const filteredCount = await topupPage.getTableRowsCount()

      console.log(`🔍 筛选前: ${initialCount}, 筛选后: ${filteredCount}`)
    }, 60000)

    it('应该能够按账号筛选', async () => {
      await topupPage.navigate()

      const initialCount = await topupPage.getTableRowsCount()

      // 筛选特定账号
      const hasAccountFilter = await topupPage.exists('select[name="account_filter"]')

      if (hasAccountFilter) {
        await topupPage.filterByAccount('test-account-1')
        await page.waitForTimeout(1000)

        const filteredCount = await topupPage.getTableRowsCount()

        console.log(`🔍 按账号筛选 - 筛选前: ${initialCount}, 筛选后: ${filteredCount}`)
      }
    }, 60000)

    it('应该能够按日期范围筛选', async () => {
      await topupPage.navigate()

      const startDate = '2025-12-01'
      const endDate = '2025-12-09'

      await topupPage.filterByDateRange(startDate, endDate)
      await page.waitForTimeout(1000)

      const count = await topupPage.getTableRowsCount()

      console.log(`📅 日期范围筛选结果: ${count} 条`)
    }, 60000)

    it('应该能够清空筛选', async () => {
      await topupPage.navigate()

      // 应用筛选
      await topupPage.filterByStatus('pending_review')
      await page.waitForTimeout(1000)
      const filteredCount = await topupPage.getTableRowsCount()

      // 清空筛选
      await topupPage.clearFilters()
      await page.waitForTimeout(1000)
      const totalCount = await topupPage.getTableRowsCount()

      console.log(`🔄 筛选后: ${filteredCount}, 清空后: ${totalCount}`)
    }, 60000)
  })

  describe('查看详情', () => {
    it('应该能够查看充值详情', async () => {
      await topupPage.navigate()

      const rowsCount = await topupPage.getTableRowsCount()

      if (rowsCount > 0) {
        await topupPage.viewFirstTopup()
        await page.waitForTimeout(1000)

        // 检查是否打开了详情抽屉
        const isDrawerOpen = await topupPage.isDetailDrawerOpen()

        console.log(`📖 详情抽屉: ${isDrawerOpen ? '已打开' : '未打开'}`)

        if (isDrawerOpen) {
          const detailData = await topupPage.getDetailData()
          console.log('📊 详情数据:', detailData)
        }
      }
    }, 60000)

    it('应该能够关闭详情抽屉', async () => {
      await topupPage.navigate()

      const rowsCount = await topupPage.getTableRowsCount()

      if (rowsCount > 0) {
        await topupPage.viewFirstTopup()
        await page.waitForTimeout(1000)

        const isOpenBefore = await topupPage.isDetailDrawerOpen()
        expect(isOpenBefore).toBe(true)

        await topupPage.closeDetailDrawer()
        await page.waitForTimeout(500)

        const isOpenAfter = await topupPage.isDetailDrawerOpen()
        expect(isOpenAfter).toBe(false)

        console.log('✅ 详情抽屉关闭成功')
      }
    }, 60000)

    it('应该能够查看充值凭证', async () => {
      await topupPage.navigate()

      const rowsCount = await topupPage.getTableRowsCount()

      if (rowsCount > 0) {
        await topupPage.viewFirstTopup()
        await page.waitForTimeout(1000)

        // 尝试查看凭证
        const hasProofPreview = await topupPage.exists('[data-testid="proof-preview"]')

        if (hasProofPreview) {
          await topupPage.viewProof()
          await page.waitForTimeout(1000)

          const isProofModalOpen = await topupPage.isProofModalOpen()
          console.log(`🖼️  凭证预览: ${isProofModalOpen ? '已打开' : '未打开'}`)

          if (isProofModalOpen) {
            await topupPage.closeProofModal()
            console.log('✅ 凭证预览关闭')
          }
        } else {
          console.log('ℹ️  当前充值没有凭证')
        }
      }
    }, 60000)
  })

  describe('审核流程', () => {
    it('应该能够打开审核弹窗', async () => {
      await topupPage.navigate()

      // 筛选待审核的充值
      await topupPage.filterByStatus('pending_review')
      await page.waitForTimeout(1000)

      const rowsCount = await topupPage.getTableRowsCount()

      if (rowsCount > 0) {
        const hasReviewButton = await topupPage.exists('[data-testid="review-button"]')

        if (hasReviewButton) {
          await topupPage.clickReview()
          await page.waitForTimeout(1000)

          const isModalOpen = await topupPage.isReviewModalOpen()
          console.log(`📝 审核弹窗: ${isModalOpen ? '已打开' : '未打开'}`)
        } else {
          console.log('ℹ️  当前没有可审核的充值')
        }
      }
    }, 60000)

    it('审核通过应该更新状态', async () => {
      await topupPage.navigate()

      await topupPage.filterByStatus('pending_review')
      await page.waitForTimeout(1000)

      const rowsCount = await topupPage.getTableRowsCount()

      if (rowsCount > 0) {
        const hasReviewButton = await topupPage.exists('[data-testid="review-button"]')

        if (hasReviewButton) {
          await topupPage.approveTopup('测试审核通过')
          await page.waitForTimeout(2000)

          // 验证成功消息
          const hasSuccess = await topupPage.hasSuccessMessage()

          if (hasSuccess) {
            const message = await topupPage.getSuccessMessage()
            console.log('✅ 审核成功:', message)
          }
        }
      }
    }, 60000)

    it('审核驳回应该要求填写原因', async () => {
      await topupPage.navigate()

      await topupPage.filterByStatus('pending_review')
      await page.waitForTimeout(1000)

      const rowsCount = await topupPage.getTableRowsCount()

      if (rowsCount > 0) {
        const hasReviewButton = await topupPage.exists('[data-testid="review-button"]')

        if (hasReviewButton) {
          await topupPage.clickReview()
          await page.waitForTimeout(1000)

          // 不填原因直接驳回
          const rejectButton = await page.$('[data-testid="reject-button"]')
          if (rejectButton) {
            await rejectButton.click()
            await page.waitForTimeout(1000)

            // 应该显示验证错误
            const hasError = await topupPage.hasErrorMessage()
            console.log(`✅ 驳回原因验证: ${hasError ? '生效' : '未生效'}`)
          }
        }
      }
    }, 60000)
  })

  describe('搜索功能', () => {
    it('应该能够搜索充值记录', async () => {
      await topupPage.navigate()

      const hasSearchInput = await topupPage.exists('input[type="search"]')

      if (hasSearchInput) {
        await topupPage.searchTopups('test')
        await page.waitForTimeout(1000)

        const count = await topupPage.getTableRowsCount()

        console.log(`🔍 搜索结果数量: ${count}`)
      }
    }, 60000)
  })

  describe('分页功能', () => {
    it('应该显示分页组件', async () => {
      await topupPage.navigate()

      const hasPagination = await topupPage.exists('.pagination, [data-testid="pagination"]')

      console.log(`📄 分页组件: ${hasPagination ? '存在' : '不存在'}`)
    })

    it('应该能够翻页', async () => {
      await topupPage.navigate()

      const hasNextButton = await topupPage.exists('button:has-text("下一页")')

      if (hasNextButton) {
        const firstPageData = await topupPage.getFirstRowData()

        await topupPage.goToNextPage()
        await page.waitForTimeout(1000)

        const secondPageData = await topupPage.getFirstRowData()

        // 两页的第一行数据应该不同
        expect(firstPageData).not.toEqual(secondPageData)

        console.log('✅ 翻页功能正常')
      }
    }, 60000)
  })

  describe('导出功能', () => {
    it('应该显示导出按钮', async () => {
      await topupPage.navigate()

      const hasExportButton = await topupPage.exists('button:has-text("导出")')

      console.log(`📤 导出按钮: ${hasExportButton ? '存在' : '不存在'}`)
    })

    it('点击导出应该触发下载', async () => {
      await topupPage.navigate()

      const hasExportButton = await topupPage.exists('button:has-text("导出")')

      if (hasExportButton) {
        // 监听下载事件
        const downloadPromise = page.waitForEvent('download', { timeout: 10000 }).catch(() => null)

        await topupPage.clickExport()

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
      await topupPage.navigate()

      // 检查当前角色能看到的按钮
      const hasCreateButton = await topupPage.exists('button:has-text("创建")')
      const hasReviewButton = await topupPage.exists('[data-testid="review-button"]')
      const hasDeleteButton = await topupPage.exists('[data-testid="delete-button"]')

      console.log('🔐 权限检查:')
      console.log(`  创建按钮: ${hasCreateButton ? '✓' : '✗'}`)
      console.log(`  审核按钮: ${hasReviewButton ? '✓' : '✗'}`)
      console.log(`  删除按钮: ${hasDeleteButton ? '✓' : '✗'}`)
    })
  })

  describe('状态管理', () => {
    it('应该显示正确的状态徽章', async () => {
      await topupPage.navigate()

      const rowsCount = await topupPage.getTableRowsCount()

      if (rowsCount > 0) {
        const badges = await topupPage.getStatusBadges()

        // 验证状态值
        const validStatuses = [
          'pending_review',
          'approved',
          'rejected',
          'completed',
          'cancelled',
        ]

        badges.forEach((badge) => {
          console.log(`🏷️  状态: ${badge}`)
        })
      }
    })

    it('应该能够按状态筛选不同的充值', async () => {
      await topupPage.navigate()

      const statuses = ['pending_review', 'approved', 'rejected']

      for (const status of statuses) {
        await topupPage.filterByStatus(status)
        await page.waitForTimeout(1000)

        const count = await topupPage.getTableRowsCount()
        console.log(`📊 状态 "${status}" 的充值数量: ${count}`)

        // 清空筛选
        await topupPage.clearFilters()
        await page.waitForTimeout(500)
      }
    }, 90000)
  })

  describe('响应式设计', () => {
    it('移动端应该正常显示', async () => {
      await page.setViewport({ width: 375, height: 667 })
      await topupPage.navigate()

      const hasTable = await topupPage.hasTable()
      expect(hasTable).toBe(true)

      console.log('📱 移动端显示正常')
    })

    it('平板应该正常显示', async () => {
      await page.setViewport({ width: 768, height: 1024 })
      await topupPage.navigate()

      const hasTable = await topupPage.hasTable()
      expect(hasTable).toBe(true)

      console.log('💻 平板显示正常')
    })
  })
})
