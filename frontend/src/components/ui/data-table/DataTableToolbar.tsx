/**
 * DataTable Toolbar Component
 *
 * Search, filter, and action buttons for DataTable
 */

'use client';

import React from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search, X, RefreshCw, Download, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface DataTableToolbarProps {
  // Search
  search?: string;
  onSearchChange?: (value: string) => void;
  searchPlaceholder?: string;
  // Actions
  onRefresh?: () => void;
  onExport?: () => void;
  onCreate?: () => void;
  createLabel?: string;
  // Filter
  filterComponent?: React.ReactNode;
  // Active filters indicator
  hasActiveFilters?: boolean;
  onClearFilters?: () => void;
  // Loading state
  loading?: boolean;
  // Custom actions
  actions?: React.ReactNode;
  // Styling
  className?: string;
}

export function DataTableToolbar({
  search,
  onSearchChange,
  searchPlaceholder = '搜索...',
  onRefresh,
  onExport,
  onCreate,
  createLabel = '新建',
  filterComponent,
  hasActiveFilters,
  onClearFilters,
  loading,
  actions,
  className,
}: DataTableToolbarProps) {
  return (
    <div className={cn('flex flex-col sm:flex-row gap-4 mb-4', className)}>
      {/* Left side: Search and filters */}
      <div className="flex flex-1 items-center gap-2">
        {/* Search input */}
        {onSearchChange && (
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder={searchPlaceholder}
              value={search || ''}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-8 pr-8"
            />
            {search && (
              <button
                onClick={() => onSearchChange('')}
                className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        )}

        {/* Filter component slot */}
        {filterComponent}

        {/* Clear filters */}
        {hasActiveFilters && onClearFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearFilters}
            className="h-8 px-2 lg:px-3"
          >
            清除筛选
            <X className="ml-1 h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Right side: Actions */}
      <div className="flex items-center gap-2">
        {/* Custom actions slot */}
        {actions}

        {/* Refresh button */}
        {onRefresh && (
          <Button
            variant="outline"
            size="icon"
            onClick={onRefresh}
            disabled={loading}
          >
            <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
          </Button>
        )}

        {/* Export button */}
        {onExport && (
          <Button variant="outline" size="sm" onClick={onExport}>
            <Download className="mr-2 h-4 w-4" />
            导出
          </Button>
        )}

        {/* Create button */}
        {onCreate && (
          <Button size="sm" onClick={onCreate}>
            <Plus className="mr-2 h-4 w-4" />
            {createLabel}
          </Button>
        )}
      </div>
    </div>
  );
}

export default DataTableToolbar;
