/**
 * ProfitAnalysisPage - 项目盈亏分析页面
 *
 * 显示项目收入、成本、利润分析，包含项目明细和渠道成本
 *
 * 路由: /finance/profit
 *
 * @module features/finance/components
 */

'use client';

import { useState } from 'react';
import { RefreshCw, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
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

  const {
    data: overviewData,
    isLoading: overviewLoading,
    refetch: refetchOverview,
  } = useProfitOverviewV2({ period });

  const {
    data: projectsData,
    isLoading: projectsLoading,
    refetch: refetchProjects,
  } = useProjectProfitsV2({ period });

  const {
    data: suppliersData,
    isLoading: suppliersLoading,
    refetch: refetchSuppliers,
  } = useSupplierCostsV2({ period });

  const {
    data: trendData,
    isLoading: trendLoading,
  } = useProfitTrendV2({ granularity, period });

  const isLoading = overviewLoading || projectsLoading || suppliersLoading || trendLoading;

  const handleRefresh = () => {
    refetchOverview();
    refetchProjects();
    refetchSuppliers();
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
      ) : overviewData ? (
        <ProfitSummaryCards
          data={{
            summary: overviewData.summary,
            changes: overviewData.changes,
            benchmarks: overviewData.benchmarks,
          }}
          currency={overviewData.currency}
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
      ) : trendData ? (
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
          ) : projectsData ? (
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
      ) : suppliersData ? (
        <SupplierCostTable items={suppliersData.items} summary={suppliersData.summary} />
      ) : null}
    </div>
  );
}
