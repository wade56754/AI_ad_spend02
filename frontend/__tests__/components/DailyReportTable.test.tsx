/**
 * DailyReportTable 组件单元测试
 * 测试日报表格组件（包含 API 交互）
 */

import { render, screen, waitFor } from '../../tests/test-utils'
import { renderWithProviders } from '../../tests/test-utils'
import {
  setupFetchMock,
  resetFetchMock,
  mockFetchSuccess,
  mockPaginatedResponse,
} from '../../tests/mocks'
import { dailyReportFactory } from '../../tests/factories'
import { DailyReportTable } from '@/components/daily-reports/DailyReportTable'

describe('DailyReportTable Component', () => {
  beforeEach(() => {
    setupFetchMock()
  })

  afterEach(() => {
    resetFetchMock()
    jest.clearAllMocks()
  })

  describe('数据加载', () => {
    it('应该显示加载状态', () => {
      mockFetchSuccess([])  // Mock API

      renderWithProviders(<DailyReportTable />)

      // 应该显示加载指示器
      expect(screen.getByText(/加载中|Loading/i)).toBeInTheDocument()
    })

    it('应该加载并显示日报数据', async () => {
      const mockReports = dailyReportFactory.buildMany(3)

      mockFetchSuccess(mockPaginatedResponse(mockReports))

      renderWithProviders(<DailyReportTable />)

      // 等待数据加载
      await waitFor(() => {
        expect(screen.queryByText(/加载中|Loading/i)).not.toBeInTheDocument()
      })

      // 验证表格显示
      expect(screen.getByRole('table')).toBeInTheDocument()

      // 验证数据行数
      const rows = screen.getAllByRole('row')
      expect(rows.length).toBeGreaterThan(3)  // 包含表头
    })

    it('应该显示空数据提示', async () => {
      mockFetchSuccess(mockPaginatedResponse([]))

      renderWithProviders(<DailyReportTable />)

      await waitFor(() => {
        expect(screen.getByText(/暂无数据|No Data/i)).toBeInTheDocument()
      })
    })
  })

  describe('表格列', () => {
    it('应该显示所有必需的列', async () => {
      const mockReports = dailyReportFactory.buildMany(1)

      mockFetchSuccess(mockPaginatedResponse(mockReports))

      renderWithProviders(<DailyReportTable />)

      await waitFor(() => {
        expect(screen.getByText(/日期|Date/i)).toBeInTheDocument()
      })

      // 验证表头
      expect(screen.getByText(/状态|Status/i)).toBeInTheDocument()
      expect(screen.getByText(/消耗|Spend/i)).toBeInTheDocument()
      expect(screen.getByText(/转化|Conversion/i)).toBeInTheDocument()
      expect(screen.getByText(/操作|Action/i)).toBeInTheDocument()
    })

    it('应该显示正确的数据', async () => {
      const mockReport = dailyReportFactory.build({
        report_date: '2025-12-09',
        conversions_raw: 100,
        raw_spend: '1000.00',
      })

      mockFetchSuccess(mockPaginatedResponse([mockReport]))

      renderWithProviders(<DailyReportTable />)

      await waitFor(() => {
        expect(screen.getByText('2025-12-09')).toBeInTheDocument()
      })

      expect(screen.getByText('100')).toBeInTheDocument()
      expect(screen.getByText(/1000/)).toBeInTheDocument()
    })
  })

  describe('分页', () => {
    it('应该显示分页组件', async () => {
      const mockReports = dailyReportFactory.buildMany(25)

      mockFetchSuccess(
        mockPaginatedResponse(mockReports.slice(0, 20), 1, 20, 25)
      )

      renderWithProviders(<DailyReportTable />)

      await waitFor(() => {
        expect(screen.getByRole('navigation')).toBeInTheDocument()
      })

      // 应该有下一页按钮
      expect(screen.getByText(/下一页|Next/i)).toBeInTheDocument()
    })

    it('应该能够切换页码', async () => {
      const mockReports = dailyReportFactory.buildMany(25)
      const page1 = mockReports.slice(0, 20)
      const page2 = mockReports.slice(20, 25)

      // Mock 第一页
      mockFetchSuccess(mockPaginatedResponse(page1, 1, 20, 25))

      const { queryClient } = renderWithProviders(<DailyReportTable />)

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Mock 第二页
      mockFetchSuccess(mockPaginatedResponse(page2, 2, 20, 25))

      // 点击下一页
      const nextButton = screen.getByText(/下一页|Next/i)
      await nextButton.click()

      await waitFor(() => {
        // 第二页的数据应该显示
        expect(queryClient.getQueryState(['dailyReports', { page: 2 }])).toBeTruthy()
      })
    })
  })

  describe('筛选', () => {
    it('应该能够按状态筛选', async () => {
      const mockReports = dailyReportFactory.buildMany(3, {
        status: 'raw_submitted',
      })

      mockFetchSuccess(mockPaginatedResponse(mockReports))

      renderWithProviders(<DailyReportTable />)

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument()  // 状态下拉框
      })

      const statusSelect = screen.getByRole('combobox')
      await statusSelect.click()

      // 选择状态
      const option = screen.getByText('raw_submitted')
      await option.click()

      // 应该触发新的查询
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('status=raw_submitted'),
          expect.any(Object)
        )
      })
    })
  })

  describe('行操作', () => {
    it('应该显示操作按钮', async () => {
      const mockReports = dailyReportFactory.buildMany(1)

      mockFetchSuccess(mockPaginatedResponse(mockReports))

      renderWithProviders(<DailyReportTable />)

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // 应该有查看、编辑、删除按钮
      expect(screen.getByTitle(/查看|View/i)).toBeInTheDocument()
      expect(screen.getByTitle(/编辑|Edit/i)).toBeInTheDocument()
      expect(screen.getByTitle(/删除|Delete/i)).toBeInTheDocument()
    })

    it('点击查看应该打开详情', async () => {
      const mockReport = dailyReportFactory.build()

      mockFetchSuccess(mockPaginatedResponse([mockReport]))

      const onView = jest.fn()

      renderWithProviders(<DailyReportTable onView={onView} />)

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      const viewButton = screen.getByTitle(/查看|View/i)
      await viewButton.click()

      expect(onView).toHaveBeenCalledWith(mockReport)
    })

    it('点击删除应该显示确认对话框', async () => {
      const mockReport = dailyReportFactory.build()

      mockFetchSuccess(mockPaginatedResponse([mockReport]))

      renderWithProviders(<DailyReportTable />)

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      const deleteButton = screen.getByTitle(/删除|Delete/i)
      await deleteButton.click()

      // 应该显示确认对话框
      await waitFor(() => {
        expect(screen.getByText(/确认删除|Confirm Delete/i)).toBeInTheDocument()
      })
    })
  })

  describe('错误处理', () => {
    it('应该显示错误消息', async () => {
      // Mock API 错误
      ;(global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

      renderWithProviders(<DailyReportTable />)

      await waitFor(() => {
        expect(screen.getByText(/错误|Error/i)).toBeInTheDocument()
      })
    })

    it('应该能够重试加载', async () => {
      // Mock API 错误
      ;(global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

      renderWithProviders(<DailyReportTable />)

      await waitFor(() => {
        expect(screen.getByText(/重试|Retry/i)).toBeInTheDocument()
      })

      // Mock 成功响应
      const mockReports = dailyReportFactory.buildMany(3)
      mockFetchSuccess(mockPaginatedResponse(mockReports))

      // 点击重试
      const retryButton = screen.getByText(/重试|Retry/i)
      await retryButton.click()

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })
    })
  })

  describe('排序', () => {
    it('应该能够按列排序', async () => {
      const mockReports = dailyReportFactory.buildMany(3)

      mockFetchSuccess(mockPaginatedResponse(mockReports))

      renderWithProviders(<DailyReportTable />)

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // 点击日期列标题
      const dateHeader = screen.getByText(/日期|Date/i)
      await dateHeader.click()

      // 应该触发排序查询
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('sort='),
          expect.any(Object)
        )
      })
    })
  })

  describe('响应式设计', () => {
    it('移动端应该显示简化视图', async () => {
      const mockReports = dailyReportFactory.buildMany(3)

      mockFetchSuccess(mockPaginatedResponse(mockReports))

      // 设置移动端视口
      global.innerWidth = 375

      renderWithProviders(<DailyReportTable />)

      await waitFor(() => {
        const container = screen.getByRole('table').parentElement
        expect(container?.className).toMatch(/mobile|sm:/)
      })
    })
  })
})
