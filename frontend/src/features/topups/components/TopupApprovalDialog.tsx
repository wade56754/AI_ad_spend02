/**
 * Topup Approval Dialog Component
 *
 * Unified dialog for data review and finance approval workflows
 * SoT: STATE_MACHINE.md v2.6 Section 9
 */

'use client';

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
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
  CheckCircle,
  XCircle,
  AlertTriangle,
  Loader2,
  FileText,
  Building2,
  CreditCard,
  User,
  Calendar,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { TopupRequest, TopupAction, TopupStatus } from '../types';
import { TopupStatusBadge, TopupAmount, TopupProgress } from './TopupStatusBadge';
import { useTopupActions } from '../hooks/useTopupActions';

// === Types ===

type ApprovalMode = 'data_review' | 'finance_approval' | 'complete' | 'cancel';

interface TopupApprovalDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  topup: TopupRequest | null;
  mode: ApprovalMode;
  userRole: string;
  onSuccess?: () => void;
}

// === Mode Configuration ===

const MODE_CONFIG: Record<ApprovalMode, {
  title: string;
  description: string;
  approveAction: TopupAction;
  rejectAction?: TopupAction;
  approveLabel: string;
  rejectLabel?: string;
  requiresNotes: boolean;
  requiresRejectReason: boolean;
}> = {
  data_review: {
    title: '数据复核',
    description: '请核实充值申请的数据准确性',
    approveAction: 'data_review_approve',
    rejectAction: 'data_review_reject',
    approveLabel: '复核通过',
    rejectLabel: '复核拒绝',
    requiresNotes: false,
    requiresRejectReason: true,
  },
  finance_approval: {
    title: '财务终审',
    description: '请确认财务审批结果',
    approveAction: 'finance_approve',
    rejectAction: 'finance_reject',
    approveLabel: '批准支付',
    rejectLabel: '拒绝支付',
    requiresNotes: false,
    requiresRejectReason: true,
  },
  complete: {
    title: '确认到账',
    description: '请确认充值金额已到账',
    approveAction: 'complete',
    approveLabel: '确认完成',
    requiresNotes: false,
    requiresRejectReason: false,
  },
  cancel: {
    title: '取消申请',
    description: '确定要取消此充值申请吗？',
    approveAction: 'cancel',
    approveLabel: '确认取消',
    requiresNotes: false,
    requiresRejectReason: false,
  },
};

// === Sub Components ===

interface TopupDetailCardProps {
  topup: TopupRequest;
}

function TopupDetailCard({ topup }: TopupDetailCardProps) {
  // Handle Money type - could be number or object
  const amountValue = typeof topup.amount === 'number'
    ? topup.amount
    : (topup.amount as { value?: number })?.value ?? 0;

  return (
    <div className="rounded-lg border bg-muted/50 p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">充值申请详情</span>
        </div>
        <TopupStatusBadge status={topup.status} size="sm" />
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="flex items-center gap-2">
          <Building2 className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-muted-foreground">项目:</span>
          <span className="font-medium truncate">{topup.project_name || '-'}</span>
        </div>
        <div className="flex items-center gap-2">
          <CreditCard className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-muted-foreground">账户:</span>
          <span className="font-medium truncate">{topup.ad_account_name || '-'}</span>
        </div>
        <div className="flex items-center gap-2">
          <User className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-muted-foreground">申请人:</span>
          <span className="font-medium">{topup.requested_by_name || '-'}</span>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-muted-foreground">申请时间:</span>
          <span className="font-medium">
            {new Date(topup.requested_at).toLocaleDateString('zh-CN')}
          </span>
        </div>
      </div>

      {/* Amount */}
      <div className="flex items-center justify-between pt-2 border-t">
        <span className="text-muted-foreground">充值金额</span>
        <TopupAmount amount={amountValue} currency={topup.currency} size="lg" />
      </div>

      {/* Notes */}
      {topup.notes && (
        <div className="pt-2 border-t">
          <span className="text-muted-foreground text-sm">备注:</span>
          <p className="text-sm mt-1">{topup.notes}</p>
        </div>
      )}

      {/* Progress */}
      <div className="pt-2 border-t">
        <TopupProgress status={topup.status} size="sm" />
      </div>
    </div>
  );
}

// === Main Component ===

