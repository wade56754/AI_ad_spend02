/**
 * ProjectsDataTable - 项目列表表格
 *
 * 显示项目列表，支持状态标签、预算进度、操作按钮
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { MoreHorizontal, ExternalLink, Pause, Play, Archive } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ModuleDataTable, type ColumnDef } from '@/modules/shared';
import type { Project } from '../types';
import { PROJECT_STATUS_CONFIG } from '../types';

interface ProjectsDataTableProps {
  projects: Project[];
  loading?: boolean;
  onRowClick?: (project: Project) => void;
  className?: string;
}

// 状态徽章变体映射
const statusVariantMap: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  success: 'default',
  warning: 'secondary',
  error: 'destructive',
  info: 'outline',
  default: 'outline',
};

export function ProjectsDataTable({
  projects,
  loading,
  onRowClick,
  className,
}: ProjectsDataTableProps) {
  const columns: ColumnDef<Project>[] = [
    {
      key: 'name',
      header: '项目名称',
      render: (_, row) => (
        <div>
          <div className="font-medium text-text-strong">{row.name}</div>
          <div className="text-xs text-text-muted">{row.client_name}</div>
        </div>
      ),
    },
    {
      key: 'status',
      header: '状态',
      width: '100px',
      render: (_, row) => {
        const config = PROJECT_STATUS_CONFIG[row.status];
        return (
          <Badge variant={statusVariantMap[config.variant]}>
            {config.label}
          </Badge>
        );
      },
    },
    {
      key: 'budget_progress',
      header: '预算进度',
      render: (_, row) => {
        const progress = (row.spent_total / row.budget_total) * 100;
        const isOverBudget = progress > 100;

        return (
          <div className="w-32">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-text-muted">
                ¥{(row.spent_total / 100).toLocaleString()}
              </span>
              <span className={cn(
                isOverBudget ? 'text-danger' : 'text-text-muted'
              )}>
                {progress.toFixed(0)}%
              </span>
            </div>
            <Progress
              value={Math.min(progress, 100)}
              className={cn(
                'h-1.5',
                isOverBudget && '[&>div]:bg-danger'
              )}
            />
          </div>
        );
      },
    },
    {
      key: 'spent_today',
      header: '今日消耗',
      align: 'right',
      render: (_, row) => (
        <span className="text-text-body">
          ¥{(row.spent_today / 100).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'ad_account_count',
      header: '账户数',
      align: 'center',
      width: '80px',
      render: (_, row) => (
        <span className="text-text-body">{row.ad_account_count}</span>
      ),
    },
    {
      key: 'actions',
      header: '',
      width: '60px',
      align: 'right',
      render: (_, row) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 hover:bg-elevated"
              onClick={(e) => e.stopPropagation()}
            >
              <MoreHorizontal className="h-4 w-4 text-text-muted" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            className="bg-card-bg border-border-default"
          >
            <DropdownMenuItem className="text-text-body hover:bg-elevated">
              <ExternalLink className="mr-2 h-4 w-4" />
              查看详情
            </DropdownMenuItem>
            {row.status === 'active' ? (
              <DropdownMenuItem className="text-text-body hover:bg-elevated">
                <Pause className="mr-2 h-4 w-4" />
                暂停项目
              </DropdownMenuItem>
            ) : row.status === 'paused' ? (
              <DropdownMenuItem className="text-text-body hover:bg-elevated">
                <Play className="mr-2 h-4 w-4" />
                恢复项目
              </DropdownMenuItem>
            ) : null}
            <DropdownMenuItem className="text-text-body hover:bg-elevated">
              <Archive className="mr-2 h-4 w-4" />
              归档
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  return (
    <ModuleDataTable
      columns={columns}
      data={projects}
      getRowKey={(row) => row.id}
      loading={loading}
      emptyText="暂无项目数据"
      title="项目列表"
      description={`共 ${projects.length} 个项目`}
      onRowClick={onRowClick}
      className={className}
    />
  );
}

export default ProjectsDataTable;
