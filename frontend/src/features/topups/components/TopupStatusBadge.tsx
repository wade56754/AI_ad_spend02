/**
 * Topup Status Badge Component
 *
 * Visual status indicator for 7-state topup workflow with progress tracking
 * SoT: STATE_MACHINE.md v2.6 Section 9
 */

'use client';

import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  FileEdit,
  ClipboardCheck,
  Wallet,
  CreditCard,
  CheckCircle,
  XCircle,
  Ban,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { TopupStatus } from '../types';
import { TOPUP_STATUS_CONFIG } from '../types';

/**
 * Extended status configuration with icons
 */
const STATUS_ICONS: Record<TopupStatus, LucideIcon> = {
  draft: FileEdit,
  pending_review: ClipboardCheck,
  finance_approve: Wallet,
  paid: CreditCard,
  completed: CheckCircle,
  rejected: XCircle,
  cancelled: Ban,
};

const STATUS_COLORS: Record<TopupStatus, { bg: string; text: string; border: string }> = {
  draft: { bg: 'bg-gray-50', text: 'text-gray-700', border: 'border-gray-200' },
  pending_review: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' },
  finance_approve: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  paid: { bg: 'bg-indigo-50', text: 'text-indigo-700', border: 'border-indigo-200' },
  completed: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
  rejected: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  cancelled: { bg: 'bg-gray-50', text: 'text-gray-500', border: 'border-gray-200' },
};

// === TopupStatusBadge Component ===

interface TopupStatusBadgeProps {
  status: TopupStatus;
  showIcon?: boolean;
  showTooltip?: boolean;
  size?: 'sm' | 'default' | 'lg';
  className?: string;
}

