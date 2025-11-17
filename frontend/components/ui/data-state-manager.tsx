import React from 'react';
import { Loader2, AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface DataStateManagerProps {
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  onRetry?: () => void;
  children: React.ReactNode;
  loadingComponent?: React.ReactNode;
  errorComponent?: React.ReactNode;
  emptyComponent?: React.ReactNode;
}

/**
 * 数据状态管理组件
 * 根据UI设计规范，统一管理loading、empty、error状态的展示
 */
export const DataStateManager: React.FC<DataStateManagerProps> = ({
  loading = false,
  error = null,
  empty = false,
  onRetry,
  children,
  loadingComponent,
  errorComponent,
  emptyComponent
}) => {
  // Loading状态
  if (loading) {
    if (loadingComponent) {
      return <>{loadingComponent}</>;
    }

    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500 mb-4" />
        <p className="text-sm text-slate-500">加载中...</p>
      </div>
    );
  }

  // Error状态
  if (error) {
    if (errorComponent) {
      return <>{errorComponent}</>;
    }

    return (
      <div className="flex flex-col items-center justify-center py-12">
        <AlertCircle className="w-8 h-8 text-red-500 mb-4" />
        <p className="text-sm text-red-600 mb-4">{error}</p>
        {onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry} className="flex items-center gap-2">
            <RefreshCw className="w-4 h-4" />
            重试
          </Button>
        )}
      </div>
    );
  }

  // Empty状态
  if (empty) {
    if (emptyComponent) {
      return <>{emptyComponent}</>;
    }

    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
          <AlertCircle className="w-8 h-8 text-slate-400" />
        </div>
        <p className="text-sm text-slate-500">暂无数据</p>
      </div>
    );
  }

  // 正常状态：渲染子组件
  return <>{children}</>;
};

/**
 * Skeleton组件 - 用于内容加载时的占位符
 */
export const SkeletonCard: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`animate-pulse bg-white rounded-xl border border-slate-200/60 shadow-sm p-6 ${className}`}>
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="w-24 h-4 bg-slate-200 rounded"></div>
        <div className="w-16 h-4 bg-slate-200 rounded"></div>
      </div>
      <div className="space-y-2">
        <div className="w-3/4 h-8 bg-slate-200 rounded"></div>
        <div className="w-1/2 h-4 bg-slate-200 rounded"></div>
      </div>
    </div>
  </div>
);

/**
 * Dashboard专用Loading组件
 */
export const DashboardSkeleton: React.FC = () => (
  <div className="space-y-6">
    {/* 指标卡片Skeleton */}
    <div className="grid gap-6 grid-cols-12">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="col-span-12 md:col-span-6 lg:col-span-3">
          <SkeletonCard />
        </div>
      ))}
    </div>

    {/* 第二行Skeleton */}
    <div className="grid gap-6 grid-cols-12">
      <div className="col-span-12 lg:col-span-8">
        <SkeletonCard className="h-64" />
      </div>
      <div className="col-span-12 lg:col-span-4">
        <SkeletonCard className="h-64" />
      </div>
    </div>

    {/* 第三行Skeleton */}
    <div className="grid gap-6 grid-cols-12">
      <div className="col-span-12 lg:col-span-8">
        <SkeletonCard className="h-64" />
      </div>
      <div className="col-span-12 lg:col-span-4">
        <SkeletonCard className="h-64" />
      </div>
    </div>
  </div>
);

export default DataStateManager;