/**
 * Topups Stats Overview Component
 *
 * Displays statistics cards for topup requests
 * Extracted from TopupsPage.tsx for better maintainability
 */

'use client';

import { Card, CardContent } from '@/components/ui/card';
import {
  ClipboardCheck,
  Wallet,
  TrendingUp,
  DollarSign,
  CheckCircle,
  FileText,
} from 'lucide-react';
import { TopupStatsCard } from './TopupStatusBadge';
import type { TopupStatus } from '../types';

interface TopupsStatsOverviewProps {
  stats: {
    by_status: Record<TopupStatus, number>;
    total_amount: number;
    pending_count: number;
  } | undefined;
  isLoading: boolean;
  onFilterByStatus: (status: TopupStatus) => void;
}

export function TopupsStatsOverview({
  stats,
  isLoading,
  onFilterByStatus,
}: TopupsStatsOverviewProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {[...Array(6)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-4">
              <div className="h-4 w-16 bg-muted rounded mb-2" />
              <div className="h-8 w-24 bg-muted rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const pendingReviewCount = stats?.by_status?.pending_review ?? 0;
  const financeApproveCount = stats?.by_status?.finance_approve ?? 0;
  const totalCount = stats
    ? Object.values(stats.by_status || {}).reduce((a, b) => a + b, 0)
    : 0;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <TopupStatsCard
        title="待数据复核"
        value={pendingReviewCount}
        icon={ClipboardCheck}
        variant="warning"
        onClick={() => onFilterByStatus('pending_review')}
      />
      <TopupStatsCard
        title="待财务终审"
        value={financeApproveCount}
        icon={Wallet}
        variant="info"
        onClick={() => onFilterByStatus('finance_approve')}
      />
      <TopupStatsCard
        title="待处理"
        value={stats?.pending_count ?? 0}
        icon={TrendingUp}
        variant="warning"
      />
      <TopupStatsCard
        title="总充值额"
        value={stats ? `¥${((stats.total_amount || 0) / 100).toLocaleString()}` : '¥0'}
        icon={DollarSign}
        variant="success"
      />
      <TopupStatsCard
        title="总申请数"
        value={totalCount}
        icon={CheckCircle}
        variant="default"
      />
      <TopupStatsCard
        title="已完成"
        value={stats?.by_status?.completed ?? 0}
        icon={FileText}
        variant="success"
      />
    </div>
  );
}

export default TopupsStatsOverview;
