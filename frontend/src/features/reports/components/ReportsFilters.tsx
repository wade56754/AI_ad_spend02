/**
 * ReportsFilters Component
 *
 * 日期范围筛选器 - 从 ReportsPage.tsx 提取
 */

'use client';

import React from 'react';
import { Calendar } from 'lucide-react';
import { type DateRange } from '../utils/reportsHelpers';

interface ReportsFiltersProps {
  dateRange: DateRange;
  onDateChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onClearFilters: () => void;
  className?: string;
}

export function ReportsFilters({
  dateRange,
  onDateChange,
  onClearFilters,
  className,
}: ReportsFiltersProps) {
  const hasFilters = dateRange.start_date || dateRange.end_date;

  return (
    <div className={`max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 ${className || ''}`} data-testid="reports-filters">
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-gray-400" />
            <input
              type="date"
              name="start_date"
              value={dateRange.start_date || ''}
              onChange={onDateChange}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-gray-400">-</span>
            <input
              type="date"
              name="end_date"
              value={dateRange.end_date || ''}
              onChange={onDateChange}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          {hasFilters && (
            <button
              onClick={onClearFilters}
              className="px-3 py-2 text-sm text-gray-600 hover:text-gray-900"
            >
              清除筛选
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default ReportsFilters;
