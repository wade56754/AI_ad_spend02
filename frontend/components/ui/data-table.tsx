'use client';

import { useState } from 'react';
import { ChevronUpIcon, ChevronDownIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './button';

interface Column<T> {
  key: keyof T;
  title: string;
  sortable?: boolean;
  render?: (value: any, record: T, index: number) => React.ReactNode;
  width?: string;
  align?: 'left' | 'center' | 'right';
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  loading?: boolean;
  pagination?: {
    current: number;
    pageSize: number;
    total: number;
    onChange: (page: number, pageSize: number) => void;
    showSizeChanger?: boolean;
    pageSizeOptions?: number[];
  };
  onRowClick?: (record: T, index: number) => void;
  rowSelection?: {
    selectedRowKeys: string[];
    onChange: (selectedRowKeys: string[], selectedRows: T[]) => void;
  };
  className?: string;
  emptyText?: string;
}

function DataTable<T extends Record<string, any>>({
  data,
  columns,
  loading = false,
  pagination,
  onRowClick,
  rowSelection,
  className = '',
  emptyText = '暂无数据'
}: DataTableProps<T>) {
  const [sortField, setSortField] = useState<keyof T | null>(null);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const handleSort = (key: keyof T) => {
    if (sortField === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(key);
      setSortOrder('asc');
    }
  };

  const getSortedData = () => {
    if (!sortField) return data;

    return [...data].sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];

      if (aValue === null || aValue === undefined) return 1;
      if (bValue === null || bValue === undefined) return -1;

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortOrder === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
      }

      return 0;
    });
  };

  const getAlignClass = (align?: string) => {
    switch (align) {
      case 'center':
        return 'text-center';
      case 'right':
        return 'text-right';
      default:
        return 'text-left';
    }
  };

  const sortedData = getSortedData();
  const paginatedData = pagination
    ? sortedData.slice(
        (pagination.current - 1) * pagination.pageSize,
        pagination.current * pagination.pageSize
      )
    : sortedData;

  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700', className)}>
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          {/* Table Header */}
          <thead className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
            <tr>
              {/* Selection Column */}
              {rowSelection && (
                <th className="px-6 py-3 text-left">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                    checked={paginatedData.length > 0 && paginatedData.every(item =>
                      rowSelection.selectedRowKeys.includes(item.id || item.key)
                    )}
                    onChange={(e) => {
                      if (e.target.checked) {
                        const newSelectedKeys = paginatedData.map(item => item.id || item.key);
                        const newSelectedRows = paginatedData;
                        rowSelection.onChange([...rowSelection.selectedRowKeys, ...newSelectedKeys], newSelectedRows);
                      } else {
                        const keysToRemove = paginatedData.map(item => item.id || item.key);
                        const newSelectedKeys = rowSelection.selectedRowKeys.filter(key => !keysToRemove.includes(key));
                        rowSelection.onChange(newSelectedKeys, []);
                      }
                    }}
                  />
                </th>
              )}

              {/* Data Columns */}
              {columns.map((column) => (
                <th
                  key={String(column.key)}
                  className={cn(
                    'px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider',
                    getAlignClass(column.align),
                    column.sortable && 'cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors'
                  )}
                  style={{ width: column.width }}
                  onClick={() => column.sortable && handleSort(column.key)}
                >
                  <div className="flex items-center space-x-1">
                    <span>{column.title}</span>
                    {column.sortable && sortField === column.key && (
                      sortOrder === 'asc' ? (
                        <ChevronUpIcon className="w-4 h-4" />
                      ) : (
                        <ChevronDownIcon className="w-4 h-4" />
                      )
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>

          {/* Table Body */}
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {loading ? (
              <tr>
                <td
                  colSpan={columns.length + (rowSelection ? 1 : 0)}
                  className="px-6 py-12 text-center text-gray-500 dark:text-gray-400"
                >
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <span className="ml-2">加载中...</span>
                  </div>
                </td>
              </tr>
            ) : paginatedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + (rowSelection ? 1 : 0)}
                  className="px-6 py-12 text-center text-gray-500 dark:text-gray-400"
                >
                  {emptyText}
                </td>
              </tr>
            ) : (
              paginatedData.map((record, index) => (
                <tr
                  key={record.id || record.key || index}
                  className={cn(
                    'hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors',
                    onRowClick && 'cursor-pointer'
                  )}
                  onClick={() => onRowClick && onRowClick(record, index)}
                >
                  {/* Selection Cell */}
                  {rowSelection && (
                    <td className="px-6 py-4">
                      <input
                        type="checkbox"
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                        checked={rowSelection.selectedRowKeys.includes(record.id || record.key)}
                        onChange={(e) => {
                          e.stopPropagation();
                          if (e.target.checked) {
                            rowSelection.onChange(
                              [...rowSelection.selectedRowKeys, record.id || record.key],
                              [...rowSelection.selectedRowKeys.map(key =>
                                data.find(item => item.id === key || item.key === key)
                              ), record]
                            );
                          } else {
                            rowSelection.onChange(
                              rowSelection.selectedRowKeys.filter(key => key !== (record.id || record.key)),
                              rowSelection.selectedRowKeys.filter(key => key !== (record.id || record.key))
                            );
                          }
                        }}
                      />
                    </td>
                  )}

                  {/* Data Cells */}
                  {columns.map((column) => (
                    <td
                      key={String(column.key)}
                      className={cn(
                        'px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100',
                        getAlignClass(column.align)
                      )}
                    >
                      {column.render
                        ? column.render(record[column.key], record, index)
                        : record[column.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pagination && (
        <div className="px-6 py-4 bg-gray-50 dark:bg-gray-700 border-t border-gray-200 dark:border-gray-600">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700 dark:text-gray-300">
              显示第 {(pagination.current - 1) * pagination.pageSize + 1} 至{' '}
              {Math.min(pagination.current * pagination.pageSize, pagination.total)} 条，
              共 {pagination.total} 条记录
            </div>

            <div className="flex items-center space-x-2">
              {/* Page Size Selector */}
              {pagination.showSizeChanger && (
                <select
                  value={pagination.pageSize}
                  onChange={(e) => {
                    const newPageSize = Number(e.target.value);
                    pagination.onChange(1, newPageSize);
                  }}
                  className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 text-sm"
                >
                  {(pagination.pageSizeOptions || [10, 20, 50, 100]).map(size => (
                    <option key={size} value={size}>
                      {size} 条/页
                    </option>
                  ))}
                </select>
              )}

              {/* Page Navigation */}
              <div className="flex space-x-1">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={pagination.current <= 1}
                  onClick={() => pagination.onChange(pagination.current - 1, pagination.pageSize)}
                >
                  上一页
                </Button>

                {/* Page Numbers */}
                <div className="flex space-x-1">
                  {Array.from({ length: Math.ceil(pagination.total / pagination.pageSize) }, (_, i) => i + 1)
                    .filter(page => {
                      const totalPages = Math.ceil(pagination.total / pagination.pageSize);
                      const current = pagination.current;

                      if (totalPages <= 7) return true;

                      if (page <= 3 || page >= totalPages - 2) return true;
                      if (page >= current - 1 && page <= current + 1) return true;

                      return false;
                    })
                    .map((page, index, array) => {
                      const prevPage = array[index - 1];
                      const showEllipsis = prevPage && page - prevPage > 1;

                      return (
                        <div key={page} className="flex items-center space-x-1">
                          {showEllipsis && (
                            <span className="px-2 text-gray-500">...</span>
                          )}
                          <Button
                            variant={page === pagination.current ? "default" : "outline"}
                            size="sm"
                            onClick={() => pagination.onChange(page, pagination.pageSize)}
                          >
                            {page}
                          </Button>
                        </div>
                      );
                    })}
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  disabled={pagination.current >= Math.ceil(pagination.total / pagination.pageSize)}
                  onClick={() => pagination.onChange(pagination.current + 1, pagination.pageSize)}
                >
                  下一页
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default DataTable;