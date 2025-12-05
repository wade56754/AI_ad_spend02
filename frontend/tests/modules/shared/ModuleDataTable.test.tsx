/**
 * ModuleDataTable 组件测试
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ModuleDataTable, type ColumnDef } from '@/modules/shared'

interface TestData {
  id: string
  name: string
  status: string
  amount: number
}

describe('ModuleDataTable', () => {
  const testData: TestData[] = [
    { id: '1', name: '项目A', status: 'active', amount: 1000 },
    { id: '2', name: '项目B', status: 'pending', amount: 2000 },
    { id: '3', name: '项目C', status: 'inactive', amount: 3000 },
  ]

  const columns: ColumnDef<TestData>[] = [
    { key: 'name', header: '名称' },
    { key: 'status', header: '状态' },
    {
      key: 'amount',
      header: '金额',
      align: 'right',
      render: (_, row) => `¥${row.amount.toLocaleString()}`,
    },
  ]

  const defaultProps = {
    columns,
    data: testData,
    getRowKey: (row: TestData) => row.id,
  }

  it('应该正确渲染表头', () => {
    render(<ModuleDataTable {...defaultProps} />)

    expect(screen.getByText('名称')).toBeInTheDocument()
    expect(screen.getByText('状态')).toBeInTheDocument()
    expect(screen.getByText('金额')).toBeInTheDocument()
  })

  it('应该正确渲染数据行', () => {
    render(<ModuleDataTable {...defaultProps} />)

    expect(screen.getByText('项目A')).toBeInTheDocument()
    expect(screen.getByText('项目B')).toBeInTheDocument()
    expect(screen.getByText('项目C')).toBeInTheDocument()
  })

  it('应该使用自定义渲染函数', () => {
    render(<ModuleDataTable {...defaultProps} />)

    expect(screen.getByText('¥1,000')).toBeInTheDocument()
    expect(screen.getByText('¥2,000')).toBeInTheDocument()
    expect(screen.getByText('¥3,000')).toBeInTheDocument()
  })

  it('应该渲染标题和描述', () => {
    render(
      <ModuleDataTable
        {...defaultProps}
        title="测试表格"
        description="共 3 条记录"
      />
    )

    expect(screen.getByText('测试表格')).toBeInTheDocument()
    expect(screen.getByText('共 3 条记录')).toBeInTheDocument()
  })

  it('空数据时应该显示空状态', () => {
    render(
      <ModuleDataTable
        {...defaultProps}
        data={[]}
        emptyText="暂无数据"
      />
    )

    expect(screen.getByText('暂无数据')).toBeInTheDocument()
  })

  it('加载状态应该显示骨架屏', () => {
    render(<ModuleDataTable {...defaultProps} loading={true} />)

    // 骨架屏应该渲染
    const skeletons = screen.getAllByRole('row')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('点击行应该触发回调', () => {
    const handleRowClick = vi.fn()
    render(
      <ModuleDataTable
        {...defaultProps}
        onRowClick={handleRowClick}
      />
    )

    const row = screen.getByText('项目A').closest('tr')
    if (row) {
      fireEvent.click(row)
      expect(handleRowClick).toHaveBeenCalledWith(testData[0])
    }
  })

  it('应该正确处理右对齐列', () => {
    render(<ModuleDataTable {...defaultProps} />)

    const amountCells = screen.getAllByText(/¥/)
    amountCells.forEach(cell => {
      expect(cell.closest('td')).toHaveClass('text-right')
    })
  })

  it('应该应用自定义 className', () => {
    const { container } = render(
      <ModuleDataTable {...defaultProps} className="custom-table" />
    )

    expect(container.querySelector('.custom-table')).toBeInTheDocument()
  })
})
