import React from 'react';
import { cn } from '@/lib/utils';

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

/**
 * 骨架屏基础组件
 *
 * 用于数据加载时的占位显示
 */
export const Skeleton: React.FC<SkeletonProps> = ({ className = '', ...props }) => {
  return (
    <div
      className={cn('animate-pulse rounded-md bg-muted', className)}
      {...props}
    />
  );
};

/**
 * 文本行骨架屏
 */
export const SkeletonText: React.FC<{ lines?: number; className?: string }> = ({
  lines = 1,
  className,
}) => (
  <div className={cn('space-y-2', className)}>
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton
        key={i}
        className={cn('h-4', i === lines - 1 ? 'w-3/4' : 'w-full')}
      />
    ))}
  </div>
);

/**
 * 卡片骨架屏
 */
export const SkeletonCard: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn('rounded-lg border bg-card p-4 space-y-3', className)}>
    <Skeleton className="h-4 w-1/3" />
    <Skeleton className="h-8 w-2/3" />
    <Skeleton className="h-4 w-1/2" />
  </div>
);

/**
 * 统计卡片骨架屏
 */
export const SkeletonStatCard: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn('rounded-lg border bg-card p-4', className)}>
    <div className="flex items-center justify-between">
      <Skeleton className="h-4 w-20" />
      <Skeleton className="h-8 w-8 rounded-full" />
    </div>
    <Skeleton className="h-8 w-24 mt-2" />
    <Skeleton className="h-3 w-16 mt-2" />
  </div>
);

/**
 * 表格行骨架屏
 */
export const SkeletonTableRow: React.FC<{ columns?: number; className?: string }> = ({
  columns = 5,
  className,
}) => (
  <div className={cn('flex items-center gap-4 py-3 border-b', className)}>
    {Array.from({ length: columns }).map((_, i) => (
      <Skeleton key={i} className="h-4 flex-1" />
    ))}
  </div>
);

/**
 * 表格骨架屏
 */
export const SkeletonTable: React.FC<{ rows?: number; columns?: number; className?: string }> = ({
  rows = 5,
  columns = 5,
  className,
}) => (
  <div className={cn('rounded-lg border', className)}>
    {/* 表头 */}
    <div className="flex items-center gap-4 p-4 border-b bg-muted/50">
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton key={i} className="h-4 flex-1" />
      ))}
    </div>
    {/* 表体 */}
    <div className="p-4 space-y-0">
      {Array.from({ length: rows }).map((_, i) => (
        <SkeletonTableRow key={i} columns={columns} />
      ))}
    </div>
  </div>
);

/**
 * 列表项骨架屏
 */
export const SkeletonListItem: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn('flex items-center gap-3 py-3', className)}>
    <Skeleton className="h-10 w-10 rounded-full" />
    <div className="flex-1 space-y-2">
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-3 w-1/2" />
    </div>
  </div>
);

/**
 * 仪表盘统计区骨架屏
 */
export const SkeletonDashboardStats: React.FC<{
  count?: number;
  className?: string;
}> = ({ count = 6, className }) => (
  <div className={cn('grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4', className)}>
    {Array.from({ length: count }).map((_, i) => (
      <SkeletonStatCard key={i} />
    ))}
  </div>
);

/**
 * 图表骨架屏
 */
export const SkeletonChart: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn('rounded-lg border bg-card p-4', className)}>
    <div className="flex items-center justify-between mb-4">
      <Skeleton className="h-5 w-32" />
      <div className="flex gap-2">
        <Skeleton className="h-8 w-20" />
        <Skeleton className="h-8 w-20" />
      </div>
    </div>
    <Skeleton className="h-64 w-full" />
  </div>
);

export default Skeleton;