export function TopupApprovalDialog({
  open,
  onOpenChange,
  topup,
  mode,
  userRole,
  onSuccess,
}: TopupApprovalDialogProps) {
  const config = MODE_CONFIG[mode];
  const { executeAction, isLoading } = useTopupActions({
    onSuccess: (action) => {
      onSuccess?.();
      onOpenChange(false);
    },
  });

  // Form state
  const [notes, setNotes] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectConfirm, setShowRejectConfirm] = useState(false);

  // Reset form when dialog opens
  useEffect(() => {
    if (open) {
      setNotes('');
      setRejectReason('');
    }
  }, [open]);

  if (!topup) return null;

  const handleApprove = async () => {
    try {
      await executeAction(config.approveAction, topup.id, {
        notes,
        version: topup.version,
      });
    } catch (error) {
      console.error('Approval failed:', error);
    }
  };

  const handleReject = async () => {
    if (!config.rejectAction) return;

    if (!rejectReason.trim()) {
      return; // Validation handled in UI
    }

    try {
      await executeAction(config.rejectAction, topup.id, {
        rejection_reason: rejectReason,
        version: topup.version,
      });
      setShowRejectConfirm(false);
    } catch (error) {
      console.error('Rejection failed:', error);
    }
  };

  const canApprove = mode !== 'cancel' || true;
  const canReject = config.rejectAction && (rejectReason.trim().length > 0 || !showRejectConfirm);

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {mode === 'cancel' ? (
                <AlertTriangle className="h-5 w-5 text-amber-500" />
              ) : mode === 'complete' ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : (
                <FileText className="h-5 w-5 text-blue-500" />
              )}
              {config.title}
            </DialogTitle>
            <DialogDescription>{config.description}</DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Topup Details */}
            <TopupDetailCard topup={topup} />

            {/* Notes Input */}
            {config.requiresNotes && (
              <div className="space-y-2">
                <Label htmlFor="notes">审批备注</Label>
                <Textarea
                  id="notes"
                  placeholder="请输入审批备注（可选）"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                />
              </div>
            )}

            {/* Optional notes for other modes */}
            {!config.requiresNotes && mode !== 'cancel' && mode !== 'complete' && (
              <div className="space-y-2">
                <Label htmlFor="notes">审批备注（可选）</Label>
                <Textarea
                  id="notes"
                  placeholder="请输入审批备注"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                />
              </div>
            )}
          </div>

          <DialogFooter className="flex gap-2 sm:gap-0">
            {/* Reject Button */}
            {config.rejectAction && (
              <Button
                type="button"
                variant="destructive"
                onClick={() => setShowRejectConfirm(true)}
                disabled={isLoading}
              >
                <XCircle className="h-4 w-4 mr-2" />
                {config.rejectLabel}
              </Button>
            )}

            {/* Cancel Button */}
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              取消
            </Button>

            {/* Approve Button */}
            <Button
              type="button"
              onClick={handleApprove}
              disabled={isLoading}
              variant={mode === 'cancel' ? 'destructive' : 'default'}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <CheckCircle className="h-4 w-4 mr-2" />
              )}
              {config.approveLabel}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reject Confirmation Dialog */}
      <AlertDialog open={showRejectConfirm} onOpenChange={setShowRejectConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <XCircle className="h-5 w-5 text-red-500" />
              确认拒绝
            </AlertDialogTitle>
            <AlertDialogDescription>
              请输入拒绝原因，此操作不可撤销。
            </AlertDialogDescription>
          </AlertDialogHeader>

          <div className="py-4">
            <Label htmlFor="reject-reason" className="text-sm font-medium">
              拒绝原因 <span className="text-red-500">*</span>
            </Label>
            <Textarea
              id="reject-reason"
              placeholder="请输入拒绝原因"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              rows={3}
              className="mt-2"
            />
            {rejectReason.trim().length === 0 && (
              <p className="text-sm text-red-500 mt-1">请输入拒绝原因</p>
            )}
          </div>

          <AlertDialogFooter>
            <AlertDialogCancel disabled={isLoading}>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleReject}
              disabled={isLoading || rejectReason.trim().length === 0}
              className="bg-red-600 hover:bg-red-700"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <XCircle className="h-4 w-4 mr-2" />
              )}
              确认拒绝
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

// === Quick Action Dialogs ===

interface TopupSubmitDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  topup: TopupRequest | null;
  onSuccess?: () => void;
}

export function TopupSubmitDialog({
  open,
  onOpenChange,
  topup,
  onSuccess,
}: TopupSubmitDialogProps) {
  const { submitForReview, isLoading } = useTopupActions({
    onSuccess: () => {
      onSuccess?.();
      onOpenChange(false);
    },
  });

  if (!topup) return null;

  // Handle Money type - could be number or object
  const amountValue = typeof topup.amount === 'number'
    ? topup.amount
    : (topup.amount as { value?: number })?.value ?? 0;

  const handleSubmit = async () => {
    try {
      await submitForReview(topup.id);
    } catch (error) {
      console.error('Submit failed:', error);
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>提交审批</AlertDialogTitle>
          <AlertDialogDescription>
            确定要提交此充值申请进行审批吗？提交后将进入数据复核流程。
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="py-4">
          <div className="rounded-lg border bg-muted/50 p-3">
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">充值金额</span>
              <TopupAmount amount={amountValue} currency={topup.currency} size="lg" />
            </div>
          </div>
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isLoading}>取消</AlertDialogCancel>
          <AlertDialogAction onClick={handleSubmit} disabled={isLoading}>
            {isLoading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <CheckCircle className="h-4 w-4 mr-2" />
            )}
            确认提交
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

interface TopupCancelDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  topup: TopupRequest | null;
  onSuccess?: () => void;
}

export function TopupCancelDialog({
  open,
  onOpenChange,
  topup,
  onSuccess,
}: TopupCancelDialogProps) {
  const { cancel, isLoading } = useTopupActions({
    onSuccess: () => {
      onSuccess?.();
      onOpenChange(false);
    },
  });

  if (!topup) return null;

  const handleCancel = async () => {
    try {
      await cancel(topup.id);
    } catch (error) {
      console.error('Cancel failed:', error);
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            取消充值申请
          </AlertDialogTitle>
          <AlertDialogDescription>
            确定要取消此充值申请吗？此操作不可撤销。
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="py-4">
          <TopupDetailCard topup={topup} />
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isLoading}>返回</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleCancel}
            disabled={isLoading}
            className="bg-red-600 hover:bg-red-700"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <XCircle className="h-4 w-4 mr-2" />
            )}
            确认取消
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

export default TopupApprovalDialog;
