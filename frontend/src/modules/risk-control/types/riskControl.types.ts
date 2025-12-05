/**
 * Risk Control Types (风险控制)
 *
 * Aligned with:
 * - STATE_MACHINE.md v2.6 (trend_flagged state)
 * - BUSINESS_RULES.md v3.1 (risk thresholds)
 * - DAILY_REPORT_SOT.md (trend analysis)
 */

import type { UUID, ISODateString, DateString, Money } from '@/types';

// === Risk Level Enum ===

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

// === Risk Type Enum ===

export type RiskType =
  | 'spend_anomaly'      // Abnormal spending pattern
  | 'trend_deviation'    // Trend significantly deviates from expected
  | 'balance_warning'    // Balance approaching threshold
  | 'rate_of_change'     // Unusual rate of change
  | 'reconciliation_gap' // Large reconciliation discrepancy
  | 'account_suspension';// Account at risk of suspension

// === Alert Status ===

export type AlertStatus =
  | 'active'      // Alert is active, needs attention
  | 'acknowledged'// Alert has been seen but not resolved
  | 'resolved'    // Alert has been resolved
  | 'dismissed';  // Alert was dismissed as false positive

// === Entity Types ===

export interface RiskAlert {
  id: UUID;
  tenant_id: UUID;
  project_id?: UUID;
  ad_account_id?: UUID;

  // Alert details
  risk_type: RiskType;
  risk_level: RiskLevel;
  status: AlertStatus;

  // Context
  title: string;
  description: string;
  metric_name: string;
  metric_value: number;
  threshold_value: number;
  deviation_percentage: number;

  // Reference
  reference_type?: 'daily_report' | 'reconciliation' | 'ad_account';
  reference_id?: UUID;
  reference_date?: DateString;

  // Display fields
  ad_account_name?: string;
  project_name?: string;

  // Resolution
  resolved_by?: UUID;
  resolved_at?: ISODateString;
  resolution_notes?: string;

  // Metadata
  detected_at: ISODateString;
  created_at: ISODateString;
  updated_at: ISODateString;
}

export interface RiskSummary {
  tenant_id: UUID;
  date: DateString;

  // Counts by level
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;

  // Counts by status
  active_count: number;
  acknowledged_count: number;
  resolved_today: number;

  // Top risk types
  top_risk_types: Array<{
    type: RiskType;
    count: number;
  }>;
}

// === List/Filter Types ===

export interface RiskAlertFilters {
  tenant_id?: UUID;
  project_id?: UUID;
  ad_account_id?: UUID;
  risk_level?: RiskLevel | RiskLevel[];
  risk_type?: RiskType | RiskType[];
  status?: AlertStatus | AlertStatus[];
  start_date?: string;
  end_date?: string;
}

export interface RiskAlertListParams extends RiskAlertFilters {
  page?: number;
  page_size?: number;
  sort_by?: 'detected_at' | 'risk_level' | 'status';
  sort_order?: 'asc' | 'desc';
}

// === Action Types ===

export interface AcknowledgeAlertInput {
  alert_id: UUID;
}

export interface ResolveAlertInput {
  alert_id: UUID;
  resolution_notes: string;
}

export interface DismissAlertInput {
  alert_id: UUID;
  reason: string;
}

// === Display Config ===

export const RISK_LEVEL_CONFIG: Record<RiskLevel, { label: string; variant: 'default' | 'success' | 'warning' | 'error' | 'info'; color: string }> = {
  low: { label: '低风险', variant: 'default', color: 'text-text-muted' },
  medium: { label: '中风险', variant: 'warning', color: 'text-warning' },
  high: { label: '高风险', variant: 'error', color: 'text-danger' },
  critical: { label: '严重', variant: 'error', color: 'text-danger' },
};

export const RISK_TYPE_CONFIG: Record<RiskType, { label: string; icon: string }> = {
  spend_anomaly: { label: '消耗异常', icon: 'trending-up' },
  trend_deviation: { label: '趋势偏离', icon: 'activity' },
  balance_warning: { label: '余额预警', icon: 'alert-circle' },
  rate_of_change: { label: '变化率异常', icon: 'zap' },
  reconciliation_gap: { label: '对账差异', icon: 'file-diff' },
  account_suspension: { label: '账户风险', icon: 'shield-alert' },
};

export const ALERT_STATUS_CONFIG: Record<AlertStatus, { label: string; variant: 'default' | 'success' | 'warning' | 'error' | 'info' }> = {
  active: { label: '待处理', variant: 'error' },
  acknowledged: { label: '已确认', variant: 'warning' },
  resolved: { label: '已解决', variant: 'success' },
  dismissed: { label: '已忽略', variant: 'default' },
};
