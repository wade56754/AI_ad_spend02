/**
 * useTransfers Hook 测试
 *
 * 对齐：TRANSFER_SOT.md v1.0
 */

import { renderHook, act } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { useTransfers } from '@/modules/transfer/hooks/useTransfers'

describe('useTransfers', () => {
  it('应该返回初始状态', () => {
    const { result } = renderHook(() => useTransfers())

    expect(result.current.transfers).toBeDefined()
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.stats).toBeDefined()
  })

  it('应该返回正确的统计数据', () => {
    const { result } = renderHook(() => useTransfers())

    expect(result.current.stats.total).toBeGreaterThan(0)
    expect(result.current.stats.byStatus).toHaveProperty('draft')
    expect(result.current.stats.byStatus).toHaveProperty('approved')
    expect(result.current.stats.byStatus).toHaveProperty('completed')
    expect(result.current.stats.byStatus).toHaveProperty('rejected')
  })

  it('应该根据状态筛选数据', () => {
    const { result } = renderHook(() => useTransfers())

    act(() => {
      result.current.setFilters({ status: 'completed' })
    })

    const completedTransfers = result.current.transfers.filter(
      (t) => t.status === 'completed'
    )
    expect(result.current.transfers.length).toBe(completedTransfers.length)
  })

  it('应该支持初始筛选条件', () => {
    const { result } = renderHook(() =>
      useTransfers({ status: 'draft' })
    )

    expect(result.current.filters.status).toBe('draft')
  })

  it('应该计算待迁移金额', () => {
    const { result } = renderHook(() => useTransfers())

    expect(result.current.stats.pendingAmount).toBeGreaterThanOrEqual(0)
    expect(result.current.stats.totalAmount).toBeGreaterThanOrEqual(
      result.current.stats.pendingAmount
    )
  })

  it('应该能更新筛选条件', () => {
    const { result } = renderHook(() => useTransfers())

    act(() => {
      result.current.setFilters({ supplier_id: 'sup-001' })
    })

    expect(result.current.filters.supplier_id).toBe('sup-001')
  })

  it('清空筛选应该返回所有数据', () => {
    const { result } = renderHook(() => useTransfers())
    const totalCount = result.current.transfers.length

    act(() => {
      result.current.setFilters({ status: 'draft' })
    })

    act(() => {
      result.current.setFilters({})
    })

    expect(result.current.transfers.length).toBe(totalCount)
  })
})
