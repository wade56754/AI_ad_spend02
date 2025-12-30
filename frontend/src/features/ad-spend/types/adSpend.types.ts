/**
 * Ad Spend Types
 *
 * SoT: docs/10.module-specs/C3-spend-detail.md §2 数据需求
 * SoT: DATA_SCHEMA.md v5.2
 * SoT: MASTER.md v4.4 §4.5.7 - 消耗 SoT = ad_spend_daily.spend
 *
 * 一句话定义: 广告消耗数据的类型定义
 *
 * 消耗 SoT 约束 (C3-spend-detail.md §1.4):
 *   Phase 1: ad_spend_daily.spend (Excel 导入)
 *   Phase 2: daily_report.real_spend (project_owner/finance 确认)
 *
 * 计算公式 (C3-spend-detail.md §2.3):
 *   CPL/CPA = spend / conversions
 *   CTR = clicks / impressions × 100%
 *   CPC = spend / clicks
 *
 * Author: AI 代码工厂 v2.4
 */

export interface AdSpendRecord {
  id: number;
  ad_account_id: number;
  ad_account_name: string; // JOIN 填充: ad_accounts.name
  project_id: number;
  project_name: string;
  channel_id: number;
  channel_name: string;
  report_date: string;
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  ctr: number; // clicks / impressions
  cpc: number; // spend / clicks
  cpa: number; // spend / conversions
  created_at: string;
  updated_at?: string;
}

export interface AdSpendSummary {
  total_spend: number;
  total_impressions: number;
  total_clicks: number;
  total_conversions: number;
  avg_ctr: number;
  avg_cpc: number;
  avg_cpa: number;
  record_count: number;
}

export interface AdSpendByProject {
  project_id: number;
  project_name: string;
  total_spend: number;
  total_conversions: number;
  account_count: number;
  avg_cpa: number;
}

export interface AdSpendByAccount {
  ad_account_id: number;
  ad_account_name: string; // JOIN 填充: ad_accounts.name
  project_name: string;
  channel_name: string;
  total_spend: number;
  total_conversions: number;
  avg_cpa: number;
}

export interface AdSpendTrendItem {
  date: string;
  spend: number;
  conversions: number;
  cpa: number;
}

// ========== 请求参数 ==========

export interface AdSpendListParams {
  project_id?: number;
  ad_account_id?: number;
  channel_id?: number;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

export interface AdSpendSummaryParams {
  project_id?: number;
  start_date?: string;
  end_date?: string;
}

// ========== 响应 ==========

export interface AdSpendListResponse {
  items: AdSpendRecord[];
  total: number;
  page: number;
  page_size: number;
  summary: AdSpendSummary;
}

export interface AdSpendTrendResponse {
  items: AdSpendTrendItem[];
  total_spend: number;
  total_conversions: number;
  avg_cpa: number;
}
