/**
 * 对账管理模块类型定义
 */

export type ReconciliationStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';

export type PlatformSpendSource = 'manual' | 'api' | 'file';

export type SortBy =
  | 'batch_name'
  | 'period_start'
  | 'status'
  | 'created_at'
  | 'completed_at'
  | 'total_difference'
  | 'difference_percentage';

export type SortOrder = 'asc' | 'desc';

export interface ReconciliationBatch {
  id: number;
  batch_name: string;
  period_start: string;
  period_end: string;
  status: ReconciliationStatus;
  total_accounts: number;
  processed_accounts: number;
  total_discrepancies: number;
  total_system_spend: number;
  total_platform_spend: number;
  total_difference: number;
  difference_percentage: number;
  created_by: number;
  created_by_name: string;
  created_by_email: string;
  created_at: string;
  completed_at?: string;
  notes?: string;
  platform_spend_source: PlatformSpendSource;
  uploaded_file?: UploadedFile;
  auto_matching_enabled: boolean;
  threshold_amount: number;
  threshold_percentage: number;
  tags?: string[];
}

export interface UploadedFile {
  id: number;
  filename: string;
  original_name: string;
  size: number;
  type: string;
  upload_time: string;
  uploaded_by: number;
  upload_path: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  processing_log?: string;
  extracted_data?: PlatformSpendData[];
}

export interface PlatformSpendData {
  id: number;
  batch_id: number;
  account_id: number;
  account_name: string;
  platform: string;
  account_id_external: string;
  platform_spend: number;
  currency: string;
  period_start: string;
  period_end: string;
  spend_source: string;
  data_confidence: number; // 数据置信度 0-100
  validation_status: 'valid' | 'warning' | 'error';
  validation_messages: string[];
  matched_system_spend?: number;
  difference_amount?: number;
  difference_percentage?: number;
  reconciliation_status: 'matched' | 'partial' | 'unmatched' | 'pending';
  notes?: string;
}

export interface ReconciliationDiscrepancy {
  id: number;
  batch_id: number;
  account_id: number;
  account_name: string;
  platform: string;
  system_spend: number;
  platform_spend: number;
  difference_amount: number;
  difference_percentage: number;
  discrepancy_type: 'overspend' | 'underspend' | 'missing_data' | 'data_mismatch';
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'investigating' | 'resolved' | 'ignored';
  auto_resolution?: boolean;
  resolution_notes?: string;
  resolved_by?: number;
  resolved_by_name?: string;
  resolved_at?: string;
  created_at: string;
  updated_at: string;
  tags?: string[];
}

export interface ReconciliationSummary {
  total_batches: number;
  pending_batches: number;
  in_progress_batches: number;
  completed_batches: number;
  failed_batches: number;
  total_difference: number;
  avg_difference_percentage: number;
  total_discrepancies: number;
  pending_discrepancies: number;
  resolved_discrepancies: number;
  last_sync_time: string;
  next_scheduled_batch?: string;
  upcoming_batches: number;
  auto_match_rate: number;
  data_quality_score: number; // 数据质量评分 0-100
  accounts_by_platform: Record<string, number>;
  spend_by_period: Array<{
    period: string;
    system_spend: number;
    platform_spend: number;
    difference: number;
  }>;
  discrepancy_trends: Array<{
    date: string;
    count: number;
    amount: number;
  }>;
}

export interface ReconciliationFilters {
  search_term: string;
  status: ReconciliationStatus | 'all';
  platform_spend_source: PlatformSpendSource | 'all';
  created_by: number | 'all';
  date_range: {
    start?: string;
    end?: string;
  };
  difference_range: {
    min?: number;
    max?: number;
  };
  discrepancy_range: {
    min?: number;
    max?: number;
  };
  has_discrepancies: boolean | null;
  is_auto_matching: boolean | null;
  tags: string[];
  sort_by: SortBy;
  sort_order: SortOrder;
}

export interface ReconciliationCreateRequest {
  batch_name: string;
  period_start: string;
  period_end: string;
  platform_spend_source: PlatformSpendSource;
  auto_matching_enabled: boolean;
  threshold_amount: number;
  threshold_percentage: number;
  notes?: string;
  tags?: string[];
  account_ids?: number[]; // 指定对账的账户，为空则对账所有账户
}

export interface ReconciliationUpdateRequest {
  batch_name?: string;
  notes?: string;
  threshold_amount?: number;
  threshold_percentage?: number;
  auto_matching_enabled?: boolean;
  tags?: string[];
}

export interface ReconciliationDetail extends ReconciliationBatch {
  account_details: ReconciliationAccountDetail[];
  discrepancy_details: ReconciliationDiscrepancy[];
  processing_log: ProcessingLogEntry[];
  matching_rules: MatchingRule[];
  audit_trail: AuditTrailEntry[];
  performance_metrics: ReconciliationMetrics;
  related_files: UploadedFile[];
  platform_data_summary: PlatformDataSummary;
}

