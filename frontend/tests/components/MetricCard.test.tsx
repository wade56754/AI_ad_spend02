/**
 * MetricCard组件测试
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { MetricCard } from '@/components/ui/MetricCard'
import { TrendingUp } from 'lucide-react'

describe('MetricCard', () => {
  const defaultProps = {
    title: '测试指标',
    value: '$1,234.56',
    change: 12.5,
    changeType: 'up' as const,
    icon: TrendingUp // 传递组件类型而非 JSX 元素
  }

  it('应该正确渲染基本指标卡片', () => {
    render(<MetricCard {...defaultProps} />)

    expect(screen.getByText('测试指标')).toBeInTheDocument()
    expect(screen.getByText('$1,234.56')).toBeInTheDocument()
  })

  it('应该显示正数变化趋势', () => {
    render(<MetricCard {...defaultProps} />)

    // 组件实际渲染格式是 "环比 +12.5%"
    expect(screen.getByText(/环比.*\+12\.5%/)).toBeInTheDocument()
  })

  it('应该显示负数变化趋势', () => {
    const props = {
      ...defaultProps,
      change: -5.2,
      changeType: 'down' as const
    }
    render(<MetricCard {...props} />)

    // 组件实际渲染格式是 "环比 -5.2%"
    expect(screen.getByText(/环比.*5\.2%/)).toBeInTheDocument()
  })

  it('应该显示中性变化趋势', () => {
    const props = {
      ...defaultProps,
      change: 0,
      changeType: 'neutral' as const
    }
    render(<MetricCard {...props} />)

    expect(screen.getByText(/环比.*0%/)).toBeInTheDocument()
  })

  it('应该正确处理不同颜色配置', () => {
    const colors = ['primary', 'success', 'warning', 'error', 'info'] as const

    colors.forEach(color => {
      const { unmount } = render(<MetricCard {...defaultProps} color={color} />)
      expect(screen.getByText('测试指标')).toBeInTheDocument()
      unmount()
    })
  })

  it('应该支持自定义描述文本', () => {
    const props = {
      ...defaultProps,
      description: '相比上个月'
    }
    render(<MetricCard {...props} />)

    expect(screen.getByText(/相比上个月/)).toBeInTheDocument()
  })

  it('应该处理无 change 的情况', () => {
    const props = {
      title: '测试指标',
      value: '100',
      icon: TrendingUp
    }

    render(<MetricCard {...props} />)

    expect(screen.getByText('测试指标')).toBeInTheDocument()
    expect(screen.getByText('100')).toBeInTheDocument()
    // 不应该显示环比信息
    expect(screen.queryByText(/环比/)).not.toBeInTheDocument()
  })

  it('应该支持点击事件', () => {
    const handleClick = jest.fn()
    const props = {
      ...defaultProps,
      onClick: handleClick
    }

    render(<MetricCard {...props} />)

    const card = screen.getByRole('button')
    fireEvent.click(card)

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('应该支持键盘交互', () => {
    const handleClick = jest.fn()
    const props = {
      ...defaultProps,
      onClick: handleClick
    }

    render(<MetricCard {...props} />)

    const card = screen.getByRole('button')
    fireEvent.keyDown(card, { key: 'Enter' })

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('应该支持加载状态', () => {
    const props = {
      ...defaultProps,
      loading: true
    }
    render(<MetricCard {...props} />)

    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.getByText('正在加载指标数据')).toBeInTheDocument()
  })

  it('应该支持不同尺寸', () => {
    const sizes = ['sm', 'md', 'lg'] as const

    sizes.forEach(size => {
      const { unmount } = render(<MetricCard {...defaultProps} size={size} />)
      expect(screen.getByText('测试指标')).toBeInTheDocument()
      unmount()
    })
  })

  it('没有 onClick 时应该是 region 角色', () => {
    render(<MetricCard {...defaultProps} />)

    expect(screen.getByRole('region')).toBeInTheDocument()
  })

  it('应该支持自定义 className', () => {
    render(<MetricCard {...defaultProps} className="custom-class" />)

    const card = screen.getByRole('region')
    expect(card).toHaveClass('custom-class')
  })
})
