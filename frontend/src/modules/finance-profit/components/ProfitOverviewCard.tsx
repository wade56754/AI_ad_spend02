/**
 * ProfitOverviewCard Component
 *
 * Displays profit overview metrics (today/week/month)
 * SoT 对齐: BUSINESS_RULES.md v3.1
 */

'use client';

import React from 'react';
import { TrendingUp, TrendingDown, DollarSign, Target, Percent } from 'lucide-react';
import type { ProfitOverviewResponse } from '../types';

interface ProfitOverviewCardProps {
  data: ProfitOverviewResponse;
  loading?: boolean;
}

interface MetricCardProps {
  title: string;
  revenue: number;
  cost: number;
  profit: number;
  margin: number;
  changeRate: number | null;
  period: 'today' | 'week' | 'month';
}

function MetricCard({ title, revenue, cost, profit, margin, changeRate, period }: MetricCardProps) {
  const isPositive = profit >= 0;
  const hasChange = changeRate !== null;
  const isChangePositive = hasChange && changeRate >= 0;

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-500">{title}</h3>
        {hasChange && (
          <span
            className={`inline-flex items-center text-sm ${
              isChangePositive ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {isChangePositive ? (
              <TrendingUp className="h-4 w-4 mr-1" />
            ) : (
              <TrendingDown className="h-4 w-4 mr-1" />
            )}
            {formatPercent(changeRate)}
          </span>
        )}
      </div>

      <div className="space-y-3">
        {/* Profit */}
        <div>
          <div className="text-2xl font-bold text-gray-900">
            {formatCurrency(profit)}
          </div>
          <div className="text-xs text-gray-500">利润</div>
        </div>

        {/* Revenue & Cost */}
        <div className="grid grid-cols-2 gap-4 pt-2 border-t">
          <div>
            <div className="flex items-center gap-1">
              <DollarSign className="h-3 w-3 text-green-500" />
              <span className="text-sm font-medium text-gray-900">
                {formatCurrency(revenue)}
              </span>
            </div>
            <div className="text-xs text-gray-500">收入</div>
          </div>
          <div>
            <div className="flex items-center gap-1">
              <Target className="h-3 w-3 text-red-500" />
              <span className="text-sm font-medium text-gray-900">
                {formatCurrency(cost)}
              </span>
            </div>
            <div className="text-xs text-gray-500">成本</div>
          </div>
        </div>

        {/* Margin */}
        <div className="flex items-center gap-2 pt-2 border-t">
          <Percent className="h-4 w-4 text-blue-500" />
          <span
            className={`text-lg font-semibold ${
              margin >= 20 ? 'text-green-600' : margin >= 10 ? 'text-yellow-600' : 'text-red-600'
            }`}
          >
            {margin.toFixed(2)}%
          </span>
          <span className="text-xs text-gray-500">利润率</span>
        </div>
      </div>
    </div>
  );
}

export function ProfitOverviewCard({ data, loading = false }: ProfitOverviewCardProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-2/3 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <MetricCard
        title="今日利润"
        revenue={data.today_revenue}
        cost={data.today_cost}
        profit={data.today_profit}
        margin={data.today_profit_margin}
        changeRate={data.profit_change_from_yesterday}
        period="today"
      />
      <MetricCard
        title="本周利润"
        revenue={data.week_revenue}
        cost={data.week_cost}
        profit={data.week_profit}
        margin={data.week_profit_margin}
        changeRate={data.profit_change_from_last_week}
        period="week"
      />
      <MetricCard
        title="本月利润"
        revenue={data.month_revenue}
        cost={data.month_cost}
        profit={data.month_profit}
        margin={data.month_profit_margin}
        changeRate={data.profit_change_from_last_month}
        period="month"
      />
    </div>
  );
}

export default ProfitOverviewCard;
