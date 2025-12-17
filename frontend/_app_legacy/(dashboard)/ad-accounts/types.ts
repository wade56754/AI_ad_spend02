/**
 * 广告账户管理模块类型定义
 */

export type Platform = 'facebook' | 'tiktok' | 'google' | 'twitter' | 'instagram' | 'youtube' | 'linkedin';

export type AccountStatus = 'active' | 'paused' | 'banned' | 'pending' | 'restricted';

export type AccountType = 'personal' | 'business' | 'agency';

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export type SortBy =
  | 'account_name'
  | 'platform'
  | 'account_status'
  | 'current_spend'
  | 'balance'
  | 'created_at'
  | 'last_active'
  | 'performance_metrics';

export type SortOrder = 'asc' | 'desc';

export interface AdAccount {
  id: number;
  account_name: string;
  platform: Platform;
  account_id: string;
  account_status: AccountStatus;
  account_type: AccountType;
  currency: string;
  timezone: string;
  spending_limit: number;
  current_spend: number;
  balance: number;
  creation_time: string;
  last_active: string;
  assigned_user_id?: number;
  assigned_user_name?: string;
  assigned_user_email?: string;
  project_id?: number;
  project_name?: string;
  client_id?: number;
  client_name?: string;
  notes?: string;
  tags?: string[];
  created_at: string;
  updated_at: string;
  created_by: string;
  performance_metrics?: PerformanceMetrics;
  health_status?: HealthStatus;
  account_settings?: AccountSettings;
  last_performance_check?: string;
  auto_optimization_enabled?: boolean;
  budget_alerts_enabled?: boolean;
}

export interface PerformanceMetrics {
  total_spend: number;
  total_impressions: number;
  total_clicks: number;
  total_conversions: number;
  avg_cpc: number;
  avg_cpm: number;
  avg_ctr: number;
  avg_cpl: number;
  avg_roas: number;
  last_7d_spend: number;
  last_30d_spend: number;
  last_7d_conversions: number;
  last_30d_conversions: number;
  trend_data?: {
    daily_spend: number[];
    daily_conversions: number[];
    daily_ctr: number[];
    dates: string[];
  };
  conversion_rate: number;
  cost_per_result: number;
  return_on_ad_spend: number;
}

export interface HealthStatus {
  risk_level: RiskLevel;
  issues: HealthIssue[];
  recommendations: string[];
  last_check: string;
  health_score: number; // 0-100
}

export interface HealthIssue {
  type: 'budget' | 'performance' | 'policy' | 'technical' | 'billing';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  impact: string;
  recommendation: string;
  detected_at: string;
}

export interface AccountSettings {
  auto_budget_optimization: boolean;
  budget_alert_threshold: number;
  performance_alert_threshold: number;
  enable_auto_pause: boolean;
  daily_budget_limit?: number;
  timezone_alerts: boolean;
  weekend_delivery: boolean;
  creative_rotation_enabled: boolean;
  audience_expansion_enabled: boolean;
}

export interface AdAccountStats {
  total_accounts: number;
  active_accounts: number;
  paused_accounts: number;
  banned_accounts: number;
  pending_accounts: number;
  total_spending_limit: number;
  total_current_spend: number;
  total_balance: number;
  average_performance_score: number;
  high_risk_accounts: number;
  accounts_needing_attention: number;
  accounts_by_platform: Record<Platform, number>;
  accounts_by_status: Record<AccountStatus, number>;
  total_conversions: number;
  average_roas: number;
  last_24h_spend: number;
  last_7d_spend: number;
  last_30d_spend: number;
  utilization_rate: number;
}

export interface AdAccountFilters {
  search_term: string;
  platform: Platform | 'all';
  status: AccountStatus | 'all';
  type: AccountType | 'all';
  assigned_user_id?: number | 'all';
  project_id?: number | 'all';
  client_id?: number | 'all';
  risk_level: RiskLevel | 'all';
  balance_range: {
    min?: number;
    max?: number;
  };
  spend_range: {
    min?: number;
    max?: number;
  };
  date_range: {
    start?: string;
    end?: string;
  };
  has_issues: boolean | null;
  auto_optimization: boolean | null;
  tags: string[];
  sort_by: SortBy;
  sort_order: SortOrder;
}

export interface AdAccountCreateRequest {
  account_name: string;
  platform: Platform;
  account_type: AccountType;
  account_id: string;
  currency: string;
  timezone: string;
  spending_limit: number;
  assigned_user_id?: number;
  project_id?: number;
  client_id?: number;
  notes?: string;
  tags?: string[];
  account_settings?: Partial<AccountSettings>;
}

