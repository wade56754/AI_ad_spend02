/**
 * ReportsPage Component
 *
 * Main reports dashboard page
 * SoT 对齐: backend/routers/reports.py v2.0
 */

'use client';

import React from 'react';
import {
  BarChart2,
  RefreshCw,
  Calendar,
  TrendingUp,
  DollarSign,
  Users,
  Wallet,
  FileText,
  Download,
} from 'lucide-react';
import { LoadingSpinner } from '@/modules/shared/components/feedback/LoadingSpinner';
import { ErrorDisplay } from '@/modules/shared/components/feedback/ErrorDisplay';
import {
  useDashboard,
  usePerformanceReport,
  useProfitReport,
} from '../hooks';
import { TrendMetric } from '../types';
import { DashboardCards } from './DashboardCards';
import { TrendChart } from './TrendChart';

type ReportTab = 'dashboard' | 'performance' | 'profit' | 'reconciliation' | 'financial';

export function ReportsPage() {
  // State
  const [activeTab, setActiveTab] = React.useState<ReportTab>('dashboard');
  const [dateRange, setDateRange] = React.useState<{
    start_date?: string;
    end_date?: string;
  }>({});

  // Dashboard query
  const {
    data: dashboardData,
    isLoading: dashboardLoading,
    isError: dashboardError,
    error: dashboardErrorObj,
    refetch: refetchDashboard,
  } = useDashboard();

  // Performance report query
  const {
    data: performanceData,
    isLoading: performanceLoading,
    refetch: refetchPerformance,
  } = usePerformanceReport(dateRange, {
    enabled: activeTab === 'performance',
  });

  // Profit report query
  const {
    data: profitData,
    isLoading: profitLoading,
    refetch: refetchProfit,
  } = useProfitReport(dateRange, {
    enabled: activeTab === 'profit',
  });

  // Handlers
  const handleRefresh = () => {
    switch (activeTab) {
      case 'dashboard':
        refetchDashboard();
        break;
      case 'performance':
        refetchPerformance();
        break;
      case 'profit':
        refetchProfit();
        break;
    }
  };

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setDateRange((prev) => ({ ...prev, [name]: value || undefined }));
  };

  const handleClearFilters = () => {
    setDateRange({});
  };

  const formatCurrency = (value: number | string) => {
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(numValue);
  };

  const tabs = [
    { id: 'dashboard', label: '仪表盘', icon: BarChart2 },
    { id: 'performance', label: '效果报表', icon: TrendingUp },
    { id: 'profit', label: '利润报表', icon: DollarSign },
  ] as const;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <BarChart2 className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">报表中心</h1>
                <p className="text-sm text-gray-500">
                  查看仪表盘、效果报表、利润报表
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleRefresh}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
              >
                <RefreshCw className="h-4 w-4" />
                刷新
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-4" aria-label="Tabs">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-4 text-sm font-medium border-b-2 transition-colors ${
                    isActive
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Filters (for non-dashboard tabs) */}
      {activeTab !== 'dashboard' && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-gray-400" />
                <input
                  type="date"
                  name="start_date"
                  value={dateRange.start_date || ''}
                  onChange={handleDateChange}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <span className="text-gray-400">-</span>
                <input
                  type="date"
                  name="end_date"
                  value={dateRange.end_date || ''}
                  onChange={handleDateChange}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
      )}

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <>
            {dashboardError ? (
              <ErrorDisplay error={dashboardErrorObj} onRetry={refetchDashboard} />
            ) : dashboardData ? (
              <div className="space-y-6">
                <DashboardCards data={dashboardData} loading={dashboardLoading} />

                {/* Trend Charts */}
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-3">
                    近7天趋势
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <TrendChart
                      data={dashboardData.spend_trend}
                      title="消耗趋势"
                      color="blue"
                      formatValue={formatCurrency}
                      loading={dashboardLoading}
                    />
                    <TrendChart
                      data={dashboardData.leads_trend}
                      title="线索趋势"
                      color="green"
                      formatValue={(v) => v.toLocaleString()}
                      loading={dashboardLoading}
                    />
                  </div>
                </div>
              </div>
            ) : dashboardLoading ? (
              <div className="flex items-center justify-center py-12">
                <LoadingSpinner />
              </div>
            ) : null}
          </>
        )}

        {/* Performance Tab */}
        {activeTab === 'performance' && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">效果报表</h3>
              {performanceData?.meta && (
                <span className="text-sm text-gray-500">
                  {performanceData.meta.start_date} ~ {performanceData.meta.end_date}
                </span>
              )}
            </div>

            {performanceLoading ? (
              <div className="flex items-center justify-center py-12">
                <LoadingSpinner />
              </div>
            ) : performanceData ? (
              <>
                {/* Summary */}
                <div className="px-6 py-4 bg-gray-50 border-b grid grid-cols-5 gap-4">
                  <div>
                    <div className="text-sm text-gray-500">总消耗</div>
                    <div className="text-lg font-bold text-gray-900">
                      {formatCurrency(parseFloat(performanceData.summary.total_spend))}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">总线索</div>
                    <div className="text-lg font-bold text-gray-900">
                      {performanceData.summary.total_leads.toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">平均CPA</div>
                    <div className="text-lg font-bold text-gray-900">
                      {performanceData.summary.avg_cpa
                        ? formatCurrency(parseFloat(performanceData.summary.avg_cpa))
                        : '-'}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">项目数</div>
                    <div className="text-lg font-bold text-gray-900">
                      {performanceData.summary.project_count}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">渠道数</div>
                    <div className="text-lg font-bold text-gray-900">
                      {performanceData.summary.channel_count}
                    </div>
                  </div>
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          项目
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          渠道
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          消耗
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          线索
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          CPA
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {performanceData.items.map((item, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm font-medium text-gray-900">
                              {item.project_name || '-'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-gray-500">
                              {item.channel_name || '-'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right">
                            <span className="text-sm font-medium text-gray-900">
                              {formatCurrency(item.total_spend)}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right">
                            <span className="text-sm text-gray-900">
                              {item.total_leads.toLocaleString()}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right">
                            <span className="text-sm text-gray-900">
                              {item.cpa ? formatCurrency(item.cpa) : '-'}
                            </span>
                          </td>
                        </tr>
                      ))}
                      {performanceData.items.length === 0 && (
                        <tr>
                          <td
                            colSpan={5}
                            className="px-6 py-12 text-center text-gray-500"
                          >
                            暂无数据
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </>
            ) : null}
          </div>
        )}

        {/* Profit Tab */}
        {activeTab === 'profit' && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">利润报表</h3>
              {profitData?.meta && (
                <span className="text-sm text-gray-500">
                  {profitData.meta.start_date} ~ {profitData.meta.end_date}
                </span>
              )}
            </div>

            {profitLoading ? (
              <div className="flex items-center justify-center py-12">
                <LoadingSpinner />
              </div>
            ) : profitData ? (
              <>
                {/* Summary */}
                <div className="px-6 py-4 bg-gray-50 border-b grid grid-cols-5 gap-4">
                  <div>
                    <div className="text-sm text-gray-500">总收入</div>
                    <div className="text-lg font-bold text-green-600">
                      {formatCurrency(parseFloat(profitData.summary.total_revenue))}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">总成本</div>
                    <div className="text-lg font-bold text-red-600">
                      {formatCurrency(parseFloat(profitData.summary.total_cost))}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">总利润</div>
                    <div
                      className={`text-lg font-bold ${
                        parseFloat(profitData.summary.total_profit) >= 0
                          ? 'text-green-600'
                          : 'text-red-600'
                      }`}
                    >
                      {formatCurrency(parseFloat(profitData.summary.total_profit))}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">利润率</div>
                    <div
                      className={`text-lg font-bold ${
                        (profitData.summary.profit_rate || 0) >= 0
                          ? 'text-green-600'
                          : 'text-red-600'
                      }`}
                    >
                      {profitData.summary.profit_rate
                        ? `${profitData.summary.profit_rate.toFixed(1)}%`
                        : '-'}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">项目数</div>
                    <div className="text-lg font-bold text-gray-900">
                      {profitData.summary.project_count}
                    </div>
                  </div>
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          项目
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          收入
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          成本
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          利润
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                          利润率
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {profitData.items.map((item, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm font-medium text-gray-900">
                              {item.project_name || '-'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right">
                            <span className="text-sm font-medium text-green-600">
                              {formatCurrency(item.revenue)}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right">
                            <span className="text-sm font-medium text-red-600">
                              {formatCurrency(item.cost)}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right">
                            <span
                              className={`text-sm font-medium ${
                                item.profit >= 0 ? 'text-green-600' : 'text-red-600'
                              }`}
                            >
                              {formatCurrency(item.profit)}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right">
                            <span
                              className={`text-sm ${
                                (item.profit_rate || 0) >= 0
                                  ? 'text-green-600'
                                  : 'text-red-600'
                              }`}
                            >
                              {item.profit_rate
                                ? `${item.profit_rate.toFixed(1)}%`
                                : '-'}
                            </span>
                          </td>
                        </tr>
                      ))}
                      {profitData.items.length === 0 && (
                        <tr>
                          <td
                            colSpan={5}
                            className="px-6 py-12 text-center text-gray-500"
                          >
                            暂无数据
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}

export default ReportsPage;
