/**
 * ModuleDataTable - 业务模块通用数据表格容器
 *
 * 提供统一的数据表格布局：
 * - 卡片容器样式
 * - 深色主题配色
 * - 加载/空状态处理
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { Loader2, Inbox } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

export interface ColumnDef<T> {
  key: string;
  header: string;
  width?: string;
  align?: 'left' | 'center' | 'right';
  render?: (value: unknown, row: T, index: number) => React.ReactNode;
}

export interface ModuleDataTableProps<T> {
  /** 列定义 */
  columns: ColumnDef<T>[];
  /** 数据源 */
  data: T[];
  /** 行键提取函数 */
  getRowKey: (row: T) => string;
  /** 是否加载中 */
  loading?: boolean;
  /** 空状态提示文字 */
  emptyText?: string;
  /** 表格标题 */
  title?: string;
  /** 表格描述 */
  description?: string;
  /** 额外操作按钮 */
  headerActions?: React.ReactNode;
  /** 行点击回调 */
  onRowClick?: (row: T) => void;
  /** 自定义类名 */
  className?: string;
}

export function ModuleDataTable<T>({
  columns,
  data,
  getRowKey,
  loading = false,
  emptyText = '暂无数据',
  title,
  description,
  headerActions,
  onRowClick,
  className,
}: ModuleDataTableProps<T>) {
  // 加载状态
  if (loading) {
    return (
      <div
        className={cn(
          'rounded-lg border bg-card-bg border-border-default p-8',
          className
        )}
      >
        <div className="flex items-center justify-center text-text-muted">
          <Loader2 className="w-6 h-6 animate-spin mr-2" />
          正在加载...
        </div>
      </div>
    );
  }

  // 空状态
  if (data.length === 0) {
    return (
      <div
        className={cn(
          'rounded-lg border bg-card-bg border-border-default p-8',
          className
        )}
      >
        <div className="flex flex-col items-center justify-center text-text-muted py-8">
          <Inbox className="w-12 h-12 mb-4 opacity-50" />
          <p>{emptyText}</p>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        'rounded-lg border bg-card-bg border-border-default overflow-hidden',
        className
      )}
    >
      {/* 表格头部 */}
      {(title || headerActions) && (
        <div className="flex justify-between items-center px-4 py-3 border-b border-border-default">
          <div>
            {title && (
              <h3 className="font-semibold text-text-strong">{title}</h3>
            )}
            {description && (
              <p className="text-sm text-text-muted mt-0.5">{description}</p>
            )}
          </div>
          {headerActions && <div className="flex gap-2">{headerActions}</div>}
        </div>
      )}

      {/* 表格主体 */}
      <Table>
        <TableHeader>
          <TableRow className="border-border-default hover:bg-transparent">
            {columns.map((col) => (
              <TableHead
                key={col.key}
                className={cn(
                  'text-text-muted font-medium',
                  col.width && `w-[${col.width}]`,
                  col.align === 'center' && 'text-center',
                  col.align === 'right' && 'text-right'
                )}
              >
                {col.header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((row, rowIndex) => (
            <TableRow
              key={getRowKey(row)}
              className={cn(
                'border-border-default',
                'hover:bg-elevated transition-colors',
                onRowClick && 'cursor-pointer'
              )}
              onClick={() => onRowClick?.(row)}
            >
              {columns.map((col) => {
                const value = (row as Record<string, unknown>)[col.key];
                return (
                  <TableCell
                    key={col.key}
                    className={cn(
                      'text-text-body',
                      col.align === 'center' && 'text-center',
                      col.align === 'right' && 'text-right'
                    )}
                  >
                    {col.render ? col.render(value, row, rowIndex) : String(value ?? '-')}
                  </TableCell>
                );
              })}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export default ModuleDataTable;
