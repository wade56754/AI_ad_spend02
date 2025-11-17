'use client';

import React, { useState } from 'react';
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
import { Checkbox } from '@/components/ui/checkbox';
import { Progress } from '@/components/ui/progress';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  MoreHorizontal,
  Eye,
  Play,
  Pause,
  FileText,
  FileSpreadsheet,
  Upload,
  Trash2,
  RefreshCw,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  BarChart3,
  Settings,
  Download,
  Calendar,
  User,
} from 'lucide-react';
import { ReconciliationBatch, ReconciliationStatus, PlatformSpendSource } from '../types';
import { format } from 'date-fns';

interface ReconciliationTableProps {
  data: ReconciliationBatch[];
  loading?: boolean;
  onRowClick?: (batch: ReconciliationBatch) => void;
  onViewDetail?: (batch: ReconciliationBatch) => void;
  onStartReconciliation?: (batch: ReconciliationBatch) => void;
  onPauseReconciliation?: (batch: ReconciliationBatch) => void;
  onExportReport?: (batch: ReconciliationBatch) => void;
  onUploadPlatformData?: (batch: ReconciliationBatch) => void;
  onDelete?: (id: number) => void;
  selectedIds: number[];
  onSelectionChange: (ids: number[]) => void;
}

/**
 * 对账数据表格组件
 *
 * 支持批量选择、状态管理、操作等功能
 */
