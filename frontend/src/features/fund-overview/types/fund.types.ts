/**
 * Fund Overview Types - 资金总览类型定义
 *
 * SoT 对齐:
 * - MASTER.md v4.4 §4.5.5: 资金口径定义
 * - MASTER.md v4.4 §6.5: 页面 2 资金总览字段集
 * - A2-fund-overview.md: 模块规格书
 *
 * @module features/fund-overview/types
 */

// ========== 核心资金指标 ==========

/**
 * 资金概览数据
 * SoT: MASTER.md §6.5 页面 2 必须字段
 */
export interface FundOverview {
  /** 累计充值 - topup_record SUM(amount WHERE status='completed') */
  total_topup: number;
  /** 累计消耗 - ad_spend_daily SUM(spend) */
  total_spend: number;
  /** 当前余额 - 累计充值 - 累计消耗 */
  current_balance: number;
  /** 应收款 - SUM(conversions × unit_price) - 累计回款 */
  total_receivable: number;
  /** 累计回款 - receivable SUM(amount WHERE status='received') */
  total_received: number;
  /** 资金占用 - 累计充值 - 累计回款 */
  fund_occupied: number;
  /** 充值变化率 (环比) */
  topup_change: number | null;
  /** 消耗变化率 (环比) */
  spend_change: number | null;
  /** 余额变化率 (环比) */
  balance_change: number | null;
  /** 资金占用率 - 资金占用 / 累计充值 × 100% */
  occupy_rate: number;
  /** 待收款笔数 */
  pending_receivable_count: number;
}

// ========== 资金分布 ==========

/**
 * 按项目的资金分布
 */
export interface FundByProjectItem {
  project_id: number;
  project_name: string;
  owner_id: number;
  owner_name: string;
  total_topup: number;
  total_spend: number;
  balance: number;
  receivable: number;
  received: number;
}

/**
 * 按渠道的资金分布
 */
export interface FundByChannelItem {
  channel_id: number;
  channel_name: string;
  total_accounts: number;
  total_topup: number;
  total_spend: number;
  balance: number;
}

// ========== 应收/回款 ==========

/**
 * 应收款明细
 */
export interface ReceivableItem {
  id: number;
  project_id: number;
  project_name: string;
  amount: number;
  days_pending: number;
  status: 'pending' | 'partial' | 'received';
  created_at: string;
}

/**
 * 回款记录
 */
export interface PaymentItem {
  id: number;
  project_id: number;
  project_name: string;
  amount: number;
  received_at: string;
  status: 'received' | 'processing';
}

// ========== API 响应 ==========

/**
 * 资金概览 API 响应
 */
export interface FundOverviewResponse {
  success: boolean;
  data: FundOverview;
  message?: string;
}

/**
 * 资金分布(按项目) API 响应
 */
export interface FundByProjectResponse {
  success: boolean;
  data: {
    items: FundByProjectItem[];
    pagination: {
      page: number;
      page_size: number;
      total: number;
    };
  };
  message?: string;
}

/**
 * 资金分布(按渠道) API 响应
 */
export interface FundByChannelResponse {
  success: boolean;
  data: {
    items: FundByChannelItem[];
    pagination: {
      page: number;
      page_size: number;
      total: number;
    };
  };
  message?: string;
}

/**
 * 应收款列表 API 响应
 */
export interface ReceivablesResponse {
  success: boolean;
  data: {
    items: ReceivableItem[];
    total_amount: number;
    pending_count: number;
  };
  message?: string;
}

/**
 * 回款记录 API 响应
 */
export interface PaymentsResponse {
  success: boolean;
  data: {
    items: PaymentItem[];
    total_amount: number;
  };
  message?: string;
}

// ========== 请求参数 ==========

export interface FundOverviewParams {
  date_from?: string;
  date_to?: string;
}

export interface FundDistributionParams {
  page?: number;
  page_size?: number;
  sort_by?: 'topup' | 'spend' | 'balance';
  order?: 'asc' | 'desc';
}

// ========== UI 配置 ==========

export type FundDistributionDimension = 'project' | 'channel';

export const FUND_DISTRIBUTION_CONFIG: Record<FundDistributionDimension, {
  label: string;
  icon: string;
}> = {
  project: {
    label: '按项目',
    icon: 'folder',
  },
  channel: {
    label: '按渠道',
    icon: 'share2',
  },
};

/**
 * 资金指标卡片配置
 */
export const FUND_STAT_CARDS_CONFIG = [
  {
    key: 'total_topup',
    title: '累计充值',
    icon: 'credit-card',
    color: 'green' as const,
    format: 'currency',
  },
  {
    key: 'total_spend',
    title: '累计消耗',
    icon: 'trending-down',
    color: 'blue' as const,
    format: 'currency',
  },
  {
    key: 'current_balance',
    title: '当前余额',
    icon: 'wallet',
    color: 'purple' as const,
    format: 'currency',
  },
  {
    key: 'total_receivable',
    title: '应收款',
    icon: 'receipt',
    color: 'orange' as const,
    format: 'currency',
  },
  {
    key: 'fund_occupied',
    title: '资金占用',
    icon: 'lock',
    color: 'red' as const,
    format: 'currency',
  },
] as const;
