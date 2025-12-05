/**
 * Ad Account Types
 *
 * 广告账户模块类型定义
 * Aligned with DATA_SCHEMA.md v5.2 (ad_accounts table)
 */

import type { UUID, ISODateString, Money } from '@/types';

// === Status Enum ===

export type AdAccountStatus = 'active' | 'paused' | 'suspended' | 'closed';

export type AdAccountPlatform = 'meta' | 'google' | 'tiktok' | 'other';

// === Entity Types ===

export interface AdAccount {
  id: UUID;
  account_id: string; // 平台账户 ID
  account_name: string;
  platform: AdAccountPlatform;
  status: AdAccountStatus;

  // 关联项目
  project_id?: UUID;
  project_name?: string;

  // 余额与消耗
  balance: Money;
  spent_total: Money;
  spent_today: Money;
  daily_budget?: Money;

  // 风控信息
  risk_level?: 'low' | 'medium' | 'high';
  last_spend_date?: string;

  // 元数据
  timezone?: string;
  currency?: string;
  created_at: ISODateString;
  updated_at: ISODateString;
}

// === List/Filter Types ===

export interface AdAccountFilters {
  status?: AdAccountStatus | AdAccountStatus[];
  platform?: AdAccountPlatform | AdAccountPlatform[];
  project_id?: UUID;
  risk_level?: 'low' | 'medium' | 'high';
  search?: string;
}

export interface AdAccountListParams extends AdAccountFilters {
  page?: number;
  page_size?: number;
  sort_by?: 'account_name' | 'balance' | 'spent_today' | 'created_at';
  sort_order?: 'asc' | 'desc';
}

// === Summary Types ===

export interface AdAccountSummary {
  total_accounts: number;
  active_accounts: number;
  total_balance: Money;
  total_spent_today: Money;
  high_risk_count: number;
}

// === Status Display Config ===

export const AD_ACCOUNT_STATUS_CONFIG: Record<AdAccountStatus, { label: string; variant: 'default' | 'success' | 'warning' | 'error' | 'info' }> = {
  active: { label: '活跃', variant: 'success' },
  paused: { label: '暂停', variant: 'warning' },
  suspended: { label: '风控中', variant: 'error' },
  closed: { label: '已关闭', variant: 'default' },
};

export const PLATFORM_CONFIG: Record<AdAccountPlatform, { label: string; color: string }> = {
  meta: { label: 'Meta', color: 'text-blue-400' },
  google: { label: 'Google', color: 'text-red-400' },
  tiktok: { label: 'TikTok', color: 'text-cyan-400' },
  other: { label: '其他', color: 'text-text-muted' },
};
