/**
 * PageShell 组件测试
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Plus } from 'lucide-react'
import { PageShell } from '@/modules/shared'

describe('PageShell', () => {
  const defaultProps = {
    title: '测试页面',
    subtitle: '测试副标题',
  }

  it('应该正确渲染标题和副标题', () => {
    render(<PageShell {...defaultProps}>内容</PageShell>)

    expect(screen.getByText('测试页面')).toBeInTheDocument()
    expect(screen.getByText('测试副标题')).toBeInTheDocument()
  })

  it('应该渲染子内容', () => {
    render(
      <PageShell {...defaultProps}>
        <div data-testid="child-content">子内容</div>
      </PageShell>
    )

    expect(screen.getByTestId('child-content')).toBeInTheDocument()
    expect(screen.getByText('子内容')).toBeInTheDocument()
  })

  it('应该渲染主要操作按钮', () => {
    const handleClick = vi.fn()
    render(
      <PageShell
        {...defaultProps}
        primaryAction={{
          label: '新建',
          icon: Plus,
          onClick: handleClick,
        }}
      >
        内容
      </PageShell>
    )

    const button = screen.getByRole('button', { name: /新建/i })
    expect(button).toBeInTheDocument()

    fireEvent.click(button)
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('应该渲染筛选器选项', () => {
    const handleChange = vi.fn()
    render(
      <PageShell
        {...defaultProps}
        filterOptions={[
          {
            key: 'status',
            label: '状态',
            options: [
              { value: 'all', label: '全部' },
              { value: 'active', label: '活跃' },
            ],
            value: 'all',
            onChange: handleChange,
          },
        ]}
      >
        内容
      </PageShell>
    )

    // 筛选器应该渲染
    expect(screen.getByText('状态')).toBeInTheDocument()
  })

  it('应该渲染 KPI 区域', () => {
    render(
      <PageShell
        {...defaultProps}
        kpiSection={<div data-testid="kpi-section">KPI 内容</div>}
      >
        内容
      </PageShell>
    )

    expect(screen.getByTestId('kpi-section')).toBeInTheDocument()
  })

  it('应该应用自定义 className', () => {
    const { container } = render(
      <PageShell {...defaultProps} className="custom-class">
        内容
      </PageShell>
    )

    expect(container.firstChild).toHaveClass('custom-class')
  })

  it('只有标题时应该正常渲染', () => {
    render(<PageShell title="仅标题">内容</PageShell>)

    expect(screen.getByText('仅标题')).toBeInTheDocument()
  })
})
