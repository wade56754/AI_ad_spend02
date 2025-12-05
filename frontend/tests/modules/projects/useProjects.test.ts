/**
 * useProjects Hook 测试
 */

import { renderHook, act } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { useProjects } from '@/modules/projects/hooks/useProjects'

describe('useProjects', () => {
  it('应该返回初始状态', () => {
    const { result } = renderHook(() => useProjects())

    expect(result.current.projects).toBeDefined()
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.stats).toBeDefined()
  })

  it('应该返回正确的统计数据', () => {
    const { result } = renderHook(() => useProjects())

    expect(result.current.stats.total).toBeGreaterThan(0)
    expect(result.current.stats.byStatus).toHaveProperty('active')
    expect(result.current.stats.byStatus).toHaveProperty('paused')
    expect(result.current.stats.byStatus).toHaveProperty('completed')
  })

  it('应该根据状态筛选数据', () => {
    const { result } = renderHook(() => useProjects())

    act(() => {
      result.current.setFilters({ status: 'active' })
    })

    result.current.projects.forEach((project) => {
      expect(project.status).toBe('active')
    })
  })

  it('应该支持初始筛选条件', () => {
    const { result } = renderHook(() =>
      useProjects({ status: 'paused' })
    )

    expect(result.current.filters.status).toBe('paused')
  })

  it('应该计算总预算和总消耗', () => {
    const { result } = renderHook(() => useProjects())

    expect(result.current.stats.totalBudget).toBeGreaterThan(0)
    expect(result.current.stats.totalSpent).toBeGreaterThanOrEqual(0)
  })

  it('清空筛选应该返回所有数据', () => {
    const { result } = renderHook(() => useProjects())
    const totalCount = result.current.projects.length

    act(() => {
      result.current.setFilters({ status: 'active' })
    })

    act(() => {
      result.current.setFilters({})
    })

    expect(result.current.projects.length).toBe(totalCount)
  })
})
