import React from 'react';

interface ChartCardProps {
  title: string;
  children: React.ReactNode;
  className?: string;
  actions?: React.ReactNode;
  loading?: boolean;
}

/**
 * 图表卡片组件
 *
 * 用于包裹图表组件的统一容器样式
 * 遵循设计系统规范，使用Tailwind语义类
 */
export function ChartCard({
  title,
  children,
  className = '',
  actions,
  loading = false
}: ChartCardProps) {
  // Loading状态
  if (loading) {
    return (
      <div className={`bg-card border border-border rounded-xl shadow-sm ${className}`}>
        <div className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-6 bg-muted rounded w-1/3"></div>
            <div className="h-64 bg-muted rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-card border border-border rounded-xl shadow-sm ${className}`}>
      {/* 头部：标题 + 操作区域 */}
      <div className="flex items-center justify-between px-6 pt-6 pb-4">
        <h3 className="text-lg font-semibold text-foreground">{title}</h3>
        {actions && (
          <div className="flex items-center gap-2">
            {actions}
          </div>
        )}
      </div>

      {/* 图表内容区域 */}
      <div className="px-6 pb-6">
        {children}
      </div>
    </div>
  );
}

export default ChartCard;