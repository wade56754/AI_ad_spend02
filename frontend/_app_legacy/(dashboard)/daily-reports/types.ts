/**
 * 日报管理模块类型定义
 */

export type ReportStatus = 'pending' | 'approved' | 'rejected' | 'needs_revision';

export type DateRange = 'today' | 'yesterday' | 'last_7_days' | 'last_30_days' | 'this_month' | 'custom';

export type SortBy =
  | 'report_date'
  | 'project_name'
  | 'account_name'
  | 'submitted_by'
  | 'spend_amount'
  | 'roi'
  | 'submitted_at'
  | 'reviewed_at';

export type SortOrder = 'asc' | 'desc';

export interface DailyReport {
  id: number;
  report_date: string;
  project_id: number;
  project_name: string;
  account_id: number;
  account_name: string;
  platform: string;
  submitted_by: number;
  submitted_by_name: string;
  submitted_by_email: string;
  status: ReportStatus;
  spend_amount: number;
  currency: string;
  follow_count: number;
  conversion_count: number;
  cpl: number;
  roi: number;
  notes?: string;
  submitted_at: string;
  reviewed_by?: number;
  reviewed_by_name?: string;
  reviewed_by_email?: string;
  reviewed_at?: string;
  review_notes?: string;
  attachments: ReportAttachment[];
  performance_metrics: PerformanceMetrics;
  quality_score?: number; // 数据质量评分 0-100
  is_anomaly?: boolean; // 是否异常数据
  anomaly_reasons?: string[]; // 异常原因
  tags?: string[];
  created_at: string;
  updated_at: string;
}

export interface PerformanceMetrics {
  ctr: number; // 点击率
  cpm: number; // 每千次展示成本
  reach: number; // 触达人数
  impressions: number; // 展示次数
  frequency: number; // 频率
  clicks: number; // 点击次数
  cpc: number; // 每次点击成本
  conversion_rate: number; // 转化率
  cost_per_conversion: number; // 每次转化成本
  return_on_ad_spend: number; // 广告支出回报
}

export interface ReportAttachment {
  id: number;
  name: string;
  url: string;
  size: number;
  type: string;
  uploaded_at: string;
  uploaded_by: number;
  description?: string;
}

export interface DailyReportStats {
  total_reports: number;
  pending_reports: number;
  approved_reports: number;
  rejected_reports: number;
  needs_revision_reports: number;
  total_spend: number;
  total_conversions: number;
  average_roi: number;
  average_cpl: number;
  reports_today: number;
  reports_this_week: number;
  reports_this_month: number;
  pending_reviews_today: number;
  approval_rate: number; // 审核通过率
  average_quality_score: number; // 平均数据质量评分
  anomaly_reports: number; // 异常报告数量
  reports_by_status: Record<ReportStatus, number>;
  reports_by_platform: Record<string, number>;
  spend_by_date: Array<{
    date: string;
    amount: number;
    conversions: number;
  }>;
  top_performers: Array<{
    account_name: string;
    roi: number;
    spend: number;
    conversions: number;
  }>;
}

export interface DailyReportFilters {
  search_term: string;
  status: ReportStatus | 'all';
  project_id: number | 'all';
  account_id: number | 'all';
  submitted_by: number | 'all';
  reviewed_by: number | 'all';
  date_range: DateRange;
  custom_date_range: {
    start?: string;
    end?: string;
  };
  spend_range: {
    min?: number;
    max?: number;
  };
  roi_range: {
    min?: number;
    max?: number;
  };
  has_attachments: boolean | null;
  has_anomalies: boolean | null;
  quality_score_range: {
    min?: number;
    max?: number;
  };
  tags: string[];
  sort_by: SortBy;
  sort_order: SortOrder;
}

export interface DailyReportCreateRequest {
  report_date: string;
  project_id: number;
  account_id: number;
  spend_amount: number;
  follow_count: number;
  conversion_count: number;
  notes?: string;
  attachments?: Array<{
    name: string;
    file: File;
    description?: string;
  }>;
  performance_metrics: Partial<PerformanceMetrics>;
  tags?: string[];
}

export interface DailyReportUpdateRequest {
  spend_amount?: number;
  follow_count?: number;
  conversion_count?: number;
  notes?: string;
  performance_metrics?: Partial<PerformanceMetrics>;
  tags?: string[];
}

export interface DailyReportReviewRequest {
  status: ReportStatus;
  review_notes?: string;
  quality_score?: number;
  is_anomaly?: boolean;
  anomaly_reasons?: string[];
}

export interface DailyReportDetail extends DailyReport {
  project_info: {
    id: number;
    name: string;
    client_name: string;
    budget: number;
    start_date: string;
    end_date?: string;
  };
  account_info: {
    id: number;
    account_name: string;
    platform: string;
    account_id: string;
    currency: string;
  };
  submitted_by_info: {
    id: number;
    name: string;
    email: string;
    role: string;
    avatar?: string;
  };
  reviewed_by_info?: {
    id: number;
    name: string;
    email: string;
    role: string;
    avatar?: string;
  };
  revision_history: ReportRevision[];
  related_reports: DailyReport[]; // 相邻日期的报告
  performance_trends: {
    last_7_days: Array<{
      date: string;
      spend: number;
      roi: number;
      conversions: number;
    }>;
  };
}

export interface ReportRevision {
  id: number;
  revision_type: 'created' | 'updated' | 'reviewed' | 'status_changed';
  old_data?: any;
  new_data?: any;
  changed_fields: string[];
  performed_by: number;
  performed_by_name: string;
  performed_at: string;
  notes?: string;
}

export interface ReportTemplate {
  id: number;
  name: string;
  description: string;
  project_id?: number;
  account_id?: number;
  required_fields: string[];
  optional_fields: string[];
  default_notes?: string;
  performance_metrics_template: Partial<PerformanceMetrics>;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface ReportComment {
  id: number;
  report_id: number;
  comment: string;
  commented_by: number;
  commented_by_name: string;
  commented_at: string;
  parent_id?: number; // 回复评论的父ID
  replies?: ReportComment[];
}

export interface ReportBatchAction {
  type: 'approve' | 'reject' | 'request_revision' | 'export' | 'delete';
  report_ids: number[];
  action_data?: {
    review_notes?: string;
    quality_score?: number;
    export_format?: 'excel' | 'pdf' | 'csv';
  };
}

export interface ReportNotification {
  id: number;
  report_id: number;
  notification_type: 'submitted' | 'approved' | 'rejected' | 'needs_revision' | 'anomaly_detected';
  recipient_id: number;
  recipient_name: string;
  message: string;
  is_read: boolean;
  created_at: string;
  read_at?: string;
}

export interface ReportAnalytics {
  submission_trends: Array<{
    date: string;
    count: number;
    pending_count: number;
    approved_count: number;
    rejected_count: number;
  }>;
  performance_trends: Array<{
    date: string;
    avg_roi: number;
    avg_cpl: number;
    total_spend: number;
    total_conversions: number;
  }>;
  quality_trends: Array<{
    date: string;
    avg_quality_score: number;
    anomaly_count: number;
  }>;
  top_projects: Array<{
    project_name: string;
    report_count: number;
    total_spend: number;
    avg_roi: number;
  }>;
  top_accounts: Array<{
    account_name: string;
    platform: string;
    report_count: number;
    total_spend: number;
    avg_roi: number;
  }>;
  reviewer_performance: Array<{
    reviewer_name: string;
    reviews_count: number;
    avg_review_time: number; // 平均审核时间（分钟）
    approval_rate: number;
  }>;
}