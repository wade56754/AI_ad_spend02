'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Eye,
  MoreHorizontal,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  RefreshCw,
  CheckSquare,
  Square,
  CreditCard,
  Building,
  User
} from 'lucide-react';
import { RechargeRecord, RechargeStatus, PaymentMethod } from '../types';
import { format } from 'date-fns';

interface RechargeTableProps {
  data: RechargeRecord[];
  loading?: boolean;
  onRowClick?: (record: RechargeRecord) => void;
  onApprove?: (id: number) => void;
  onReject?: (id: number) => void;
  onViewDetail?: (record: RechargeRecord) => void;
  selectedIds?: number[];
  onSelectionChange?: (selectedIds: number[]) => void;
  empty?: boolean;
}

/**
 * 充值管理列表表格组件
 *
 * 显示充值申请记录，支持批量选择、行操作等功能
 */
export function RechargeTable({
  data,
  loading = false,
  onRowClick,
  onApprove,
  onReject,
  onViewDetail,
  selectedIds = [],
  onSelectionChange,
  empty = false
}: RechargeTableProps) {
  const [currentSelectedIds, setCurrentSelectedIds] = useState<number[]>(selectedIds);

  // 处理单行选择
  const handleRowSelect = (id: number, checked: boolean) => {
    let newSelectedIds: number[];
    if (checked) {
      newSelectedIds = [...currentSelectedIds, id];
    } else {
      newSelectedIds = currentSelectedIds.filter(selectedId => selectedId !== id);
    }
    setCurrentSelectedIds(newSelectedIds);
    onSelectionChange?.(newSelectedIds);
  };

  // 处理全选
  const handleSelectAll = (checked: boolean) => {
    const newSelectedIds = checked ? data.map(record => record.id) : [];
    setCurrentSelectedIds(newSelectedIds);
    onSelectionChange?.(newSelectedIds);
  };

  // 检查是否全选
  const isAllSelected = data.length > 0 && currentSelectedIds.length === data.length;
  const isIndeterminate = currentSelectedIds.length > 0 && currentSelectedIds.length < data.length;

  // 获取状态Badge配置
  const getStatusConfig = (status: RechargeStatus) => {
    const configs = {
      pending: {
        label: '待审核',
        variant: 'warning' as const,
        icon: Clock,
      },
      processing: {
        label: '充值中',
        variant: 'info' as const,
        icon: RefreshCw,
      },
      completed: {
        label: '已完成',
        variant: 'success' as const,
        icon: CheckCircle,
      },
      rejected: {
        label: '已驳回',
        variant: 'destructive' as const,
        icon: XCircle,
      },
      cancelled: {
        label: '已取消',
        variant: 'secondary' as const,
        icon: XCircle,
      },
    };
    return configs[status];
  };

  // 获取支付方式标签
  const getPaymentMethodLabel = (method: PaymentMethod) => {
    const labels = {
      alipay: '支付宝',
      wechat: '微信支付',
      bank_transfer: '银行转账',
      credit_card: '信用卡',
    };
    return labels[method] || method;
  };

  // 获取支付方式图标
  const getPaymentMethodIcon = (method: PaymentMethod) => {
    switch (method) {
      case 'alipay':
      case 'wechat':
      case 'credit_card':
        return <CreditCard className="h-4 w-4" />;
      case 'bank_transfer':
        return <Building className="h-4 w-4" />;
      default:
        return <CreditCard className="h-4 w-4" />;
    }
  };

  // Loading状态
  if (loading) {
    return (
      <Card className="bg-card border-border">
        <CardContent className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-6 bg-muted rounded w-1/4"></div>
            <div className="space-y-2">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="h-12 bg-muted rounded"></div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty状态
  if (empty || data.length === 0) {
    return (
      <Card className="bg-card border-border">
        <CardContent className="p-12">
          <div className="text-center">
            <div className="mx-auto w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
              <CreditCard className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">
              暂无充值申请
            </h3>
            <p className="text-muted-foreground max-w-md mx-auto">
              当前筛选条件下没有找到充值申请记录，请尝试调整筛选条件或创建新的充值申请。
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">充值申请列表</CardTitle>
          {currentSelectedIds.length > 0 && (
            <Badge variant="secondary" className="gap-1">
              <CheckSquare className="h-3 w-3" />
              已选 {currentSelectedIds.length} 条
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-b border-border">
                <TableHead className="w-12">
                  <Checkbox
                    checked={isAllSelected}
                    onCheckedChange={handleSelectAll}
                    ref={(node) => {
                      if (node) node.indeterminate = isIndeterminate;
                    }}
                    aria-label="全选"
                  />
                </TableHead>
                <TableHead className="w-40">充值单号</TableHead>
                <TableHead className="w-48">关联广告账户</TableHead>
                <TableHead className="w-24">平台</TableHead>
                <TableHead className="w-32 text-right">充值金额</TableHead>
                <TableHead className="w-28">支付方式</TableHead>
                <TableHead className="w-24 text-center">状态</TableHead>
                <TableHead className="w-20 text-center">优先级</TableHead>
                <TableHead className="w-32">申请人</TableHead>
                <TableHead className="w-28">申请时间</TableHead>
                <TableHead className="w-20 text-center">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((record) => {
                const isSelected = currentSelectedIds.includes(record.id);
                const statusConfig = getStatusConfig(record.status);
                const StatusIcon = statusConfig.icon;

                return (
                  <TableRow
                    key={record.id}
                    className={`border-b border-border hover:bg-muted/40 transition-colors cursor-pointer ${
                      isSelected ? 'bg-muted/20' : ''
                    }`}
                    onClick={() => onRowClick?.(record)}
                  >
                    <TableCell>
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={(checked) => {
                          handleRowSelect(record.id, !!checked);
                        }}
                        onClick={(e) => e.stopPropagation()}
                        aria-label={`选择申请 ${record.request_code}`}
                      />
                    </TableCell>

                    {/* 充值单号 */}
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-medium text-sm">{record.request_code}</div>
                        {record.project_name && (
                          <div className="text-xs text-muted-foreground">
                            {record.project_name}
                          </div>
                        )}
                      </div>
                    </TableCell>

                    {/* 关联广告账户 */}
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-medium text-sm">{record.account_name}</div>
                        <div className="text-xs text-muted-foreground font-mono">
                          {record.account_id}
                        </div>
                      </div>
                    </TableCell>

                    {/* 平台 */}
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {record.platform.toUpperCase()}
                      </Badge>
                    </TableCell>

                    {/* 充值金额 */}
                    <TableCell className="text-right">
                      <div className="space-y-1">
                        <div className="font-medium text-sm">
                          ${record.amount.toLocaleString()}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {record.currency}
                        </div>
                      </div>
                    </TableCell>

                    {/* 支付方式 */}
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getPaymentMethodIcon(record.payment_method)}
                        <span className="text-sm">
                          {getPaymentMethodLabel(record.payment_method)}
                        </span>
                      </div>
                    </TableCell>

                    {/* 状态 */}
                    <TableCell className="text-center">
                      <Badge variant={statusConfig.variant} className="gap-1">
                        <StatusIcon className="h-3 w-3" />
                        {statusConfig.label}
                      </Badge>
                    </TableCell>

                    {/* 优先级 */}
                    <TableCell className="text-center">
                      <Badge
                        variant={
                          record.priority === 'urgent' ? 'destructive' :
                          record.priority === 'high' ? 'warning' :
                          record.priority === 'low' ? 'secondary' :
                          'default'
                        }
                        className="text-xs"
                      >
                        {record.priority === 'urgent' ? '紧急' :
                         record.priority === 'high' ? '高' :
                         record.priority === 'low' ? '低' : '中'}
                      </Badge>
                    </TableCell>

                    {/* 申请人 */}
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">{record.requested_by}</span>
                      </div>
                    </TableCell>

                    {/* 申请时间 */}
                    <TableCell>
                      <div className="text-sm text-muted-foreground">
                        {format(new Date(record.requested_at), 'MM/dd HH:mm')}
                      </div>
                    </TableCell>

                    {/* 操作 */}
                    <TableCell className="text-center">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              onViewDetail?.(record);
                            }}
                            className="cursor-pointer"
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            查看详情
                          </DropdownMenuItem>

                          {record.status === 'pending' && (
                            <>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onApprove?.(record.id);
                                }}
                                className="cursor-pointer text-green-600 focus:text-green-700"
                              >
                                <CheckCircle className="h-4 w-4 mr-2" />
                                通过审核
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onReject?.(record.id);
                                }}
                                className="cursor-pointer text-red-600 focus:text-red-700"
                              >
                                <XCircle className="h-4 w-4 mr-2" />
                                驳回申请
                              </DropdownMenuItem>
                            </>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

export default RechargeTable;