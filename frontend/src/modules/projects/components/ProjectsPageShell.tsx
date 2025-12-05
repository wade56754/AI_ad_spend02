/**
 * ProjectsPageShell - 项目管理页面主容器
 *
 * 布局结构：
 * - Header: 标题 + 筛选器 + 新建按钮
 * - KPI 区: 项目数量、预算、消耗等关键指标
 * - 主内容: 项目列表表格
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React, { useEffect } from 'react';
import { LayoutDashboard, Plus, Filter, Search } from 'lucide-react';
import { PageShell } from '@/modules/shared';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ProjectsKpiRow } from './ProjectsKpiRow';
import { ProjectsDataTable } from './ProjectsDataTable';
import { useProjects } from '../hooks';

export function ProjectsPageShell() {
  const { projects, summary, loading, refresh, filters, setFilters } = useProjects();

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleSearch = (value: string) => {
    setFilters({ ...filters, search: value });
  };

  return (
    <PageShell
      title="项目管理"
      description="管理广告投放项目，查看项目状态和数据"
      icon={LayoutDashboard}
      filters={
        <>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <Input
              placeholder="搜索项目..."
              className="pl-9 w-[200px] bg-card-bg border-border-default text-text-body placeholder:text-text-muted"
              onChange={(e) => handleSearch(e.target.value)}
            />
          </div>
          <Button
            variant="outline"
            size="sm"
            className="gap-2 bg-card-bg border-border-default text-text-body hover:bg-elevated"
          >
            <Filter className="w-4 h-4" />
            筛选
          </Button>
        </>
      }
      actions={
        <Button
          size="sm"
          className="gap-2 bg-accent hover:bg-accent-hover shadow-lg shadow-accent/20"
        >
          <Plus className="w-4 h-4" />
          新建项目
        </Button>
      }
      kpiSection={<ProjectsKpiRow summary={summary} loading={loading} />}
    >
      <ProjectsDataTable
        projects={projects}
        loading={loading}
        onRowClick={(project) => console.log('View project:', project)}
      />
    </PageShell>
  );
}

export default ProjectsPageShell;
