/**
 * Audit Logs Types
 */

export interface AuditLog {
  id: number;
  user_id: string;
  user_name: string;
  user_role: string;
  action: string;
  resource_type: string;
  resource_id: string;
  resource_name?: string;
  ip_address: string;
  user_agent: string;
  details?: Record<string, unknown>;
  created_at: string;
}

export interface AuditLogListParams {
  page?: number;
  page_size?: number;
  user_id?: string;
  action?: string;
  resource_type?: string;
  start_date?: string;
  end_date?: string;
}

export interface AuditLogStatistics {
  total_logs: number;
  today_logs: number;
  unique_users: number;
  top_actions: Array<{ action: string; count: number }>;
}
