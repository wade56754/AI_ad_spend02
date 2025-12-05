/**
 * useAdAccounts Hook 测试
 */

import { renderHook, act } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { useAdAccounts } from '@/modules/ad-accounts/hooks/useAdAccounts'

describe('useAdAccounts', () => {
  it('应该返回初始状态', () => {
    const { result } = renderHook(() => useAdAccounts())

    expect(result.current.accounts).toBeDefined()
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.stats).toBeDefined()
  })

  it('应该返回正确的统计数据', () => {
    const { result } = renderHook(() => useAdAccounts())

    expect(result.current.stats.total).toBeGreaterThan(0)
    expect(result.current.stats.byStatus).toHaveProperty('active')
    expect(result.current.stats.byStatus).toHaveProperty('paused')
    expect(result.current.stats.byStatus).toHaveProperty('dead')
  })

  it('应该根据状态筛选数据', () => {
    const { result } = renderHook(() => useAdAccounts())

    act(() => {
      result.current.setFilters({ status: 'active' })
    })

    result.current.accounts.forEach((account) => {
      expect(account.status).toBe('active')
    })
  })

  it('应该根据平台筛选数据', () => {
    const { result } = renderHook(() => useAdAccounts())

    act(() => {
      result.current.setFilters({ platform: 'tencent' })
    })

    result.current.accounts.forEach((account) => {
      expect(account.platform).toBe('tencent')
    })
  })

  it('应该支持初始筛选条件', () => {
    const { result } = renderHook(() =>
      useAdAccounts({ status: 'dead' })
    )

    expect(result.current.filters.status).toBe('dead')
  })

  it('应该计算总余额', () => {
    const { result } = renderHook(() => useAdAccounts())

    expect(result.current.stats.totalBalance).toBeGreaterThanOrEqual(0)
  })

  it('清空筛选应该返回所有数据', () => {
    const { result } = renderHook(() => useAdAccounts())
    const totalCount = result.current.accounts.length

    act(() => {
      result.current.setFilters({ status: 'active' })
    })

    act(() => {
      result.current.setFilters({})
    })

    expect(result.current.accounts.length).toBe(totalCount)
  })
})
