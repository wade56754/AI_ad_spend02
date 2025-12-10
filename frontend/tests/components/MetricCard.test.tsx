/**
 * MetricCard组件测试
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import MetricCard from '@/components/ui/MetricCard'

describe('MetricCard', () => {
  const defaultProps = {
    title: '测试指标',
    value: '$1,234.56',
    change: 12.5,
    changeType: 'up' as const,
    icon: <div data-testid="test-icon">Icon</div>
  }

  it('应该正确渲染基本指标卡片', () => {
    render(<MetricCard {...defaultProps} />)

    expect(screen.getByText('测试指标')).toBeInTheDocument()
    expect(screen.getByText('$1,234.56')).toBeInTheDocument()
    expect(screen.getByTestId('test-icon')).toBeInTheDocument()
  })

  it('应该显示正数变化趋势', () => {
    render(<MetricCard {...defaultProps} />)

    expect(screen.getByText('+12.5%')).toBeInTheDocument()
    // 应该显示上升趋势的样式或图标
  })

  it('应该显示负数变化趋势', () => {
    const props = {
      ...defaultProps,
      change: -5.2,
      changeType: 'down' as const
    }
    render(<MetricCard {...props} />)

    expect(screen.getByText('-5.2%')).toBeInTheDocument()
  })

  it('应该显示中性变化趋势', () => {
    const props = {
      ...defaultProps,
      change: 0,
      changeType: 'neutral' as const
    }
    render(<MetricCard {...props} />)

    expect(screen.getByText('0%')).toBeInTheDocument()
  })

  it('应该支持自定义颜色', () => {
    const props = {
      ...defaultProps,
      color: 'blue' as const
    }
    render(<MetricCard {...props} />)

    const card = screen.getByText('测试指标').closest('[data-testid="metric-card"]')
    expect(card).toHaveClass('text-blue-600') // 或相应的颜色类
  })

  it('应该支持自定义描述文本', () => {
    const props = {
      ...defaultProps,
      subtitle: '相比上个月'
    }
    render(<MetricCard {...props} />)

    expect(screen.getByText('相比上个月')).toBeInTheDocument()
  })

  it('应该处理空值或null值', () => {
    const props = {
      title: '测试指标',
      value: null,
      change: undefined,
      changeType: 'up' as const,
      icon: <div>Icon</div>
    }

    render(<MetricCard {...props} />)

    expect(screen.getByText('测试指标')).toBeInTheDocument()
    // 应该显示占位符或空值
  })

  it('应该支持点击事件', () => {
    const handleClick = vitest.fn()
    const props = {
      ...defaultProps,
      onClick: handleClick
    }

    render(<MetricCard {...props} />)

    const card = screen.getByTestId('metric-card') || screen.getByText('测试指标').closest('div')
    card?.click()

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('应该支持加载状态', () => {
    const props = {
      ...defaultProps,
      loading: true
    }
    render(<MetricCard {...props} />)

    expect(screen.getByTestId('metric-card')).toBeInTheDocument()
    // 可能显示骨架屏或加载指示器
  })
})