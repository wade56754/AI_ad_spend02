/**
 * ProfitAnalysisPage - 项目盈亏分析页面
 *
 * 显示项目收入、成本、利润分析，包含项目明细和渠道成本
 *
 * 路由: /finance/profit
 *
 * SoT: BR-PROFIT.md v1.3 §BR-PROFIT-001~008 (利润公式)
 * 修复: 2026-01-12 刷新逻辑完整化 + 错误状态展示
 *
 * @module features/finance/components
 */

'use client';

import { useState } from 'react';
import { RefreshCw, Download, AlertCircle } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  useProfitOverviewV2,
  useProjectProfitsV2,
  useSupplierCostsV2,
  useProfitTrendV2,
} from '../hooks/useFinance';
import {
  ProfitSummaryCards,
  ProjectProfitTable,
  SupplierCostTable,
  ProfitTrendChart,
} from './ProfitAnalysis';
import type { TrendGranularity } from '../types/finance.types';

export function ProfitAnalysisPage() {
  const [period, setPeriod] = useState<string | undefined>(undefined);
  const [granularity, setGranularity] = useState<TrendGranularity>('day');
  const queryClient = useQueryClient();

  const {
    data: overviewData,
    isLoading: overviewLoading,
    isError: overviewError,
    error: overviewErrorMsg,
  } = useProfitOverviewV2({ period });

  const {
    data: projectsData,
    isLoading: projectsLoading,
    isError: projectsError,
    error: projectsErrorMsg,
  } = useProjectProfitsV2({ period });

  const {
    data: suppliersData,
    isLoading: suppliersLoading,
    isError: suppliersError,
    error: suppliersErrorMsg,
  } = useSupplierCostsV2({ period });

  const {
    data: trendData,
    isLoading: trendLoading,
    isError: trendError,
    error: trendErrorMsg,
  } = useProfitTrendV2({ granularity, period });

  const isLoading = overviewLoading || projectsLoading || suppliersLoading || trendLoading;
  const hasError = overviewError || projectsError || suppliersError || trendError;

  // 刷新所有相关查询（最佳实践）
  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['finance', 'profit'] });
  };

  const handleExport = () => {
    // TODO: 实现导出功能
    console.log('Export profit data');
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            📊 项目盈亏
          </h1>
          <p className="text-muted-foreground">项目收入、成本、利润分析</p>
        </div>
        <div className="flex items-center gap-2">
          {/* 趋势粒度选择 */}
          <Select value={granularity} onValueChange={(v) => setGranularity(v as TrendGranularity)}>
            <SelectTrigger className="w-[100px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="day">按日</SelectItem>
              <SelectItem value="week">按周</SelectItem>
              <SelectItem value="month">按月</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            导出
          </Button>
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isLoading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>
      </div>

      {/* 错误提示 */}
      {hasError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>数据加载失败</AlertTitle>
          <AlertDescription>
            {overviewError && '盈亏概览加载失败。'}
            {projectsError && '项目利润加载失败。'}
            {suppliersError && '渠道成本加载失败。'}
            {trendError && '趋势数据加载失败。'}
            请检查网络连接或稍后重试。
          </AlertDescription>
        </Alert>
      )}

      {/* 统计卡片 */}
      {overviewLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-20" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-24 mb-2" />
                <Skeleton className="h-3 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : overviewError ? (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>盈亏概览加载失败</AlertTitle>
          <AlertDescription>
            {overviewErrorMsg?.message || '请检查网络连接或稍后重试'}
          </AlertDescription>
        </Alert>
      ) : overviewData?.summary ? (
        <ProfitSummaryCards
          data={{
            summary: overviewData.summary,
            changes: overviewData.changes ?? { revenue_change_pct: null, profit_change_pct: null },
            benchmarks: overviewData.benchmarks ?? { industry_avg_profit_rate: 0.15, company_target_profit_rate: 0.20 },
          }}
          currency={overviewData.currency ?? 'CNY'}
        />
      ) : null}

      {/* 利润趋势图 */}
      {trendLoading ? (
        <Card>
          <CardHeader>
            <Skeleton className="h-5 w-32" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-40 w-full" />
          </CardContent>
        </Card>
      ) : trendError ? (
        <Card>
          <CardHeader>
            <CardTitle>利润趋势</CardTitle>
          </CardHeader>
          <CardContent>
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>趋势数据加载失败</AlertTitle>
              <AlertDescription>
                {trendErrorMsg?.message || '请检查网络连接或稍后重试'}
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      ) : trendData?.series ? (
        <ProfitTrendChart granularity={trendData.granularity} series={trendData.series} />
      ) : null}

      {/* 项目利润明细 */}
      <Card>
        <CardHeader>
          <CardTitle>项目利润明细</CardTitle>
        </CardHeader>
        <CardContent>
          {projectsLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : projectsError ? (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>项目利润加载失败</AlertTitle>
              <AlertDescription>
                {projectsErrorMsg?.message || '请检查网络连接或稍后重试'}
              </AlertDescription>
            </Alert>
          ) : projectsData?.items ? (
            <ProjectProfitTable items={projectsData.items} />
          ) : null}
        </CardContent>
      </Card>

      {/* 渠道成本分析 */}
      {suppliersLoading ? (
        <Card>
          <CardHeader>
            <Skeleton className="h-5 w-32" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-40 w-full" />
          </CardContent>
        </Card>
      ) : suppliersError ? (
        <Card>
          <CardHeader>
            <CardTitle>渠道成本分析</CardTitle>
          </CardHeader>
          <CardContent>
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>渠道成本加载失败</AlertTitle>
              <AlertDescription>
                {suppliersErrorMsg?.message || '请检查网络连接或稍后重试'}
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      ) : suppliersData?.items ? (
        <SupplierCostTable items={suppliersData.items} summary={suppliersData.summary ?? { avg_fee_rate: 0, total_spend: 0, total_fee: 0 }} />
      ) : null}
    </div>
  );
}
