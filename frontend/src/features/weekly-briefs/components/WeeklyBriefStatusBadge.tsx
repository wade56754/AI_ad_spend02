/**
 * Weekly Brief Status Badge Component
 *
 * SoT: B3-weekly-brief.md §3.4
 */

'use client';

import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { FileText, CheckCircle, type LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { WeeklyBriefStatus } from '../types';

/**
 * Status configuration
 * SoT: B3-weekly-brief.md §3.4
 */
export const WEEKLY_BRIEF_STATUS_CONFIG: Record<
  WeeklyBriefStatus,
  {
    label: string;
    icon: LucideIcon;
    variant: 'default' | 'success' | 'outline';
    bgColor: string;
    textColor: string;
    description: string;
  }
> = {
  draft: {
    label: '草稿',
    icon: FileText,
    variant: 'outline',
    bgColor: 'bg-gray-100',
    textColor: 'text-gray-600',
    description: '草稿状态，可继续编辑',
  },
  submitted: {
    label: '已提交',
    icon: CheckCircle,
    variant: 'success',
    bgColor: 'bg-green-100',
    textColor: 'text-green-700',
    description: '已提交，不可修改',
  },
};

interface WeeklyBriefStatusBadgeProps {
  status: WeeklyBriefStatus;
  showIcon?: boolean;
  showTooltip?: boolean;
  size?: 'sm' | 'default' | 'lg';
  className?: string;
}

export function WeeklyBriefStatusBadge({
  status,
  showIcon = true,
  showTooltip = true,
  size = 'default',
  className,
}: WeeklyBriefStatusBadgeProps) {
  const config = WEEKLY_BRIEF_STATUS_CONFIG[status];

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

export default WeeklyBriefStatusBadge;
