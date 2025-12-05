/**
 * useRiskAlerts Hook
 *
 * Mock data hook for Risk Control module
 */

import { useState, useCallback, useMemo } from 'react';
import type { RiskAlert, RiskAlertFilters, RiskLevel, AlertStatus, RiskType } from '../types';

// Mock data for development
const mockAlerts: RiskAlert[] = [
  {
    id: 'alert-001',
    tenant_id: 'tenant-001',
    project_id: 'proj-001',
    ad_account_id: 'acc-001',
    risk_type: 'spend_anomaly',
    risk_level: 'critical',
    status: 'active',
    title: '消耗异常暴增',
    description: '账户消耗较前日增长 250%，超过阈值 50%',
    metric_name: '日消耗',
    metric_value: 150000,
    threshold_value: 50000,
    deviation_percentage: 250,
    ad_account_name: '腾讯广告-A001',
    project_name: '项目A',
    reference_type: 'daily_report',
    reference_id: 'dr-001',
    reference_date: '2025-01-24',
    detected_at: '2025-01-24T08:00:00Z',
    created_at: '2025-01-24T08:00:00Z',
    updated_at: '2025-01-24T08:00:00Z',
  },
  {
    id: 'alert-002',
    tenant_id: 'tenant-001',
    project_id: 'proj-002',
    ad_account_id: 'acc-002',
    risk_type: 'balance_warning',
    risk_level: 'high',
    status: 'acknowledged',
    title: '余额不足预警',
    description: '账户余额低于 3 天消耗预估，建议充值',
    metric_name: '剩余天数',
    metric_value: 2.5,
    threshold_value: 3,
    deviation_percentage: -16.7,
    ad_account_name: '巨量引擎-B002',
    project_name: '项目B',
    detected_at: '2025-01-24T06:00:00Z',
    created_at: '2025-01-24T06:00:00Z',
    updated_at: '2025-01-24T10:00:00Z',
  },
  {
    id: 'alert-003',
    tenant_id: 'tenant-001',
    project_id: 'proj-001',
    ad_account_id: 'acc-003',
    risk_type: 'trend_deviation',
    risk_level: 'medium',
    status: 'active',
    title: '趋势偏离预警',
    description: 'ROI 连续 3 天下降，较基线偏离 -15%',
    metric_name: 'ROI',
    metric_value: 1.2,
    threshold_value: 1.5,
    deviation_percentage: -20,
    ad_account_name: '腾讯广告-A003',
    project_name: '项目A',
    reference_type: 'daily_report',
    reference_date: '2025-01-24',
    detected_at: '2025-01-23T18:00:00Z',
    created_at: '2025-01-23T18:00:00Z',
    updated_at: '2025-01-23T18:00:00Z',
  },
  {
    id: 'alert-004',
    tenant_id: 'tenant-001',
    project_id: 'proj-003',
    risk_type: 'reconciliation_gap',
    risk_level: 'high',
    status: 'active',
    title: '对账差异超限',
    description: '对账差异金额 ¥2,500，超过阈值 ¥1,000',
    metric_name: '差异金额',
    metric_value: 250000,
    threshold_value: 100000,
    deviation_percentage: 150,
    project_name: '项目C',
    reference_type: 'reconciliation',
    reference_id: 'recon-001',
    reference_date: '2025-01-23',
    detected_at: '2025-01-24T02:00:00Z',
    created_at: '2025-01-24T02:00:00Z',
    updated_at: '2025-01-24T02:00:00Z',
  },
  {
    id: 'alert-005',
    tenant_id: 'tenant-001',
    ad_account_id: 'acc-005',
    risk_type: 'account_suspension',
    risk_level: 'critical',
    status: 'resolved',
    title: '账户封禁风险',
    description: '账户违规次数达到警告阈值',
    metric_name: '违规次数',
    metric_value: 3,
    threshold_value: 3,
    deviation_percentage: 0,
    ad_account_name: '快手广告-C005',
    resolved_by: 'user-001',
    resolved_at: '2025-01-23T16:00:00Z',
    resolution_notes: '已联系平台处理，账户恢复正常',
    detected_at: '2025-01-23T10:00:00Z',
    created_at: '2025-01-23T10:00:00Z',
    updated_at: '2025-01-23T16:00:00Z',
  },
  {
    id: 'alert-006',
    tenant_id: 'tenant-001',
    project_id: 'proj-002',
    ad_account_id: 'acc-006',
    risk_type: 'rate_of_change',
    risk_level: 'low',
    status: 'dismissed',
    title: '消耗变化率异常',
    description: '单日消耗变化率 -40%，低于正常波动范围',
    metric_name: '变化率',
    metric_value: -40,
    threshold_value: -30,
    deviation_percentage: -33.3,
    ad_account_name: '巨量引擎-B006',
    project_name: '项目B',
    detected_at: '2025-01-22T18:00:00Z',
    created_at: '2025-01-22T18:00:00Z',
    updated_at: '2025-01-23T09:00:00Z',
  },
];

interface UseRiskAlertsResult {
  alerts: RiskAlert[];
  loading: boolean;
  error: Error | null;
  filters: RiskAlertFilters;
  setFilters: (filters: RiskAlertFilters) => void;
  stats: {
    total: number;
    byLevel: Record<RiskLevel, number>;
    byStatus: Record<AlertStatus, number>;
    activeCount: number;
  };
}

export function useRiskAlerts(initialFilters: RiskAlertFilters = {}): UseRiskAlertsResult {
  const [filters, setFilters] = useState<RiskAlertFilters>(initialFilters);
  const [loading] = useState(false);
  const [error] = useState<Error | null>(null);

  const filteredAlerts = useMemo(() => {
    return mockAlerts.filter((a) => {
      if (filters.status) {
        const statuses = Array.isArray(filters.status) ? filters.status : [filters.status];
        if (!statuses.includes(a.status)) return false;
      }
      if (filters.risk_level) {
        const levels = Array.isArray(filters.risk_level) ? filters.risk_level : [filters.risk_level];
        if (!levels.includes(a.risk_level)) return false;
      }
      if (filters.risk_type) {
        const types = Array.isArray(filters.risk_type) ? filters.risk_type : [filters.risk_type];
        if (!types.includes(a.risk_type)) return false;
      }
      return true;
    });
  }, [filters]);

  const stats = useMemo(() => {
    const byLevel: Record<RiskLevel, number> = {
      low: 0,
      medium: 0,
      high: 0,
      critical: 0,
    };
    const byStatus: Record<AlertStatus, number> = {
      active: 0,
      acknowledged: 0,
      resolved: 0,
      dismissed: 0,
    };

    mockAlerts.forEach((a) => {
      byLevel[a.risk_level]++;
      byStatus[a.status]++;
    });

    return {
      total: mockAlerts.length,
      byLevel,
      byStatus,
      activeCount: byStatus.active + byStatus.acknowledged,
    };
  }, []);

  const handleSetFilters = useCallback((newFilters: RiskAlertFilters) => {
    setFilters(newFilters);
  }, []);

  return {
    alerts: filteredAlerts,
    loading,
    error,
    filters,
    setFilters: handleSetFilters,
    stats,
  };
}
