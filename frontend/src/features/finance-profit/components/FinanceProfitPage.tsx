/**
 * FinanceProfitPage Component
 *
 * SoT: docs/10.module-specs/A3-project-pnl.md §3.1 页面布局
 * SoT: MASTER.md v4.4 §6.5 页面 3 项目盈亏字段集
 * SoT: BUSINESS_RULES.md v3.2: 利润计算公式
 *   - revenue = conversions_final × unit_price
 *   - cost = real_spend + fee
 *   - profit = revenue - cost
 *   - profit_margin = profit / revenue × 100
 *
 * 一句话定义: 让老板/项目负责人快速了解"每个项目赚了多少钱？谁在亏钱？"
 *
 * @module features/finance-profit/components
 */

'use client';

import React from 'react';
import { DollarSign, RefreshCw, Calendar } from 'lucide-react';
import { ErrorDisplay } from '@/modules/shared/components/feedback/ErrorDisplay';
import {
  useProfitOverview,
  useProfitByProject,
  useProfitByAccount,
  useProfitByChannel,
  useProfitTrend,
  useRefreshProfit,
} from '../hooks';
import {
  ProfitDimension,
  TrendGranularity,
  type ProfitByDimensionParams,
  type ProfitTrendParams,
} from '../types';
import { ProfitOverviewCard } from './ProfitOverviewCard';
import { ProfitTrendChart } from './ProfitTrendChart';
import { ProfitTable } from './ProfitTable';

