/**
 * Channel Types - 渠道类型定义
 *
 * SoT 对齐:
 * - DATA_SCHEMA.md v5.2 (channels entity)
 * - backend/schemas/__init__.py (ChannelRead/ChannelCreate/ChannelUpdate)
 */

// ========== 枚举 ==========

export enum ChannelStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
}

export enum ServiceFeeType {
  PERCENT = 'percent',
  FIXED = 'fixed',
}

// ========== 基础接口 ==========

/**
 * Channel entity - 对齐 backend ChannelRead schema
 */
export interface Channel {
  id: string; // UUID
  name: string;
  service_fee_type: ServiceFeeType | string;
  service_fee_value: number;
  is_active: boolean;
  created_by: string | null;
  updated_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChannelPerformance {
  id: string;
  channel_id: string;
  stat_date: string;
  total_accounts: number;
  active_accounts: number;
  dead_accounts: number;
  total_spend: number;
  avg_account_lifespan: number | null;
  death_rate: number | null;
  created_at: string;
}

// ========== 请求接口 ==========

/**
 * Create input - 对齐 backend ChannelCreate schema
 */
export interface ChannelCreateInput {
  name: string;
  service_fee_type?: string;
  service_fee_value?: number;
  is_active?: boolean;
  created_by?: string;
  updated_by?: string;
}

/**
 * Update input - 对齐 backend ChannelUpdate schema
 */
export interface ChannelUpdateInput {
  name?: string;
  service_fee_type?: string;
  service_fee_value?: number;
  is_active?: boolean;
  created_by?: string;
  updated_by?: string;
}

export interface ChannelListParams {
  page?: number;
  page_size?: number;
  is_active?: boolean;
  search?: string;
}

// ========== 响应接口 ==========

export interface ChannelListResponse {
  data: Channel[];
  meta: {
    pagination: {
      page: number;
      page_size: number;
      total: number;
      total_pages: number;
    };
  };
}

// ========== UI 配置 ==========

export const CHANNEL_STATUS_CONFIG: Record<ChannelStatus, {
  label: string;
  color: 'default' | 'success' | 'warning' | 'error';
  description: string;
}> = {
  [ChannelStatus.ACTIVE]: {
    label: '活跃',
    color: 'success',
    description: '渠道正常运营中',
  },
  [ChannelStatus.INACTIVE]: {
    label: '停用',
    color: 'default',
    description: '渠道已停用',
  },
};

export const SERVICE_FEE_TYPE_CONFIG: Record<ServiceFeeType, {
  label: string;
  suffix: string;
}> = {
  [ServiceFeeType.PERCENT]: {
    label: '百分比',
    suffix: '%',
  },
  [ServiceFeeType.FIXED]: {
    label: '固定金额',
    suffix: '',
  },
};

// 常见渠道预设
export const COMMON_CHANNELS = [
  { code: 'FACEBOOK', name: 'Facebook Ads', icon: 'facebook' },
  { code: 'GOOGLE', name: 'Google Ads', icon: 'google' },
  { code: 'TIKTOK', name: 'TikTok Ads', icon: 'tiktok' },
  { code: 'TWITTER', name: 'Twitter/X Ads', icon: 'twitter' },
  { code: 'SNAPCHAT', name: 'Snapchat Ads', icon: 'snapchat' },
  { code: 'PINTEREST', name: 'Pinterest Ads', icon: 'pinterest' },
  { code: 'LINKEDIN', name: 'LinkedIn Ads', icon: 'linkedin' },
  { code: 'BING', name: 'Bing Ads', icon: 'bing' },
];
