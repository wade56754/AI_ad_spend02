/**
 * KpiCards Component
 *
 * SoT: docs/10.module-specs/A1-dashboard.md
 * SoT: MASTER.md v4.4 §6.5 核心页面最小字段集
 * CodeBlock: CB-FE-002 (StatCard)
 *
 * 功能: 4 个核心 KPI 指标卡片
 * - 本月总消耗
 * - 本月总进粉
 * - 整体 CPL
 * - 预计毛利
 */

'use client';

import React from 'react';
import { DollarSign, Users, BarChart3, Target } from 'lucide-react';
import { StatCard } from './StatCard';
import { formatCurrency } from '../utils/formatters';
import type { MetricType } from './MainTrendChart';

export interface KpiData {
  // 本月核心指标 (MASTER.md §6.5 必须字段)
  month_spend: number;
  month_conversions: number;
  overall_cpl: number;
  estimated_profit: number;
  // 今日指标
  today_spend: number;
  today_conversions: number;
  today_profit: number;
  // 变化率
  spend_change: number;
  conversions_change: number;
  cpl_change: number;
  profit_change: number;
  // 目标值
  cpl_target: number;
}

export interface Average7d {
  spend: string;
  revenue: string;
  profit: string;
  conversions: string;
}

export interface KpiCardsProps {
  data: KpiData;
  average7d: Average7d;
  activeMetric: MetricType;
  onMetricChange: (metric: MetricType) => void;
}

/**
 * KPI 卡片组件
 * 展示 4 个核心业务指标
 */
export function KpiCards({
  data,
  average7d,
  activeMetric,
  onMetricChange,
}: KpiCardsProps) {
  return (
    <section data-testid="kpi-cards">
      <h2 className="text-2xl font-semibold text-foreground mb-4">本月概览</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* 本月总消耗 */}
        <StatCard
          title="本月总消耗"
          value={formatCurrency(data.month_spend)}
          change={data.spend_change}
          average7d={average7d.spend}
          target={`今日 ${formatCurrency(data.today_spend)}`}
          icon={<DollarSign className="h-6 w-6" />}
          color="blue"
          onClick={() => onMetricChange('spend')}
          isActive={activeMetric === 'spend'}
          testId="kpi-spend"
        />

        {/* 本月总进粉 */}
        <StatCard
          title="本月总进粉"
          value={data.month_conversions.toLocaleString()}
          change={data.conversions_change}
          average7d={average7d.conversions}
          target={`今日 ${data.today_conversions.toLocaleString()}`}
          icon={<Users className="h-6 w-6" />}
          color="purple"
          onClick={() => onMetricChange('conversions')}
          isActive={activeMetric === 'conversions'}
          testId="kpi-conversions"
        />

        {/* 整体 CPL */}
        <StatCard
          title="整体 CPL"
          value={`¥${data.overall_cpl.toFixed(2)}`}
          change={data.cpl_change}
          target={`目标 ¥${data.cpl_target}`}
          icon={<BarChart3 className="h-6 w-6" />}
          color={
            data.overall_cpl > data.cpl_target * 1.3
              ? 'red'
              : data.overall_cpl > data.cpl_target
              ? 'orange'
              : 'green'
          }
          testId="kpi-cpl"
        />

        {/* 预计毛利 */}
        <StatCard
          title="预计毛利"
          value={formatCurrency(data.estimated_profit)}
          change={data.profit_change}
          average7d={average7d.profit}
          target={`今日 ${formatCurrency(data.today_profit)}`}
          icon={<Target className="h-6 w-6" />}
          color={data.estimated_profit >= 0 ? 'green' : 'red'}
          onClick={() => onMetricChange('profit')}
          isActive={activeMetric === 'profit'}
          testId="kpi-profit"
        />
      </div>
    </section>
  );
}

export default KpiCards;