export function TopupStatusBadge({
  status,
  showIcon = true,
  showTooltip = true,
  size = 'default',
  className,
}: TopupStatusBadgeProps) {
  const config = TOPUP_STATUS_CONFIG[status];
  const colors = STATUS_COLORS[status];
  const Icon = STATUS_ICONS[status];

  if (!config) {
    return <Badge variant="outline">未知状态</Badge>;
  }

  const sizeStyles = {
    sm: 'text-xs px-1.5 py-0.5',
    default: 'text-sm px-2 py-1',
    lg: 'text-base px-3 py-1.5',
  };

  const iconSizes = {
    sm: 'h-3 w-3',
    default: 'h-4 w-4',
    lg: 'h-5 w-5',
  };

  const badge = (
    <Badge
      variant="outline"
      className={cn(
        'inline-flex items-center gap-1 font-medium border',
        colors.bg,
        colors.text,
        colors.border,
        sizeStyles[size],
        className
      )}
    >
      {showIcon && <Icon className={iconSizes[size]} />}
      {config.label}
    </Badge>
  );

  if (!showTooltip) {
    return badge;
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>{badge}</TooltipTrigger>
        <TooltipContent>
          <p>{config.description}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

// === Topup Progress Indicator ===

interface TopupProgressProps {
  status: TopupStatus;
  showLabels?: boolean;
  size?: 'sm' | 'default';
  className?: string;
}

const PROGRESS_STEPS = [
  { status: 'draft' as TopupStatus, label: '草稿' },
  { status: 'pending_review' as TopupStatus, label: '数据复核' },
  { status: 'finance_approve' as TopupStatus, label: '财务终审' },
  { status: 'paid' as TopupStatus, label: '已支付' },
  { status: 'completed' as TopupStatus, label: '已完成' },
];

export function TopupProgress({
  status,
  showLabels = true,
  size = 'default',
  className,
}: TopupProgressProps) {
  const config = TOPUP_STATUS_CONFIG[status];
  const currentStep = config?.step ?? 0;
  const isTerminal = status === 'rejected' || status === 'cancelled';

  if (isTerminal) {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        <TopupStatusBadge status={status} />
        <span className="text-sm text-muted-foreground">
          {status === 'rejected' ? '审批流程已终止' : '申请已取消'}
        </span>
      </div>
    );
  }

  const stepSize = size === 'sm' ? 'h-2 w-2' : 'h-3 w-3';
  const lineHeight = size === 'sm' ? 'h-0.5' : 'h-1';

  return (
    <div className={cn('flex items-center', className)}>
      {PROGRESS_STEPS.map((step, index) => {
        const isCompleted = currentStep > step.status === status ? index + 1 : index;
        const isCurrent = TOPUP_STATUS_CONFIG[step.status]?.step === currentStep;
        const isPast = (TOPUP_STATUS_CONFIG[step.status]?.step ?? 0) < currentStep;

        return (
          <div key={step.status} className="flex items-center">
            {/* Step indicator */}
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  'rounded-full transition-all',
                  stepSize,
                  isCurrent
                    ? 'bg-blue-500 ring-4 ring-blue-100'
                    : isPast
                    ? 'bg-green-500'
                    : 'bg-gray-300'
                )}
              />
              {showLabels && (
                <span
                  className={cn(
                    'text-xs mt-1 whitespace-nowrap',
                    isCurrent
                      ? 'text-blue-600 font-medium'
                      : isPast
                      ? 'text-green-600'
                      : 'text-gray-400'
                  )}
                >
                  {step.label}
                </span>
              )}
            </div>
            {/* Connector line */}
            {index < PROGRESS_STEPS.length - 1 && (
              <div
                className={cn(
                  'flex-1 min-w-[20px] mx-1',
                  lineHeight,
                  isPast ? 'bg-green-500' : 'bg-gray-200'
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

// === Topup Stats Card ===

interface TopupStatsCardProps {
  title: string;
  value: number | string;
  icon: LucideIcon;
  trend?: { value: number; isPositive: boolean };
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  onClick?: () => void;
  className?: string;
}

export function TopupStatsCard({
  title,
  value,
  icon: Icon,
  trend,
  variant = 'default',
  onClick,
  className,
}: TopupStatsCardProps) {
  const variantStyles = {
    default: 'bg-gray-50 text-gray-700',
    success: 'bg-green-50 text-green-700',
    warning: 'bg-amber-50 text-amber-700',
    error: 'bg-red-50 text-red-700',
    info: 'bg-blue-50 text-blue-700',
  };

  return (
    <div
      className={cn(
        'rounded-lg border bg-card p-4 transition-all',
        onClick && 'cursor-pointer hover:shadow-md hover:ring-2 hover:ring-primary/20',
        className
      )}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold mt-1">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
          {trend && (
            <p
              className={cn(
                'text-xs mt-1',
                trend.isPositive ? 'text-green-600' : 'text-red-600'
              )}
            >
              {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
            </p>
          )}
        </div>
        <div className={cn('p-3 rounded-full', variantStyles[variant])}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}

// === Status Legend ===

export function TopupStatusLegend() {
  return (
    <div className="flex flex-wrap gap-4">
      {(Object.entries(TOPUP_STATUS_CONFIG) as [TopupStatus, typeof TOPUP_STATUS_CONFIG[TopupStatus]][]).map(
        ([status, config]) => {
          const Icon = STATUS_ICONS[status];
          const colors = STATUS_COLORS[status];
          return (
            <div key={status} className="flex items-center gap-2 text-sm">
              <div className={cn('p-1 rounded', colors.bg)}>
                <Icon className={cn('h-3 w-3', colors.text)} />
              </div>
              <span className="text-muted-foreground">{config.label}</span>
            </div>
          );
        }
      )}
    </div>
  );
}

// === Amount Display ===

interface TopupAmountProps {
  amount: number;
  currency?: string;
  size?: 'sm' | 'default' | 'lg';
  showSign?: boolean;
  className?: string;
}

export function TopupAmount({
  amount,
  currency = 'CNY',
  size = 'default',
  showSign = false,
  className,
}: TopupAmountProps) {
  // Amount is stored in cents
  const displayAmount = amount / 100;

  const formatAmount = () => {
    if (currency === 'CNY') {
      if (displayAmount >= 10000) {
        return `¥${(displayAmount / 10000).toFixed(2)}万`;
      }
      return `¥${displayAmount.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}`;
    }
    return `${currency} ${displayAmount.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
  };

  const sizeStyles = {
    sm: 'text-sm',
    default: 'text-base',
    lg: 'text-xl font-bold',
  };

  return (
    <span className={cn(sizeStyles[size], showSign && 'text-green-600', className)}>
      {showSign && '+'}{formatAmount()}
    </span>
  );
}

export default TopupStatusBadge;
