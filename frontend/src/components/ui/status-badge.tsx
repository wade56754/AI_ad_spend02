'use client';

/**
 * 类型安全的状态标签组件
 *
 * SoT 引用:
 * - STATE_MACHINE.md v2.9 §4 (全局状态一览表)
 * - STATE_MACHINE.md v2.9 §4A.1 (Phase 边界说明)
 *
 * @module components/ui/status-badge
 */

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  DAILY_REPORT_STATUS_CONFIG,
  ACCOUNT_STATUS_CONFIG,
  TOPUP_STATUS_CONFIG,
  PROJECT_STATUS_CONFIG,
  CHANNEL_STATUS_CONFIG,
  type StatusConfig,
} from '@/lib/constants/status-config';
import type {
  DailyReportStatus,
  AccountStatus,
  TopupStatus,
  ProjectStatus,
  ChannelStatus,
} from '@/types/status';

// ═══════════════════════════════════════════════════════════════════════════
// 类型定义
// ═══════════════════════════════════════════════════════════════════════════

/** 支持的状态类型 */
export type StatusType =
  | 'daily_report'
  | 'account'
  | 'topup'
  | 'project'
  | 'channel';

/** 状态值映射 */
type StatusValueMap = {
  daily_report: DailyReportStatus;
  account: AccountStatus;
  topup: TopupStatus;
  project: ProjectStatus;
  channel: ChannelStatus;
};

/** StatusBadge Props */
export interface TypedStatusBadgeProps<T extends StatusType> {
  /** 状态类型 */
  type: T;
  /** 状态值 */
  status: StatusValueMap[T];
  /** 尺寸 */
  size?: 'sm' | 'md' | 'lg';
  /** 是否显示圆点 */
  dot?: boolean;
  /** 自定义类名 */
  className?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// 配置映射
// ═══════════════════════════════════════════════════════════════════════════

const STATUS_CONFIG_MAP: Record<StatusType, Record<string, StatusConfig>> = {
  daily_report: DAILY_REPORT_STATUS_CONFIG,
  account: ACCOUNT_STATUS_CONFIG,
  topup: TOPUP_STATUS_CONFIG,
  project: PROJECT_STATUS_CONFIG,
  channel: CHANNEL_STATUS_CONFIG,
};

// 变体样式映射
const VARIANT_CLASSES = {
  default: 'bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700',
  success: 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900/50 dark:text-green-200 dark:border-green-800',
  warning: 'bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/50 dark:text-amber-200 dark:border-amber-800',
  error: 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/50 dark:text-red-200 dark:border-red-800',
  info: 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/50 dark:text-blue-200 dark:border-blue-800',
} as const;

// 圆点样式映射
const DOT_CLASSES = {
  default: 'bg-gray-500',
  success: 'bg-green-500',
  warning: 'bg-amber-500',
  error: 'bg-red-500',
  info: 'bg-blue-500',
} as const;

// 尺寸样式
const SIZE_CLASSES = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-0.5',
  lg: 'text-base px-3 py-1',
} as const;

const DOT_SIZE_CLASSES = {
  sm: 'w-1.5 h-1.5',
  md: 'w-2 h-2',
  lg: 'w-2.5 h-2.5',
} as const;

// ═══════════════════════════════════════════════════════════════════════════
// 组件实现
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 类型安全的状态标签组件
 *
 * @example
 * ```tsx
 * // 日报状态
 * <TypedStatusBadge type="daily_report" status="trend_ok" />
 *
 * // 账户状态
 * <TypedStatusBadge type="account" status="active" size="sm" />
 *
 * // 充值状态（带圆点）
 * <TypedStatusBadge type="topup" status="pending_review" dot />
 * ```
 */
export function TypedStatusBadge<T extends StatusType>({
  type,
  status,
  size = 'md',
  dot = false,
  className,
}: TypedStatusBadgeProps<T>) {
  // 获取状态配置
  const configMap = STATUS_CONFIG_MAP[type];
  const config = configMap?.[status as string];

  // 未找到配置时显示默认样式
  if (!config) {
    return (
      <Badge
        variant="outline"
        className={cn(
          VARIANT_CLASSES.default,
          SIZE_CLASSES[size],
          'inline-flex items-center gap-1.5 font-medium border rounded-full',
          className
        )}
      >
        {dot && (
          <span
            className={cn(DOT_CLASSES.default, DOT_SIZE_CLASSES[size], 'rounded-full')}
            aria-hidden="true"
          />
        )}
        未知状态
      </Badge>
    );
  }

  const variantClass = VARIANT_CLASSES[config.variant] || VARIANT_CLASSES.default;
  const dotClass = DOT_CLASSES[config.variant] || DOT_CLASSES.default;

  return (
    <Badge
      variant="outline"
      className={cn(
        variantClass,
        SIZE_CLASSES[size],
        'inline-flex items-center gap-1.5 font-medium border rounded-full',
        className
      )}
      title={config.description}
    >
      {dot && (
        <span
          className={cn(dotClass, DOT_SIZE_CLASSES[size], 'rounded-full flex-shrink-0')}
          aria-hidden="true"
        />
      )}
      {config.label}
    </Badge>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// 便捷组件
// ═══════════════════════════════════════════════════════════════════════════

/** 日报状态标签 */
export function DailyReportStatusBadge({
  status,
  ...props
}: Omit<TypedStatusBadgeProps<'daily_report'>, 'type'>) {
  return <TypedStatusBadge type="daily_report" status={status} {...props} />;
}

/** 账户状态标签 */
export function AccountStatusBadge({
  status,
  ...props
}: Omit<TypedStatusBadgeProps<'account'>, 'type'>) {
  return <TypedStatusBadge type="account" status={status} {...props} />;
}

/** 充值状态标签 */
export function TopupStatusBadge({
  status,
  ...props
}: Omit<TypedStatusBadgeProps<'topup'>, 'type'>) {
  return <TypedStatusBadge type="topup" status={status} {...props} />;
}

/** 项目状态标签 */
export function ProjectStatusBadge({
  status,
  ...props
}: Omit<TypedStatusBadgeProps<'project'>, 'type'>) {
  return <TypedStatusBadge type="project" status={status} {...props} />;
}

/** 渠道状态标签 */
export function ChannelStatusBadge({
  status,
  ...props
}: Omit<TypedStatusBadgeProps<'channel'>, 'type'>) {
  return <TypedStatusBadge type="channel" status={status} {...props} />;
}

// 默认导出
export default TypedStatusBadge;
