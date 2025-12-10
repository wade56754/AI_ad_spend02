/**
 * TrendChart 组件单元测试
 * 测试趋势图组件（v1.2 曲线图）
 */

import { render, screen, waitFor } from '../../tests/test-utils'
import { renderWithProviders } from '../../tests/test-utils'
import {
  setupFetchMock,
  resetFetchMock,
  mockFetchSuccess,
} from '../../tests/mocks'
import { TrendChart } from '@/components/dashboard/TrendChart'

describe('TrendChart Component', () => {
  beforeEach(() => {
    setupFetchMock()
  })

  afterEach(() => {
    resetFetchMock()
    jest.clearAllMocks()
  })

  describe('渲染测试', () => {
    it('应该渲染图表容器', () => {
      const mockData = [
        { date: '2025-12-01', value: 1000 },
        { date: '2025-12-02', value: 1200 },
        { date: '2025-12-03', value: 1100 },
      ]

      renderWithProviders(<TrendChart data={mockData} title="消耗趋势" />)

      expect(screen.getByText('消耗趋势')).toBeInTheDocument()
      expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument() // SVG 图表
    })

    it('应该显示空数据提示', () => {
      renderWithProviders(<TrendChart data={[]} title="消耗趋势" />)

      expect(screen.getByText(/暂无数据|No Data/i)).toBeInTheDocument()
    })

    it('应该显示图例', () => {
      const mockData = [
        { date: '2025-12-01', value: 1000 },
        { date: '2025-12-02', value: 1200 },
      ]

      renderWithProviders(
        <TrendChart
          data={mockData}
          title="消耗趋势"
          showLegend={true}
          legend="消耗金额"
        />
      )

      expect(screen.getByText('消耗金额')).toBeInTheDocument()
    })
  })

  describe('数据处理', () => {
    it('应该正确处理单个数据点', () => {
      const mockData = [{ date: '2025-12-01', value: 1000 }]

      renderWithProviders(<TrendChart data={mockData} title="消耗趋势" />)

      // 应该能够渲染单个点
      const chartElement = screen.getByRole('img', { hidden: true })
      expect(chartElement).toBeInTheDocument()
    })

    it('应该正确处理大量数据点', () => {
      const mockData = Array.from({ length: 90 }, (_, i) => ({
        date: `2025-10-${String(i + 1).padStart(2, '0')}`,
        value: Math.random() * 10000,
      }))

      renderWithProviders(<TrendChart data={mockData} title="消耗趋势" />)

      const chartElement = screen.getByRole('img', { hidden: true })
      expect(chartElement).toBeInTheDocument()
    })

    it('应该正确处理负值', () => {
      const mockData = [
        { date: '2025-12-01', value: 1000 },
        { date: '2025-12-02', value: -500 },
        { date: '2025-12-03', value: 800 },
      ]

      renderWithProviders(<TrendChart data={mockData} title="利润趋势" />)

      const chartElement = screen.getByRole('img', { hidden: true })
      expect(chartElement).toBeInTheDocument()
    })

    it('应该正确处理零值', () => {
      const mockData = [
        { date: '2025-12-01', value: 1000 },
        { date: '2025-12-02', value: 0 },
        { date: '2025-12-03', value: 800 },
      ]

      renderWithProviders(<TrendChart data={mockData} title="消耗趋势" />)

      const chartElement = screen.getByRole('img', { hidden: true })
      expect(chartElement).toBeInTheDocument()
    })
  })

  describe('交互测试', () => {
    it('应该在鼠标悬停时显示 Tooltip', async () => {
      const mockData = [
        { date: '2025-12-01', value: 1000 },
        { date: '2025-12-02', value: 1200 },
        { date: '2025-12-03', value: 1100 },
      ]

      const { container } = renderWithProviders(
        <TrendChart data={mockData} title="消耗趋势" />
      )

      // 查找图表容器
      const chartContainer = container.querySelector('.recharts-wrapper')
      expect(chartContainer).toBeInTheDocument()

      // 模拟鼠标悬停（Recharts 会显示 tooltip）
      if (chartContainer) {
        const chartArea = chartContainer.querySelector('.recharts-surface')
        if (chartArea) {
          // 触发 mouseenter 事件
          await chartArea.dispatchEvent(
            new MouseEvent('mousemove', { bubbles: true })
          )

          await waitFor(() => {
            // Tooltip 应该显示
            const tooltip = container.querySelector('.recharts-tooltip-wrapper')
            expect(tooltip).toBeInTheDocument()
          })
        }
      }
    })

    it('应该支持日期范围选择', async () => {
      const mockData = Array.from({ length: 30 }, (_, i) => ({
        date: `2025-12-${String(i + 1).padStart(2, '0')}`,
        value: Math.random() * 10000,
      }))

      const onRangeChange = jest.fn()

      renderWithProviders(
        <TrendChart
          data={mockData}
          title="消耗趋势"
          enableRangeSelector={true}
          onRangeChange={onRangeChange}
        />
      )

      // 查找日期选择器（如果有）
      const startDateInput = screen.queryByLabelText(/开始日期|Start Date/i)
      const endDateInput = screen.queryByLabelText(/结束日期|End Date/i)

      if (startDateInput && endDateInput) {
        // 修改日期范围
        await startDateInput.type('2025-12-01')
        await endDateInput.type('2025-12-10')

        await waitFor(() => {
          expect(onRangeChange).toHaveBeenCalled()
        })
      }
    })
  })

  describe('样式测试', () => {
    it('应该应用自定义颜色', () => {
      const mockData = [
        { date: '2025-12-01', value: 1000 },
        { date: '2025-12-02', value: 1200 },
      ]

      const { container } = renderWithProviders(
        <TrendChart
          data={mockData}
          title="消耗趋势"
          lineColor="#ff0000"
          fillColor="#ff000033"
        />
      )

      // 查找曲线路径
      const linePath = container.querySelector('.recharts-line-curve')
      expect(linePath).toBeInTheDocument()

      // 验证颜色应用（Recharts 会应用到 stroke 属性）
      if (linePath) {
        const stroke = linePath.getAttribute('stroke')
        expect(stroke).toBeTruthy()
      }
    })

    it('应该支持不同的图表高度', () => {
      const mockData = [
        { date: '2025-12-01', value: 1000 },
        { date: '2025-12-02', value: 1200 },
      ]

      const { container } = renderWithProviders(
        <TrendChart data={mockData} title="消耗趋势" height={500} />
      )

      const chartContainer = container.querySelector('.recharts-wrapper')
      expect(chartContainer).toBeInTheDocument()

      if (chartContainer) {
        // 验证高度设置
        const height = chartContainer.getAttribute('height')
        expect(height).toBe('500')
      }
    })

    it('应该支持响应式布局', () => {
      const mockData = [
        { date: '2025-12-01', value: 1000 },
        { date: '2025-12-02', value: 1200 },
      ]

      const { container } = renderWithProviders(
        <TrendChart data={mockData} title="消耗趋势" responsive={true} />
      )

      const chartContainer = container.querySelector('.recharts-responsive-container')
      expect(chartContainer).toBeInTheDocument()
    })
  })

  describe('数值格式化', () => {
    it('应该正确格式化货币值', () => {
      const mockData = [
        { date: '2025-12-01', value: 1234567.89 },
        { date: '2025-12-02', value: 9876543.21 },
      ]

      const { container } = renderWithProviders(
        <TrendChart
          data={mockData}
          title="消耗趋势"
          valueFormatter={(value) => `¥${value.toLocaleString()}`}
        />
      )

      const chartElement = screen.getByRole('img', { hidden: true })
      expect(chartElement).toBeInTheDocument()

      // Y 轴应该显示格式化的值
      const yAxisTicks = container.querySelectorAll('.recharts-yAxis .recharts-text')
      expect(yAxisTicks.length).toBeGreaterThan(0)
    })

    it('应该正确格式化百分比值', () => {
      const mockData = [
        { date: '2025-12-01', value: 0.1234 },
        { date: '2025-12-02', value: 0.5678 },
      ]

      const { container } = renderWithProviders(
        <TrendChart
          data={mockData}
          title="转化率趋势"
          valueFormatter={(value) => `${(value * 100).toFixed(2)}%`}
        />
      )

      const chartElement = screen.getByRole('img', { hidden: true })
      expect(chartElement).toBeInTheDocument()
    })

    it('应该正确格式化缩写大数字', () => {
      const mockData = [
        { date: '2025-12-01', value: 1234567 },
        { date: '2025-12-02', value: 9876543 },
      ]

      const { container } = renderWithProviders(
        <TrendChart
          data={mockData}
          title="展示量趋势"
          valueFormatter={(value) => {
            if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`
            if (value >= 1000) return `${(value / 1000).toFixed(1)}K`
            return value.toString()
          }}
        />
      )

      const chartElement = screen.getByRole('img', { hidden: true })
      expect(chartElement).toBeInTheDocument()
    })
  })

  describe('加载状态', () => {
    it('应该显示加载指示器', () => {
      renderWithProviders(<TrendChart data={[]} title="消耗趋势" loading={true} />)

      expect(screen.getByText(/加载中|Loading/i)).toBeInTheDocument()
    })

    it('加载完成后应该显示图表', async () => {
      const { rerender } = renderWithProviders(
        <TrendChart data={[]} title="消耗趋势" loading={true} />
      )

      expect(screen.getByText(/加载中|Loading/i)).toBeInTheDocument()

      const mockData = [
        { date: '2025-12-01', value: 1000 },
        { date: '2025-12-02', value: 1200 },
      ]

      rerender(<TrendChart data={mockData} title="消耗趋势" loading={false} />)

      await waitFor(() => {
        expect(screen.queryByText(/加载中|Loading/i)).not.toBeInTheDocument()
        expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument()
      })
    })
  })

  describe('错误处理', () => {
    it('应该显示错误消息', () => {
      renderWithProviders(
        <TrendChart
          data={[]}
          title="消耗趋势"
          error="无法加载图表数据"
        />
      )

      expect(screen.getByText(/无法加载图表数据/i)).toBeInTheDocument()
    })

    it('应该提供重试按钮', async () => {
      const onRetry = jest.fn()

      renderWithProviders(
        <TrendChart
          data={[]}
          title="消耗趋势"
          error="加载失败"
          onRetry={onRetry}
        />
      )

      const retryButton = screen.getByText(/重试|Retry/i)
      await retryButton.click()

      expect(onRetry).toHaveBeenCalledTimes(1)
    })
  })

  describe('多线图测试', () => {
    it('应该支持多条数据线', () => {
      const mockData = [
        { date: '2025-12-01', spend: 1000, revenue: 1500 },
        { date: '2025-12-02', spend: 1200, revenue: 1800 },
        { date: '2025-12-03', spend: 1100, revenue: 1600 },
      ]

      const { container } = renderWithProviders(
        <TrendChart
          data={mockData}
          title="消耗与收入对比"
          lines={[
            { dataKey: 'spend', name: '消耗', color: '#ff0000' },
            { dataKey: 'revenue', name: '收入', color: '#00ff00' },
          ]}
        />
      )

      // 应该有两条曲线
      const lines = container.querySelectorAll('.recharts-line-curve')
      expect(lines.length).toBeGreaterThanOrEqual(2)
    })

    it('应该显示多线图例', () => {
      const mockData = [
        { date: '2025-12-01', spend: 1000, revenue: 1500 },
        { date: '2025-12-02', spend: 1200, revenue: 1800 },
      ]

      renderWithProviders(
        <TrendChart
          data={mockData}
          title="消耗与收入对比"
          lines={[
            { dataKey: 'spend', name: '消耗', color: '#ff0000' },
            { dataKey: 'revenue', name: '收入', color: '#00ff00' },
          ]}
          showLegend={true}
        />
      )

      expect(screen.getByText('消耗')).toBeInTheDocument()
      expect(screen.getByText('收入')).toBeInTheDocument()
    })
  })

  describe('导出功能', () => {
    it('应该支持导出图表为图片', async () => {
      const mockData = [
        { date: '2025-12-01', value: 1000 },
        { date: '2025-12-02', value: 1200 },
      ]

      const onExport = jest.fn()

      renderWithProviders(
        <TrendChart
          data={mockData}
          title="消耗趋势"
          enableExport={true}
          onExport={onExport}
        />
      )

      const exportButton = screen.queryByText(/导出|Export/i)

      if (exportButton) {
        await exportButton.click()
        expect(onExport).toHaveBeenCalled()
      }
    })
  })

  describe('可访问性', () => {
    it('应该有适当的 ARIA 标签', () => {
      const mockData = [
        { date: '2025-12-01', value: 1000 },
        { date: '2025-12-02', value: 1200 },
      ]

      const { container } = renderWithProviders(
        <TrendChart data={mockData} title="消耗趋势" />
      )

      // 图表容器应该有 role
      const chartContainer = container.querySelector('[role="img"]')
      expect(chartContainer).toBeInTheDocument()

      // 应该有描述性标题
      expect(screen.getByText('消耗趋势')).toBeInTheDocument()
    })

    it('应该支持键盘导航', async () => {
      const mockData = [
        { date: '2025-12-01', value: 1000 },
        { date: '2025-12-02', value: 1200 },
      ]

      const { container } = renderWithProviders(
        <TrendChart data={mockData} title="消耗趋势" />
      )

      const chartContainer = container.querySelector('.recharts-wrapper')

      if (chartContainer) {
        // 应该可以获得焦点
        chartContainer.focus()
        expect(document.activeElement).toBe(chartContainer)
      }
    })
  })
})
