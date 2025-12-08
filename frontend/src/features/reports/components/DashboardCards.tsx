/**
 * DashboardCards Component
 *
 * Display key metrics from dashboard summary
 */

'use client';

import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  Wallet,
  BarChart2,
  Clock,
  AlertTriangle,
  Building,
} from 'lucide-react';
import type { DashboardSummary } from '../types';

interface DashboardCardsProps {
  data: DashboardSummary;
  loading?: boolean;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: number | null;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
  loading?: boolean;
}

function MetricCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  color = 'blue',
  loading = false,
}: MetricCardProps) {
  const colorStyles = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    red: 'bg-red-50 text-red-600',
    purple: 'bg-purple-50 text-purple-600',
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="h-8 bg-gray-200 rounded w-3/4 mb-2"></div>
        <div className="h-3 bg-gray-200 rounded w-1/3"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-gray-500">{title}</span>
        <div className={`p-2 rounded-lg ${colorStyles[color]}`}>{icon}</div>
      </div>
      <div className="flex items-end justify-between">
        <div>
          <div className="text-2xl font-bold text-gray-900">{value}</div>
          {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
        </div>
        {trend !== null && trend !== undefined && (
          <div
            className={`flex items-center text-sm ${
              trend >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {trend >= 0 ? (
              <TrendingUp className="h-4 w-4 mr-1" />
            ) : (
              <TrendingDown className="h-4 w-4 mr-1" />
            )}
            <span>{Math.abs(trend).toFixed(1)}%</span>
          </div>
        )}
      </div>
    </div>
  );
}

export function DashboardCards({ data, loading = false }: DashboardCardsProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('zh-CN').format(value);
  };

  return (
    <div className="space-y-6">
      {/* Today's Metrics */}
      <div>
        <h3 className="text-sm font-medium text-gray-500 mb-3">今日数据</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MetricCard
            title="今日消耗"
            value={formatCurrency(data.today_spend)}
            icon={<DollarSign className="h-5 w-5" />}
            color="blue"
            loading={loading}
          />
          <MetricCard
            title="今日线索"
            value={formatNumber(data.today_leads)}
            icon={<Users className="h-5 w-5" />}
            color="green"
            loading={loading}
          />
          <MetricCard
            title="今日充值"
            value={formatCurrency(data.today_topup)}
            icon={<Wallet className="h-5 w-5" />}
            color="purple"
            loading={loading}
          />
        </div>
      </div>

      {/* Month's Metrics */}
      <div>
        <h3 className="text-sm font-medium text-gray-500 mb-3">本月数据</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <MetricCard
            title="本月消耗"
            value={formatCurrency(data.month_spend)}
            icon={<DollarSign className="h-5 w-5" />}
            color="blue"
            loading={loading}
          />
          <MetricCard
            title="本月线索"
            value={formatNumber(data.month_leads)}
            icon={<Users className="h-5 w-5" />}
            color="green"
            loading={loading}
          />
          <MetricCard
            title="本月充值"
            value={formatCurrency(data.month_topup)}
            icon={<Wallet className="h-5 w-5" />}
            color="purple"
            loading={loading}
          />
          <MetricCard
            title="本月利润"
            value={formatCurrency(data.month_profit)}
            icon={<BarChart2 className="h-5 w-5" />}
            color={data.month_profit >= 0 ? 'green' : 'red'}
            loading={loading}
          />
        </div>
      </div>

      {/* Account & Project Stats */}
      <div>
        <h3 className="text-sm font-medium text-gray-500 mb-3">账户与项目</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <MetricCard
            title="总账户"
            value={formatNumber(data.total_accounts)}
            subtitle={`活跃: ${data.active_accounts}`}
            icon={<Building className="h-5 w-5" />}
            color="blue"
            loading={loading}
          />
          <MetricCard
            title="低余额账户"
            value={formatNumber(data.low_balance_accounts)}
            subtitle="余额 < ¥1,000"
            icon={<AlertTriangle className="h-5 w-5" />}
            color={data.low_balance_accounts > 5 ? 'red' : 'yellow'}
            loading={loading}
          />
          <MetricCard
            title="总项目"
            value={formatNumber(data.total_projects)}
            subtitle={`活跃: ${data.active_projects}`}
            icon={<Building className="h-5 w-5" />}
            color="purple"
            loading={loading}
          />
          <div className="bg-white rounded-lg shadow p-6">
            <h4 className="text-sm font-medium text-gray-500 mb-3">待办事项</h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">待审批充值</span>
                <span className="font-medium text-orange-600">
                  {data.pending_topups}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">待对账批次</span>
                <span className="font-medium text-orange-600">
                  {data.pending_reconciliations}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">待提交日报</span>
                <span className="font-medium text-orange-600">
                  {data.pending_reports}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DashboardCards;
