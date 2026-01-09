'use client';

/**
 * 分页组件
 *
 * SoT 引用:
 * - FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)
 * - PROMPT_LIBRARY_FRONTEND.md TASK-FE-COMMON-005
 *
 * @module components/common/ListPagination
 */

import { Button } from '@/components/ui/button';
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// ═══════════════════════════════════════════════════════════════════════════
// 类型定义
// ═══════════════════════════════════════════════════════════════════════════

export interface ListPaginationProps {
  /** 当前页码 */
  page: number;
  /** 每页条数 */
  pageSize: number;
  /** 总记录数 */
  total: number;
  /** 页码变更回调 */
  onPageChange: (page: number) => void;
  /** 是否显示首页/末页按钮 */
  showFirstLast?: boolean;
  /** 是否显示总数信息 */
  showTotal?: boolean;
  /** 显示的页码按钮数量（默认 5） */
  visiblePages?: number;
  /** 自定义类名 */
  className?: string;
  /** 是否禁用（加载中） */
  disabled?: boolean;
}

// ═══════════════════════════════════════════════════════════════════════════
// 辅助函数
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 计算要显示的页码列表
 */
function getVisiblePages(
  currentPage: number,
  totalPages: number,
  visibleCount: number
): number[] {
  if (totalPages <= visibleCount) {
    return Array.from({ length: totalPages }, (_, i) => i + 1);
  }

  const half = Math.floor(visibleCount / 2);
  let start = Math.max(1, currentPage - half);
  const end = Math.min(totalPages, start + visibleCount - 1);

  // 调整起始位置确保显示足够的页码
  if (end - start + 1 < visibleCount) {
    start = Math.max(1, end - visibleCount + 1);
  }

  return Array.from({ length: end - start + 1 }, (_, i) => start + i);
}

// ═══════════════════════════════════════════════════════════════════════════
// 主组件
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 分页组件
 *
 * @example
 * ```tsx
 * <ListPagination
 *   page={1}
 *   pageSize={20}
 *   total={100}
 *   onPageChange={(page) => setPage(page)}
 * />
 * ```
 */
export function ListPagination({
  page,
  pageSize,
  total,
  onPageChange,
  showFirstLast = true,
  showTotal = true,
  visiblePages = 5,
  className,
  disabled = false,
}: ListPaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  // 如果只有一页或无数据，不显示分页
  if (totalPages <= 1 && total <= pageSize) {
    return showTotal && total > 0 ? (
      <div className={cn('flex justify-end py-4', className)}>
        <p className="text-sm text-muted-foreground">共 {total} 条记录</p>
      </div>
    ) : null;
  }

  const pages = getVisiblePages(page, totalPages, visiblePages);
  const isFirstPage = page <= 1;
  const isLastPage = page >= totalPages;

  // 计算当前显示范围
  const startRecord = (page - 1) * pageSize + 1;
  const endRecord = Math.min(page * pageSize, total);

  return (
    <div
      className={cn(
        'flex items-center justify-between py-4 border-t',
        className
      )}
    >
      {/* 总数信息 */}
      {showTotal && (
        <p className="text-sm text-muted-foreground">
          显示 {startRecord}-{endRecord} 条，共 {total} 条记录
        </p>
      )}

      {/* 分页按钮 */}
      <div className="flex items-center gap-1">
        {/* 首页按钮 */}
        {showFirstLast && (
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            onClick={() => onPageChange(1)}
            disabled={disabled || isFirstPage}
            title="首页"
          >
            <ChevronsLeft className="h-4 w-4" />
          </Button>
        )}

        {/* 上一页按钮 */}
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          onClick={() => onPageChange(page - 1)}
          disabled={disabled || isFirstPage}
          title="上一页"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        {/* 页码按钮 */}
        <div className="flex items-center gap-1 mx-1">
          {/* 显示起始省略号 */}
          {pages[0] > 1 && (
            <span className="px-2 text-muted-foreground">...</span>
          )}

          {pages.map((p) => (
            <Button
              key={p}
              variant={p === page ? 'default' : 'outline'}
              size="icon"
              className="h-8 w-8"
              onClick={() => onPageChange(p)}
              disabled={disabled}
            >
              {p}
            </Button>
          ))}

          {/* 显示结尾省略号 */}
          {pages[pages.length - 1] < totalPages && (
            <span className="px-2 text-muted-foreground">...</span>
          )}
        </div>

        {/* 下一页按钮 */}
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          onClick={() => onPageChange(page + 1)}
          disabled={disabled || isLastPage}
          title="下一页"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>

        {/* 末页按钮 */}
        {showFirstLast && (
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            onClick={() => onPageChange(totalPages)}
            disabled={disabled || isLastPage}
            title="末页"
          >
            <ChevronsRight className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}

export default ListPagination;
