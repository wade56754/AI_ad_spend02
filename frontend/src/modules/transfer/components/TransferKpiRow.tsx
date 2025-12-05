/**
 * TransferKpiRow - 迁移模块 KPI 指标
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { Repeat, Clock, CheckCircle, XCircle } from 'lucide-react';
import type { TransferStatus } from '../types';

interface TransferKpiRowProps {
  stats: {
    total: number;
    byStatus: Record<TransferStatus, number>;
    totalAmount: number;
    pendingAmount: number;
  };
}

export function TransferKpiRow({ stats }: TransferKpiRowProps) {
  const kpis = [
    {
      label: '总迁移数',
      value: stats.total.toString(),
      icon: Repeat,
      iconBg: 'bg-info/10',
      iconColor: 'text-info',
    },
    {
      label: '待处理',
      value: (stats.byStatus.draft + stats.byStatus.approved).toString(),
      icon: Clock,
      iconBg: 'bg-warning/10',
      iconColor: 'text-warning',
    },
    {
      label: '已完成',
      value: stats.byStatus.completed.toString(),
      icon: CheckCircle,
      iconBg: 'bg-success/10',
      iconColor: 'text-success',
    },
    {
      label: '待迁移金额',
      value: `¥${(stats.pendingAmount / 100).toLocaleString()}`,
      icon: XCircle,
      iconBg: 'bg-danger/10',
      iconColor: 'text-danger',
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

export default TransferKpiRow;
