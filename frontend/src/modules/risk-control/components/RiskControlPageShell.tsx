/**
 * RiskControlPageShell - 风险控制页面容器
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { RefreshCw } from 'lucide-react';
import { PageShell } from '@/modules/shared';
import { useRiskAlerts } from '../hooks';
import { RiskControlKpiRow } from './RiskControlKpiRow';
import { RiskAlertDataTable } from './RiskAlertDataTable';

export function RiskControlPageShell() {
  const { alerts, loading, stats, filters, setFilters } = useRiskAlerts();

  const statusOptions = [
    { value: 'all', label: '全部状态' },
    { value: 'active', label: '待处理' },
    { value: 'acknowledged', label: '已确认' },
    { value: 'resolved', label: '已解决' },
    { value: 'dismissed', label: '已忽略' },
  ];

  const levelOptions = [
    { value: 'all', label: '全部级别' },
    { value: 'critical', label: '严重' },
    { value: 'high', label: '高风险' },
    { value: 'medium', label: '中风险' },
    { value: 'low', label: '低风险' },
  ];

  const handleStatusChange = (value: string) => {
    if (value === 'all') {
      setFilters({ ...filters, status: undefined });
    } else {
      setFilters({ ...filters, status: value as 'active' | 'acknowledged' | 'resolved' | 'dismissed' });
    }
  };

  const handleLevelChange = (value: string) => {
    if (value === 'all') {
      setFilters({ ...filters, risk_level: undefined });
    } else {
      setFilters({ ...filters, risk_level: value as 'low' | 'medium' | 'high' | 'critical' });
    }
  };

  return (
    <PageShell
      title="风险控制"
      subtitle="风险预警与处理"
      primaryAction={{
        label: '刷新',
        icon: RefreshCw,
        onClick: () => console.log('Refresh alerts'),
      }}
      filterOptions={[
        {
          key: 'status',
          label: '状态',
          options: statusOptions,
          value: filters.status?.toString() || 'all',
          onChange: handleStatusChange,
        },
        {
          key: 'level',
          label: '风险级别',
          options: levelOptions,
          value: filters.risk_level?.toString() || 'all',
          onChange: handleLevelChange,
        },
      ]}
      kpiSection={<RiskControlKpiRow stats={stats} />}
    >
      <RiskAlertDataTable
        alerts={alerts}
        loading={loading}
      />
    </PageShell>
  );
}

export default RiskControlPageShell;
