/**
 * AdAccountsDataTable 组件测试
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { AdAccountsDataTable } from '@/modules/ad-accounts'
import type { AdAccount } from '@/modules/ad-accounts'

describe('AdAccountsDataTable', () => {
  const mockAccounts: AdAccount[] = [
    {
      id: 'acc-001',
      tenant_id: 'tenant-001',
      project_id: 'proj-001',
      account_id: 'ACC-12345',
      name: '腾讯广告账户A',
      platform: 'tencent',
      status: 'active',
      balance: 5000000,
      daily_budget: 100000,
      today_spent: 50000,
      supplier_id: 'sup-001',
      supplier_name: '腾讯广告',
      project_name: '项目A',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-20T00:00:00Z',
    },
    {
      id: 'acc-002',
      tenant_id: 'tenant-001',
      project_id: 'proj-001',
      account_id: 'ACC-67890',
      name: '巨量引擎账户B',
      platform: 'bytedance',
      status: 'dead',
      balance: 0,
      daily_budget: 0,
      today_spent: 0,
      supplier_id: 'sup-002',
      supplier_name: '巨量引擎',
      project_name: '项目A',
      created_at: '2025-01-05T00:00:00Z',
      updated_at: '2025-01-18T00:00:00Z',
    },
  ]

  it('应该正确渲染账户名称', () => {
    render(<AdAccountsDataTable accounts={mockAccounts} />)

    expect(screen.getByText('腾讯广告账户A')).toBeInTheDocument()
    expect(screen.getByText('巨量引擎账户B')).toBeInTheDocument()
  })

  it('应该正确渲染账户ID', () => {
    render(<AdAccountsDataTable accounts={mockAccounts} />)

    expect(screen.getByText('ACC-12345')).toBeInTheDocument()
    expect(screen.getByText('ACC-67890')).toBeInTheDocument()
  })

  it('应该正确渲染平台名称', () => {
    render(<AdAccountsDataTable accounts={mockAccounts} />)

    expect(screen.getByText('腾讯广告')).toBeInTheDocument()
    expect(screen.getByText('巨量引擎')).toBeInTheDocument()
  })

  it('应该正确渲染状态标签', () => {
    render(<AdAccountsDataTable accounts={mockAccounts} />)

    expect(screen.getByText('活跃')).toBeInTheDocument()
    expect(screen.getByText('已死亡')).toBeInTheDocument()
  })

  it('应该正确格式化余额', () => {
    render(<AdAccountsDataTable accounts={mockAccounts} />)

    expect(screen.getByText('¥50,000')).toBeInTheDocument()
  })

  it('空数据应该显示空状态', () => {
    render(<AdAccountsDataTable accounts={[]} />)

    expect(screen.getByText('暂无账户')).toBeInTheDocument()
  })

  it('点击行应该触发回调', () => {
    const handleRowClick = vi.fn()
    render(
      <AdAccountsDataTable
        accounts={mockAccounts}
        onRowClick={handleRowClick}
      />
    )

    const row = screen.getByText('腾讯广告账户A').closest('tr')
    if (row) {
      row.click()
      expect(handleRowClick).toHaveBeenCalledWith(mockAccounts[0])
    }
  })
})
