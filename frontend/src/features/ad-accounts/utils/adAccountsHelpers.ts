/**
 * Ad Accounts Helper Functions
 *
 * 从 AdAccountsPageV2.tsx 提取的辅助函数
 */

import type { AdAccountStatus } from '../types/adAccount.types';

// 格式化货币
export const formatCurrency = (value: number): string => {
  if (value >= 10000) {
    return `$${(value / 1000).toFixed(1)}k`;
  }
  return `$${value.toFixed(2)}`;
};

// 格式化百分比
export const formatPercent = (value: number): string => {
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
};

// 状态配置
export interface StatusConfig {
  label: string;
  color: string;
  textColor: string;
  bgColor: string;
}

export const getStatusConfig = (status: AdAccountStatus | string): StatusConfig => {
  const configs: Record<string, StatusConfig> = {
    active: { label: '投放中', color: 'bg-green-500', textColor: 'text-green-700', bgColor: 'bg-green-50' },
    testing: { label: '测试中', color: 'bg-blue-500', textColor: 'text-blue-700', bgColor: 'bg-blue-50' },
    suspended: { label: '已暂停', color: 'bg-yellow-500', textColor: 'text-yellow-700', bgColor: 'bg-yellow-50' },
    dead: { label: '死号', color: 'bg-red-500', textColor: 'text-red-700', bgColor: 'bg-red-50' },
    new: { label: '新建', color: 'bg-gray-400', textColor: 'text-gray-700', bgColor: 'bg-gray-50' },
    archived: { label: '已归档', color: 'bg-gray-300', textColor: 'text-gray-600', bgColor: 'bg-gray-50' },
  };
  return configs[status] || configs.new;
};

// 平台配置
export interface PlatformConfig {
  label: string;
  color: string;
}

export const getPlatformConfig = (platform: 'FB' | 'TK' | string): PlatformConfig => {
  const configs: Record<string, PlatformConfig> = {
    FB: { label: 'Facebook', color: 'bg-blue-600' },
    TK: { label: 'TikTok', color: 'bg-black' },
  };
  return configs[platform] || { label: platform, color: 'bg-gray-500' };
};

// V2 专用的临时账户类型 (用于 V2 页面内部)
export interface AdAccountV2Display {
  id: number;
  name: string;
  platformId: string;
  accountType: string;
  platform: 'FB' | 'TK';
  supplier: string;
  buyer: string;
  region: string;
  status: 'active' | 'testing' | 'suspended' | 'dead' | 'new';
  todaySpend: number;
  yesterdaySpend: number;
  monthSpend: number;
  feeRate: number;
  lastUpdated: string;
  trend: number;
}

// 提取唯一筛选值
export const extractUniqueValues = (accounts: AdAccountV2Display[]) => ({
  buyers: [...new Set(accounts.map(a => a.buyer))],
  suppliers: [...new Set(accounts.map(a => a.supplier))],
  accountTypes: [...new Set(accounts.map(a => a.accountType))],
  regions: [...new Set(accounts.map(a => a.region))],
});
