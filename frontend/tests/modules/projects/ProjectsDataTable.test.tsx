/**
 * ProjectsDataTable 组件测试
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ProjectsDataTable } from '@/modules/projects'
import type { Project } from '@/modules/projects'

describe('ProjectsDataTable', () => {
  const mockProjects: Project[] = [
    {
      id: 'proj-001',
      tenant_id: 'tenant-001',
      name: '测试项目A',
      code: 'PROJ-A',
      status: 'active',
      budget: 10000000, // 10万元 (分)
      spent: 5000000,   // 5万元 (分)
      account_manager_id: 'user-001',
      account_manager_name: '张三',
      ad_account_count: 5,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-20T00:00:00Z',
    },
    {
      id: 'proj-002',
      tenant_id: 'tenant-001',
      name: '测试项目B',
      code: 'PROJ-B',
      status: 'paused',
      budget: 5000000,
      spent: 4500000,
      account_manager_id: 'user-002',
      account_manager_name: '李四',
      ad_account_count: 3,
      created_at: '2025-01-05T00:00:00Z',
      updated_at: '2025-01-18T00:00:00Z',
    },
  ]

  it('应该正确渲染项目名称', () => {
    render(<ProjectsDataTable projects={mockProjects} />)

    expect(screen.getByText('测试项目A')).toBeInTheDocument()
    expect(screen.getByText('测试项目B')).toBeInTheDocument()
  })

  it('应该正确渲染项目代码', () => {
    render(<ProjectsDataTable projects={mockProjects} />)

    expect(screen.getByText('PROJ-A')).toBeInTheDocument()
    expect(screen.getByText('PROJ-B')).toBeInTheDocument()
  })

  it('应该正确渲染状态标签', () => {
    render(<ProjectsDataTable projects={mockProjects} />)

    expect(screen.getByText('进行中')).toBeInTheDocument()
    expect(screen.getByText('已暂停')).toBeInTheDocument()
  })

  it('应该正确格式化预算金额', () => {
    render(<ProjectsDataTable projects={mockProjects} />)

    expect(screen.getByText('¥100,000')).toBeInTheDocument()
    expect(screen.getByText('¥50,000')).toBeInTheDocument()
  })

  it('应该正确渲染账户管理员', () => {
    render(<ProjectsDataTable projects={mockProjects} />)

    expect(screen.getByText('张三')).toBeInTheDocument()
    expect(screen.getByText('李四')).toBeInTheDocument()
  })

  it('应该正确渲染账户数量', () => {
    render(<ProjectsDataTable projects={mockProjects} />)

    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('空数据应该显示空状态', () => {
    render(<ProjectsDataTable projects={[]} />)

    expect(screen.getByText('暂无项目')).toBeInTheDocument()
  })

  it('点击行应该触发回调', () => {
    const handleRowClick = vi.fn()
    render(
      <ProjectsDataTable
        projects={mockProjects}
        onRowClick={handleRowClick}
      />
    )

    const row = screen.getByText('测试项目A').closest('tr')
    if (row) {
      row.click()
      expect(handleRowClick).toHaveBeenCalledWith(mockProjects[0])
    }
  })
})
