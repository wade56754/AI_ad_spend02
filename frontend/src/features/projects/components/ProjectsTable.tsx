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

  // 格式化单价
  const formatCPL = (price: number | null | undefined) => {
    if (price === null || price === undefined) return '--';
    return `¥${Number(price).toFixed(2)}`;
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

  // 格式化日期
  const formatDate = (dateStr: string | undefined | null) => {
    if (!dateStr) return '--';
    const d = new Date(dateStr);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  };

  // 格式化进粉数
  const formatFollows = (follows: number | undefined | null) => {
    const num = Number(follows) || 0;
    if (num >= 10000) {
      return `${(num / 10000).toFixed(1)}万`;
    }
    return num.toLocaleString();
  };

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>项目名</TableHead>
            <TableHead>开始日期</TableHead>
            <TableHead>地区</TableHead>
            <TableHead className="text-right">单价</TableHead>
            <TableHead className="text-right">进粉数</TableHead>
            <TableHead>负责人</TableHead>
            <TableHead>状态</TableHead>
            <TableHead className="w-[80px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {projects.length === 0 ? (
            <TableRow>
              <TableCell colSpan={8} className="text-center text-muted-foreground">
                暂无数据
              </TableCell>
            </TableRow>
          ) : (
            projects.map((project) => {
              const statusConfig = PROJECT_STATUS_CONFIG[project.status];
              // 获取负责人名称 (优先 owner_name，兼容旧字段)
              const ownerName = project.owner_name || project.account_manager_name;
              return (
                <TableRow key={project.id}>
                  <TableCell>
                    <div className="font-medium">{project.name}</div>
                  </TableCell>
                  <TableCell>
                    <span className="text-muted-foreground">
                      {formatDate(project.start_date)}
                    </span>
                  </TableCell>
                  <TableCell>
                    <span className={project.region ? 'text-foreground' : 'text-muted-foreground'}>
                      {project.region || '--'}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    {formatCPL(project.unit_price)}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatFollows(project.total_follows)}
                  </TableCell>
                  <TableCell>
                    <span className={ownerName ? 'text-foreground' : 'text-muted-foreground'}>
                      {ownerName || '未分配'}
                    </span>
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
