/**
 * Dashboard Filter Context
 *
 * 全局筛选状态管理：日期、渠道、账户
 * 所有 Dashboard 组件（KPI、趋势、Top 列表、待办）统一使用此状态
 */

'use client';

import React, { createContext, useContext, useState, type ReactNode } from 'react';

export type DateRangePreset = 'today' | '7d' | '30d' | 'custom';
export type Channel = 'all' | 'facebook' | 'google' | 'tiktok' | 'other';

export interface DateRange {
  from: Date;
  to: Date;
}

export interface DashboardFilters {
  datePreset: DateRangePreset;
  customDateRange?: DateRange;
  channel: Channel;
  accountId?: string; // 选中的广告账户 ID
}

interface FilterContextValue {
  filters: DashboardFilters;
  updateFilters: (updates: Partial<DashboardFilters>) => void;
  resetFilters: () => void;
}

const FilterContext = createContext<FilterContextValue | undefined>(undefined);

const DEFAULT_FILTERS: DashboardFilters = {
  datePreset: '7d',
  channel: 'all',
  accountId: undefined,
};

export function FilterProvider({ children }: { children: ReactNode }) {
  const [filters, setFilters] = useState<DashboardFilters>(DEFAULT_FILTERS);

  const updateFilters = (updates: Partial<DashboardFilters>) => {
    setFilters((prev) => ({ ...prev, ...updates }));
  };

  const resetFilters = () => {
    setFilters(DEFAULT_FILTERS);
  };

  return (
    <FilterContext.Provider value={{ filters, updateFilters, resetFilters }}>
      {children}
    </FilterContext.Provider>
  );
}

export function useFilters(): FilterContextValue {
  const context = useContext(FilterContext);
  if (!context) {
    throw new Error('useFilters must be used within FilterProvider');
  }
  return context;
}

/**
 * 根据日期预设获取日期范围
 */
export function getDateRangeFromPreset(preset: DateRangePreset, customRange?: DateRange): DateRange {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  if (preset === 'custom' && customRange) {
    return customRange;
  }

  const from = new Date(today);

  switch (preset) {
    case 'today':
      return { from: today, to: today };
    case '7d':
      from.setDate(today.getDate() - 6);
      return { from, to: today };
    case '30d':
      from.setDate(today.getDate() - 29);
      return { from, to: today };
    default:
      from.setDate(today.getDate() - 6);
      return { from, to: today };
  }
}

/**
 * 根据日期预设获取天数
 */
export function getDaysFromPreset(preset: DateRangePreset): number {
  switch (preset) {
    case 'today':
      return 1;
    case '7d':
      return 7;
    case '30d':
      return 30;
    default:
      return 7;
  }
}
