/**
 * FundOverviewPage Component
 *
 * SoT: docs/10.module-specs/A2-fund-overview.md
 * SoT: MASTER.md v4.4 §4.5.5 资金口径定义
 * SoT: MASTER.md v4.4 §6.5 页面 2 资金总览字段集
 *
 * 一句话定义: 让老板在 5 秒内掌握"钱在哪里？能收回多少？"
 *
 * @module features/fund-overview/components
 */

'use client';

import React, { useState, useMemo } from 'react';
import {
  CreditCard,
  TrendingDown,
  Wallet,
  Receipt,
  Lock,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { StatCard } from '@/features/dashboard/components/StatCard';
import {
  useFundOverview,
  useFundByProject,
  useFundByChannel,
  useRefreshFundOverview,
} from '../hooks';
import type {
  FundOverview,
  FundDistributionDimension,
} from '../types';
import { FUND_STAT_CARDS_CONFIG } from '../types';
import { FundDistributionTable } from './FundDistributionTable';

// ========== 辅助函数 ==========

/**
 * 格式化金额显示（单位：万）
 */
function formatCurrency(value: number): string {
  if (value === 0) return '¥0';
  const wan = value / 10000;
  if (Math.abs(wan) >= 1) {
    return `¥${wan.toFixed(1)} 万`;
  }
  return `¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * 格式化百分比
 */
function formatPercent(value: number | null): string {
  if (value === null || value === undefined) return '--';
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
}

// Note: Mock 数据已移至 services/fundApi.ts

// ========== 组件 ==========

/**
 * 指标卡片加载骨架屏
 */
function StatCardSkeleton() {
  return (
    <Card className="rounded-xl" data-testid="loading-skeleton">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <Skeleton className="h-12 w-12 rounded-lg" />
          <Skeleton className="h-6 w-16 rounded-full" />
        </div>
        <Skeleton className="h-9 w-32 mb-2" />
        <Skeleton className="h-4 w-20 mb-3" />
        <div className="pt-3 border-t">
          <Skeleton className="h-3 w-full" />
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * 资金预警横幅
 */
function FundAlertBanner({ occupyRate }: { occupyRate: number }) {
  if (occupyRate < 80) return null;

  const severity = occupyRate >= 90 ? 'destructive' : 'default';
  const message = occupyRate >= 90
    ? `资金占用率已达 ${occupyRate.toFixed(1)}%，请尽快催收回款！`
    : `资金占用率 ${occupyRate.toFixed(1)}%，建议关注回款进度`;

  return (
    <Alert variant={severity} className="mb-6">
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle>资金预警</AlertTitle>
      <AlertDescription>{message}</AlertDescription>
    </Alert>
  );
}

/**
 * 资金总览主页面
 * SoT: A2-fund-overview.md §3.1 页面布局
 */
export function FundOverviewPage() {
  // ============ 状态管理 ============
  const [dimension, setDimension] = useState<FundDistributionDimension>('project');

  // ============ 数据查询 (TanStack Query) ============
  // SoT: A2-fund-overview.md §2.4 数据刷新策略

  const {
    data: overview,
    isLoading: overviewLoading,
    isFetching: overviewFetching,
  } = useFundOverview();

  const {
    data: projectData,
    isLoading: projectLoading,
  } = useFundByProject({ page: 1, page_size: 20, sort_by: 'topup', order: 'desc' });

  const {
    data: channelData,
    isLoading: channelLoading,
  } = useFundByChannel({ page: 1, page_size: 20, sort_by: 'topup', order: 'desc' });

  const { refreshAll } = useRefreshFundOverview();

  // 提取数据 (API 服务已包含 mock 回退)
  const overviewData: FundOverview = overview || {
    total_topup: 0,
    total_spend: 0,
    current_balance: 0,
    total_receivable: 0,
    total_received: 0,
    fund_occupied: 0,
    topup_change: null,
    spend_change: null,
    balance_change: null,
    occupy_rate: 0,
    pending_receivable_count: 0,
  };
  const projectItems = projectData?.data?.items || [];
  const channelItems = channelData?.data?.items || [];

  // 是否正在刷新 (非初次加载)
  const isRefreshing = overviewFetching && !overviewLoading;

  // 刷新处理
  const handleRefresh = () => {
    refreshAll();
  };

  // 指标卡片图标映射
  const iconMap: Record<string, React.ReactNode> = {
    'credit-card': <CreditCard className="h-6 w-6" />,
    'trending-down': <TrendingDown className="h-6 w-6" />,
    wallet: <Wallet className="h-6 w-6" />,
    receipt: <Receipt className="h-6 w-6" />,
    lock: <Lock className="h-6 w-6" />,
  };

  // 获取指标值
  const getStatValue = (key: string): number => {
    const keyMap: Record<string, keyof FundOverview> = {
      total_topup: 'total_topup',
      total_spend: 'total_spend',
      current_balance: 'current_balance',
      total_receivable: 'total_receivable',
      fund_occupied: 'fund_occupied',
    };
    const mappedKey = keyMap[key];
    if (mappedKey && typeof overviewData[mappedKey] === 'number') {
      return overviewData[mappedKey] as number;
    }
    return 0;
  };

  // 获取变化值
  const getChangeValue = (key: string): number | null => {
    const changeMap: Record<string, keyof FundOverview> = {
      total_topup: 'topup_change',
      total_spend: 'spend_change',
      current_balance: 'balance_change',
    };
    const mappedKey = changeMap[key];
    if (mappedKey) {
      return overviewData[mappedKey] as number | null;
    }
    return null;
  };

  // 获取副信息
  const getSubInfo = (key: string): string | undefined => {
    if (key === 'total_receivable') {
      return `${overviewData.pending_receivable_count} 笔待收`;
    }
    if (key === 'fund_occupied') {
      return `占用率 ${overviewData.occupy_rate.toFixed(1)}%`;
    }
    return undefined;
  };

  return (
    <div className="space-y-6" data-testid="fund-overview-page">
      {/* 页面头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">资金总览</h1>
          <p className="text-sm text-muted-foreground mt-1">
            一眼看清公司资金全貌，掌握资金流向
          </p>
        </div>
        <Button
          variant="outline"
          onClick={handleRefresh}
          disabled={isRefreshing}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
          刷新
        </Button>
      </div>

      {/* 资金预警 - SoT: A2-fund-overview.md §3.1 AlertBanner */}
      <FundAlertBanner occupyRate={overviewData.occupy_rate} />

      {/* 核心资金指标 - 5 个卡片 */}
      <section data-testid="fund-summary">
        <h2 className="text-lg font-semibold text-foreground mb-4">核心指标</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {overviewLoading ? (
            <>
              <StatCardSkeleton />
              <StatCardSkeleton />
              <StatCardSkeleton />
              <StatCardSkeleton />
              <StatCardSkeleton />
            </>
          ) : (
            FUND_STAT_CARDS_CONFIG.map((config) => {
              // 映射测试 ID
              const testIdMap: Record<string, string> = {
                total_topup: 'summary-topup',
                total_spend: 'summary-spend',
                current_balance: 'summary-balance',
                total_receivable: 'summary-receivable',
                fund_occupied: 'summary-occupied',
              };
              return (
                <StatCard
                  key={config.key}
                  title={config.title}
                  value={formatCurrency(getStatValue(config.key))}
                  change={getChangeValue(config.key)}
                  target={getSubInfo(config.key)}
                  icon={iconMap[config.icon]}
                  color={config.color}
                  testId={testIdMap[config.key] || `fund-stat-${config.key}`}
                />
              );
            })
          )}
        </div>
      </section>

      {/* 资金分布 - 按项目/按渠道 */}
      <section data-testid="fund-transactions">
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">资金分布</CardTitle>
              <Tabs value={dimension} onValueChange={(v) => setDimension(v as FundDistributionDimension)}>
                <TabsList>
                  <TabsTrigger value="project">按项目</TabsTrigger>
                  <TabsTrigger value="channel">按渠道</TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          </CardHeader>
          <CardContent>
            {dimension === 'project' ? (
              <FundDistributionTable
                dimension="project"
                data={projectItems}
                loading={projectLoading}
              />
            ) : (
              <FundDistributionTable
                dimension="channel"
                data={channelItems}
                loading={channelLoading}
              />
            )}
          </CardContent>
        </Card>
      </section>

      {/* 底部区域：应收明细 + 回款记录 (Phase 2 实现) */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 应收明细 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">应收明细</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-muted-foreground">
              <Receipt className="h-12 w-12 mx-auto mb-2 opacity-30" />
              <p>应收款明细功能即将上线</p>
            </div>
          </CardContent>
        </Card>

        {/* 回款记录 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">回款记录</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-muted-foreground">
              <Wallet className="h-12 w-12 mx-auto mb-2 opacity-30" />
              <p>回款记录功能即将上线</p>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

export default FundOverviewPage;
