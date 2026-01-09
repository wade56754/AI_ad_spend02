'use client';

/**
 * 通用列表页模板
 *
 * SoT 引用:
 * - FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)
 * - PROMPT_LIBRARY_FRONTEND.md TASK-FE-COMMON-005
 *
 * @module components/common/ListPage
 */

import { ReactNode } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, InboxIcon } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';

// ═══════════════════════════════════════════════════════════════════════════
// 类型定义
// ═══════════════════════════════════════════════════════════════════════════

export interface ListPageProps {
  /** 页面标题 */
  title: string;
  /** 页面描述（可选） */
  description?: string;
  /** 操作按钮区域 */
  actions?: ReactNode;
  /** 筛选器区域 */
  filters?: ReactNode;
  /** 主内容区域（通常是 DataTable） */
  children: ReactNode;
  /** 分页组件 */
  pagination?: ReactNode;
  /** 是否加载中 */
  isLoading?: boolean;
  /** 是否加载失败 */
  isError?: boolean;
  /** 错误信息 */
  error?: Error | null;
  /** 数据是否为空 */
  isEmpty?: boolean;
  /** 空状态提示文字 */
  emptyMessage?: string;
  /** 空状态图标 */
  emptyIcon?: ReactNode;
  /** 自定义类名 */
  className?: string;
  /** 标题区域自定义类名 */
  headerClassName?: string;
  /** 内容区域自定义类名 */
  contentClassName?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// 骨架屏组件
// ═══════════════════════════════════════════════════════════════════════════

function ListSkeleton() {
  return (
    <div className="space-y-4">
      {/* 表头骨架 */}
      <div className="flex items-center gap-4 px-4 py-3 bg-muted/50 rounded-t-lg">
        <Skeleton className="h-4 w-4" />
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-4 w-28 ml-auto" />
      </div>
      {/* 数据行骨架 */}
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 px-4 py-4 border-b">
          <Skeleton className="h-4 w-4" />
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-6 w-16 rounded-full" />
          <Skeleton className="h-8 w-20 ml-auto" />
        </div>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// 空状态组件
// ═══════════════════════════════════════════════════════════════════════════

interface EmptyStateProps {
  message: string;
  icon?: ReactNode;
}

function EmptyState({ message, icon }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
      {icon || <InboxIcon className="h-12 w-12 mb-4 opacity-50" />}
      <p className="text-base">{message}</p>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// 错误状态组件
// ═══════════════════════════════════════════════════════════════════════════

interface ErrorStateProps {
  error: Error | null;
}

function ErrorState({ error }: ErrorStateProps) {
  return (
    <Alert variant="destructive" className="my-8">
      <AlertCircle className="h-4 w-4" />
      <AlertDescription>
        {error?.message || '加载数据失败，请稍后重试'}
      </AlertDescription>
    </Alert>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// 主组件
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 通用列表页模板
 *
 * 提供统一的列表页面结构，包括：
 * - 页面标题和描述
 * - 操作按钮区域
 * - 筛选器区域
 * - 主内容区域（加载/错误/空/数据状态）
 * - 分页区域
 *
 * @example
 * ```tsx
 * <ListPage
 *   title="用户管理"
 *   description="管理系统中的所有用户"
 *   actions={<Button>新建用户</Button>}
 *   filters={<UserFilters />}
 *   isLoading={isLoading}
 *   isError={isError}
 *   error={error}
 *   isEmpty={users.length === 0}
 *   pagination={<ListPagination {...paginationProps} />}
 * >
 *   <DataTable columns={columns} data={users} />
 * </ListPage>
 * ```
 */
export function ListPage({
  title,
  description,
  actions,
  filters,
  children,
  pagination,
  isLoading = false,
  isError = false,
  error = null,
  isEmpty = false,
  emptyMessage = '暂无数据',
  emptyIcon,
  className,
  headerClassName,
  contentClassName,
}: ListPageProps) {
  return (
    <div className={cn('space-y-6', className)}>
      {/* 页面头部 */}
      <div className={cn('flex items-center justify-between', headerClassName)}>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
          {description && (
            <p className="text-muted-foreground mt-1">{description}</p>
          )}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>

      {/* 筛选器区域 */}
      {filters && (
        <Card>
          <CardContent className="pt-6">{filters}</CardContent>
        </Card>
      )}

      {/* 主内容区域 */}
      <Card>
        <CardContent className={cn('pt-6', contentClassName)}>
          {isLoading ? (
            <ListSkeleton />
          ) : isError ? (
            <ErrorState error={error} />
          ) : isEmpty ? (
            <EmptyState message={emptyMessage} icon={emptyIcon} />
          ) : (
            <>
              {children}
              {pagination && <div className="mt-4">{pagination}</div>}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default ListPage;