export function FinanceProfitPage() {
  // State
  const [dimension, setDimension] = React.useState<ProfitDimension>(ProfitDimension.PROJECT);
  const [granularity, setGranularity] = React.useState<TrendGranularity>(TrendGranularity.DAILY);
  const [dateRange, setDateRange] = React.useState<{
    start_date?: string;
    end_date?: string;
  }>({});

  // Build params
  const dimensionParams: ProfitByDimensionParams = {
    ...dateRange,
    limit: 20,
  };

  const trendParams: ProfitTrendParams = {
    ...dateRange,
    granularity,
  };

  // Queries - SoT: A3-project-pnl.md §5 API 接口
  const {
    data: overviewData,
    isLoading: overviewLoading,
    isError: overviewError,
    error: overviewErrorObj,
  } = useProfitOverview();

  const {
    data: projectData,
    isLoading: projectLoading,
  } = useProfitByProject(dimensionParams, {
    enabled: dimension === ProfitDimension.PROJECT,
  });

  const {
    data: accountData,
    isLoading: accountLoading,
  } = useProfitByAccount(dimensionParams, {
    enabled: dimension === ProfitDimension.ACCOUNT,
  });

  const {
    data: channelData,
    isLoading: channelLoading,
  } = useProfitByChannel(dimensionParams, {
    enabled: dimension === ProfitDimension.CHANNEL,
  });

  const {
    data: trendData,
    isLoading: trendLoading,
  } = useProfitTrend(trendParams);

  // 刷新 hook - SoT: A3-project-pnl.md §2.4 数据刷新策略
  const { refreshAll } = useRefreshProfit();

  // Get current dimension data
  const getCurrentDimensionData = () => {
    switch (dimension) {
      case ProfitDimension.PROJECT:
        return {
          items: projectData?.items || [],
          totalProfit: projectData?.total_profit || 0,
          overallMargin: projectData?.overall_profit_margin || 0,
          loading: projectLoading,
        };
      case ProfitDimension.ACCOUNT:
        return {
          items: accountData?.items || [],
          totalProfit: accountData?.total_profit || 0,
          overallMargin: accountData?.overall_profit_margin || 0,
          loading: accountLoading,
        };
      case ProfitDimension.CHANNEL:
        return {
          items: channelData?.items || [],
          totalProfit: channelData?.total_profit || 0,
          overallMargin: channelData?.overall_profit_margin || 0,
          loading: channelLoading,
        };
      default:
        return {
          items: [],
          totalProfit: 0,
          overallMargin: 0,
          loading: false,
        };
    }
  };

  const currentData = getCurrentDimensionData();

  // Handlers
  const handleRefreshAll = () => {
    // 使用 refreshAll 刷新所有利润数据
    // SoT: A3-project-pnl.md §2.4 数据刷新策略
    refreshAll();
  };

  const handleDateRangeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setDateRange((prev) => ({ ...prev, [name]: value || undefined }));
  };

  const handleClearFilters = () => {
    setDateRange({});
  };

  return (
    <div className="min-h-screen bg-gray-50" data-testid="pnl-page">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <DollarSign className="h-8 w-8 text-green-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">项目盈亏</h1>
                <p className="text-sm text-gray-500">
                  利润 = 收入 - 成本 | 收入 = 粉数 × 单价 | 成本 = 消耗 + 服务费
                </p>
              </div>
            </div>
            <button
              onClick={handleRefreshAll}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
            >
              <RefreshCw className="h-4 w-4" />
              刷新
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="bg-white rounded-lg shadow p-4" data-testid="pnl-filters">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2" data-testid="date-filter">
              <Calendar className="h-4 w-4 text-gray-400" />
              <input
                type="date"
                name="start_date"
                value={dateRange.start_date || ''}
                onChange={handleDateRangeChange}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="开始日期"
              />
              <span className="text-gray-400">-</span>
              <input
                type="date"
                name="end_date"
                value={dateRange.end_date || ''}
                onChange={handleDateRangeChange}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="结束日期"
              />
            </div>

            {(dateRange.start_date || dateRange.end_date) && (
              <button
                onClick={handleClearFilters}
                className="px-3 py-2 text-sm text-gray-600 hover:text-gray-900"
              >
                清除筛选
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8 space-y-6" data-testid="pnl-summary">
        {/* Overview Cards - SoT: A3-project-pnl.md §3.2 组件清单 */}
        {overviewError ? (
          <ErrorDisplay error={overviewErrorObj} onRetry={refreshAll} />
        ) : overviewData ? (
          <ProfitOverviewCard data={overviewData} loading={overviewLoading} />
        ) : overviewLoading ? (
          <ProfitOverviewCard
            data={{
              today_revenue: 0,
              today_cost: 0,
              today_profit: 0,
              today_profit_margin: 0,
              week_revenue: 0,
              week_cost: 0,
              week_profit: 0,
              week_profit_margin: 0,
              month_revenue: 0,
              month_cost: 0,
              month_profit: 0,
              month_profit_margin: 0,
              profit_change_from_yesterday: null,
              profit_change_from_last_week: null,
              profit_change_from_last_month: null,
              top_profit_projects: [],
            }}
            loading={true}
          />
        ) : null}

        {/* Trend Chart */}
        <ProfitTrendChart
          data={trendData}
          loading={trendLoading}
          granularity={granularity}
          onGranularityChange={setGranularity}
        />

        {/* Top Projects (from overview) */}
        {overviewData?.top_profit_projects && overviewData.top_profit_projects.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">TOP 利润项目</h3>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              {overviewData.top_profit_projects.slice(0, 5).map((project, index) => (
                <div
                  key={project.project_id}
                  className="p-4 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-white text-sm font-bold ${
                        index === 0
                          ? 'bg-yellow-500'
                          : index === 1
                          ? 'bg-gray-400'
                          : index === 2
                          ? 'bg-amber-600'
                          : 'bg-gray-300'
                      }`}
                    >
                      {index + 1}
                    </span>
                    <span className="text-sm font-medium text-gray-900 truncate">
                      {project.project_name}
                    </span>
                  </div>
                  <div className="text-lg font-bold text-green-600">
                    ¥{project.profit.toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Profit Table by Dimension */}
        <div data-testid="pnl-table">
          <ProfitTable
            data={currentData.items}
            dimension={dimension}
            loading={currentData.loading}
            onDimensionChange={setDimension}
            totalProfit={currentData.totalProfit}
            overallMargin={currentData.overallMargin}
          />
        </div>
      </div>
    </div>
  );
}

export default FinanceProfitPage;
