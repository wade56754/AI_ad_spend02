/**
 * ReportsPageRefactored Component
 *
 * 报表中心页面 - 重构版本 (使用拆分后的子组件)
 * Route: /reports
 * SoT 对齐: backend/routers/reports.py v2.0
 */

'use client';

import React from 'react';
import { LoadingSpinner } from '@/modules/shared/components/feedback/LoadingSpinner';
import { ErrorDisplay } from '@/modules/shared/components/feedback/ErrorDisplay';
import {
  useDashboard,
  usePerformanceReport,
  useProfitReport,
} from '../hooks';
import { DashboardCards } from './DashboardCards';
import { TrendChart } from './TrendChart';
import { ReportsHeader } from './ReportsHeader';
import { ReportsFilters } from './ReportsFilters';
import { ReportsPerformanceTab } from './ReportsPerformanceTab';
import { ReportsProfitTab } from './ReportsProfitTab';
import { formatCurrency, type ReportTab, type DateRange } from '../utils/reportsHelpers';

export function ReportsPageRefactored() {
  // State
  const [activeTab, setActiveTab] = React.useState<ReportTab>('dashboard');
  const [dateRange, setDateRange] = React.useState<DateRange>({});

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

  return (
    <div className="min-h-screen bg-gray-50" data-testid="reports-page">
      {/* Header + Tabs */}
      <ReportsHeader
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onRefresh={handleRefresh}
      />

      {/* Filters (for non-dashboard tabs) */}
      {activeTab !== 'dashboard' && (
        <ReportsFilters
          dateRange={dateRange}
          onDateChange={handleDateChange}
          onClearFilters={handleClearFilters}
        />
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
          <ReportsPerformanceTab data={performanceData} isLoading={performanceLoading} />
        )}

        {/* Profit Tab */}
        {activeTab === 'profit' && (
          <ReportsProfitTab data={profitData} isLoading={profitLoading} />
        )}
      </div>
    </div>
  );
}

export default ReportsPageRefactored;
