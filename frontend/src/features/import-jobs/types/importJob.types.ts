/**
 * Import Job Types
 *
 * SoT 对齐: DATA_SCHEMA.md v5.2
 */

/** 导入任务状态 */
export type ImportJobStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'cancelled';

/** 导入任务类型 */
export type ImportJobType =
  | 'finance'
  | 'spend'
  | 'reconciliation'
  | 'daily_report';

/** 状态配置 */
export const IMPORT_JOB_STATUS_CONFIG: Record<ImportJobStatus, {
  label: string;
  variant: 'default' | 'secondary' | 'destructive' | 'outline';
}> = {
  pending: { label: '待处理', variant: 'secondary' },
  processing: { label: '处理中', variant: 'outline' },
  completed: { label: '已完成', variant: 'default' },
  failed: { label: '失败', variant: 'destructive' },
  cancelled: { label: '已取消', variant: 'secondary' },
};

/** 类型配置 */
export const IMPORT_JOB_TYPE_CONFIG: Record<ImportJobType, { label: string }> = {
  finance: { label: '财务数据' },
  spend: { label: '消耗数据' },
  reconciliation: { label: '对账数据' },
  daily_report: { label: '日报数据' },
};

/** 导入任务 */
export interface ImportJob {
  id: number;
  job_no: string;
  type: ImportJobType;
  status: ImportJobStatus;
  file_name?: string;
  file_path?: string;
  file_hash?: string;
  file_size?: number;
  total_rows?: number;
  processed_rows?: number;
  success_rows?: number;
  failed_rows?: number;
  error_log?: Array<{ row: number; error: string; data?: Record<string, unknown> }>;
  result_summary?: Record<string, unknown>;
  started_at?: string;
  completed_at?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
  progress_percent?: number;
  success_rate?: number;
}

/** 导入任务进度 */
export interface ImportJobProgress {
  job_id: number;
  job_no: string;
  status: ImportJobStatus;
  total_rows: number;
  processed_rows: number;
  success_rows: number;
  failed_rows: number;
  progress_percent: number;
  started_at?: string;
  estimated_remaining_seconds?: number;
}

/** 导入任务统计 */
export interface ImportJobStatistics {
  total_jobs: number;
  pending_jobs: number;
  processing_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  cancelled_jobs: number;
  overall_success_rate: number;
  total_rows_processed: number;
  total_rows_success: number;
  total_rows_failed: number;
  by_type: Record<string, number>;
  recent_jobs: Array<Record<string, unknown>>;
}

/** 导入任务列表查询参数 */
export interface ImportJobListParams {
  page?: number;
  page_size?: number;
  status?: ImportJobStatus;
  type?: ImportJobType;
}
