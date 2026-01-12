/**
 * 状态变体配置 - StatusBadge 颜色变体
 *
 * TASK-FE-COMMON-003: 状态配置与 StatusBadge
 *
 * SoT 引用:
 * - STATE_MACHINE.md v2.9 §4 (全局状态一览表)
 * - FRONTEND_PAGE_DESIGN_v2.1.md §7.2 (StatusBadge 配置)
 */

import type { StatusVariant } from '@/types/common';

// === 变体颜色映射 ===

export const STATUS_VARIANT_COLORS: Record<StatusVariant, {
  bg: string;
  text: string;
  border: string;
  dot: string;
}> = {
  default: {
    bg: 'bg-gray-100 dark:bg-gray-800',
    text: 'text-gray-700 dark:text-gray-300',
    border: 'border-gray-200 dark:border-gray-700',
    dot: 'bg-gray-500',
  },
  success: {
    bg: 'bg-green-100 dark:bg-green-900/30',
    text: 'text-green-700 dark:text-green-400',
    border: 'border-green-200 dark:border-green-800',
    dot: 'bg-green-500',
  },
  warning: {
    bg: 'bg-yellow-100 dark:bg-yellow-900/30',
    text: 'text-yellow-700 dark:text-yellow-400',
    border: 'border-yellow-200 dark:border-yellow-800',
    dot: 'bg-yellow-500',
  },
  error: {
    bg: 'bg-red-100 dark:bg-red-900/30',
    text: 'text-red-700 dark:text-red-400',
    border: 'border-red-200 dark:border-red-800',
    dot: 'bg-red-500',
  },
  info: {
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    text: 'text-blue-700 dark:text-blue-400',
    border: 'border-blue-200 dark:border-blue-800',
    dot: 'bg-blue-500',
  },
};

// === 变体标签 ===

export const STATUS_VARIANT_LABELS: Record<StatusVariant, string> = {
  default: '默认',
  success: '成功',
  warning: '警告',
  error: '错误',
  info: '信息',
};

// === 获取变体样式 ===

export function getVariantClasses(variant: StatusVariant): string {
  const colors = STATUS_VARIANT_COLORS[variant];
  return `${colors.bg} ${colors.text}`;
}

// === 状态到变体的快速映射 ===

/**
 * 通用状态值到变体的映射
 * 用于快速获取常见状态的颜色
 */
export const COMMON_STATUS_VARIANTS: Record<string, StatusVariant> = {
  // 成功类
  success: 'success',
  completed: 'success',
  active: 'success',
  approved: 'success',
  confirmed: 'success',
  final_confirmed: 'success',
  trend_ok: 'success',

  // 警告类
  warning: 'warning',
  pending: 'warning',
  pending_review: 'warning',
  finance_approve: 'warning',
  paid: 'warning',
  suspended: 'warning',
  testing: 'warning',

  // 错误类
  error: 'error',
  failed: 'error',
  rejected: 'error',
  dead: 'error',

  // 信息类
  info: 'info',
  new: 'info',
  raw_submitted: 'info',

  // 默认类
  default: 'default',
  draft: 'default',
  cancelled: 'default',
  archived: 'default',
  inactive: 'default',
};

/**
 * 根据状态值获取变体
 */
export function getVariantFromStatus(status: string): StatusVariant {
  return COMMON_STATUS_VARIANTS[status] || 'default';
}
