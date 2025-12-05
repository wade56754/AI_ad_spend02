/**
 * RiskAlertDataTable 组件测试
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { RiskAlertDataTable } from '@/modules/risk-control'
import type { RiskAlert } from '@/modules/risk-control'

describe('RiskAlertDataTable', () => {
  const mockAlerts: RiskAlert[] = [
    {
      id: 'alert-001',
      tenant_id: 'tenant-001',
      project_id: 'proj-001',
      ad_account_id: 'acc-001',
      risk_type: 'spend_anomaly',
      risk_level: 'critical',
      status: 'active',
      title: '消耗异常暴增',
      description: '账户消耗较前日增长 250%',
      metric_name: '日消耗',
      metric_value: 150000,
      threshold_value: 50000,
      deviation_percentage: 250,
      ad_account_name: '腾讯广告-A001',
      project_name: '项目A',
      detected_at: '2025-01-24T08:00:00Z',
      created_at: '2025-01-24T08:00:00Z',
      updated_at: '2025-01-24T08:00:00Z',
    },
    {
      id: 'alert-002',
      tenant_id: 'tenant-001',
      risk_type: 'balance_warning',
      risk_level: 'high',
      status: 'acknowledged',
      title: '余额不足预警',
      description: '账户余额低于 3 天消耗预估',
      metric_name: '剩余天数',
      metric_value: 2.5,
      threshold_value: 3,
      deviation_percentage: -16.7,
      ad_account_name: '巨量引擎-B002',
      project_name: '项目B',
      detected_at: '2025-01-24T06:00:00Z',
      created_at: '2025-01-24T06:00:00Z',
      updated_at: '2025-01-24T10:00:00Z',
    },
    {
      id: 'alert-003',
      tenant_id: 'tenant-001',
      risk_type: 'trend_deviation',
      risk_level: 'medium',
      status: 'resolved',
      title: 'ROI 趋势偏离',
      description: 'ROI 连续下降',
      metric_name: 'ROI',
      metric_value: 1.2,
      threshold_value: 1.5,
      deviation_percentage: -20,
      resolved_by: 'user-001',
      resolved_at: '2025-01-23T16:00:00Z',
      resolution_notes: '已处理',
      detected_at: '2025-01-23T10:00:00Z',
      created_at: '2025-01-23T10:00:00Z',
      updated_at: '2025-01-23T16:00:00Z',
    },
  ]

  it('应该正确渲染表格标题', () => {
    render(<RiskAlertDataTable alerts={mockAlerts} />)

    expect(screen.getByText('风险预警列表')).toBeInTheDocument()
    expect(screen.getByText('共 3 条预警')).toBeInTheDocument()
  })

  it('应该正确渲染预警标题', () => {
    render(<RiskAlertDataTable alerts={mockAlerts} />)

    expect(screen.getByText('消耗异常暴增')).toBeInTheDocument()
    expect(screen.getByText('余额不足预警')).toBeInTheDocument()
  })

  it('应该正确渲染风险类型', () => {
    render(<RiskAlertDataTable alerts={mockAlerts} />)

    expect(screen.getByText('消耗异常')).toBeInTheDocument()
    expect(screen.getByText('余额预警')).toBeInTheDocument()
    expect(screen.getByText('趋势偏离')).toBeInTheDocument()
  })

  it('应该正确渲染状态标签', () => {
    render(<RiskAlertDataTable alerts={mockAlerts} />)

    expect(screen.getByText('待处理')).toBeInTheDocument()
    expect(screen.getByText('已确认')).toBeInTheDocument()
    expect(screen.getByText('已解决')).toBeInTheDocument()
  })

  it('应该正确渲染关联对象', () => {
    render(<RiskAlertDataTable alerts={mockAlerts} />)

    expect(screen.getByText('腾讯广告-A001')).toBeInTheDocument()
    expect(screen.getByText('项目A')).toBeInTheDocument()
  })

  it('应该正确显示偏离度（带正负号）', () => {
    render(<RiskAlertDataTable alerts={mockAlerts} />)

    expect(screen.getByText('+250%')).toBeInTheDocument()
    expect(screen.getByText('-16.7%')).toBeInTheDocument()
    expect(screen.getByText('-20%')).toBeInTheDocument()
  })

  it('空数据应该显示空状态', () => {
    render(<RiskAlertDataTable alerts={[]} />)

    expect(screen.getByText('暂无风险预警')).toBeInTheDocument()
  })

  it('加载状态应该显示骨架屏', () => {
    render(<RiskAlertDataTable alerts={[]} loading={true} />)

    const rows = screen.getAllByRole('row')
    expect(rows.length).toBeGreaterThan(0)
  })

  it('点击行应该触发回调', () => {
    const handleRowClick = vi.fn()
    render(
      <RiskAlertDataTable
        alerts={mockAlerts}
        onRowClick={handleRowClick}
      />
    )

    const row = screen.getByText('消耗异常暴增').closest('tr')
    if (row) {
      row.click()
      expect(handleRowClick).toHaveBeenCalledWith(mockAlerts[0])
    }
  })
})
