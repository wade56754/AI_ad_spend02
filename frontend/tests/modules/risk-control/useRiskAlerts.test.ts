/**
 * useRiskAlerts Hook 测试
 */

import { renderHook, act } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { useRiskAlerts } from '@/modules/risk-control/hooks/useRiskAlerts'

describe('useRiskAlerts', () => {
  it('应该返回初始状态', () => {
    const { result } = renderHook(() => useRiskAlerts())

    expect(result.current.alerts).toBeDefined()
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.stats).toBeDefined()
  })

  it('应该返回正确的统计数据', () => {
    const { result } = renderHook(() => useRiskAlerts())

    expect(result.current.stats.total).toBeGreaterThan(0)
    expect(result.current.stats.byLevel).toHaveProperty('low')
    expect(result.current.stats.byLevel).toHaveProperty('medium')
    expect(result.current.stats.byLevel).toHaveProperty('high')
    expect(result.current.stats.byLevel).toHaveProperty('critical')
  })

  it('应该返回正确的状态统计', () => {
    const { result } = renderHook(() => useRiskAlerts())

    expect(result.current.stats.byStatus).toHaveProperty('active')
    expect(result.current.stats.byStatus).toHaveProperty('acknowledged')
    expect(result.current.stats.byStatus).toHaveProperty('resolved')
    expect(result.current.stats.byStatus).toHaveProperty('dismissed')
  })

  it('应该根据状态筛选数据', () => {
    const { result } = renderHook(() => useRiskAlerts())

    act(() => {
      result.current.setFilters({ status: 'active' })
    })

    result.current.alerts.forEach((alert) => {
      expect(alert.status).toBe('active')
    })
  })

  it('应该根据风险级别筛选数据', () => {
    const { result } = renderHook(() => useRiskAlerts())

    act(() => {
      result.current.setFilters({ risk_level: 'critical' })
    })

    result.current.alerts.forEach((alert) => {
      expect(alert.risk_level).toBe('critical')
    })
  })

  it('应该根据风险类型筛选数据', () => {
    const { result } = renderHook(() => useRiskAlerts())

    act(() => {
      result.current.setFilters({ risk_type: 'spend_anomaly' })
    })

    result.current.alerts.forEach((alert) => {
      expect(alert.risk_type).toBe('spend_anomaly')
    })
  })

  it('应该支持初始筛选条件', () => {
    const { result } = renderHook(() =>
      useRiskAlerts({ status: 'active' })
    )

    expect(result.current.filters.status).toBe('active')
  })

  it('应该计算活跃预警数量', () => {
    const { result } = renderHook(() => useRiskAlerts())

    const expectedActive =
      result.current.stats.byStatus.active +
      result.current.stats.byStatus.acknowledged

    expect(result.current.stats.activeCount).toBe(expectedActive)
  })

  it('清空筛选应该返回所有数据', () => {
    const { result } = renderHook(() => useRiskAlerts())
    const totalCount = result.current.alerts.length

    act(() => {
      result.current.setFilters({ status: 'active' })
    })

    act(() => {
      result.current.setFilters({})
    })

    expect(result.current.alerts.length).toBe(totalCount)
  })

  it('应该能组合多个筛选条件', () => {
    const { result } = renderHook(() => useRiskAlerts())

    act(() => {
      result.current.setFilters({
        status: 'active',
        risk_level: 'critical',
      })
    })

    result.current.alerts.forEach((alert) => {
      expect(alert.status).toBe('active')
      expect(alert.risk_level).toBe('critical')
    })
  })
})
