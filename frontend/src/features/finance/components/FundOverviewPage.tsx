/**
 * FundOverviewPage - 资金总览页面
 *
 * 显示公司资金流向全景：收款、支出、应收未收、余额、资金分布
 *
 * 路由: /finance/fund
 *
 * SoT: BR-FIN.md v1.1 §BR-FIN-004 (预收款非收入)
 * 修复: 2026-01-12 刷新逻辑完整化 + 错误状态展示
 *
 * @module features/finance/components
 */

'use client';

import { useState } from 'react';
import { RefreshCw, AlertCircle } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  useFundOverviewV2,
  useReceivablesV2,
  useFundDistributionV2,
} from '../hooks/useFinance';
import { FundSummaryCards, ReceivablesTable, FundDistribution } from './FundOverview';

export function FundOverviewPage() {
  const [period, setPeriod] = useState<string | undefined>(undefined);
  const queryClient = useQueryClient();

  const {
    data: overviewData,
    isLoading: overviewLoading,
    isError: overviewError,
    error: overviewErrorMsg,
  } = useFundOverviewV2({ date: period });

  const {
    data: receivablesData,
    isLoading: receivablesLoading,
    isError: receivablesError,
    error: receivablesErrorMsg,
  } = useReceivablesV2();

  const {
    data: projectDistribution,
    isLoading: projectDistLoading,
    isError: projectDistError,
  } = useFundDistributionV2({ group_by: 'project' });

  const {
    data: supplierDistribution,
    isLoading: supplierDistLoading,
    isError: supplierDistError,
  } = useFundDistributionV2({ group_by: 'supplier' });

  const isLoading = overviewLoading || receivablesLoading || projectDistLoading || supplierDistLoading;
  const hasError = overviewError || receivablesError || projectDistError || supplierDistError;

  // 刷新所有相关查询（最佳实践）
  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['finance', 'fund'] });
  };

  const handleExport = () => {
    // TODO: 实现导出功能
    console.log('Export receivables');
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            💰 资金总览
          </h1>
          <p className="text-muted-foreground">公司资金流向全景</p>
        </div>
        <div className="flex items-center gap-2">
          {/* 月份选择器 - 简化版 */}
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
            {overviewError && '资金概览加载失败。'}
            {receivablesError && '应收账款加载失败。'}
            {projectDistError && '项目分布加载失败。'}
            {supplierDistError && '渠道分布加载失败。'}
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
          <AlertTitle>资金概览加载失败</AlertTitle>
          <AlertDescription>
            {overviewErrorMsg?.message || '请检查网络连接或稍后重试'}
          </AlertDescription>
        </Alert>
      ) : overviewData?.summary ? (
        <FundSummaryCards
          data={{
            summary: overviewData.summary,
            changes: overviewData.changes ?? { income_change_pct: null, expense_change_pct: null, balance_change_pct: null },
          }}
          currency={overviewData.currency ?? 'CNY'}
        />
      ) : null}

      {/* 应收账款表格 */}
      <Card>
        <CardHeader>
          <CardTitle>应收账款</CardTitle>
          <CardDescription>各项目的打款和回款情况</CardDescription>
        </CardHeader>
        <CardContent>
          {receivablesLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : receivablesError ? (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>应收账款加载失败</AlertTitle>
              <AlertDescription>
                {receivablesErrorMsg?.message || '请检查网络连接或稍后重试'}
              </AlertDescription>
            </Alert>
          ) : receivablesData ? (
            <ReceivablesTable
              items={receivablesData.items}
              totals={receivablesData.totals}
              onExport={handleExport}
            />
          ) : null}
        </CardContent>
      </Card>

      {/* 资金分布 */}
      <div className="grid gap-4 md:grid-cols-2">
        {projectDistLoading ? (
          <Card>
            <CardHeader>
              <Skeleton className="h-5 w-32" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-40 w-full" />
            </CardContent>
          </Card>
        ) : projectDistribution ? (
          <FundDistribution
            title="资金分布 (按项目)"
            items={projectDistribution.items}
            total={projectDistribution.total}
          />
        ) : null}

        {supplierDistLoading ? (
          <Card>
            <CardHeader>
              <Skeleton className="h-5 w-32" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-40 w-full" />
            </CardContent>
          </Card>
        ) : supplierDistribution ? (
          <FundDistribution
            title="资金分布 (按渠道)"
            items={supplierDistribution.items}
            total={supplierDistribution.total}
          />
        ) : null}
      </div>
    </div>
  );
}
