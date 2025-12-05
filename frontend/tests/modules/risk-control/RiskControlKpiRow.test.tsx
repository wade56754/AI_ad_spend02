/**
 * RiskControlKpiRow 组件测试
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { RiskControlKpiRow } from '@/modules/risk-control/components/RiskControlKpiRow'
import type { RiskLevel, AlertStatus } from '@/modules/risk-control'

describe('RiskControlKpiRow', () => {
  const mockStats = {
    total: 20,
    byLevel: {
      low: 5,
      medium: 8,
      high: 4,
      critical: 3,
    } as Record<RiskLevel, number>,
    byStatus: {
      active: 6,
      acknowledged: 4,
      resolved: 8,
      dismissed: 2,
    } as Record<AlertStatus, number>,
    activeCount: 10, // active + acknowledged
  }

  it('应该正确渲染严重风险数量', () => {
    render(<RiskControlKpiRow stats={mockStats} />)

    expect(screen.getByText('严重风险')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('应该正确渲染高风险数量', () => {
    render(<RiskControlKpiRow stats={mockStats} />)

    expect(screen.getByText('高风险')).toBeInTheDocument()
    expect(screen.getByText('4')).toBeInTheDocument()
  })

  it('应该正确渲染待处理数量', () => {
    render(<RiskControlKpiRow stats={mockStats} />)

    expect(screen.getByText('待处理')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
  })

  it('应该正确渲染已解决数量', () => {
    render(<RiskControlKpiRow stats={mockStats} />)

    expect(screen.getByText('已解决')).toBeInTheDocument()
    expect(screen.getByText('8')).toBeInTheDocument()
  })

  it('应该渲染四个 KPI 卡片', () => {
    const { container } = render(<RiskControlKpiRow stats={mockStats} />)

    const kpiCards = container.querySelectorAll('.rounded-lg')
    expect(kpiCards.length).toBe(4)
  })

  it('零值应该正确显示', () => {
    const zeroStats = {
      total: 0,
      byLevel: {
        low: 0,
        medium: 0,
        high: 0,
        critical: 0,
      } as Record<RiskLevel, number>,
      byStatus: {
        active: 0,
        acknowledged: 0,
        resolved: 0,
        dismissed: 0,
      } as Record<AlertStatus, number>,
      activeCount: 0,
    }

    render(<RiskControlKpiRow stats={zeroStats} />)

    const zeros = screen.getAllByText('0')
    expect(zeros.length).toBe(4)
  })

  it('应该有正确的图标颜色', () => {
    const { container } = render(<RiskControlKpiRow stats={mockStats} />)

    // 严重风险应该是红色 (danger)
    const dangerIcons = container.querySelectorAll('.text-danger')
    expect(dangerIcons.length).toBeGreaterThan(0)

    // 已解决应该是绿色 (success)
    const successIcons = container.querySelectorAll('.text-success')
    expect(successIcons.length).toBeGreaterThan(0)
  })
})
