/**
 * Projects Table Component
 *
 * SoT 对齐: DATA_SCHEMA.md v5.2
 */

'use client';

import { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MoreHorizontal, Edit, Trash, Users } from 'lucide-react';
import { useProjects, useDeleteProject } from '../hooks';
import { PROJECT_STATUS_CONFIG } from '../types';
import type { Project, ProjectListParams } from '../types';

interface ProjectsTableProps {
  onEdit?: (project: Project) => void;
  onViewMembers?: (project: Project) => void;
}

export function ProjectsTable({ onEdit, onViewMembers }: ProjectsTableProps) {
  const [params, setParams] = useState<ProjectListParams>({
    page: 1,
    page_size: 20,
  });

  const { data, isLoading, error } = useProjects(params);
  const deleteMutation = useDeleteProject();

  const handlePageChange = (newPage: number) => {
    setParams((prev) => ({ ...prev, page: newPage }));
  };

  const handleDelete = (id: number) => {
    if (confirm('确定要删除此项目吗？')) {
      deleteMutation.mutate(id);
    }
  };

  const formatAmount = (amount: number | undefined | null) => {
    const num = Number(amount) || 0;
    return `¥${num.toFixed(2)}`;
  };

  if (isLoading) {
    return <div className="py-8 text-center text-muted-foreground">加载中...</div>;
  }

  if (error) {
    return (
      <div className="py-8 text-center text-destructive">
        加载失败: {error.message}
      </div>
    );
  }

  const projects = data?.data ?? [];
  const pagination = data?.meta?.pagination;

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>项目名称</TableHead>
            <TableHead>客户</TableHead>
            <TableHead>预算使用</TableHead>
            <TableHead>账户数</TableHead>
            <TableHead>状态</TableHead>
            <TableHead className="w-[80px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {projects.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-muted-foreground">
                暂无数据
              </TableCell>
            </TableRow>
          ) : (
            projects.map((project) => {
              const statusConfig = PROJECT_STATUS_CONFIG[project.status];
              const usagePercent = project.budget > 0
                ? Math.min((project.total_spent / project.budget) * 100, 100)
                : 0;
              return (
                <TableRow key={project.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{project.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {project.account_manager_name || '未分配经理'}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <div>{project.client_name}</div>
                      <div className="text-sm text-muted-foreground">
                        {project.client_company}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <Progress value={usagePercent} className="h-2" />
                      <div className="text-xs text-muted-foreground">
                        {formatAmount(project.total_spent)} / {formatAmount(project.budget)}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <span className="text-green-600">{project.active_accounts}</span>
                      <span className="text-muted-foreground"> / {project.total_accounts}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        statusConfig.variant === 'success'
                          ? 'default'
                          : statusConfig.variant === 'error'
                          ? 'destructive'
                          : statusConfig.variant === 'warning'
                          ? 'outline'
                          : 'secondary'
                      }
                    >
                      {statusConfig.label}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => onEdit?.(project)}>
                          <Edit className="mr-2 h-4 w-4" />
                          编辑
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => onViewMembers?.(project)}>
                          <Users className="mr-2 h-4 w-4" />
                          成员
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleDelete(project.id)}
                          className="text-destructive"
                          disabled={deleteMutation.isPending}
                        >
                          <Trash className="mr-2 h-4 w-4" />
                          删除
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              );
            })
          )}
        </TableBody>
      </Table>

      {pagination && pagination.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            共 {pagination.total} 条，第 {pagination.page} / {pagination.total_pages} 页
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(pagination.page - 1)}
              disabled={pagination.page <= 1}
            >
              上一页
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(pagination.page + 1)}
              disabled={pagination.page >= pagination.total_pages}
            >
              下一页
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
