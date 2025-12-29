/**
 * Topup Detail Dialog Component
 *
 * Displays detailed information about a topup request
 * with approval timeline and action buttons
 * Extracted from TopupsPage.tsx for better maintainability
 */

'use client';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  ClipboardCheck,
  Wallet,
  CheckCircle,
  Ban,
  FileText,
} from 'lucide-react';
import {
  TopupStatusBadge,
  TopupAmount,
} from './TopupStatusBadge';
import { TopupApprovalTimeline } from './TopupApprovalTimeline';
import type { TopupRequest } from '../types';

/** Local action type for this dialog */
export type TopupDialogAction = 'data_review' | 'finance_approval' | 'complete' | 'cancel' | 'submit';

interface TopupDetailDialogProps {
  topup: TopupRequest | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAction: (action: TopupDialogAction) => void;
  userRole: string;
}

export function TopupDetailDialog({
  topup,
  open,
  onOpenChange,
  onAction,
  userRole,
}: TopupDetailDialogProps) {
  if (!topup) return null;

  // 权限检查 (SoT: MASTER.md v4.6, backend/routers/topup.py)
  const canDataReview =
    topup.status === 'pending_review' &&
    ['project_owner', 'finance', 'admin'].includes(userRole);
  const canFinanceApprove =
    topup.status === 'finance_approve' &&
    ['finance', 'admin'].includes(userRole);
  const canComplete =
    topup.status === 'paid' &&
    ['finance', 'system', 'admin'].includes(userRole);
  const canCancel =
    ['draft', 'pending_review', 'finance_approve'].includes(topup.status) &&
    ['pitcher', 'media_buyer', 'account_manager', 'admin'].includes(userRole);
  const canSubmit =
    topup.status === 'draft' &&
    ['pitcher', 'media_buyer', 'account_manager', 'admin'].includes(userRole);

  // Handle Money type - could be number or object
  const amountValue = typeof topup.amount === 'number'
    ? topup.amount
    : (topup.amount as { value?: number })?.value ?? 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[540px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            充值申请详情
          </DialogTitle>
          <DialogDescription>
            查看充值申请的详细信息和审批历史
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Status Badge */}
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">当前状态</span>
            <TopupStatusBadge status={topup.status} size="lg" />
          </div>

          {/* Amount */}
          <div className="flex items-center justify-between py-4 border-y">
            <span className="text-muted-foreground">充值金额</span>
            <TopupAmount amount={amountValue} currency={topup.currency} size="lg" />
          </div>

          {/* Basic Info */}
          <div className="space-y-3">
            <h4 className="font-medium text-sm text-muted-foreground">基本信息</h4>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-muted-foreground">项目</span>
                <p className="font-medium">{topup.project_name || topup.project_id.slice(0, 8)}</p>
              </div>
              <div>
                <span className="text-muted-foreground">广告账户</span>
                <p className="font-medium">{topup.ad_account_name || '-'}</p>
              </div>
              <div>
                <span className="text-muted-foreground">申请人</span>
                <p className="font-medium">{topup.requested_by_name || '-'}</p>
              </div>
              <div>
                <span className="text-muted-foreground">申请时间</span>
                <p className="font-medium">
                  {new Date(topup.requested_at).toLocaleString('zh-CN')}
                </p>
              </div>
            </div>
            {topup.notes && (
              <div>
                <span className="text-muted-foreground text-sm">备注</span>
                <p className="text-sm mt-1 p-2 bg-muted rounded">{topup.notes}</p>
              </div>
            )}
          </div>

          {/* Timeline */}
          <div className="space-y-3">
            <h4 className="font-medium text-sm text-muted-foreground">审批历史</h4>
            <TopupApprovalTimeline topup={topup} showDetails />
          </div>

          {/* Actions */}
          <div className="space-y-2 pt-4 border-t">
            {canSubmit && (
              <Button onClick={() => onAction('submit')} className="w-full">
                <CheckCircle className="h-4 w-4 mr-2" />
                提交审批
              </Button>
            )}
            {canDataReview && (
              <Button onClick={() => onAction('data_review')} className="w-full">
                <ClipboardCheck className="h-4 w-4 mr-2" />
                数据复核
              </Button>
            )}
            {canFinanceApprove && (
              <Button onClick={() => onAction('finance_approval')} className="w-full">
                <Wallet className="h-4 w-4 mr-2" />
                财务终审
              </Button>
            )}
            {canComplete && (
              <Button onClick={() => onAction('complete')} className="w-full">
                <CheckCircle className="h-4 w-4 mr-2" />
                确认到账
              </Button>
            )}
            {canCancel && (
              <Button variant="outline" onClick={() => onAction('cancel')} className="w-full">
                <Ban className="h-4 w-4 mr-2" />
                取消申请
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default TopupDetailDialog;
