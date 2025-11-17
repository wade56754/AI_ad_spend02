'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  AlertTriangle,
  Calendar,
  User,
  CreditCard,
  Building,
  FileText,
  MessageSquare,
  DollarSign,
  Globe,
  Settings,
  Download
} from 'lucide-react';
import { RechargeRecordDetail, RechargeStatus, PaymentMethod } from '../types';
import { format } from 'date-fns';

interface RechargeDetailDrawerProps {
  open: boolean;
  onClose: () => void;
  record: RechargeRecordDetail | null;
  onApprove?: (id: number) => void;
  onReject?: (id: number) => void;
  onMarkException?: (id: number) => void;
  loading?: boolean;
}

/**
 * 充值详情抽屉组件
 *
 * 显示充值申请的详细信息，包括基本信息、支付信息、操作记录时间线等
 */
export function RechargeDetailDrawer({
  open,
  onClose,
  record,
  onApprove,
  onReject,
  onMarkException,
  loading = false
}: RechargeDetailDrawerProps) {
  const [rejectionReason, setRejectionReason] = useState('');
  const [showRejectForm, setShowRejectForm] = useState(false);

  if (!record) return null;

  // 获取状态配置
  const getStatusConfig = (status: RechargeStatus) => {
    const configs = {
      pending: {
        label: '待审核',
        variant: 'warning' as const,
        icon: Clock,
        description: '等待财务审核批准',
      },
      processing: {
        label: '充值中',
        variant: 'info' as const,
        icon: RefreshCw,
        description: '正在处理充值流程',
      },
      completed: {
        label: '已完成',
        variant: 'success' as const,
        icon: CheckCircle,
        description: '充值已完成到账',
      },
      rejected: {
        label: '已驳回',
        variant: 'destructive' as const,
        icon: XCircle,
        description: record.rejection_reason || '申请已被驳回',
      },
      cancelled: {
        label: '已取消',
        variant: 'secondary' as const,
        icon: XCircle,
        description: '申请已取消',
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

  const statusConfig = getStatusConfig(record.status);
  const StatusIcon = statusConfig.icon;

  // 渲染操作记录时间线
  const renderTimeline = () => {
    const timelineItems = [
      {
        action: 'created',
        title: '申请创建',
        actor: record.requested_by,
        time: record.requested_at,
        description: `${record.requested_by} 创建了充值申请`,
        icon: FileText,
        color: 'blue',
      },
      ...(record.approved_at && record.approved_by ? [{
        action: 'approved',
        title: '审核通过',
        actor: record.approved_by,
        time: record.approved_at,
        description: `${record.approved_by} 批准了充值申请`,
        icon: CheckCircle,
        color: 'green',
      }] : []),
      ...(record.completed_at ? [{
        action: 'completed',
        title: '充值完成',
        actor: '系统',
        time: record.completed_at,
        description: `充值已完成，支付参考号: ${record.payment_reference || 'N/A'}`,
        icon: CheckCircle,
        color: 'green',
      }] : []),
      ...(record.rejection_reason ? [{
        action: 'rejected',
        title: '申请驳回',
        actor: record.approved_by || '系统',
        time: record.approved_at || record.requested_at,
        description: `驳回原因: ${record.rejection_reason}`,
        icon: XCircle,
        color: 'red',
      }] : []),
    ].sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime());

    return (
      <div className="space-y-4">
        {timelineItems.map((item, index) => {
          const Icon = item.icon;
          return (
            <div key={index} className="flex gap-4">
              <div className="flex flex-col items-center">
                <div className={`w-8 h-8 rounded-full bg-${item.color}-100 flex items-center justify-center`}>
                  <Icon className={`h-4 w-4 text-${item.color}-600`} />
                </div>
                {index < timelineItems.length - 1 && (
                  <div className="w-0.5 h-16 bg-border mt-2"></div>
                )}
              </div>
              <div className="flex-1 min-w-0 pb-4">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="text-sm font-medium text-foreground">
                    {item.title}
                  </h4>
                  <span className="text-xs text-muted-foreground">
                    {format(new Date(item.time), 'MM/dd HH:mm')}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mb-1">
                  {item.description}
                </p>
                <p className="text-xs text-muted-foreground">
                  操作人: {item.actor}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="w-full max-w-2xl overflow-y-auto">
        <DialogHeader className="mb-6">
          <div className="flex items-center justify-between">
            <DialogTitle className="text-xl">充值申请详情</DialogTitle>
            <Badge variant={statusConfig.variant} className="gap-1">
              <StatusIcon className="h-3 w-3" />
              {statusConfig.label}
            </Badge>
          </div>
          <DialogDescription>
            充值单号: {record.request_code}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* 基础信息 */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <FileText className="h-4 w-4" />
                基础信息
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">申请单号</label>
                  <p className="text-sm font-mono mt-1">{record.request_code}</p>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">项目名称</label>
                  <p className="text-sm mt-1">{record.project_name || '未指定'}</p>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">申请人</label>
                  <div className="flex items-center gap-2 mt-1">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{record.requested_by}</span>
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">申请时间</label>
                  <div className="flex items-center gap-2 mt-1">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">
                      {format(new Date(record.requested_at), 'yyyy-MM-dd HH:mm:ss')}
                    </span>
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">关联账户</label>
                  <p className="text-sm mt-1">{record.account_name}</p>
                  <p className="text-xs text-muted-foreground font-mono">{record.account_id}</p>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">平台</label>
                  <div className="flex items-center gap-2 mt-1">
                    <Globe className="h-4 w-4 text-muted-foreground" />
                    <Badge variant="outline" className="text-xs">
                      {record.platform.toUpperCase()}
                    </Badge>
                  </div>
                </div>
              </div>

              {/* 备注 */}
              {record.notes && (
                <div>
                  <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                    <MessageSquare className="h-3 w-3" />
                    申请备注
                  </label>
                  <div className="mt-1 p-3 bg-muted/50 rounded-lg">
                    <p className="text-sm">{record.notes}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 金额信息 */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <DollarSign className="h-4 w-4" />
                金额信息
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">申请金额</label>
                  <p className="text-lg font-semibold text-foreground mt-1">
                    ${record.amount.toLocaleString()} {record.currency}
                  </p>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">币种</label>
                  <p className="text-sm mt-1">{record.currency}</p>
                </div>
                {record.exchange_rate && (
                  <>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">汇率</label>
                      <p className="text-sm mt-1">{record.exchange_rate}</p>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">实际到账金额</label>
                      <p className="text-sm font-medium mt-1">
                        ${record.actual_amount?.toLocaleString() || 'N/A'}
                      </p>
                    </div>
                  </>
                )}
                {record.fee && (
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">手续费</label>
                    <p className="text-sm mt-1">${record.fee}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 支付信息 */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <CreditCard className="h-4 w-4" />
                支付信息
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">支付方式</label>
                  <div className="flex items-center gap-2 mt-1">
                    <CreditCard className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{getPaymentMethodLabel(record.payment_method)}</span>
                  </div>
                </div>
                {record.payment_reference && (
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">支付参考号</label>
                    <p className="text-sm font-mono mt-1">{record.payment_reference}</p>
                  </div>
                )}
              </div>

              {record.payment_account && (
                <div>
                  <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                    <Building className="h-3 w-3" />
                    收款账户信息
                  </label>
                  <div className="mt-2 p-3 bg-muted/50 rounded-lg space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">账户名称:</span>
                      <span className="text-sm font-medium">{record.payment_account.account_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">账户号码:</span>
                      <span className="text-sm font-mono">{record.payment_account.account_number}</span>
                    </div>
                    {record.payment_account.bank_name && (
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">开户银行:</span>
                        <span className="text-sm">{record.payment_account.bank_name}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 操作记录 */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Settings className="h-4 w-4" />
                操作记录
              </CardTitle>
            </CardHeader>
            <CardContent>
              {renderTimeline()}
            </CardContent>
          </Card>

          {/* 驳回原因 */}
          {record.rejection_reason && (
            <Card className="border-red-200 bg-red-50">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-red-800 mb-1">驳回原因</h4>
                    <p className="text-sm text-red-700">{record.rejection_reason}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 操作按钮 */}
          {record.status === 'pending' && (
            <div className="flex gap-3 pt-4 border-t">
              <Button
                className="flex-1"
                onClick={() => onApprove?.(record.id)}
                disabled={loading}
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                通过审核
              </Button>
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => setShowRejectForm(!showRejectForm)}
                disabled={loading}
              >
                <XCircle className="h-4 w-4 mr-2" />
                驳回申请
              </Button>
              <Button
                variant="outline"
                onClick={() => onMarkException?.(record.id)}
                disabled={loading}
              >
                <AlertTriangle className="h-4 w-4 mr-2" />
                标记异常
              </Button>
            </div>
          )}

          {/* 驳回表单 */}
          {showRejectForm && (
            <Card className="border-red-200">
              <CardContent className="p-4">
                <h4 className="text-sm font-medium mb-3">请输入驳回原因</h4>
                <textarea
                  className="w-full p-3 border rounded-lg text-sm resize-none"
                  rows={3}
                  placeholder="请说明驳回原因..."
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                />
                <div className="flex gap-2 mt-3">
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => {
                      onReject?.(record.id);
                      setShowRejectForm(false);
                    }}
                    disabled={!rejectionReason.trim() || loading}
                  >
                    确认驳回
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setShowRejectForm(false);
                      setRejectionReason('');
                    }}
                  >
                    取消
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default RechargeDetailDrawer;