export interface AdAccountUpdateRequest {
  account_name?: string;
  account_status?: AccountStatus;
  spending_limit?: number;
  assigned_user_id?: number;
  project_id?: number;
  notes?: string;
  tags?: string[];
  account_settings?: Partial<AccountSettings>;
}

export interface AdAccountDetail extends AdAccount {
  recent_performance: PerformanceMetrics[];
  account_history: AccountHistoryItem[];
  health_check_history: HealthStatus[];
  assigned_user_info?: UserInfo;
  project_info?: ProjectInfo;
  client_info?: ClientInfo;
  recent_activities: AccountActivity[];
  budget_utilization: BudgetUtilization;
  optimization_suggestions: OptimizationSuggestion[];
}

export interface AccountHistoryItem {
  id: number;
  action_type: 'created' | 'updated' | 'status_changed' | 'budget_updated' | 'assigned' | 'unassigned';
  old_value?: any;
  new_value?: any;
  performed_by: string;
  performed_at: string;
  notes?: string;
}

export interface UserInfo {
  id: number;
  name: string;
  email: string;
  role: string;
  avatar?: string;
  department?: string;
}

export interface ProjectInfo {
  id: number;
  name: string;
  status: string;
  client_name: string;
  budget: number;
  start_date: string;
  end_date?: string;
}

export interface ClientInfo {
  id: number;
  name: string;
  industry: string;
  contact_person: string;
  email: string;
  phone?: string;
}

export interface AccountActivity {
  id: number;
  type: 'login' | 'campaign_created' | 'budget_updated' | 'performance_alert' | 'health_check';
  description: string;
  timestamp: string;
  details?: any;
}

export interface BudgetUtilization {
  daily_average: number;
  weekly_average: number;
  monthly_average: number;
  utilization_rate: number;
  projected_month_end: number;
  days_remaining: number;
  trend: 'increasing' | 'decreasing' | 'stable';
}

export interface OptimizationSuggestion {
  id: number;
  type: 'budget' | 'bidding' | 'targeting' | 'creative' | 'schedule';
  priority: 'low' | 'medium' | 'high';
  title: string;
  description: string;
  expected_impact: string;
  implementation_difficulty: 'easy' | 'medium' | 'hard';
  estimated_improvement: number; // percentage
  created_at: string;
  status: 'pending' | 'implemented' | 'dismissed';
}

export interface KPICardConfig {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: 'primary' | 'success' | 'warning' | 'destructive' | 'info' | 'default';
  icon?: React.ComponentType<{ className?: string }>;
  trend?: {
    type: 'up' | 'down' | 'neutral';
    value: number;
    period?: string;
  };
}

export interface AccountTableRow {
  account: AdAccount;
  isSelected: boolean;
}

export interface AccountTableColumn {
  key: string;
  title: string;
  width?: string;
  sortable?: boolean;
  align?: 'left' | 'center' | 'right';
  render?: (value: any, account: AdAccount) => React.ReactNode;
}

export interface BatchOperation {
  type: 'status_change' | 'assign' | 'unassign' | 'delete' | 'export' | 'bulk_update';
  targetIds: number[];
  payload?: any;
}

export interface AccountFormData {
  account_name: string;
  platform: Platform;
  account_type: AccountType;
  account_id: string;
  currency: string;
  timezone: string;
  spending_limit: string;
  assigned_user_id?: number;
  project_id?: number;
  client_id?: number;
  notes?: string;
  tags: string[];
}

export interface PlatformConfig {
  platform: Platform;
  display_name: string;
  icon: string;
  color: string;
  features: string[];
  supported_account_types: AccountType[];
  default_currency: string;
  default_timezone: string;
}

export interface BulkImportResult {
  total_processed: number;
  successful_imports: number;
  failed_imports: number;
  errors: ImportError[];
  created_accounts: AdAccount[];
}

export interface ImportError {
  row_number: number;
  error_type: 'validation' | 'duplicate' | 'api_error' | 'missing_field';
  field?: string;
  message: string;
  raw_data?: any;
}

export interface ExportOptions {
  format: 'csv' | 'xlsx' | 'json';
  include_performance_data: boolean;
  include_health_status: boolean;
  date_range?: {
    start: string;
    end: string;
  };
  filters?: AdAccountFilters;
}