/**
 * TransferDataTable 组件测试
 *
 * 对齐：TRANSFER_SOT.md v1.0, FRONTEND_STYLE_GUIDE v2.3
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { TransferDataTable } from '@/modules/transfer'
import type { TransferRequest } from '@/modules/transfer'

describe('TransferDataTable', () => {
  const mockTransfers: TransferRequest[] = [
    {
      id: 'tr-001',
      request_no: 'TRF-20250122-001',
      tenant_id: 'tenant-001',
      source_ad_account_id: 'acc-001',
      target_ad_account_id: 'acc-002',
      source_ad_account_name: '账户A-已死亡',
      target_ad_account_name: '账户B-活跃',
      supplier_id: 'sup-001',
      supplier_name: '腾讯广告',
      transfer_amount: 1234500,
      status: 'completed',
      version: 2,
      created_by: 'user-001',
      created_by_name: '张三',
      notes: '账户异常关停',
      approved_by: 'user-002',
      approved_by_name: '李四',
      approved_at: '2025-01-22T10:30:00Z',
      completed_at: '2025-01-22T10:35:00Z',
      created_at: '2025-01-22T09:00:00Z',
      updated_at: '2025-01-22T10:35:00Z',
    },
    {
      id: 'tr-002',
      request_no: 'TRF-20250123-001',
      tenant_id: 'tenant-001',
      source_ad_account_id: 'acc-003',
      target_ad_account_id: 'acc-004',
      source_ad_account_name: '账户C-已死亡',
      target_ad_account_name: '账户D-活跃',
      supplier_id: 'sup-002',
      supplier_name: '巨量引擎',
      transfer_amount: 567800,
      status: 'draft',
      version: 0,
      created_by: 'user-001',
      created_by_name: '张三',
      created_at: '2025-01-23T11:00:00Z',
      updated_at: '2025-01-23T11:00:00Z',
    },
  ]

  it('应该正确渲染表格标题', () => {
    render(<TransferDataTable transfers={mockTransfers} />)

    expect(screen.getByText('迁移申请列表')).toBeInTheDocument()
    expect(screen.getByText('共 2 条记录')).toBeInTheDocument()
  })

  it('应该正确渲染申请单号', () => {
    render(<TransferDataTable transfers={mockTransfers} />)

    expect(screen.getByText('TRF-20250122-001')).toBeInTheDocument()
    expect(screen.getByText('TRF-20250123-001')).toBeInTheDocument()
  })

  it('应该正确渲染源账户和目标账户', () => {
    render(<TransferDataTable transfers={mockTransfers} />)

    expect(screen.getByText('账户A-已死亡')).toBeInTheDocument()
    expect(screen.getByText('账户B-活跃')).toBeInTheDocument()
  })

  it('应该正确渲染供应商名称', () => {
    render(<TransferDataTable transfers={mockTransfers} />)

    expect(screen.getByText('腾讯广告')).toBeInTheDocument()
    expect(screen.getByText('巨量引擎')).toBeInTheDocument()
  })

  it('应该正确渲染状态标签', () => {
    render(<TransferDataTable transfers={mockTransfers} />)

    expect(screen.getByText('已完成')).toBeInTheDocument()
    expect(screen.getByText('草稿')).toBeInTheDocument()
  })

  it('应该正确格式化金额（分转元）', () => {
    render(<TransferDataTable transfers={mockTransfers} />)

    // 1234500 分 = ¥12,345
    expect(screen.getByText('¥12,345')).toBeInTheDocument()
    // 567800 分 = ¥5,678
    expect(screen.getByText('¥5,678')).toBeInTheDocument()
  })

  it('应该正确渲染发起人', () => {
    render(<TransferDataTable transfers={mockTransfers} />)

    const creators = screen.getAllByText('张三')
    expect(creators.length).toBe(2)
  })

  it('空数据应该显示空状态提示', () => {
    render(<TransferDataTable transfers={[]} />)

    expect(screen.getByText('暂无迁移申请')).toBeInTheDocument()
  })

  it('加载状态应该显示骨架屏', () => {
    render(<TransferDataTable transfers={[]} loading={true} />)

    // 骨架屏应该渲染
    const rows = screen.getAllByRole('row')
    expect(rows.length).toBeGreaterThan(0)
  })

  it('点击行应该触发回调', () => {
    const handleRowClick = vi.fn()
    render(
      <TransferDataTable
        transfers={mockTransfers}
        onRowClick={handleRowClick}
      />
    )

    const row = screen.getByText('TRF-20250122-001').closest('tr')
    if (row) {
      row.click()
      expect(handleRowClick).toHaveBeenCalledWith(mockTransfers[0])
    }
  })
})
