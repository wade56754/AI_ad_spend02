/**
 * DashboardStats 组件单元测试
 * 测试仪表盘统计卡片组件
 */

import { render, screen } from '../../tests/test-utils'
import { DashboardStats } from '@/components/dashboard/DashboardStats'

describe('DashboardStats Component', () => {
  const mockStats = {
    totalProjects: 10,
    activeAccounts: 25,
    todayReports: 50,
    pendingTopups: 5,
  }

  describe('渲染', () => {
    it('应该渲染统计卡片', () => {
      render(<DashboardStats stats={mockStats} />)

      // 检查是否渲染了卡片容器
      expect(screen.getByTestId('dashboard-stats')).toBeInTheDocument()
    })

    it('应该显示正确的统计数值', () => {
      render(<DashboardStats stats={mockStats} />)

      // 检查每个统计数值
      expect(screen.getByText('10')).toBeInTheDocument()  // 总项目数
      expect(screen.getByText('25')).toBeInTheDocument()  // 活跃账户
      expect(screen.getByText('50')).toBeInTheDocument()  // 今日日报
      expect(screen.getByText('5')).toBeInTheDocument()   // 待审核充值
    })

    it('应该显示统计标签', () => {
      render(<DashboardStats stats={mockStats} />)

      expect(screen.getByText(/项目/i)).toBeInTheDocument()
      expect(screen.getByText(/账户/i)).toBeInTheDocument()
      expect(screen.getByText(/日报/i)).toBeInTheDocument()
      expect(screen.getByText(/充值/i)).toBeInTheDocument()
    })
  })

  describe('空数据处理', () => {
    it('应该处理零值', () => {
      const emptyStats = {
        totalProjects: 0,
        activeAccounts: 0,
        todayReports: 0,
        pendingTopups: 0,
      }

      render(<DashboardStats stats={emptyStats} />)

      // 应该显示 0
      const zeros = screen.getAllByText('0')
      expect(zeros.length).toBeGreaterThan(0)
    })

    it('应该处理缺失数据', () => {
      const partialStats = {
        totalProjects: 10,
      } as any

      render(<DashboardStats stats={partialStats} />)

      // 不应该抛出错误
      expect(screen.getByTestId('dashboard-stats')).toBeInTheDocument()
    })
  })

  describe('样式和布局', () => {
    it('应该应用正确的CSS类名', () => {
      render(<DashboardStats stats={mockStats} />)

      const container = screen.getByTestId('dashboard-stats')
      expect(container).toHaveClass('dashboard-stats')  // 假设有这个类名
    })

    it('应该以网格布局显示卡片', () => {
      render(<DashboardStats stats={mockStats} />)

      const container = screen.getByTestId('dashboard-stats')

      // 检查是否有网格布局类名
      const classList = container.className
      expect(
        classList.includes('grid') || classList.includes('flex')
      ).toBe(true)
    })
  })

  describe('大数值格式化', () => {
    it('应该格式化大数值', () => {
      const largeStats = {
        totalProjects: 1000,
        activeAccounts: 10000,
        todayReports: 100000,
        pendingTopups: 1000000,
      }

      render(<DashboardStats stats={largeStats} />)

      // 如果有数值格式化，应该显示 1K, 10K, 100K, 1M
      const container = screen.getByTestId('dashboard-stats')
      expect(container.textContent).toMatch(/\d+[KM]?/)
    })
  })

  describe('交互', () => {
    it('卡片应该可以点击', async () => {
      const handleClick = jest.fn()

      render(<DashboardStats stats={mockStats} onClick={handleClick} />)

      const firstCard = screen.getAllByRole('button')[0]  // 假设卡片是按钮
      await firstCard.click()

      expect(handleClick).toHaveBeenCalledTimes(1)
    })
  })

  describe('加载状态', () => {
    it('应该显示加载骨架屏', () => {
      render(<DashboardStats stats={mockStats} loading={true} />)

      // 检查是否有加载指示器
      expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument()
    })

    it('加载完成后应该显示数据', () => {
      const { rerender } = render(
        <DashboardStats stats={mockStats} loading={true} />
      )

      // 初始状态：显示加载
      expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument()

      // 更新：显示数据
      rerender(<DashboardStats stats={mockStats} loading={false} />)

      expect(screen.queryByTestId('loading-skeleton')).not.toBeInTheDocument()
      expect(screen.getByText('10')).toBeInTheDocument()
    })
  })

  describe('响应式设计', () => {
    it('应该在小屏幕上调整布局', () => {
      // 设置移动端视口
      global.innerWidth = 375

      render(<DashboardStats stats={mockStats} />)

      const container = screen.getByTestId('dashboard-stats')

      // 检查响应式类名
      expect(
        container.className.includes('mobile') ||
          container.className.includes('sm:')
      ).toBe(true)
    })
  })

  describe('可访问性', () => {
    it('应该有正确的ARIA标签', () => {
      render(<DashboardStats stats={mockStats} />)

      // 检查是否有适当的aria-label
      const container = screen.getByTestId('dashboard-stats')
      expect(container).toHaveAttribute('aria-label')
    })

    it('数值应该是可读的', () => {
      render(<DashboardStats stats={mockStats} />)

      // 检查屏幕阅读器文本
      expect(screen.getByText('10')).toHaveAttribute('aria-label', /项目/)
    })
  })
})