export function ReconciliationTable({
  data,
  loading = false,
  onRowClick,
  onViewDetail,
  onStartReconciliation,
  onPauseReconciliation,
  onExportReport,
  onUploadPlatformData,
  onDelete,
  selectedIds,
  onSelectionChange
}: ReconciliationTableProps) {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [batchToDelete, setBatchToDelete] = useState<number | null>(null);

  // 处理全选/取消全选
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      onSelectionChange(data.map(batch => batch.id));
    } else {
      onSelectionChange([]);
    }
  };

  // 处理单个选择
  const handleSelectBatch = (batchId: number, checked: boolean) => {
    if (checked) {
      onSelectionChange([...selectedIds, batchId]);
    } else {
      onSelectionChange(selectedIds.filter(id => id !== batchId));
    }
  };

  // 获取状态配置
  const getStatusConfig = (status: ReconciliationStatus) => {
    const configs = {
      pending: {
        label: '待处理',
        variant: 'warning' as const,
        icon: Clock,
        color: 'text-yellow-600 bg-yellow-50 border-yellow-200'
      },
      in_progress: {
        label: '对账中',
        variant: 'default' as const,
        icon: RefreshCw,
        color: 'text-blue-600 bg-blue-50 border-blue-200'
      },
      completed: {
        label: '已完成',
        variant: 'default' as const,
        icon: CheckCircle,
        color: 'text-green-600 bg-green-50 border-green-200'
      },
      failed: {
        label: '失败',
        variant: 'destructive' as const,
        icon: XCircle,
        color: 'text-red-600 bg-red-50 border-red-200'
      },
      cancelled: {
        label: '已取消',
        variant: 'secondary' as const,
        icon: XCircle,
        color: 'text-gray-600 bg-gray-50 border-gray-200'
      }
    };
    return configs[status];
  };

  // 获取平台数据源配置
  const getPlatformSourceConfig = (source: PlatformSpendSource) => {
    const configs = {
      manual: {
        label: '手动录入',
        color: 'bg-gray-100 text-gray-700'
      },
      api: {
        label: 'API获取',
        color: 'bg-blue-100 text-blue-700'
      },
      file: {
        label: '文件上传',
        color: 'bg-green-100 text-green-700'
      }
    };
    return configs[source];
  };

  // 获取差异金额颜色
  const getDifferenceColor = (difference: number) => {
    if (difference === 0) return 'text-green-600';
    if (difference > 0) return 'text-red-600';
    return 'text-orange-600';
  };

  // 删除确认
  const handleDelete = (batchId: number) => {
    setBatchToDelete(batchId);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (batchToDelete) {
      onDelete?.(batchToDelete);
      setDeleteDialogOpen(false);
      setBatchToDelete(null);
    }
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(10)].map((_, index) => (
          <div key={index} className="bg-card rounded-lg border p-4 animate-pulse">
            <div className="grid grid-cols-12 gap-4">
              <div className="col-span-1 h-4 bg-muted rounded"></div>
              <div className="col-span-3 h-4 bg-muted rounded"></div>
              <div className="col-span-2 h-4 bg-muted rounded"></div>
              <div className="col-span-2 h-4 bg-muted rounded"></div>
              <div className="col-span-2 h-4 bg-muted rounded"></div>
              <div className="col-span-2 h-4 bg-muted rounded"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
          <FileSpreadsheet className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-medium text-foreground mb-2">暂无对账批次</h3>
        <p className="text-muted-foreground mb-4 max-w-md">
          还没有创建任何对账批次，点击右上角的"新建批次"按钮开始创建第一个对账批次。
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 批量操作工具栏 */}
      {selectedIds.length > 0 && (
        <div className="bg-card rounded-lg border p-3 flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            已选择 <span className="font-medium text-foreground">{selectedIds.length}</span> 个批次
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled>
              <Download className="h-4 w-4 mr-2" />
              批量导出
            </Button>
          </div>
        </div>
      )}

      {/* 数据表格 */}
      <div className="bg-card rounded-lg border overflow-hidden">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[50px]">
                  <Checkbox
                    checked={selectedIds.length === data.length && data.length > 0}
                    onCheckedChange={handleSelectAll}
                  />
                </TableHead>
                <TableHead>批次信息</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>进度</TableHead>
                <TableHead>差异情况</TableHead>
                <TableHead>财务汇总</TableHead>
                <TableHead>平台数据源</TableHead>
                <TableHead>创建信息</TableHead>
                <TableHead className="w-[80px]">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((batch) => {
                const statusConfig = getStatusConfig(batch.status);
                const StatusIcon = statusConfig.icon;
                const isSelected = selectedIds.includes(batch.id);
                const progress = batch.total_accounts > 0 ? (batch.processed_accounts / batch.total_accounts) * 100 : 0;
                const sourceConfig = getPlatformSourceConfig(batch.platform_spend_source);

                return (
                  <TableRow
                    key={batch.id}
                    className={`cursor-pointer transition-colors hover:bg-muted/50 ${
                      isSelected ? 'bg-muted/30' : ''
                    }`}
                    onClick={() => onRowClick?.(batch)}
                  >
                    <TableCell>
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={(checked) => handleSelectBatch(batch.id, checked as boolean)}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-medium text-foreground">
                          {batch.batch_name}
                        </div>
                        <div className="text-sm text-muted-foreground flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {format(new Date(batch.period_start), 'yyyy/MM/dd')} - {format(new Date(batch.period_end), 'yyyy/MM/dd')}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${statusConfig.color}`}>
                        <StatusIcon className="h-3 w-3" />
                        {statusConfig.label}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span>{batch.processed_accounts}/{batch.total_accounts}</span>
                          <span>{progress.toFixed(0)}%</span>
                        </div>
                        <Progress
                          value={progress}
                          className={`h-2 ${
                            batch.status === 'completed' ? 'bg-green-500' :
                            batch.status === 'failed' ? 'bg-red-500' :
                            'bg-blue-500'
                          }`}
                        />
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          {batch.total_discrepancies > 0 ? (
                            <AlertTriangle className="h-4 w-4 text-orange-500" />
                          ) : (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          )}
                          <span className="text-sm font-medium">
                            {batch.total_discrepancies} 个差异
                          </span>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          差异率: {Math.abs(batch.difference_percentage).toFixed(2)}%
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm space-y-1">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">系统:</span>
                          <span className="font-medium">¥{batch.total_system_spend.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">平台:</span>
                          <span className="font-medium">¥{batch.total_platform_spend.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">差异:</span>
                          <span className={`font-medium ${getDifferenceColor(batch.total_difference)}`}>
                            ¥{Math.abs(batch.total_difference).toLocaleString()}
                          </span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <Badge variant="outline" className={sourceConfig.color}>
                          {sourceConfig.label}
                        </Badge>
                        {batch.uploaded_file && (
                          <div className="text-xs text-muted-foreground">
                            {batch.uploaded_file.filename}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm space-y-1">
                        <div className="flex items-center gap-1">
                          <User className="h-3 w-3 text-muted-foreground" />
                          <span className="font-medium text-foreground">
                            {batch.created_by_name}
                          </span>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {format(new Date(batch.created_at), 'MM/dd HH:mm')}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>操作</DropdownMenuLabel>
                          <DropdownMenuItem onClick={() => onViewDetail?.(batch)}>
                            <Eye className="h-4 w-4 mr-2" />
                            查看详情
                          </DropdownMenuItem>
                          {batch.status === 'completed' && (
                            <DropdownMenuItem onClick={() => onExportReport?.(batch)}>
                              <FileSpreadsheet className="h-4 w-4 mr-2" />
                              导出报告
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          {batch.status === 'pending' && (
                            <DropdownMenuItem onClick={() => onStartReconciliation?.(batch)}>
                              <Play className="h-4 w-4 mr-2" />
                              开始对账
                            </DropdownMenuItem>
                          )}
                          {batch.status === 'in_progress' && (
                            <DropdownMenuItem onClick={() => onPauseReconciliation?.(batch)}>
                              <Pause className="h-4 w-4 mr-2" />
                              暂停对账
                            </DropdownMenuItem>
                          )}
                          {(batch.status === 'pending' || batch.status === 'failed') && (
                            <DropdownMenuItem onClick={() => onUploadPlatformData?.(batch)}>
                              <Upload className="h-4 w-4 mr-2" />
                              上传平台账单
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => handleDelete(batch.id)}
                            className="text-destructive focus:text-destructive"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            删除批次
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* 删除确认对话框 */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              您确定要删除这个对账批次吗？此操作不可撤销，所有相关数据将被永久删除。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              确认删除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

export default ReconciliationTable;