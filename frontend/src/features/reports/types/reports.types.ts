/**
 * Reports Module Type Definitions
 *
 * SoT 对齐:
 * - backend/schemas/reports.py
 * - backend/routers/reports.py v2.0
 */

// ========== Enums ==========

export enum ReportPeriod {
  DAILY = 'daily',
  WEEKLY = 'weekly',
  MONTHLY = 'monthly',
  QUARTERLY = 'quarterly',
  YEARLY = 'yearly',
  CUSTOM = 'custom',
}

export enum ReportGroupBy {
  PROJECT = 'project',
  CHANNEL = 'channel',
  ACCOUNT = 'account',
  DATE = 'date',
  SUPPLIER = 'supplier',
}

export enum TrendMetric {
  SPEND = 'spend',
  LEADS = 'leads',
  TOPUP = 'topup',
}

// ========== Request Params ==========

export interface ReportQueryParams {
  start_date?: string;
  end_date?: string;
  project_ids?: string; // comma-separated
  channel_ids?: string; // comma-separated
}

export interface TrendReportParams {
  metric: TrendMetric;
  period?: 'daily' | 'weekly' | 'monthly';
  start_date?: string;
  end_date?: string;
}

// ========== Response Types ==========

// Dashboard Summary
export interface DashboardSummary {
  // Today data
  today_spend: number;
  today_leads: number;
  today_topup: number;

  // Month data
  month_spend: number;
  month_leads: number;
  month_topup: number;
  month_profit: number;

  // Account stats
  total_accounts: number;
  active_accounts: number;
  low_balance_accounts: number;

  // Project stats
  total_projects: number;
  active_projects: number;

  // Pending items
  pending_topups: number;
  pending_reconciliations: number;
  pending_reports: number;

  // Trends (7 days)
  spend_trend: TrendDataPoint[];
  leads_trend: TrendDataPoint[];
}

export interface TrendDataPoint {
  date: string;
  value: number;
}

// Performance Report
export interface PerformanceReportItem {
  project_id: number | null;
  project_name: string | null;
  channel_id: number | null;
  channel_name: string | null;
  ad_account_id: number | null;
  ad_account_name: string | null; // JOIN 填充: ad_accounts.name
  date: string | null;
  total_spend: number;
  total_leads: number;
  cpa: number | null;
  spend_change_rate: number | null;
  leads_change_rate: number | null;
}

export interface PerformanceReportResponse {
  items: PerformanceReportItem[];
  summary: {
    total_spend: string;
    total_leads: number;
    avg_cpa: string | null;
    project_count: number;
    channel_count: number;
  };
  meta: {
    start_date: string;
    end_date: string;
    generated_at: string;
  };
}

// Profit Report
export interface ProfitReportItem {
  project_id: number | null;
  project_name: string | null;
  date: string | null;
  revenue: number;
  cost: number;
  profit: number;
  profit_rate: number | null;
  ad_spend: number;
  topup_amount: number;
}

export interface ProfitReportResponse {
  items: ProfitReportItem[];
  summary: {
    total_revenue: string;
    total_cost: string;
    total_profit: string;
    profit_rate: number | null;
    project_count: number;
  };
  meta: {
    start_date: string;
    end_date: string;
    generated_at: string;
  };
}

// Reconciliation Report
export interface ReconciliationReportItem {
  period: string;
  total_batches: number;
  draft_batches: number;
  pending_review_batches: number;
  approved_batches: number;
  completed_batches: number;
  total_system_spend: number;
  total_actual_spend: number;
  total_discrepancy: number;
  completion_rate: number | null;
  discrepancy_rate: number | null;
}

export interface ReconciliationReportResponse {
  items: ReconciliationReportItem[];
  summary: {
    total_batches: number;
    completed_batches: number;
    completion_rate: number | null;
    total_discrepancy: string;
  };
  meta: {
    start_date: string;
    end_date: string;
    generated_at: string;
  };
}

// Financial Summary
export interface FinancialSummaryItem {
  ad_account_id: number;
  ad_account_name: string; // JOIN 填充: ad_accounts.name
  project_id: number | null;
  project_name: string | null;
  channel_id: number | null;
  channel_name: string | null;
  current_balance: number;
  total_topup: number;
  total_spend: number;
  total_transfer_in: number;
  total_transfer_out: number;
  net_change: number;
}

export interface FinancialSummaryResponse {
  items: FinancialSummaryItem[];
  summary: {
    total_accounts: number;
    total_balance: string;
    total_topup: string;
    total_spend: string;
  };
  meta: {
    start_date: string;
    end_date: string;
    generated_at: string;
  };
}

// Trend Report
export interface TrendReportDataPoint {
  date: string;
  value: string;
  label: string | null;
}

export interface TrendReportResponse {
  period: string;
  data_points: TrendReportDataPoint[];
  summary: {
    total: string;
    average: string;
    max: string;
    min: string;
    count: number;
  };
}
