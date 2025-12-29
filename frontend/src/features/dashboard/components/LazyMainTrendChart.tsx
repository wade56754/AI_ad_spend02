/**
 * LazyMainTrendChart - 延迟加载的趋势图表组件
 *
 * 性能优化 (Phase 3 TASK-PERF-004):
 * - 使用 Next.js dynamic import 延迟加载 recharts 库 (~500KB)
 * - 显示骨架屏直到图表加载完成
 * - 减少初始包体积，提升 FCP
 */

'use client';

import dynamic from 'next/dynamic';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import type { MainTrendChartProps, TrendDataPoint, MetricType } from './MainTrendChart';

export type { MainTrendChartProps, TrendDataPoint, MetricType };

// 骨架屏组件
function ChartSkeleton() {
  return (
    <Card className="rounded-xl border shadow-sm">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <Skeleton className="h-7 w-32" />
          <Skeleton className="h-8 w-24" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2 mb-6">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-9 w-16" />
          ))}
        </div>
        <Skeleton className="h-[320px] w-full" />
        <div className="mt-6 pt-4 border-t flex items-center justify-between">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-5 w-24" />
        </div>
      </CardContent>
    </Card>
  );
}

// 动态导入 MainTrendChart (包含 recharts)
const DynamicMainTrendChart = dynamic(
  () => import('./MainTrendChart').then((mod) => mod.MainTrendChart),
  {
    loading: () => <ChartSkeleton />,
    ssr: false, // recharts 不支持 SSR
  }
);

// 导出延迟加载版本
export function LazyMainTrendChart(props: MainTrendChartProps) {
  return <DynamicMainTrendChart {...props} />;
}

export default LazyMainTrendChart;
