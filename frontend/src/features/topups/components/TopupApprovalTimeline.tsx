/**
 * Topup Approval Timeline Component
 *
 * Visual timeline showing the complete approval history of a topup request
 * SoT: STATE_MACHINE.md v2.6 Section 9
 */

'use client';

import { useMemo } from 'react';
import {
  FileEdit,
  Send,
  ClipboardCheck,
  Wallet,
  CreditCard,
  CheckCircle,
  XCircle,
  Ban,
  Clock,
  User,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { TopupRequest, TopupApprovalLog, TopupStatus, TopupAction } from '../types';
import { TOPUP_STATUS_CONFIG } from '../types';

// === Types ===

interface TimelineEvent {
  id: string;
  timestamp: string;
  type: 'status_change' | 'action';
  status?: TopupStatus;
  action?: TopupAction;
  actor: string;
  actorRole?: string;
  notes?: string;
  icon: LucideIcon;
  iconColor: string;
  title: string;
  description: string;
}

interface TopupApprovalTimelineProps {
  topup: TopupRequest;
  approvalLogs?: TopupApprovalLog[];
  showDetails?: boolean;
  className?: string;
}

// === Icon/Color Mapping ===

const ACTION_ICONS: Record<TopupAction | string, { icon: LucideIcon; color: string }> = {
  create: { icon: FileEdit, color: 'text-gray-500' },
  submit: { icon: Send, color: 'text-blue-500' },
  data_review_approve: { icon: ClipboardCheck, color: 'text-green-500' },
  data_review_reject: { icon: XCircle, color: 'text-red-500' },
  finance_approve: { icon: Wallet, color: 'text-green-500' },
  finance_reject: { icon: XCircle, color: 'text-red-500' },
  mark_paid: { icon: CreditCard, color: 'text-indigo-500' },
  complete: { icon: CheckCircle, color: 'text-green-500' },
  cancel: { icon: Ban, color: 'text-gray-500' },
};

const STATUS_ICONS: Record<TopupStatus, { icon: LucideIcon; color: string }> = {
  draft: { icon: FileEdit, color: 'text-gray-500' },
  pending_review: { icon: ClipboardCheck, color: 'text-amber-500' },
  finance_approve: { icon: Wallet, color: 'text-blue-500' },
  paid: { icon: CreditCard, color: 'text-indigo-500' },
  completed: { icon: CheckCircle, color: 'text-green-500' },
  rejected: { icon: XCircle, color: 'text-red-500' },
  cancelled: { icon: Ban, color: 'text-gray-500' },
};

const ACTION_LABELS: Record<TopupAction | string, string> = {
  create: '创建申请',
  submit: '提交审批',
  data_review_approve: '数据复核通过',
  data_review_reject: '数据复核拒绝',
  finance_approve: '财务终审通过',
  finance_reject: '财务终审拒绝',
  mark_paid: '标记已支付',
  complete: '确认到账',
  cancel: '取消申请',
};

// === Helper Functions ===

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const diffHours = diff / (1000 * 60 * 60);
  const diffDays = diff / (1000 * 60 * 60 * 24);

  if (diffHours < 1) {
    const minutes = Math.floor(diff / (1000 * 60));
    return `${minutes} 分钟前`;
  } else if (diffHours < 24) {
    return `${Math.floor(diffHours)} 小时前`;
  } else if (diffDays < 7) {
    return `${Math.floor(diffDays)} 天前`;
  }

  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function buildTimelineFromTopup(topup: TopupRequest): TimelineEvent[] {
  const events: TimelineEvent[] = [];

  // 1. Created event
  events.push({
    id: 'created',
    timestamp: topup.created_at,
    type: 'action',
    action: 'create',
    actor: topup.requested_by_name || '未知用户',
    icon: FileEdit,
    iconColor: 'text-gray-500',
    title: '创建充值申请',
    description: topup.notes || '申请已创建',
  });

  // 2. Submitted event (if past draft)
  if (topup.status !== 'draft') {
    events.push({
      id: 'submitted',
      timestamp: topup.requested_at,
      type: 'action',
      action: 'submit',
      actor: topup.requested_by_name || '未知用户',
      icon: Send,
      iconColor: 'text-blue-500',
      title: '提交审批',
      description: '申请已提交，等待数据复核',
    });
  }

  // 3. Data review event
  if (topup.data_reviewed_at) {
    const isApproved = topup.status !== 'rejected' || topup.finance_approved_at;
    events.push({
      id: 'data_reviewed',
      timestamp: topup.data_reviewed_at,
      type: 'action',
      action: isApproved ? 'data_review_approve' : 'data_review_reject',
      actor: topup.data_reviewed_by_name || '数据运营',
      actorRole: '数据运营',
      notes: topup.data_review_notes,
      icon: isApproved ? ClipboardCheck : XCircle,
      iconColor: isApproved ? 'text-green-500' : 'text-red-500',
      title: isApproved ? '数据复核通过' : '数据复核拒绝',
      description: topup.data_review_notes || (isApproved ? '数据核实无误' : '数据核实存在问题'),
    });
  }

  // 4. Finance approval event
  if (topup.finance_approved_at) {
    const isApproved = topup.status !== 'rejected';
    events.push({
      id: 'finance_approved',
      timestamp: topup.finance_approved_at,
      type: 'action',
      action: isApproved ? 'finance_approve' : 'finance_reject',
      actor: topup.finance_approved_by_name || '财务',
      actorRole: '财务',
      notes: topup.finance_approval_notes,
      icon: isApproved ? Wallet : XCircle,
      iconColor: isApproved ? 'text-green-500' : 'text-red-500',
      title: isApproved ? '财务终审通过' : '财务终审拒绝',
      description: topup.finance_approval_notes || (isApproved ? '审批通过，准备支付' : '审批未通过'),
    });
  }

  // 5. Paid event
  if (topup.paid_at) {
    events.push({
      id: 'paid',
      timestamp: topup.paid_at,
      type: 'status_change',
      status: 'paid',
      actor: '系统',
      icon: CreditCard,
      iconColor: 'text-indigo-500',
      title: '已支付',
      description: topup.payment_reference
        ? `支付凭证: ${topup.payment_reference}`
        : '资金已支付',
    });
  }

  // 6. Completed event
  if (topup.completed_at) {
    events.push({
      id: 'completed',
      timestamp: topup.completed_at,
      type: 'status_change',
      status: 'completed',
      actor: '系统',
      icon: CheckCircle,
      iconColor: 'text-green-500',
      title: '充值完成',
      description: '资金已到账，充值流程完成',
    });
  }

  // 7. Rejected event
  if (topup.rejected_at && topup.status === 'rejected') {
    events.push({
      id: 'rejected',
      timestamp: topup.rejected_at,
      type: 'status_change',
      status: 'rejected',
      actor: topup.rejected_by_name || '审批人',
      notes: topup.rejection_reason,
      icon: XCircle,
      iconColor: 'text-red-500',
      title: '申请被拒绝',
      description: topup.rejection_reason || '审批未通过',
    });
  }

  // 8. Cancelled event
  if (topup.cancelled_at) {
    events.push({
      id: 'cancelled',
      timestamp: topup.cancelled_at,
      type: 'status_change',
      status: 'cancelled',
      actor: topup.cancelled_by ? '申请人' : '系统',
      icon: Ban,
      iconColor: 'text-gray-500',
      title: '申请已取消',
      description: '充值申请已被取消',
    });
  }

  // Sort by timestamp descending (newest first)
  return events.sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

function buildTimelineFromLogs(logs: TopupApprovalLog[]): TimelineEvent[] {
  return logs.map((log) => {
    const actionConfig = ACTION_ICONS[log.action] || { icon: Clock, color: 'text-gray-500' };

    return {
      id: log.id,
      timestamp: log.created_at,
      type: 'action',
      action: log.action,
      actor: log.operator_name,
      actorRole: log.operator_role,
      notes: log.notes,
      icon: actionConfig.icon,
      iconColor: actionConfig.color,
      title: ACTION_LABELS[log.action] || log.action,
      description: log.notes || `${log.from_status} → ${log.to_status}`,
    };
  });
}

// === Timeline Item Component ===

interface TimelineItemProps {
  event: TimelineEvent;
  isFirst: boolean;
  isLast: boolean;
  showDetails: boolean;
}

function TimelineItem({ event, isFirst, isLast, showDetails }: TimelineItemProps) {
  const Icon = event.icon;

  return (
    <div className="relative flex gap-4">
      {/* Connector Line */}
      {!isLast && (
        <div
          className="absolute left-4 top-8 bottom-0 w-0.5 bg-gray-200"
          style={{ transform: 'translateX(-50%)' }}
        />
      )}

      {/* Icon */}
      <div
        className={cn(
          'relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white border-2',
          isFirst ? 'border-gray-300' : 'border-gray-200'
        )}
      >
        <Icon className={cn('h-4 w-4', event.iconColor)} />
      </div>

      {/* Content */}
      <div className={cn('flex-1 pb-6', isLast && 'pb-0')}>
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-sm">{event.title}</h4>
          <span className="text-xs text-muted-foreground">
            {formatTimestamp(event.timestamp)}
          </span>
        </div>

        {showDetails && (
          <>
            <p className="text-sm text-muted-foreground mt-1">{event.description}</p>

            <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
              <User className="h-3 w-3" />
              <span>{event.actor}</span>
              {event.actorRole && (
                <span className="px-1.5 py-0.5 bg-gray-100 rounded">{event.actorRole}</span>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// === Main Component ===

export function TopupApprovalTimeline({
  topup,
  approvalLogs,
  showDetails = true,
  className,
}: TopupApprovalTimelineProps) {
  const events = useMemo(() => {
    // If we have approval logs, use them; otherwise build from topup data
    if (approvalLogs && approvalLogs.length > 0) {
      return buildTimelineFromLogs(approvalLogs);
    }
    return buildTimelineFromTopup(topup);
  }, [topup, approvalLogs]);

  if (events.length === 0) {
    return (
      <div className={cn('text-center py-8 text-muted-foreground', className)}>
        <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p>暂无审批记录</p>
      </div>
    );
  }

  return (
    <div className={cn('space-y-0', className)}>
      {events.map((event, index) => (
        <TimelineItem
          key={event.id}
          event={event}
          isFirst={index === 0}
          isLast={index === events.length - 1}
          showDetails={showDetails}
        />
      ))}
    </div>
  );
}

// === Compact Timeline ===

interface CompactTimelineProps {
  topup: TopupRequest;
  className?: string;
}

export function TopupCompactTimeline({ topup, className }: CompactTimelineProps) {
  const config = TOPUP_STATUS_CONFIG[topup.status];
  const StatusIcon = STATUS_ICONS[topup.status];

  // Key milestones
  const milestones = [
    {
      label: '申请',
      done: true,
      timestamp: topup.requested_at,
    },
    {
      label: '数据复核',
      done: !!topup.data_reviewed_at,
      timestamp: topup.data_reviewed_at,
    },
    {
      label: '财务终审',
      done: !!topup.finance_approved_at,
      timestamp: topup.finance_approved_at,
    },
    {
      label: '支付',
      done: !!topup.paid_at,
      timestamp: topup.paid_at,
    },
    {
      label: '完成',
      done: topup.status === 'completed',
      timestamp: topup.completed_at,
    },
  ];

  const isTerminal = topup.status === 'rejected' || topup.status === 'cancelled';

  return (
    <div className={cn('space-y-3', className)}>
      {/* Current Status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StatusIcon.icon className={cn('h-4 w-4', StatusIcon.color)} />
          <span className="font-medium">{config.label}</span>
        </div>
        <span className="text-sm text-muted-foreground">
          {formatTimestamp(topup.updated_at)}
        </span>
      </div>

      {/* Milestone Progress */}
      {!isTerminal && (
        <div className="flex items-center gap-1">
          {milestones.map((milestone, index) => (
            <div key={milestone.label} className="flex items-center">
              <div
                className={cn(
                  'flex flex-col items-center',
                  milestone.done ? 'opacity-100' : 'opacity-40'
                )}
              >
                <div
                  className={cn(
                    'w-2 h-2 rounded-full',
                    milestone.done ? 'bg-green-500' : 'bg-gray-300'
                  )}
                />
                <span className="text-[10px] mt-1 whitespace-nowrap">{milestone.label}</span>
              </div>
              {index < milestones.length - 1 && (
                <div
                  className={cn(
                    'h-0.5 w-6 mx-1',
                    milestone.done ? 'bg-green-500' : 'bg-gray-200'
                  )}
                />
              )}
            </div>
          ))}
        </div>
      )}

      {/* Terminal Status Message */}
      {isTerminal && (
        <div
          className={cn(
            'text-sm px-3 py-2 rounded',
            topup.status === 'rejected' ? 'bg-red-50 text-red-700' : 'bg-gray-50 text-gray-600'
          )}
        >
          {topup.status === 'rejected'
            ? topup.rejection_reason || '申请已被拒绝'
            : '申请已取消'}
        </div>
      )}
    </div>
  );
}

export default TopupApprovalTimeline;
