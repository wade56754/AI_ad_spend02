/**
 * Projects Page Component
 *
 * Main page for project management with filters, stats, and team management
 * SoT: DATA_SCHEMA.md v5.2, STATE_MACHINE.md v2.6 Section 5
 */

'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Plus,
  RefreshCw,
  Download,
  Filter,
  FolderKanban,
  DollarSign,
  TrendingUp,
  LayoutGrid,
  Table as TableIcon,
} from 'lucide-react';
import { ProjectsTable } from './ProjectsTable';
import { ProjectForm } from './ProjectForm';
import { ProjectMembersDialog } from './ProjectMembersDialog';
import {
  ProjectStatusBadge,
  ProjectStatsCard,
  ProjectStatusLegend,
} from './ProjectStatusBadge';
import { useProjects, useProjectStatistics } from '../hooks';
import type { Project, ProjectStatus, ProjectListParams } from '../types';
import { PROJECT_STATUS_CONFIG } from '../types';

export function ProjectsPage() {
  // Form state
  const [formOpen, setFormOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);

  // Members dialog state
  const [membersDialogOpen, setMembersDialogOpen] = useState(false);
  const [selectedProjectForMembers, setSelectedProjectForMembers] = useState<Project | null>(null);

  // Filter state
  const [filters, setFilters] = useState<ProjectListParams>({
    page: 1,
    page_size: 20,
  });
  const [statusFilter, setStatusFilter] = useState<ProjectStatus | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // View mode
  const [viewMode, setViewMode] = useState<'table' | 'kanban'>('table');

  // Data fetching
  const { data: projectsData, refetch } = useProjects(filters);
  const { data: statsData } = useProjectStatistics();

  const stats = statsData?.data;
  const totalProjects = projectsData?.meta?.pagination?.total ?? 0;

  // Handle filter changes
  const handleStatusFilter = (status: ProjectStatus | 'all') => {
    setStatusFilter(status);
    setFilters((prev) => ({
      ...prev,
      status: status === 'all' ? undefined : status,
      page: 1,
    }));
  };

  const handleSearch = () => {
    setFilters((prev) => ({
      ...prev,
      client_name: searchQuery || undefined,
      page: 1,
    }));
  };

  const clearFilters = () => {
    setStatusFilter('all');
    setSearchQuery('');
    setFilters({
      page: 1,
      page_size: 20,
    });
  };

  // Handle CRUD actions
  const handleCreate = () => {
    setEditingProject(null);
    setFormOpen(true);
  };

  const handleEdit = (project: Project) => {
    setEditingProject(project);
    setFormOpen(true);
  };

  const handleFormClose = (open: boolean) => {
    setFormOpen(open);
    if (!open) {
      setEditingProject(null);
    }
  };

  // Handle members dialog
  const handleManageMembers = (project: Project) => {
    setSelectedProjectForMembers(project);
    setMembersDialogOpen(true);
  };

  const handleMembersDialogClose = (open: boolean) => {
    setMembersDialogOpen(open);
    if (!open) {
      setSelectedProjectForMembers(null);
    }
  };

  // Format currency - 使用固定格式避免 SSR hydration 不匹配
  const formatCurrency = (amount: number) => {
    if (amount >= 10000) {
      return `¥${(amount / 10000).toFixed(1)}万`;
    }
    // 使用 Intl.NumberFormat 固定 locale 避免 hydration 问题
    return `¥${new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 0 }).format(amount)}`;
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">项目管理</h1>
          <p className="text-muted-foreground">管理广告投放项目及预算</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            导出
          </Button>
          <Button onClick={handleCreate}>
            <Plus className="mr-2 h-4 w-4" />
            新建项目
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <ProjectStatsCard
          title="项目总数"
          value={stats?.total_projects ?? totalProjects}
          icon={FolderKanban}
          onClick={() => handleStatusFilter('all')}
        />
        <ProjectStatsCard
          title="进行中"
          value={stats?.active_projects ?? 0}
          icon={TrendingUp}
          variant="success"
          onClick={() => handleStatusFilter('active')}
        />
        <ProjectStatsCard
          title="总预算"
          value={formatCurrency(stats?.total_budget ?? 0)}
          icon={DollarSign}
        />
        <ProjectStatsCard
          title="总消耗"
          value={formatCurrency(stats?.total_spent ?? 0)}
          icon={DollarSign}
          variant={
            stats?.total_spent && stats?.total_budget
              ? stats.total_spent / stats.total_budget > 0.9
                ? 'error'
                : stats.total_spent / stats.total_budget > 0.7
                  ? 'warning'
                  : 'default'
              : 'default'
          }
        />
      </div>

      {/* Filters */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-base">筛选条件</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                清除筛选
              </Button>
              {/* View Mode Toggle */}
              <div className="flex items-center gap-1 border rounded-lg p-1">
                <Button
                  variant={viewMode === 'table' ? 'secondary' : 'ghost'}
                  size="sm"
                  className="h-7 px-2"
                  onClick={() => setViewMode('table')}
                >
                  <TableIcon className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'kanban' ? 'secondary' : 'ghost'}
                  size="sm"
                  className="h-7 px-2"
                  onClick={() => setViewMode('kanban')}
                >
                  <LayoutGrid className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-4">
            {/* Status Filter */}
            <Select
              value={statusFilter}
              onValueChange={(value) => handleStatusFilter(value as ProjectStatus | 'all')}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                {(Object.keys(PROJECT_STATUS_CONFIG) as ProjectStatus[]).map((status) => (
                  <SelectItem key={status} value={status}>
                    {PROJECT_STATUS_CONFIG[status].label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Search */}
            <div className="flex items-center gap-2">
              <Input
                placeholder="搜索客户名称..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="w-[200px]"
              />
              <Button variant="secondary" size="sm" onClick={handleSearch}>
                搜索
              </Button>
            </div>
          </div>

          {/* Status Legend */}
          <div className="mt-4 pt-4 border-t">
            <p className="text-xs text-muted-foreground mb-2">状态说明</p>
            <ProjectStatusLegend />
          </div>
        </CardContent>
      </Card>

      {/* Content Tabs */}
      <Tabs defaultValue="list" className="space-y-4">
        <TabsList>
          <TabsTrigger value="list" className="gap-2">
            <FolderKanban className="h-4 w-4" />
            项目列表
          </TabsTrigger>
          <TabsTrigger value="stats" className="gap-2">
            <TrendingUp className="h-4 w-4" />
            统计分析
          </TabsTrigger>
        </TabsList>

        <TabsContent value="list">
          {viewMode === 'table' ? (
            <Card>
              <CardContent className="p-0">
                <ProjectsTable
                  onEdit={handleEdit}
                  onViewMembers={handleManageMembers}
                />
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-6">
                <p className="text-muted-foreground text-center py-8">
                  看板视图正在开发中...
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="stats">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Status Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>状态分布</CardTitle>
                <CardDescription>各状态项目数量</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {(Object.keys(PROJECT_STATUS_CONFIG) as ProjectStatus[]).map((status) => {
                    const count =
                      stats?.[`${status}_projects` as keyof typeof stats] ?? 0;
                    const total = stats?.total_projects ?? 1;
                    // 使用 Math.round 避免浮点精度导致的 hydration 不匹配
                    const percent = Math.round(((count as number) / total) * 100);

                    return (
                      <div
                        key={status}
                        className="flex items-center justify-between cursor-pointer hover:bg-gray-50 p-2 rounded-lg -mx-2"
                        onClick={() => handleStatusFilter(status)}
                      >
                        <div className="flex items-center gap-3">
                          <ProjectStatusBadge status={status} showTooltip={false} />
                          <span className="text-2xl font-bold">{count as number}</span>
                        </div>
                        <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-500 rounded-full"
                            style={{ width: `${percent}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Budget Overview */}
            <Card>
              <CardHeader>
                <CardTitle>预算概览</CardTitle>
                <CardDescription>项目预算与消耗情况</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-muted-foreground">总预算</span>
                      <span className="font-medium">
                        {formatCurrency(stats?.total_budget ?? 0)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-muted-foreground">已消耗</span>
                      <span className="font-medium">
                        {formatCurrency(stats?.total_spent ?? 0)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">剩余预算</span>
                      <span className="font-medium text-green-600">
                        {formatCurrency((stats?.total_budget ?? 0) - (stats?.total_spent ?? 0))}
                      </span>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-muted-foreground">消耗进度</span>
                      <span className="font-medium">
                        {stats?.total_budget
                          ? ((stats.total_spent / stats.total_budget) * 100).toFixed(1)
                          : 0}%
                      </span>
                    </div>
                    <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full transition-all duration-300"
                        style={{
                          width: `${
                            stats?.total_budget
                              ? Math.round(Math.min((stats.total_spent / stats.total_budget) * 100, 100))
                              : 0
                          }%`,
                        }}
                      />
                    </div>
                  </div>

                  <div className="pt-4 border-t">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">客户总数</span>
                      <span className="font-medium">{stats?.total_clients ?? 0}</span>
                    </div>
                    <div className="flex justify-between text-sm mt-2">
                      <span className="text-muted-foreground">平均项目价值</span>
                      <span className="font-medium">
                        {formatCurrency(stats?.avg_project_value ?? 0)}
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Top Performers */}
            {stats?.top_performers && stats.top_performers.length > 0 && (
              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle>ROI 排行榜</CardTitle>
                  <CardDescription>表现最佳的项目</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {stats.top_performers.map((project, index) => (
                      <div
                        key={project.id}
                        className="flex items-center gap-4 p-4 rounded-lg border"
                      >
                        <div className="text-2xl font-bold text-muted-foreground">
                          #{index + 1}
                        </div>
                        <div className="flex-1">
                          <p className="font-medium">{project.name}</p>
                          <p className="text-sm text-green-600">
                            ROI: {(project.roi * 100).toFixed(1)}%
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* Project Form Dialog */}
      <ProjectForm
        project={editingProject}
        open={formOpen}
        onOpenChange={handleFormClose}
      />

      {/* Members Management Dialog */}
      {selectedProjectForMembers && (
        <ProjectMembersDialog
          open={membersDialogOpen}
          onOpenChange={handleMembersDialogClose}
          project={selectedProjectForMembers}
        />
      )}
    </div>
  );
}
