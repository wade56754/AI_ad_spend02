'use client';

import { DollarSign, Target, TrendingUp, FileText } from 'lucide-react';
import { MetricCard } from '@/components/ui/MetricCard';
import type { KpiMetric } from '../types';

interface KpiCardsProps {
  metrics: KpiMetric[];
  loading?: boolean;
  className?: string;
}

// 图标映射
const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  DollarSign,
  Target,
  TrendingUp,
  FileText,
};

export function KpiCards({ metrics, loading = false, className = '' }: KpiCardsProps) {
  if (loading) {
    return (
      <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 ${className}`}>
        {Array.from({ length: 4 }).map((_, index) => (
          <div
            key={index}
            className="bg-white rounded-xl border border-slate-200/60 p-4 animate-pulse"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="w-20 h-4 bg-slate-200 rounded" />
              <div className="w-5 h-5 bg-slate-200 rounded" />
            </div>
            <div className="w-24 h-8 bg-slate-200 rounded mb-2" />
            <div className="w-16 h-3 bg-slate-200 rounded" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 ${className}`}>
      {metrics.map((metric) => {
        const IconComponent = ICON_MAP[metric.icon];
        return (
          <MetricCard
            key={metric.id}
            title={metric.title}
            value={metric.value}
            change={metric.change}
            changeType={metric.changeType}
            description={metric.description}
            icon={IconComponent}
            color={metric.color}
            size="sm"
          />
        );
      })}
    </div>
  );
}

export default KpiCards;
