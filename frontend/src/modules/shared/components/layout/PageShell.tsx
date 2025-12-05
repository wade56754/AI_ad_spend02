/**
 * PageShell - 业务模块页面容器组件
 *
 * 提供统一的页面布局结构：
 * - Header（标题 + 描述 + 筛选器 + 操作按钮）
 * - 可选的 KPI 区域
 * - 主内容区
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3, COMPONENT_LIBRARY_GUIDE v1.1
 */

'use client';

import React from 'react';
import { LucideIcon } from 'lucide-react';
import PageContainer from '@/components/layout/page-container';
import { cn } from '@/lib/utils';

export interface PageShellProps {
  /** 页面标题 */
  title: string;
  /** 页面描述 */
  description?: string;
  /** 标题图标 */
  icon?: LucideIcon;
  /** 图标颜色类名 */
  iconColorClass?: string;
  /** 筛选器区域 */
  filters?: React.ReactNode;
  /** 操作按钮区域 */
  actions?: React.ReactNode;
  /** KPI 指标区域（可选，放在 Header 下方） */
  kpiSection?: React.ReactNode;
  /** 主内容区 */
  children: React.ReactNode;
  /** 是否显示加载状态 */
  loading?: boolean;
  /** 自定义类名 */
  className?: string;
}

export function PageShell({
  title,
  description,
  icon: Icon,
  iconColorClass = 'text-accent',
  filters,
  actions,
  kpiSection,
  children,
  loading = false,
  className,
}: PageShellProps) {
  return (
    <div className={cn('min-h-screen bg-shell text-text-body antialiased', className)}>
      <PageContainer>
        <div className="flex flex-col gap-6 w-full py-6">
          {/* Header: 标题 + 筛选器 + 操作按钮 */}
          <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div className="flex items-center gap-3">
              {Icon && (
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10">
                  <Icon className={cn('h-5 w-5', iconColorClass)} />
                </div>
              )}
              <div>
                <h1 className="text-2xl font-semibold tracking-tight text-text-strong">
                  {title}
                </h1>
                {description && (
                  <p className="text-text-muted text-sm mt-1">{description}</p>
                )}
              </div>
            </div>

            {/* 筛选器和操作按钮 */}
            {(filters || actions) && (
              <div className="flex flex-wrap gap-3 items-center">
                {filters && <div className="flex gap-2">{filters}</div>}
                {filters && actions && (
                  <div className="hidden md:block h-8 w-px bg-border-muted mx-1" />
                )}
                {actions && <div className="flex gap-2">{actions}</div>}
              </div>
            )}
          </header>

          {/* KPI 指标区（可选） */}
          {kpiSection && <div>{kpiSection}</div>}

          {/* 主内容区 */}
          <main>{children}</main>
        </div>
      </PageContainer>
    </div>
  );
}

export default PageShell;
