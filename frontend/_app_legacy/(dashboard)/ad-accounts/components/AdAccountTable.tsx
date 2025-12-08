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
} from '@/components/ui/dropdown-menu';
import { Progress } from '@/components/ui/progress';
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
  Play,
  Pause,
  AlertTriangle,
  CheckCircle,
  Clock,
  XCircle,
  Shield,
  DollarSign,
  BarChart3,
  Calendar,
  User,
  Settings,
  Trash2,
  Download
} from 'lucide-react';
import { AdAccount, AccountStatus, Platform } from '../types';
import { format } from 'date-fns';

interface AdAccountTableProps {
  data: AdAccount[];
  loading?: boolean;
  onRowClick?: (account: AdAccount) => void;
  onViewDetail?: (account: AdAccount) => void;
  onEdit?: (account: AdAccount) => void;
  onStatusChange?: (id: number, status: AccountStatus) => void;
  onDelete?: (id: number) => void;
  onExportSelected?: (selectedIds: number[]) => void;
  selectedIds: number[];
  onSelectionChange: (ids: number[]) => void;
}

/**
 * 广告账户数据表格组件
 *
 * 支持批量选择、状态管理、操作等功能
 */
export function AdAccountTable({
  data,
  loading = false,
  onRowClick,
  onViewDetail,
  onEdit,
  onStatusChange,
  onDelete,
  onExportSelected,
  selectedIds,
  onSelectionChange
}: AdAccountTableProps) {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [accountToDelete, setAccountToDelete] = useState<number | null>(null);

  // 处理全选/取消全选
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      onSelectionChange(data.map(account => account.id));
    } else {
      onSelectionChange([]);
    }
  };

  // 处理单个选择
  const handleSelectAccount = (accountId: number, checked: boolean) => {
    if (checked) {
      onSelectionChange([...selectedIds, accountId]);
    } else {
      onSelectionChange(selectedIds.filter(id => id !== accountId));
    }
  };

  // 获取状态配置
  const getStatusConfig = (status: AccountStatus) => {
    const configs = {
      active: {
        label: '投放中',
        variant: 'default' as const,
        icon: Play,
        color: 'text-green-600 bg-green-50 border-green-200'
      },
      paused: {
        label: '已暂停',
        variant: 'secondary' as const,
        icon: Pause,
        color: 'text-yellow-600 bg-yellow-50 border-yellow-200'
      },
      banned: {
        label: '已封禁',
        variant: 'destructive' as const,
        icon: XCircle,
        color: 'text-red-600 bg-red-50 border-red-200'
      },
      pending: {
        label: '待审核',
        variant: 'warning' as const,
        icon: Clock,
        color: 'text-orange-600 bg-orange-50 border-orange-200'
      },
      restricted: {
        label: '受限制',
        variant: 'outline' as const,
        icon: AlertTriangle,
        color: 'text-purple-600 bg-purple-50 border-purple-200'
      }
    };
    return configs[status];
  };

  // 获取平台配置
  const getPlatformConfig = (platform: Platform) => {
    const configs = {
      facebook: { label: 'Facebook', color: 'bg-blue-100 text-blue-700' },
      tiktok: { label: 'TikTok', color: 'bg-black text-white' },
      google: { label: 'Google', color: 'bg-red-100 text-red-700' },
      twitter: { label: 'Twitter', color: 'bg-sky-100 text-sky-700' },
      instagram: { label: 'Instagram', color: 'bg-pink-100 text-pink-700' },
      youtube: { label: 'YouTube', color: 'bg-red-100 text-red-700' },
      linkedin: { label: 'LinkedIn', color: 'bg-blue-100 text-blue-700' }
    };
    return configs[platform];
  };

  // 获取风险等级颜色
  const getRiskLevelColor = (riskLevel: string) => {
    const colors = {
      low: 'text-green-600',
      medium: 'text-yellow-600',
      high: 'text-orange-600',
      critical: 'text-red-600'
    };
    return colors[riskLevel as keyof typeof colors] || 'text-gray-600';
  };

  // 删除确认
  const handleDelete = (accountId: number) => {
    setAccountToDelete(accountId);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (accountToDelete) {
      onDelete?.(accountToDelete);
      setDeleteDialogOpen(false);
      setAccountToDelete(null);
    }
  };

  // 导出选中项
  const handleExportSelected = () => {
    onExportSelected?.(selectedIds);
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
          <Shield className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-medium text-foreground mb-2">暂无广告账户</h3>
        <p className="text-muted-foreground mb-4 max-w-md">
          还没有创建任何广告账户，点击右上角的"新建账户"按钮开始创建第一个广告账户。
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
            已选择 <span className="font-medium text-foreground">{selectedIds.length}</span> 个账户
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleExportSelected}>
              <Download className="h-4 w-4 mr-2" />
              导出选中
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
                <TableHead>账户信息</TableHead>
                <TableHead>平台</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>类型</TableHead>
                <TableHead>余额/消耗</TableHead>
                <TableHead>健康状态</TableHead>
                <TableHead>负责人</TableHead>
                <TableHead>最近活跃</TableHead>
                <TableHead className="w-[80px]">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((account) => {
                const statusConfig = getStatusConfig(account.account_status);
                const platformConfig = getPlatformConfig(account.platform);
                const StatusIcon = statusConfig.icon;
                const isSelected = selectedIds.includes(account.id);

                return (
                  <TableRow
                    key={account.id}
                    className={`cursor-pointer transition-colors hover:bg-muted/50 ${
                      isSelected ? 'bg-muted/30' : ''
                    }`}
                    onClick={() => onRowClick?.(account)}
                  >
                    <TableCell>
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={(checked) => handleSelectAccount(account.id, checked as boolean)}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-medium text-foreground">
                          {account.account_name}
                        </div>
                        <div className="text-xs text-muted-foreground font-mono">
                          {account.account_id}
                        </div>
                        {account.tags && account.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {account.tags.slice(0, 2).map((tag, index) => (
                              <Badge key={index} variant="outline" className="text-xs px-1 py-0">
                                {tag}
                              </Badge>
                            ))}
                            {account.tags.length > 2 && (
                              <Badge variant="outline" className="text-xs px-1 py-0">
                                +{account.tags.length - 2}
                              </Badge>
                            )}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={platformConfig.color}>
                        {platformConfig.label}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusConfig.color}`}>
                        <StatusIcon className="h-3 w-3" />
                        {statusConfig.label}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">
                        {account.account_type === 'personal' ? '个人' :
                         account.account_type === 'business' ? '商业' : '代理商'}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <DollarSign className="h-3 w-3 text-muted-foreground" />
                          <span className="font-medium">${account.balance.toLocaleString()}</span>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          消耗: ${account.current_spend.toLocaleString()}
                        </div>
                        {account.spending_limit > 0 && (
                          <div className="w-full">
                            <Progress
                              value={(account.current_spend / account.spending_limit) * 100}
                              className="h-1"
                            />
                            <div className="text-xs text-muted-foreground mt-1">
                              {Math.round((account.current_spend / account.spending_limit) * 100)}% 预算使用
                            </div>
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {account.health_status ? (
                        <div className="space-y-1">
                          <div className={`text-sm font-medium ${getRiskLevelColor(account.health_status.risk_level)}`}>
                            {account.health_status.risk_level === 'low' ? '低风险' :
                             account.health_status.risk_level === 'medium' ? '中风险' :
                             account.health_status.risk_level === 'high' ? '高风险' : '紧急'}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            评分: {account.health_status.health_score}/100
                          </div>
                          {account.health_status.issues.length > 0 && (
                            <Badge variant="outline" className="text-xs">
                              {account.health_status.issues.length} 个问题
                            </Badge>
                          )}
                        </div>
                      ) : (
                        <span className="text-sm text-muted-foreground">未评估</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {account.assigned_user_name ? (
                        <div className="space-y-1">
                          <div className="flex items-center gap-1">
                            <User className="h-3 w-3 text-muted-foreground" />
                            <span className="text-sm">{account.assigned_user_name}</span>
                          </div>
                          {account.project_name && (
                            <div className="text-xs text-muted-foreground">
                              {account.project_name}
                            </div>
                          )}
                        </div>
                      ) : (
                        <span className="text-sm text-muted-foreground">未分配</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Calendar className="h-3 w-3" />
                        {format(new Date(account.last_active), 'MM/dd HH:mm')}
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
                          <DropdownMenuItem onClick={() => onViewDetail?.(account)}>
                            <Eye className="h-4 w-4 mr-2" />
                            查看详情
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => onEdit?.(account)}>
                            <Edit className="h-4 w-4 mr-2" />
                            编辑账户
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          {account.account_status === 'active' ? (
                            <DropdownMenuItem onClick={() => onStatusChange?.(account.id, 'paused')}>
                              <Pause className="h-4 w-4 mr-2" />
                              暂停投放
                            </DropdownMenuItem>
                          ) : (
                            <DropdownMenuItem onClick={() => onStatusChange?.(account.id, 'active')}>
                              <Play className="h-4 w-4 mr-2" />
                              开始投放
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => handleDelete(account.id)}
                            className="text-destructive focus:text-destructive"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            删除账户
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
              您确定要删除这个广告账户吗？此操作不可撤销，所有相关数据将被永久删除。
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

export default AdAccountTable;