/**
 * Ad Spend Page Component
 *
 * SoT: docs/10.module-specs/C3-spend-detail.md §3.1 页面布局
 * SoT: MASTER.md v4.4 §4.5.7 - 消耗 SoT = ad_spend_daily.spend
 * SoT: API_SOT.md v9.0 (Ad Spend endpoints)
 * CodeBlock: CB-FE-001 (DataTable), CB-FE-002 (StatCard)
 *
 * 一句话定义: 让用户查看"某天/某账户消耗多少？"
 *
 * Author: AI 代码工厂 v2.4
 */

'use client';

import React, { useState } from 'react';
import {
  DollarSign,
  RefreshCw,
  Download,
  BarChart3,
  Users,
  MousePointer,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { StatCard } from '@/features/dashboard/components/StatCard';
import { SpendFilters } from './SpendFilters';
import { SpendTable } from './SpendTable';
import {
  useAdSpendList,
  useAdSpendSummary,
  useExportAdSpend,
  useRefreshAdSpend,
} from '../hooks';
import type { AdSpendListParams } from '../types';

function formatCurrency(value: number): string {
  if (value === 0) return '¥0';
  const wan = value / 10000;
  if (Math.abs(wan) >= 1) {
    return '¥' + wan.toFixed(1) + ' 万';
  }
  return '¥' + value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('zh-CN').format(value);
}

function KpiSkeleton() {
  return (
    <Card className="rounded-xl">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <Skeleton className="h-12 w-12 rounded-lg" />
          <Skeleton className="h-6 w-16 rounded-full" />
        </div>
        <Skeleton className="h-9 w-32 mb-2" />
        <Skeleton className="h-4 w-20" />
      </CardContent>
    </Card>
  );
}

export function AdSpendPage() {
  const [filters, setFilters] = useState<AdSpendListParams>({
    start_date: '',
    end_date: '',
    project_id: undefined,
    channel_id: undefined,
    ad_account_id: undefined,
    page: 1,
    page_size: 20,
  });

  const [aggregateBy, setAggregateBy] = useState<'none' | 'date' | 'project' | 'account'>('none');

  const {
    data: listData,
    isLoading: listLoading,
    error: listError,
    refetch: refetchList,
  } = useAdSpendList(filters);

  const {
    data: summaryData,
    isLoading: summaryLoading,
    error: summaryError,
  } = useAdSpendSummary({
    project_id: filters.project_id,
    start_date: filters.start_date,
    end_date: filters.end_date,
  });

  const exportMutation = useExportAdSpend();
  const { refreshAll } = useRefreshAdSpend();

  const handleFiltersChange = (newFilters: Partial<AdSpendListParams>) => {
    setFilters((prev) => ({ ...prev, ...newFilters, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  const handleRefresh = () => {
    refreshAll();
    refetchList();
  };

  const handleExport = () => {
    exportMutation.mutate(filters);
  };

  const summary = summaryData || listData?.summary;
  const spendChange = 8.5;
  const conversionsChange = 12.3;

  const isLoading = listLoading || summaryLoading;
  const hasError = listError || summaryError;

  return (
    <div className="min-h-screen bg-background" data-testid="spend-page">
      <div className="bg-card border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-950/30 rounded-lg">
                <DollarSign className="h-8 w-8 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-foreground">消耗明细</h1>
                <p className="text-sm text-muted-foreground">
                  查看和分析广告投放消耗数据
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                onClick={handleExport}
                disabled={exportMutation.isPending}
              >
                {exportMutation.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Download className="h-4 w-4 mr-2" />
                )}
                导出
              </Button>
              <Button onClick={handleRefresh} disabled={isLoading}>
                <RefreshCw className={"h-4 w-4 mr-2 " + (isLoading ? 'animate-spin' : '')} />
                刷新
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4" data-testid="spend-filters">
        <SpendFilters
          filters={filters}
          onChange={handleFiltersChange}
          aggregateBy={aggregateBy}
          onAggregateChange={setAggregateBy}
        />
      </div>

      {hasError && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>加载数据失败，请稍后重试。</AlertDescription>
          </Alert>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4" data-testid="spend-stats">
        {summaryLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" data-testid="loading-skeleton">
            <KpiSkeleton />
            <KpiSkeleton />
            <KpiSkeleton />
            <KpiSkeleton />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="总消耗"
              value={formatCurrency(summary?.total_spend || 0)}
              change={spendChange}
              icon={<DollarSign className="h-6 w-6" />}
              color="blue"
              testId="spend-stat-total"
            />
            <StatCard
              title="总粉数"
              value={formatNumber(summary?.total_conversions || 0)}
              change={conversionsChange}
              icon={<Users className="h-6 w-6" />}
              color="green"
              testId="spend-stat-conversions"
            />
            <StatCard
              title="平均CPA"
              value={formatCurrency(summary?.avg_cpa || 0)}
              icon={<BarChart3 className="h-6 w-6" />}
              color="purple"
              testId="spend-stat-cpa"
            />
            <StatCard
              title="平均CTR"
              value={(summary?.avg_ctr || 0).toFixed(2) + '%'}
              icon={<MousePointer className="h-6 w-6" />}
              color="orange"
              testId="spend-stat-ctr"
            />
          </div>
        )}
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 pb-8" data-testid="spend-table">
        <SpendTable
          data={listData?.items || []}
          total={listData?.total || 0}
          page={filters.page || 1}
          pageSize={filters.page_size || 20}
          loading={listLoading}
          onPageChange={handlePageChange}
        />
      </div>
    </div>
  );
}

export default AdSpendPage;
