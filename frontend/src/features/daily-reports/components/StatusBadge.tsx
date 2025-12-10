/**
 * Daily Report Status Badge Component
 *
 * Displays the current status of a daily report with appropriate styling
 * SoT: STATE_MACHINE.md v2.6 § 8 (8-state machine)
 */

'use client';

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  Clock,
  CheckCircle,
  AlertTriangle,
  Lock,
  Send,
  FileCheck,
  AlertCircle,
  ShieldCheck,
} from 'lucide-react';
import type { DailyReportStatus } from '../types';
import { STATUS_CONFIG } from '../types';

interface StatusBadgeProps {
  status: DailyReportStatus;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  className?: string;
}

/**
 * Icon mapping for each status
 */
const STATUS_ICONS: Record<DailyReportStatus, React.ComponentType<{ className?: string }>> = {
  raw_submitted: Send,
  trend_pending: Clock,
  trend_ok: CheckCircle,
  trend_flagged: AlertTriangle,
  trend_resolved: ShieldCheck,
  final_pending: FileCheck,
  final_confirmed: CheckCircle,
  final_locked: Lock,
};

/**
 * Color mapping for each status variant
 */
const VARIANT_STYLES: Record<string, string> = {
  default: 'bg-gray-100 text-gray-800 border-gray-200',
  success: 'bg-green-100 text-green-800 border-green-200',
  warning: 'bg-amber-100 text-amber-800 border-amber-200',
  error: 'bg-red-100 text-red-800 border-red-200',
  info: 'bg-blue-100 text-blue-800 border-blue-200',
};

/**
 * Size styles
 */
const SIZE_STYLES = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-1',
  lg: 'text-base px-3 py-1.5',
};

const ICON_SIZES = {
  sm: 'h-3 w-3',
  md: 'h-4 w-4',
  lg: 'h-5 w-5',
};

export function StatusBadge({
  status,
  size = 'md',
  showIcon = true,
  className,
}: StatusBadgeProps) {
  const config = STATUS_CONFIG[status];
  const Icon = STATUS_ICONS[status];

  return (
    <Badge
      variant="outline"
      className={cn(
        'font-medium border inline-flex items-center gap-1.5',
        VARIANT_STYLES[config.variant],
        SIZE_STYLES[size],
        className
      )}
    >
      {showIcon && Icon && <Icon className={ICON_SIZES[size]} />}
      <span>{config.label}</span>
    </Badge>
  );
}

/**
 * Status Progress indicator showing current position in workflow
 */
interface StatusProgressProps {
  status: DailyReportStatus;
  className?: string;
}

const STATUS_ORDER: DailyReportStatus[] = [
  'raw_submitted',
  'trend_pending',
  'trend_ok',
  'final_pending',
  'final_confirmed',
  'final_locked',
];

// Alternative path for flagged reports
const FLAGGED_PATH: DailyReportStatus[] = [
  'raw_submitted',
  'trend_pending',
  'trend_flagged',
  'trend_resolved',
  'final_pending',
  'final_confirmed',
  'final_locked',
];

export function StatusProgress({ status, className }: StatusProgressProps) {
  const isFlaggedPath = status === 'trend_flagged' || status === 'trend_resolved';
  const statusPath = isFlaggedPath ? FLAGGED_PATH : STATUS_ORDER;
  const currentIndex = statusPath.indexOf(status);

  return (
    <div className={cn('flex items-center gap-1', className)}>
      {statusPath.map((s, index) => {
        const isCompleted = index < currentIndex;
        const isCurrent = index === currentIndex;
        const config = STATUS_CONFIG[s];

        return (
          <div key={s} className="flex items-center">
            <div
              className={cn(
                'w-2 h-2 rounded-full transition-colors',
                isCompleted && 'bg-green-500',
                isCurrent && VARIANT_STYLES[config.variant].includes('green')
                  ? 'bg-green-500'
                  : isCurrent && VARIANT_STYLES[config.variant].includes('amber')
                  ? 'bg-amber-500'
                  : isCurrent && VARIANT_STYLES[config.variant].includes('blue')
                  ? 'bg-blue-500'
                  : isCurrent
                  ? 'bg-gray-500'
                  : 'bg-gray-200'
              )}
              title={config.label}
            />
            {index < statusPath.length - 1 && (
              <div
                className={cn(
                  'w-4 h-0.5',
                  isCompleted ? 'bg-green-500' : 'bg-gray-200'
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

/**
 * Status Legend component for displaying all possible statuses
 */
export function StatusLegend() {
  const allStatuses: DailyReportStatus[] = [
    'raw_submitted',
    'trend_pending',
    'trend_ok',
    'trend_flagged',
    'trend_resolved',
    'final_pending',
    'final_confirmed',
    'final_locked',
  ];

  return (
    <div className="flex flex-wrap gap-2">
      {allStatuses.map((status) => (
        <StatusBadge key={status} status={status} size="sm" />
      ))}
    </div>
  );
}

export default StatusBadge;