export interface ReconciliationAccountDetail {
  account_id: number;
  account_name: string;
  platform: string;
  account_id_external: string;
  system_spend: number;
  platform_spend: number;
  difference_amount: number;
  difference_percentage: number;
  reconciliation_status: 'matched' | 'partial' | 'unmatched' | 'pending';
  last_activity: string;
  spend_entries: number;
  confidence_score: number;
  notes?: string;
}

export interface ProcessingLogEntry {
  id: number;
  batch_id: number;
  step: string;
  status: 'started' | 'completed' | 'failed' | 'warning';
  message: string;
  details?: any;
  timestamp: string;
  duration?: number; // 处理时间（秒）
}

export interface MatchingRule {
  id: number;
  rule_name: string;
  rule_type: 'exact_match' | 'fuzzy_match' | 'date_range' | 'amount_tolerance';
  config: any;
  priority: number;
  is_active: boolean;
  created_by: number;
  created_at: string;
}

export interface AuditTrailEntry {
  id: number;
  batch_id: number;
  action_type: 'created' | 'started' | 'completed' | 'modified' | 'exported';
  action_details: any;
  performed_by: number;
  performed_by_name: string;
  ip_address?: string;
  user_agent?: string;
  timestamp: string;
}

export interface ReconciliationMetrics {
  total_processing_time: number; // 总处理时间（秒）
  accounts_processed_per_second: number;
  auto_match_rate: number;
  data_accuracy_score: number;
  discrepancy_detection_rate: number;
  file_processing_success_rate: number;
  api_call_success_rate: number;
  error_rate: number;
  performance_comparison: {
    current_batch: ReconciliationMetrics;
    previous_batch?: ReconciliationMetrics;
    improvement_percentage: number;
  };
}

export interface PlatformDataSummary {
  total_records: number;
  successful_matches: number;
  failed_matches: number;
  data_quality_score: number;
  platform_coverage: Record<string, {
    total_accounts: number;
    matched_accounts: number;
    total_spend: number;
    average_spend_per_account: number;
  }>;
  data_sources: Record<string, {
    record_count: number;
    success_rate: number;
    average_confidence: number;
  }>;
}

export interface ReconciliationReport {
  id: number;
  batch_id: number;
  report_type: 'summary' | 'detailed' | 'discrepancy' | 'audit';
  format: 'excel' | 'pdf' | 'csv';
  generated_by: number;
  generated_by_name: string;
  generated_at: string;
  file_path: string;
  file_size: number;
  download_count: number;
  expires_at?: string;
  parameters: any;
}

export interface ReconciliationExportOptions {
  format: 'excel' | 'pdf' | 'csv';
  include_discrepancies: boolean;
  include_matched_accounts: boolean;
  include_unmatched_accounts: boolean;
  include_processing_logs: boolean;
  include_audit_trail: boolean;
  date_range?: {
    start: string;
    end: string;
  };
  filters?: ReconciliationFilters;
}

export interface ReconciliationSchedule {
  id: number;
  schedule_name: string;
  schedule_type: 'daily' | 'weekly' | 'monthly';
  schedule_config: {
    day_of_week?: number; // 1-7 for weekly
    day_of_month?: number; // 1-31 for monthly
    time_of_day: string; // HH:mm format
    timezone: string;
  };
  auto_start: boolean;
  notification_settings: {
    email_on_completion: boolean;
    email_on_failure: boolean;
    notify_users: number[];
  };
  source_config: {
    platform_spend_source: PlatformSpendSource;
    auto_fetch_enabled: boolean;
    file_upload_location?: string;
  };
  created_by: number;
  created_at: string;
  last_run?: string;
  next_run?: string;
  is_active: boolean;
}

export interface ReconciliationAnalytics {
  batch_performance_trends: Array<{
    month: string;
    total_batches: number;
    success_rate: number;
    avg_processing_time: number;
    avg_difference_percentage: number;
  }>;
  discrepancy_analysis: {
    by_platform: Record<string, {
      total_discrepancies: number;
      avg_amount: number;
      most_common_type: string;
    }>;
    by_type: Record<string, {
      count: number;
      total_amount: number;
      avg_amount: number;
    }>;
    by_severity: Record<string, {
      count: number;
      resolution_rate: number;
      avg_resolution_time: number;
    }>;
  };
  data_quality_metrics: {
    platform_data_confidence: Record<string, number>;
    auto_match_success_rate: number;
    manual_intervention_rate: number;
    error_reduction_rate: number;
  };
  cost_impact_analysis: {
    total_financial_impact: number;
    recovered_amount: number;
    prevented_losses: number;
    roi_improvement: number;
  };
  operational_efficiency: {
    avg_processing_time_trend: number;
    automation_rate: number;
    user_satisfaction_score: number;
    compliance_rate: number;
  };
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