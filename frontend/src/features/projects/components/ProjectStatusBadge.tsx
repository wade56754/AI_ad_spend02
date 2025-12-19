/**
 * Project Status Badge Component
 *
 * Visual status indicator for 4-state project workflow
 * SoT: STATE_MACHINE.md v2.6 Section 5
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
  Play,
  Pause,
  CheckCircle,
  XCircle,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ProjectStatus } from '../types';

/**
 * Status configuration with icons, colors, and descriptions
 * (Component-specific version with icons)
 */
const PROJECT_STATUS_BADGE_CONFIG: Record<ProjectStatus, {
  label: string;
  icon: LucideIcon;
  variant: 'default' | 'success' | 'warning' | 'destructive' | 'outline';
  bgColor: string;
  textColor: string;
  description: string;
}> = {
  active: {
    label: '进行中',
    icon: Play,
    variant: 'success',
    bgColor: 'bg-green-50',
    textColor: 'text-green-700',
    description: '项目正在进行中，广告投放活跃',
  },
  paused: {
    label: '已暂停',
    icon: Pause,
    variant: 'warning',
    bgColor: 'bg-amber-50',
    textColor: 'text-amber-700',
    description: '项目已暂停，等待恢复',
  },
  completed: {
    label: '已完成',
    icon: CheckCircle,
    variant: 'default',
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-700',
    description: '项目已完成，所有投放任务结束',
  },
  cancelled: {
    label: '已取消',
    icon: XCircle,
    variant: 'destructive',
    bgColor: 'bg-red-50',
    textColor: 'text-red-700',
    description: '项目已取消',
  },
};

// === ProjectStatusBadge Component ===

interface ProjectStatusBadgeProps {
  status: ProjectStatus;
  showIcon?: boolean;
  showTooltip?: boolean;
  size?: 'sm' | 'default' | 'lg';
  className?: string;
}

export function ProjectStatusBadge({
  status,
  showIcon = true,
  showTooltip = true,
  size = 'default',
  className,
}: ProjectStatusBadgeProps) {
  const config = PROJECT_STATUS_BADGE_CONFIG[status];

  if (!config) {
    return <Badge variant="outline">未知状态</Badge>;
  }

  const Icon = config.icon;

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
      variant={config.variant}
      className={cn(
        'inline-flex items-center gap-1 font-medium',
        config.bgColor,
        config.textColor,
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

// === Budget Progress Component ===

interface BudgetProgressProps {
  budget: number;
  spent: number;
  currency?: string;
  showAmount?: boolean;
  size?: 'sm' | 'default' | 'lg';
  className?: string;
}

export function BudgetProgress({
  budget,
  spent,
  currency = 'CNY',
  showAmount = true,
  size = 'default',
  className,
}: BudgetProgressProps) {
  const percent = budget > 0 ? Math.min((spent / budget) * 100, 100) : 0;

  // Determine color based on usage percentage
  const getColorClass = () => {
    if (percent >= 90) return 'bg-red-500';
    if (percent >= 75) return 'bg-amber-500';
    if (percent >= 50) return 'bg-blue-500';
    return 'bg-green-500';
  };

  const formatAmount = (amount: number) => {
    if (currency === 'CNY') {
      if (amount >= 10000) {
        return `¥${(amount / 10000).toFixed(1)}万`;
      }
      return `¥${amount.toLocaleString()}`;
    }
    return `${currency} ${amount.toLocaleString()}`;
  };

  const sizeStyles = {
    sm: { bar: 'h-1.5', text: 'text-xs' },
    default: { bar: 'h-2', text: 'text-sm' },
    lg: { bar: 'h-3', text: 'text-base' },
  };

  return (
    <div className={cn('space-y-1', className)}>
      {showAmount && (
        <div className={cn('flex justify-between', sizeStyles[size].text)}>
          <span className="text-muted-foreground">
            已消耗: {formatAmount(spent)}
          </span>
          <span className="font-medium">
            {percent.toFixed(0)}%
          </span>
        </div>
      )}
      <div className={cn('w-full bg-gray-200 rounded-full overflow-hidden', sizeStyles[size].bar)}>
        <div
          className={cn('h-full rounded-full transition-all duration-300', getColorClass())}
          style={{ width: `${percent}%` }}
        />
      </div>
      {showAmount && (
        <div className={cn('text-muted-foreground', sizeStyles[size].text)}>
          预算: {formatAmount(budget)}
        </div>
      )}
    </div>
  );
}

// === Project Stats Card ===

interface ProjectStatsCardProps {
  title: string;
  value: number | string;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  variant?: 'default' | 'success' | 'warning' | 'error';
  onClick?: () => void;
  className?: string;
}

export function ProjectStatsCard({
  title,
  value,
  icon: Icon,
  trend,
  variant = 'default',
  onClick,
  className,
}: ProjectStatsCardProps) {
  const variantStyles = {
    default: 'bg-gray-50 text-gray-700',
    success: 'bg-green-50 text-green-700',
    warning: 'bg-amber-50 text-amber-700',
    error: 'bg-red-50 text-red-700',
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
            <p className={cn(
              'text-xs mt-1',
              trend.isPositive ? 'text-green-600' : 'text-red-600'
            )}>
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

export function ProjectStatusLegend() {
  return (
    <div className="flex flex-wrap gap-4">
      {(Object.entries(PROJECT_STATUS_BADGE_CONFIG) as [ProjectStatus, typeof PROJECT_STATUS_BADGE_CONFIG[ProjectStatus]][]).map(
        ([status, config]) => {
          const Icon = config.icon;
          return (
            <div key={status} className="flex items-center gap-2 text-sm">
              <div className={cn('p-1 rounded', config.bgColor)}>
                <Icon className={cn('h-3 w-3', config.textColor)} />
              </div>
              <span className="text-muted-foreground">{config.label}</span>
            </div>
          );
        }
      )}
    </div>
  );
}

export default ProjectStatusBadge;
