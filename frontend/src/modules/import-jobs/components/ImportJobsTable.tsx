/**
 * Import Jobs Table Component
 *
 * Table for displaying and managing import jobs
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
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  MoreHorizontal,
  PlayCircle,
  XCircle,
  Trash2,
  Eye,
} from 'lucide-react';
import {
  useImportJobs,
  useStartImportJob,
  useCancelImportJob,
  useDeleteImportJob,
} from '../hooks';
import {
  IMPORT_JOB_STATUS_CONFIG,
  IMPORT_JOB_TYPE_CONFIG,
} from '../types';
import type { ImportJob, ImportJobListParams } from '../types';

export function ImportJobsTable() {
  const [params, setParams] = useState<ImportJobListParams>({
    page: 1,
    page_size: 20,
  });

  const { data, isLoading, error } = useImportJobs(params);
  const startMutation = useStartImportJob();
  const cancelMutation = useCancelImportJob();
  const deleteMutation = useDeleteImportJob();

  const handlePageChange = (newPage: number) => {
    setParams((prev) => ({ ...prev, page: newPage }));
  };

  const handleStart = (id: number) => {
    startMutation.mutate(id);
  };

  const handleCancel = (id: number) => {
    if (confirm('确定要取消此导入任务吗？')) {
      cancelMutation.mutate(id);
    }
  };

  const handleDelete = (id: number) => {
    if (confirm('确定要删除此导入任务吗？此操作不可撤销。')) {
      deleteMutation.mutate(id);
    }
  };

  const isPending =
    startMutation.isPending ||
    cancelMutation.isPending ||
    deleteMutation.isPending;

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

  const jobs = data?.data ?? [];
  const pagination = data?.meta?.pagination;

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>任务编号</TableHead>
            <TableHead>类型</TableHead>
            <TableHead>文件名</TableHead>
            <TableHead>状态</TableHead>
            <TableHead>进度</TableHead>
            <TableHead>成功/失败</TableHead>
            <TableHead>创建时间</TableHead>
            <TableHead className="w-[80px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {jobs.length === 0 ? (
            <TableRow>
              <TableCell colSpan={8} className="text-center text-muted-foreground">
                暂无数据
              </TableCell>
            </TableRow>
          ) : (
            jobs.map((job: ImportJob) => {
              const statusConfig = IMPORT_JOB_STATUS_CONFIG[job.status];
              const typeConfig = IMPORT_JOB_TYPE_CONFIG[job.type];
              const progressPercent = job.progress_percent ?? 0;
              const canStart = job.status === 'pending';
              const canCancel = job.status === 'pending';
              const canDelete = job.status === 'pending';

              return (
                <TableRow key={job.id}>
                  <TableCell className="font-mono text-sm">
                    {job.job_no}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{typeConfig.label}</Badge>
                  </TableCell>
                  <TableCell className="max-w-[200px] truncate" title={job.file_name}>
                    {job.file_name || '-'}
                  </TableCell>
                  <TableCell>
                    <Badge variant={statusConfig.variant}>
                      {statusConfig.label}
                    </Badge>
                  </TableCell>
                  <TableCell className="w-[120px]">
                    {job.status === 'processing' ? (
                      <div className="space-y-1">
                        <Progress value={progressPercent} className="h-2" />
                        <span className="text-xs text-muted-foreground">
                          {progressPercent.toFixed(1)}%
                        </span>
                      </div>
                    ) : job.status === 'completed' ? (
                      <span className="text-sm text-green-600">100%</span>
                    ) : (
                      <span className="text-sm text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell className="text-sm">
                    {job.total_rows ? (
                      <span>
                        <span className="text-green-600">{job.success_rows || 0}</span>
                        {' / '}
                        <span className="text-red-600">{job.failed_rows || 0}</span>
                        {' (共 '}
                        {job.total_rows}
                        {')'}
                      </span>
                    ) : (
                      '-'
                    )}
                  </TableCell>
                  <TableCell className="text-sm">
                    {new Date(job.created_at).toLocaleDateString('zh-CN')}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem disabled>
                          <Eye className="mr-2 h-4 w-4" />
                          查看详情
                        </DropdownMenuItem>
                        {canStart && (
                          <DropdownMenuItem
                            onClick={() => handleStart(job.id)}
                            disabled={isPending}
                          >
                            <PlayCircle className="mr-2 h-4 w-4" />
                            开始处理
                          </DropdownMenuItem>
                        )}
                        {canCancel && (
                          <DropdownMenuItem
                            onClick={() => handleCancel(job.id)}
                            disabled={isPending}
                          >
                            <XCircle className="mr-2 h-4 w-4" />
                            取消任务
                          </DropdownMenuItem>
                        )}
                        {canDelete && (
                          <>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => handleDelete(job.id)}
                              disabled={isPending}
                              className="text-destructive"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              删除
                            </DropdownMenuItem>
                          </>
                        )}
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
