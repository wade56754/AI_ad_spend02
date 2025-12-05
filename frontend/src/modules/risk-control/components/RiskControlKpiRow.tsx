/**
 * RiskControlKpiRow - 风险控制 KPI 指标
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { AlertTriangle, AlertCircle, CheckCircle, Shield } from 'lucide-react';
import type { RiskLevel, AlertStatus } from '../types';

interface RiskControlKpiRowProps {
  stats: {
    total: number;
    byLevel: Record<RiskLevel, number>;
    byStatus: Record<AlertStatus, number>;
    activeCount: number;
  };
}

export function RiskControlKpiRow({ stats }: RiskControlKpiRowProps) {
  const kpis = [
    {
      label: '严重风险',
      value: stats.byLevel.critical.toString(),
      icon: AlertTriangle,
      iconBg: 'bg-danger/10',
      iconColor: 'text-danger',
    },
    {
      label: '高风险',
      value: stats.byLevel.high.toString(),
      icon: AlertCircle,
      iconBg: 'bg-warning/10',
      iconColor: 'text-warning',
    },
    {
      label: '待处理',
      value: stats.activeCount.toString(),
      icon: Shield,
      iconBg: 'bg-info/10',
      iconColor: 'text-info',
    },
    {
      label: '已解决',
      value: stats.byStatus.resolved.toString(),
      icon: CheckCircle,
      iconBg: 'bg-success/10',
      iconColor: 'text-success',
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {kpis.map((kpi) => (
        <div
          key={kpi.label}
          className="flex items-center gap-3 rounded-lg bg-card-bg p-4 border border-border-default"
        >
          <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${kpi.iconBg}`}>
            <kpi.icon className={`h-5 w-5 ${kpi.iconColor}`} />
          </div>
          <div>
            <p className="text-sm text-text-muted">{kpi.label}</p>
            <p className="text-lg font-semibold text-text-strong">{kpi.value}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default RiskControlKpiRow;
