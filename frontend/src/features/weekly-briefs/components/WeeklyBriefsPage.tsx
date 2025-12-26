/**
 * Weekly Briefs Page Component
 *
 * SoT: docs/10.module-specs/B3-weekly-brief.md §3.1 页面布局
 * SoT: STATE_MACHINE.md v2.6 (周报状态: draft → submitted)
 * SoT: API_SOT.md v9.0 Section 5.7 (Weekly Brief endpoints)
 *
 * 一句话定义: 让项目负责人/老板了解"项目这周进展如何？"
 *
 * 周报 2 状态机:
 *   draft → submitted (终态)
 *
 * Phase 约束 (MASTER.md §3.1/§3.2):
 * - Phase 1: 周报可选提交，用于观察习惯
 * - Phase 2: 必须提交 + 考核关联
 *
 * 视觉规范 (v3.0):
 * - 白色卡片容器 + 投影
 * - KPI 卡片 5 个
 * - 周选择器 + 项目/状态筛选
 */

'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { format } from 'date-fns';
import {
  FileText,
  Download,
  Plus,
  CheckCircle,
  Clock,
  Percent,
  DollarSign,
  FolderOpen,
} from 'lucide-react';

import { PageTemplate } from '@/components/layout/page-template';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/data-state';
import { StatCard } from '@/features/dashboard/components/StatCard';

import { WeekPicker, getWeekStart, getWeekString } from './WeekPicker';
import { WeeklyBriefStatusBadge } from './WeeklyBriefStatusBadge';
import {
  useWeeklyBriefList,
  useWeeklyBriefStats,
  useExportWeeklyBriefs,
  useRefreshWeeklyBriefs,
} from '../hooks';
import type { WeeklyBrief, WeeklyBriefStatus } from '../types';

// Format currency
function formatCurrency(amount: number | null | undefined): string {
  if (amount === null || amount === undefined) return '¥0';
  if (amount >= 10000) {
    return `¥${(amount / 10000).toFixed(1)}万`;
  }
  return `¥${amount.toLocaleString('zh-CN', { maximumFractionDigits: 0 })}`;
}

// Format CPL
function formatCPL(cpl: number | null | undefined): string {
  if (cpl === null || cpl === undefined || cpl === 0) return '--';
  return `¥${cpl.toFixed(2)}`;
}

// Format date
function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '--';
  return format(new Date(dateStr), 'MM-dd HH:mm');
}

