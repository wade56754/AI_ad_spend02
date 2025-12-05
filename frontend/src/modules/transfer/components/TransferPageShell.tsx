/**
 * TransferPageShell - 死号余额迁移页面容器
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3, TRANSFER_SOT.md v1.0
 */

'use client';

import React from 'react';
import { Plus } from 'lucide-react';
import { PageShell } from '@/modules/shared';
import { useTransfers } from '../hooks';
import { TransferKpiRow } from './TransferKpiRow';
import { TransferDataTable } from './TransferDataTable';

export function TransferPageShell() {
  const { transfers, loading, stats, filters, setFilters } = useTransfers();

  const statusOptions = [
    { value: 'all', label: '全部状态' },
    { value: 'draft', label: '草稿' },
    { value: 'approved', label: '已审批' },
    { value: 'completed', label: '已完成' },
    { value: 'rejected', label: '已拒绝' },
  ];

  const handleStatusChange = (value: string) => {
    if (value === 'all') {
      setFilters({ ...filters, status: undefined });
    } else {
      setFilters({ ...filters, status: value as 'draft' | 'approved' | 'completed' | 'rejected' });
    }
  };

  return (
    <PageShell
      title="余额迁移"
      subtitle="死号余额迁移管理"
      primaryAction={{
        label: '发起迁移',
        icon: Plus,
        onClick: () => console.log('Create transfer'),
      }}
      filterOptions={[
        {
          key: 'status',
          label: '状态',
          options: statusOptions,
          value: filters.status?.toString() || 'all',
          onChange: handleStatusChange,
        },
      ]}
      kpiSection={<TransferKpiRow stats={stats} />}
    >
      <TransferDataTable
        transfers={transfers}
        loading={loading}
      />
    </PageShell>
  );
}

export default TransferPageShell;
