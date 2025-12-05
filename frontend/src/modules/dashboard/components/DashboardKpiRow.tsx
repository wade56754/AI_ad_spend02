/**
 * Dashboard KPI 指标行组件
 * 
 * 功能：
 * - 区分 Primary（主要指标）和 Secondary（次要指标）
 * - 告警卡片高亮显示
 * - 统一视觉层级和间距
 */

'use client';

import React from 'react';
import { ArrowUpRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { KpiMetric } from '../types';

interface DashboardKpiRowProps {
  metrics: KpiMetric[];
  className?: string;
}

export function DashboardKpiRow({ metrics, className }: DashboardKpiRowProps) {
  const primaryMetrics = metrics.filter(m => m.priority === 'primary');
  const secondaryMetrics = metrics.filter(m => m.priority === 'secondary');

  return (
    <div className={cn('grid grid-cols-12 gap-4', className)}>
      {/* Primary KPI: 每个占 4 栅格（共 8 栅格） */}
      {primaryMetrics.map((metric) => (
        <KpiCard key={metric.id} metric={metric} span={4} isPrimary />
      ))}
      
      {/* Secondary KPI: 每个占 2 栅格（共 4 栅格） */}
      {secondaryMetrics.map((metric) => {
        const isAlert = metric.id === 'pending_reports';
        return (
          <KpiCard 
            key={metric.id} 
            metric={metric} 
            span={2} 
            isPrimary={false}
            isAlert={isAlert}
          />
        );
      })}
    </div>
  );
}

interface KpiCardProps {
  metric: KpiMetric;
  span: number;
  isPrimary: boolean;
  isAlert?: boolean;
}

function KpiCard({ metric, span, isPrimary, isAlert }: KpiCardProps) {
  const IconComponent = metric.icon;

  return (
    <div
      className={cn(
        'col-span-12 sm:col-span-6 lg:col-span-' + span,
        'rounded-lg border p-4 transition-all duration-200',
        'bg-card-bg border-default',
        'hover:bg-elevated hover:border-muted hover:shadow-md',
        // 告警卡片：左侧红色边框，不整块背景
        isAlert && 'border-l-4 border-danger'
      )}
    >
      <div className="flex justify-between items-start mb-3">
        {/* 图标 */}
        <div
          className={cn(
            'p-2 rounded-lg transition-transform hover:scale-105',
            isAlert
              ? 'bg-danger/10'
              : isPrimary
              ? 'bg-accent/10'
              : 'bg-elevated'
          )}
        >
          <IconComponent
            className={cn(
              'w-5 h-5',
              isAlert
                ? 'text-danger'
                : isPrimary
                ? 'text-accent'
                : 'text-text-muted'
            )}
          />
        </div>

        {/* 趋势标签 */}
        {metric.change !== undefined && (
          <div
            className={cn(
              'flex items-center text-xs font-semibold px-2 py-0.5 rounded-full',
              'bg-elevated',
              metric.changeType === 'up'
                ? 'text-success'
                : metric.changeType === 'down'
                ? 'text-danger'
                : 'text-text-muted'
            )}
          >
            {metric.change > 0 ? '+' : ''}
            {metric.change}%
            {metric.changeType === 'up' && (
              <ArrowUpRight className="w-3 h-3 ml-0.5" />
            )}
          </div>
        )}
      </div>

      {/* 标题和数值 */}
      <div>
        <div className="text-text-muted text-xs font-medium uppercase tracking-wider mb-1.5">
          {metric.title}
        </div>
        <div className="flex items-baseline gap-2">
          <span
            className={cn(
              'font-bold tracking-tight',
              isPrimary ? 'text-2xl' : 'text-xl',
              isAlert ? 'text-danger' : 'text-text-strong'
            )}
          >
            {metric.value}
          </span>
          {metric.description && (
            <span className="text-xs text-text-muted">{metric.description}</span>
          )}
        </div>
      </div>
    </div>
  );
}