export function WeeklyBriefsPage() {
  const router = useRouter();

  // Filter state
  const [selectedWeek, setSelectedWeek] = useState<Date>(() => getWeekStart(new Date()));
  const [selectedProjectId, setSelectedProjectId] = useState<string>('__all__');
  const [selectedStatus, setSelectedStatus] = useState<string>('__all__');

  // Build query params
  const queryParams = useMemo(() => {
    const params: Record<string, unknown> = {
      week_start: format(selectedWeek, 'yyyy-MM-dd'),
    };
    if (selectedProjectId !== '__all__') {
      params.project_id = parseInt(selectedProjectId, 10);
    }
    if (selectedStatus !== '__all__') {
      params.status = selectedStatus as WeeklyBriefStatus;
    }
    return params;
  }, [selectedWeek, selectedProjectId, selectedStatus]);

  // Data hooks
  // SoT: B3-weekly-brief.md §4 API 接口
  const {
    data: briefsData,
    isLoading: isLoadingBriefs,
    error: briefsError,
  } = useWeeklyBriefList(queryParams);

  const {
    data: statsData,
    isLoading: isLoadingStats,
  } = useWeeklyBriefStats({
    week_start: format(selectedWeek, 'yyyy-MM-dd'),
  });

  const exportMutation = useExportWeeklyBriefs();
  const { refreshAll } = useRefreshWeeklyBriefs();

  // Extract unique projects for filter
  const projectOptions = useMemo(() => {
    if (!briefsData?.items) return [];
    const projectMap = new Map<number, string>();
    briefsData.items.forEach((brief) => {
      if (brief.project_id && brief.project_name) {
        projectMap.set(brief.project_id, brief.project_name);
      }
    });
    return Array.from(projectMap.entries()).map(([id, name]) => ({
      value: String(id),
      label: name,
    }));
  }, [briefsData?.items]);

  // Handlers
  const handleCreateBrief = () => {
    router.push('/weekly-briefs/new');
  };

  const handleExport = () => {
    exportMutation.mutate({
      week: getWeekString(selectedWeek),
      format: 'excel',
    });
  };

  const handleRowClick = (brief: WeeklyBrief) => {
    if (brief.status === 'draft') {
      router.push(`/weekly-briefs/${brief.id}/edit`);
    } else {
      router.push(`/weekly-briefs/${brief.id}`);
    }
  };

  // Stats
  const stats = statsData || briefsData?.stats;

  // Render loading state
  if (isLoadingBriefs && !briefsData) {
    return (
      <PageTemplate title="周简报" subtitle="项目周度进展复盘">
        <LoadingState />
      </PageTemplate>
    );
  }

  // Render error state
  if (briefsError) {
    return (
      <PageTemplate title="周简报" subtitle="项目周度进展复盘">
        <ErrorState error={briefsError} onRetry={refreshAll} />
      </PageTemplate>
    );
  }

  return (
    <PageTemplate
      title="周简报"
      subtitle="项目周度进展复盘"
      actions={
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExport} disabled={exportMutation.isPending} data-testid="export-btn">
            <Download className="h-4 w-4 mr-2" />
            导出
          </Button>
          <Button onClick={handleCreateBrief} data-testid="create-btn">
            <Plus className="h-4 w-4 mr-2" />
            创建周报
          </Button>
        </div>
      }
    >
      <div className="space-y-6" data-testid="weekly-brief-page">
        {/* Filters */}
        <Card>
          <CardContent className="py-4">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2" data-testid="week-filter">
                <span className="text-sm text-muted-foreground">周次:</span>
                <WeekPicker
                  value={selectedWeek}
                  onChange={(date) => setSelectedWeek(date)}
                />
              </div>

              <div className="flex items-center gap-2" data-testid="project-filter">
                <span className="text-sm text-muted-foreground">项目:</span>
                <Select value={selectedProjectId} onValueChange={setSelectedProjectId}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="全部项目" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all__">全部项目</SelectItem>
                    {projectOptions.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center gap-2" data-testid="status-filter">
                <span className="text-sm text-muted-foreground">状态:</span>
                <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                  <SelectTrigger className="w-[120px]">
                    <SelectValue placeholder="全部" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all__">全部</SelectItem>
                    <SelectItem value="draft">草稿</SelectItem>
                    <SelectItem value="submitted">已提交</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <StatCard
              title="本周项目数"
              value={stats.total_projects}
              icon={<FolderOpen className="h-5 w-5" />}
              color="blue"
            />
            <StatCard
              title="已提交"
              value={stats.submitted_count}
              icon={<CheckCircle className="h-5 w-5" />}
              color="green"
            />
            <StatCard
              title="待提交"
              value={stats.draft_count}
              icon={<Clock className="h-5 w-5" />}
              color="orange"
            />
            <StatCard
              title="提交率"
              value={`${(stats.submission_rate ?? 0).toFixed(1)}%`}
              icon={<Percent className="h-5 w-5" />}
              color="purple"
            />
            <StatCard
              title="本周总消耗"
              value={formatCurrency(stats.total_weekly_spend)}
              icon={<DollarSign className="h-5 w-5" />}
              color="blue"
            />
          </div>
        )}

        {/* Table */}
        <Card data-testid="weekly-brief-table">
          <CardContent className="p-0">
            {!briefsData?.items?.length ? (
              <EmptyState
                icon={<FileText className="h-12 w-12" />}
                title="暂无周报数据"
                description='点击"创建周报"添加本周周报'
              />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>项目</TableHead>
                    <TableHead>负责人</TableHead>
                    <TableHead className="text-right">周消耗</TableHead>
                    <TableHead className="text-right">周进粉</TableHead>
                    <TableHead className="text-right">CPL</TableHead>
                    <TableHead>提交时间</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead className="text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {briefsData.items.map((brief) => (
                    <TableRow
                      key={brief.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleRowClick(brief)}
                    >
                      <TableCell className="font-medium">
                        {brief.project_name || `项目 ${brief.project_id}`}
                      </TableCell>
                      <TableCell>{brief.submitter_name || '--'}</TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(brief.weekly_spend)}
                      </TableCell>
                      <TableCell className="text-right">
                        {brief.weekly_conversions?.toLocaleString() || '--'}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCPL(brief.weekly_cpl)}
                        {brief.cpl_trend !== null && brief.cpl_trend !== undefined && (
                          <span
                            className={`ml-1 text-xs ${
                              brief.cpl_trend < 0 ? 'text-green-600' : 'text-red-600'
                            }`}
                          >
                            {brief.cpl_trend < 0 ? '↓' : '↑'}
                            {Math.abs(brief.cpl_trend).toFixed(1)}%
                          </span>
                        )}
                      </TableCell>
                      <TableCell>{formatDate(brief.submitted_at)}</TableCell>
                      <TableCell>
                        <WeeklyBriefStatusBadge status={brief.status} showTooltip={false} />
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRowClick(brief);
                          }}
                        >
                          {brief.status === 'draft' ? '编辑' : '查看'}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </PageTemplate>
  );
}

export default WeeklyBriefsPage;
