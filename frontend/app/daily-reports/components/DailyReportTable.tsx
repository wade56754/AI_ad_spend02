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
  Edit,
  Download,
  FileText,
  Calendar,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  User,
  DollarSign,
  Target,
  TrendingUp,
  Paperclip,
  Star,
  RefreshCw
} from 'lucide-react';
import { DailyReport, ReportStatus } from '../types';
import { format } from 'date-fns';

interface DailyReportTableProps {
  data: DailyReport[];
  loading?: boolean;
  onRowClick?: (report: DailyReport) => void;
  onViewDetail?: (report: DailyReport) => void;
  onEdit?: (report: DailyReport) => void;
  onReview?: (report: DailyReport) => void;
  onDownload?: (report: DailyReport) => void;
  onExportSelected?: (selectedIds: number[]) => void;
  onBatchReview?: (selectedIds: number[], status: ReportStatus, notes?: string) => void;
  selectedIds: number[];
  onSelectionChange: (ids: number[]) => void;
}

/**
 * 日报数据表格组件
 *
 * 支持批量选择、状态管理、操作等功能
 */
export function DailyReportTable({
  data,
  loading = false,
  onRowClick,
  onViewDetail,
  onEdit,
  onReview,
  onDownload,
  onExportSelected,
  onBatchReview,
  selectedIds,
  onSelectionChange
}: DailyReportTableProps) {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [reportToDelete, setReportToDelete] = useState<number | null>(null);
  const [batchReviewDialogOpen, setBatchReviewDialogOpen] = useState(false);
  const [batchReviewStatus, setBatchReviewStatus] = useState<ReportStatus>('approved');
  const [batchReviewNotes, setBatchReviewNotes] = useState('');

  // 处理全选/取消全选
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      onSelectionChange(data.map(report => report.id));
    } else {
      onSelectionChange([]);
    }
  };

  // 处理单个选择
  const handleSelectReport = (reportId: number, checked: boolean) => {
    if (checked) {
      onSelectionChange([...selectedIds, reportId]);
    } else {
      onSelectionChange(selectedIds.filter(id => id !== reportId));
    }
  };

  // 获取状态配置
  const getStatusConfig = (status: ReportStatus) => {
    const configs = {
      pending: {
        label: '待审核',
        variant: 'warning' as const,
        icon: Clock,
        color: 'text-yellow-600 bg-yellow-50 border-yellow-200'
      },
      approved: {
        label: '已通过',
        variant: 'default' as const,
        icon: CheckCircle,
        color: 'text-green-600 bg-green-50 border-green-200'
      },
      rejected: {
        label: '已拒绝',
        variant: 'destructive' as const,
        icon: XCircle,
        color: 'text-red-600 bg-red-50 border-red-200'
      },
      needs_revision: {
        label: '需修改',
        variant: 'secondary' as const,
        icon: AlertTriangle,
        color: 'text-orange-600 bg-orange-50 border-orange-200'
      }
    };
    return configs[status];
  };

  // 获取质量评分颜色
  const getQualityScoreColor = (score?: number) => {
    if (!score) return 'text-gray-500';
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-blue-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  // 获取ROI颜色
  const getRoiColor = (roi: number) => {
    if (roi >= 3.0) return 'text-green-600';
    if (roi >= 2.0) return 'text-blue-600';
    if (roi >= 1.0) return 'text-yellow-600';
    return 'text-red-600';
  };

  // 批量审核处理
  const handleBatchReview = () => {
    onBatchReview?.(selectedIds, batchReviewStatus, batchReviewNotes);
    setBatchReviewDialogOpen(false);
    setBatchReviewNotes('');
    onSelectionChange([]);
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
          <FileText className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-medium text-foreground mb-2">暂无日报数据</h3>
        <p className="text-muted-foreground mb-4 max-w-md">
          还没有提交任何日报，点击右上角的"提交日报"按钮开始创建第一份日报。
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
            已选择 <span className="font-medium text-foreground">{selectedIds.length}</span> 份日报
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => onExportSelected?.(selectedIds)}>
              <Download className="h-4 w-4 mr-2" />
              导出选中
            </Button>
            <Button variant="outline" size="sm" onClick={() => setBatchReviewDialogOpen(true)}>
              <CheckCircle className="h-4 w-4 mr-2" />
              批量审核
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
                <TableHead>日报信息</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>投放数据</TableHead>
                <TableHead>成本指标</TableHead>
                <TableHead>质量评分</TableHead>
                <TableHead>提交信息</TableHead>
                <TableHead>审核信息</TableHead>
                <TableHead className="w-[80px]">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((report) => {
                const statusConfig = getStatusConfig(report.status);
                const StatusIcon = statusConfig.icon;
                const isSelected = selectedIds.includes(report.id);

                return (
                  <TableRow
                    key={report.id}
                    className={`cursor-pointer transition-colors hover:bg-muted/50 ${
                      isSelected ? 'bg-muted/30' : ''
                    }`}
                    onClick={() => onRowClick?.(report)}
                  >
                    <TableCell>
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={(checked) => handleSelectReport(report.id, checked as boolean)}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium text-foreground">
                            {format(new Date(report.report_date), 'yyyy-MM-dd')}
                          </span>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {report.project_name}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {report.account_name} ({report.platform})
                        </div>
                        {report.attachments.length > 0 && (
                          <div className="flex items-center gap-1">
                            <Paperclip className="h-3 w-3 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">
                              {report.attachments.length} 个附件
                            </span>
                          </div>
                        )}
                        {report.is_anomaly && (
                          <Badge variant="outline" className="text-xs border-red-500/20 text-red-600">
                            异常数据
                          </Badge>
                        )}
                        {report.tags && report.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {report.tags.slice(0, 2).map((tag, index) => (
                              <Badge key={index} variant="outline" className="text-xs px-1 py-0">
                                {tag}
                              </Badge>
                            ))}
                            {report.tags.length > 2 && (
                              <Badge variant="outline" className="text-xs px-1 py-0">
                                +{report.tags.length - 2}
                              </Badge>
                            )}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${statusConfig.color}`}>
                        <StatusIcon className="h-3 w-3" />
                        {statusConfig.label}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">消耗:</span>
                          <span className="font-medium text-foreground">
                            ${report.spend_amount.toFixed(2)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">粉丝:</span>
                          <span className="font-medium text-foreground">
                            {report.follow_count.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">转化:</span>
                          <span className="font-medium text-foreground">
                            {report.conversion_count}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">ROI:</span>
                          <span className={`font-medium ${getRoiColor(report.roi)}`}>
                            {report.roi.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">CPL:</span>
                          <span className="font-medium text-foreground">
                            ${report.cpl.toFixed(2)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">CTR:</span>
                          <span className="font-medium text-foreground">
                            {(report.performance_metrics.ctr * 100).toFixed(2)}%
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">展示:</span>
                          <span className="font-medium text-foreground">
                            {report.performance_metrics.impressions.toLocaleString()}
                          </span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Star className={`h-4 w-4 ${getQualityScoreColor(report.quality_score)}`} />
                        <span className={`font-medium ${getQualityScoreColor(report.quality_score)}`}>
                          {report.quality_score || 'N/A'}
                        </span>
                      </div>
                      {report.quality_score && (
                        <div className="text-xs text-muted-foreground">
                          {report.quality_score >= 90 ? '优秀' :
                           report.quality_score >= 80 ? '良好' :
                           report.quality_score >= 70 ? '一般' : '需改进'}
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center gap-1">
                          <User className="h-3 w-3 text-muted-foreground" />
                          <span className="text-sm font-medium text-foreground">
                            {report.submitted_by_name}
                          </span>
                        </div>
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          <span>{format(new Date(report.submitted_at), 'MM/dd HH:mm')}</span>
                        </div>
                        {report.notes && (
                          <div className="text-xs text-muted-foreground max-w-xs truncate" title={report.notes}>
                            {report.notes}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {report.reviewed_by_name ? (
                        <div className="space-y-1">
                          <div className="flex items-center gap-1">
                            <User className="h-3 w-3 text-muted-foreground" />
                            <span className="text-sm font-medium text-foreground">
                              {report.reviewed_by_name}
                            </span>
                          </div>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            <span>{format(new Date(report.reviewed_at!), 'MM/dd HH:mm')}</span>
                          </div>
                          {report.review_notes && (
                            <div className="text-xs text-muted-foreground max-w-xs truncate" title={report.review_notes}>
                              {report.review_notes}
                            </div>
                          )}
                        </div>
                      ) : (
                        <span className="text-sm text-muted-foreground">待审核</span>
                      )}
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
                          <DropdownMenuItem onClick={() => onViewDetail?.(report)}>
                            <Eye className="h-4 w-4 mr-2" />
                            查看详情
                          </DropdownMenuItem>
                          {report.status === 'pending' && (
                            <DropdownMenuItem onClick={() => onReview?.(report)}>
                              <CheckCircle className="h-4 w-4 mr-2" />
                              审核报告
                            </DropdownMenuItem>
                          )}
                          {['pending', 'needs_revision'].includes(report.status) && (
                            <DropdownMenuItem onClick={() => onEdit?.(report)}>
                              <Edit className="h-4 w-4 mr-2" />
                              编辑日报
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          {report.attachments.length > 0 && (
                            <DropdownMenuItem onClick={() => onDownload?.(report)}>
                              <Download className="h-4 w-4 mr-2" />
                              下载附件
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuItem>
                            <FileText className="h-4 w-4 mr-2" />
                            导出报告
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

      {/* 批量审核对话框 */}
      <AlertDialog open={batchReviewDialogOpen} onOpenChange={setBatchReviewDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>批量审核日报</AlertDialogTitle>
            <AlertDialogDescription>
              您将对 {selectedIds.length} 份日报进行批量审核，请选择审核状态并填写审核意见。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium">审核状态</label>
              <div className="grid grid-cols-2 gap-2 mt-2">
                {(['approved', 'rejected', 'needs_revision'] as ReportStatus[]).map((status) => {
                  const config = getStatusConfig(status);
                  return (
                    <Button
                      key={status}
                      variant={batchReviewStatus === status ? 'default' : 'outline'}
                      onClick={() => setBatchReviewStatus(status)}
                      className="flex items-center gap-2"
                    >
                      <config.icon className="h-4 w-4" />
                      {config.label}
                    </Button>
                  );
                })}
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">审核意见（可选）</label>
              <textarea
                className="w-full mt-2 p-3 border rounded-lg text-sm resize-none"
                rows={3}
                placeholder="请输入审核意见..."
                value={batchReviewNotes}
                onChange={(e) => setBatchReviewNotes(e.target.value)}
              />
            </div>
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleBatchReview}>
              确认审核
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

export default DailyReportTable;