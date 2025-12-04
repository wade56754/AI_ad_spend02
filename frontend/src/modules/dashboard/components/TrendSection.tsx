'use client';

import { TrendChartCard } from '@/components/dashboard/TrendChartCard';
import type { TrendChartData } from '../types';

interface TrendSectionProps {
  spendTrend: TrendChartData;
  roiTrend: TrendChartData;
  loading?: boolean;
  className?: string;
}

export function TrendSection({
  spendTrend,
  roiTrend,
  loading = false,
  className = ''
}: TrendSectionProps) {
  if (loading) {
    return (
      <div className={`grid grid-cols-1 lg:grid-cols-2 gap-4 ${className}`}>
        {Array.from({ length: 2 }).map((_, index) => (
          <div
            key={index}
            className="bg-white rounded-2xl border border-slate-200/60 p-5 animate-pulse"
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="w-24 h-5 bg-slate-200 rounded mb-2" />
                <div className="w-32 h-4 bg-slate-200 rounded" />
              </div>
              <div className="w-16 h-6 bg-slate-200 rounded-full" />
            </div>
            <div className="h-40 bg-slate-100 rounded-lg" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={`grid grid-cols-1 lg:grid-cols-2 gap-4 ${className}`}>
      <TrendChartCard
        title={spendTrend.title}
        description={spendTrend.description}
        trend={spendTrend.trend}
        dataPoints={spendTrend.dataPoints}
      />
      <TrendChartCard
        title={roiTrend.title}
        description={roiTrend.description}
        trend={roiTrend.trend}
        dataPoints={roiTrend.dataPoints}
      />
    </div>
  );
}

export default TrendSection;
