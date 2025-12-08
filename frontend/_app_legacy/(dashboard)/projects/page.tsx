'use client';

import React, { useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import AppLayout from '@/components/dashboard/AppLayout';
import { PageHeader } from '@/components/layout/page-header';
import ProjectSummaryCards from './components/ProjectSummaryCards';
import ProjectFilters from './components/ProjectFilters';
import ProjectTable from './components/ProjectTable';
import {
  Project,
  ProjectStats,
  ProjectFilters as IProjectFilters,
  ProjectStatus,
  ProjectPriority,
  Platform,
} from './types';
import {
  AlertTriangle,
  Plus,
  Download,
  Target,
  Clock,
} from 'lucide-react';
import { format, subDays } from 'date-fns';

// 模拟项目数据
const mockProjects: Project[] = [
  {
    id: 1,
    name: '春季推广活动',
    description: '针对春季产品的全面推广活动',
    client_name: 'ABC科技公司',
    client_id: 101,
    status: 'active',
    priority: 'high',
    budget: 50000,
    current_spend: 32500,
    remaining_budget: 17500,
    budget_utilization: 65.0,
    team_lead: '张经理',
    team_lead_id: 1001,
    team_size: 5,
    start_date: '2025-01-01',
    end_date: '2025-03-31',
    roi: 3.8,
    total_conversions: 1250,
    total_impressions: 450000,
    total_clicks: 8900,
    cpc: 3.65,
    cpm: 72.2,
    ctr: 1.98,
    created_at: '2024-12-15T09:30:00Z',
    updated_at: '2025-01-10T14:20:00Z',
    created_by: '项目经理-李四',
    notes: '重点客户，需优先保障资源',
    tags: ['春季', '重点客户', '电商'],
    platforms: ['facebook', 'google'],
    industry: '科技',
    region: '华东',
  },
  {
    id: 2,
    name: '品牌形象提升',
    description: '提升品牌知名度和美誉度',
    client_name: 'XYZ时尚集团',
    client_id: 102,
    status: 'active',
    priority: 'medium',
    budget: 30000,
    current_spend: 18500,
    remaining_budget: 11500,
    budget_utilization: 61.7,
    team_lead: '李主管',
    team_lead_id: 1002,
    team_size: 3,
    start_date: '2025-01-01',
    end_date: '2025-06-30',
    roi: 2.1,
    total_conversions: 650,
    total_impressions: 280000,
    total_clicks: 5200,
    cpc: 3.56,
    cpm: 66.1,
    ctr: 1.86,
    created_at: '2024-12-20T11:15:00Z',
    updated_at: '2025-01-08T16:45:00Z',
    created_by: '项目经理-王五',
    notes: '长期合作品牌客户',
    tags: ['品牌', '时尚', '长期合作'],
    platforms: ['instagram', 'tiktok'],
    industry: '时尚',
    region: '全国',
  },
  {
    id: 3,
    name: '夏季促销活动',
    description: '夏季产品促销推广',
    client_name: 'DEF零售连锁',
    client_id: 103,
    status: 'planning',
    priority: 'high',
    budget: 80000,
    current_spend: 0,
    remaining_budget: 80000,
    budget_utilization: 0.0,
    team_lead: '王总监',
    team_lead_id: 1003,
    team_size: 8,
    start_date: '2025-06-01',
    end_date: '2025-08-31',
    roi: 0,
    total_conversions: 0,
    total_impressions: 0,
    total_clicks: 0,
    cpc: 0,
    cpm: 0,
    ctr: 0,
    created_at: '2025-01-05T10:00:00Z',
    updated_at: '2025-01-05T10:00:00Z',
    created_by: '项目经理-赵六',
    notes: '夏季重点活动，需要提前规划',
    tags: ['夏季', '促销', '重点活动'],
    platforms: ['facebook', 'google', 'tiktok'],
    industry: '零售',
    region: '华南',
  },
  {
    id: 4,
    name: '新品发布推广',
    description: '新产品线上市推广',
    client_name: 'GHI制造企业',
    client_id: 104,
    status: 'paused',
    priority: 'medium',
    budget: 25000,
    current_spend: 12000,
    remaining_budget: 13000,
    budget_utilization: 48.0,
    team_lead: '陈经理',
    team_lead_id: 1004,
    team_size: 4,
    start_date: '2025-02-01',
    end_date: '2025-04-30',
    roi: 1.2,
    total_conversions: 320,
    total_impressions: 150000,
    total_clicks: 2800,
    cpc: 4.29,
    cpm: 80.0,
    ctr: 1.87,
    created_at: '2024-12-10T13:45:00Z',
    updated_at: '2025-01-12T09:30:00Z',
    created_by: '项目经理-孙七',
    notes: '客户要求暂停，等待产品准备完成',
    tags: ['新品', '制造', '已暂停'],
    platforms: ['linkedin', 'google'],
    industry: '制造',
    region: '华北',
  },
  {
    id: 5,
    name: '会员增长活动',
    description: '增加平台会员数量',
    client_name: 'JKL互联网公司',
    client_id: 105,
    status: 'completed',
    priority: 'low',
    budget: 15000,
    current_spend: 14800,
    remaining_budget: 200,
    budget_utilization: 98.7,
    team_lead: '刘主管',
    team_lead_id: 1005,
    team_size: 2,
    start_date: '2024-11-01',
    end_date: '2024-12-31',
    actual_end_date: '2024-12-28T17:00:00Z',
    roi: 4.2,
    total_conversions: 2100,
    total_impressions: 520000,
    total_clicks: 12400,
    cpc: 1.19,
    cpm: 28.5,
    ctr: 2.38,
    created_at: '2024-10-25T08:30:00Z',
    updated_at: '2024-12-28T18:00:00Z',
    created_by: '项目经理-周八',
    notes: '项目顺利完成，效果超出预期',
    tags: ['会员', '互联网', '已完成'],
    platforms: ['facebook', 'instagram'],
    industry: '互联网',
    region: '全国',
  },
];

/**
 * 项目管理主页面
 *
 * 采用限宽居中布局，包含KPI统计、筛选工具栏、数据表格
 */
export default function ProjectsPage() {
  const [loading, setLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  // 筛选条件状态
  const [filters, setFilters] = useState<IProjectFilters>({
    search_term: '',
    status: 'all',
    priority: 'all',
    platform: 'all',
    date_range: {
      start: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
      end: format(new Date(), 'yyyy-MM-dd'),
    },
    budget_range: {
      min: undefined,
      max: undefined,
    },
    roi_range: {
      min: undefined,
      max: undefined,
    },
    has_overdue: null,
    tags: [],
    sort_by: 'updated_at',
    sort_order: 'desc',
  });

  // 计算统计数据
  const stats: ProjectStats = useMemo(() => {
    return {
      total_projects: mockProjects.length,
      active_projects: mockProjects.filter(p => p.status === 'active').length,
      completed_projects: mockProjects.filter(p => p.status === 'completed').length,
      planning_projects: mockProjects.filter(p => p.status === 'planning').length,
      paused_projects: mockProjects.filter(p => p.status === 'paused').length,
      total_budget: mockProjects.reduce((sum, p) => sum + p.budget, 0),
      total_spend: mockProjects.reduce((sum, p) => sum + p.current_spend, 0),
      remaining_budget: mockProjects.reduce((sum, p) => sum + p.remaining_budget, 0),
      average_roi: mockProjects.reduce((sum, p) => sum + p.roi, 0) / mockProjects.length,
      total_conversions: mockProjects.reduce((sum, p) => sum + (p.total_conversions || 0), 0),
      total_impressions: mockProjects.reduce((sum, p) => sum + (p.total_impressions || 0), 0),
      total_clicks: mockProjects.reduce((sum, p) => sum + (p.total_clicks || 0), 0),
      average_ctr: mockProjects.reduce((sum, p) => sum + (p.ctr || 0), 0) / mockProjects.length,
      average_cpc: mockProjects.reduce((sum, p) => sum + (p.cpc || 0), 0) / mockProjects.filter(p => p.cpc > 0).length,
      high_priority_projects: mockProjects.filter(p => p.priority === 'high').length,
      overdue_projects: mockProjects.filter(p =>
        new Date(p.end_date) < new Date() && p.status !== 'completed'
      ).length,
      projects_this_month: mockProjects.filter(p => {
        const createdAt = new Date(p.created_at);
        const now = new Date();
        return createdAt.getMonth() === now.getMonth() &&
               createdAt.getFullYear() === now.getFullYear();
      }).length,
      completion_rate: (mockProjects.filter(p => p.status === 'completed').length / mockProjects.length) * 100,
    };
  }, []);

  // 筛选数据
  const filteredData: Project[] = useMemo(() => {
    return mockProjects.filter(project => {
      // 搜索筛选
      const matchesSearch = filters.search_term === '' ||
        project.name.toLowerCase().includes(filters.search_term.toLowerCase()) ||
        project.client_name.toLowerCase().includes(filters.search_term.toLowerCase()) ||
        project.team_lead.toLowerCase().includes(filters.search_term.toLowerCase());

      // 状态筛选
      const matchesStatus = filters.status === 'all' || project.status === filters.status;

      // 优先级筛选
      const matchesPriority = filters.priority === 'all' || project.priority === filters.priority;

      // 平台筛选
      const matchesPlatform = filters.platform === 'all' ||
        (project.platforms && project.platforms.includes(filters.platform as Platform));

      // 日期范围筛选
      const startDate = filters.date_range.start ? new Date(filters.date_range.start) : null;
      const endDate = filters.date_range.end ? new Date(filters.date_range.end + 'T23:59:59') : null;
      const createdDate = new Date(project.created_at);

      const matchesDateRange = (!startDate || createdDate >= startDate) &&
        (!endDate || createdDate <= endDate);

      // 预算范围筛选
      const matchesBudgetRange = (!filters.budget_range.min || project.budget >= filters.budget_range.min) &&
        (!filters.budget_range.max || project.budget <= filters.budget_range.max);

      // ROI范围筛选
      const matchesROIRange = (!filters.roi_range.min || project.roi >= filters.roi_range.min) &&
        (!filters.roi_range.max || project.roi <= filters.roi_range.max);

      // 逾期筛选
      const isOverdue = new Date(project.end_date) < new Date() && project.status !== 'completed';
      const matchesOverdue = filters.has_overdue === null ||
        (filters.has_overdue && isOverdue) ||
        (!filters.has_overdue && !isOverdue);

      // 标签筛选
      const matchesTags = filters.tags.length === 0 ||
        filters.tags.some(tag => project.tags && project.tags.includes(tag));

      return matchesSearch && matchesStatus && matchesPriority && matchesPlatform &&
             matchesDateRange && matchesBudgetRange && matchesROIRange && matchesOverdue && matchesTags;
    }).sort((a, b) => {
      // 排序
      let aValue: any = a[filters.sort_by];
      let bValue: any = b[filters.sort_by];

      if (aValue instanceof Date) aValue = aValue.getTime();
      if (bValue instanceof Date) bValue = bValue.getTime();

      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (filters.sort_order === 'asc') {
        return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
      } else {
        return aValue < bValue ? 1 : aValue > bValue ? -1 : 0;
      }
    });
  }, [filters]);

  // 处理筛选条件变化
  const handleFiltersChange = (newFilters: IProjectFilters) => {
    setFilters(newFilters);
  };

  // 重置筛选条件
  const handleReset = () => {
    setFilters({
      search_term: '',
      status: 'all',
      priority: 'all',
      platform: 'all',
      date_range: {
        start: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
        end: format(new Date(), 'yyyy-MM-dd'),
      },
      budget_range: {
        min: undefined,
        max: undefined,
      },
      roi_range: {
        min: undefined,
        max: undefined,
      },
      has_overdue: null,
      tags: [],
      sort_by: 'updated_at',
      sort_order: 'desc',
    });
    setSelectedIds([]);
  };

  // 导出数据
  const handleExport = () => {
    console.log('导出项目数据:', filteredData);
    // TODO: 实现导出功能
  };

  // 新建项目
  const handleNewProject = () => {
    console.log('新建项目');
    // TODO: 实现新建功能
  };

  // 查看详情
  const handleViewDetail = (project: Project) => {
    console.log('查看项目详情:', project);
    // TODO: 实现详情查看功能
  };

  // 编辑项目
  const handleEdit = (project: Project) => {
    console.log('编辑项目:', project);
    // TODO: 实现编辑功能
  };

  // 状态变更
  const handleStatusChange = (id: number, status: ProjectStatus) => {
    console.log('更改项目状态:', id, status);
    // TODO: 实现状态变更功能
  };

  // 检查是否有逾期项目
  const hasOverdueProjects = filteredData.some(p =>
    new Date(p.end_date) < new Date() && p.status !== 'completed'
  );

  return (
    <AppLayout>
      {/* 主内容区域：限宽居中 */}
      <div className="flex-1 bg-background">
        <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
          {/* 页面标题 */}
          <PageHeader
            title="项目管理"
            subtitle="查看并管理所有广告投放项目，跟踪项目进度和ROI表现"
            actions={
              <div className="flex gap-2">
                <Button variant="outline" onClick={handleExport}>
                  <Download className="h-4 w-4 mr-2" />
                  导出数据
                </Button>
                <Button onClick={handleNewProject}>
                  <Plus className="h-4 w-4 mr-2" />
                  新建项目
                </Button>
              </div>
            }
          />

          {/* 逾期项目提醒 */}
          {hasOverdueProjects && (
            <Alert className="border-orange-200 bg-orange-50">
              <AlertTriangle className="h-4 w-4 text-orange-600" />
              <AlertDescription className="text-orange-800">
                您有 {filteredData.filter(p =>
                  new Date(p.end_date) < new Date() && p.status !== 'completed'
                ).length} 个项目已逾期，请及时处理。
              </AlertDescription>
            </Alert>
          )}

          {/* KPI 统计卡片区域 */}
          <section>
            <ProjectSummaryCards stats={stats} loading={loading} />
          </section>

          {/* 筛选 / 工具栏区域 */}
          <section>
            <ProjectFilters
              filters={filters}
              onFiltersChange={handleFiltersChange}
              totalCount={filteredData.length}
              onReset={handleReset}
              onExport={handleExport}
              onNewProject={handleNewProject}
              loading={loading}
            />
          </section>

          {/* 列表区域 */}
          <section>
            <ProjectTable
              data={filteredData}
              loading={loading}
              onRowClick={handleViewDetail}
              onViewDetail={handleViewDetail}
              onEdit={handleEdit}
              onStatusChange={handleStatusChange}
              selectedIds={selectedIds}
              onSelectionChange={setSelectedIds}
            />
          </section>
        </div>
      </div>
    </AppLayout>
  );
}