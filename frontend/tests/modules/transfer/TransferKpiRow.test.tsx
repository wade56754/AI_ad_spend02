/**
 * TransferKpiRow 组件测试
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { TransferKpiRow } from '@/modules/transfer/components/TransferKpiRow'
import type { TransferStatus } from '@/modules/transfer'

describe('TransferKpiRow', () => {
  const mockStats = {
    total: 10,
    byStatus: {
      draft: 2,
      approved: 3,
      completed: 4,
      rejected: 1,
    } as Record<TransferStatus, number>,
    totalAmount: 5000000, // 5万元 (分)
    pendingAmount: 1500000, // 1.5万元 (分)
  }

  it('应该正确渲染总迁移数', () => {
    render(<TransferKpiRow stats={mockStats} />)

    expect(screen.getByText('总迁移数')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
  })

  it('应该正确计算待处理数量（draft + approved）', () => {
    render(<TransferKpiRow stats={mockStats} />)

    expect(screen.getByText('待处理')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument() // 2 + 3 = 5
  })

  it('应该正确渲染已完成数量', () => {
    render(<TransferKpiRow stats={mockStats} />)

    expect(screen.getByText('已完成')).toBeInTheDocument()
    expect(screen.getByText('4')).toBeInTheDocument()
  })

  it('应该正确格式化待迁移金额', () => {
    render(<TransferKpiRow stats={mockStats} />)

    expect(screen.getByText('待迁移金额')).toBeInTheDocument()
    expect(screen.getByText('¥15,000')).toBeInTheDocument() // 1500000 分 = ¥15,000
  })

  it('应该渲染四个 KPI 卡片', () => {
    const { container } = render(<TransferKpiRow stats={mockStats} />)

    const kpiCards = container.querySelectorAll('.rounded-lg')
    expect(kpiCards.length).toBe(4)
  })

  it('零值应该正确显示', () => {
    const zeroStats = {
      total: 0,
      byStatus: {
        draft: 0,
        approved: 0,
        completed: 0,
        rejected: 0,
      } as Record<TransferStatus, number>,
      totalAmount: 0,
      pendingAmount: 0,
    }

    render(<TransferKpiRow stats={zeroStats} />)

    const zeros = screen.getAllByText('0')
    expect(zeros.length).toBeGreaterThanOrEqual(3)
  })
})
