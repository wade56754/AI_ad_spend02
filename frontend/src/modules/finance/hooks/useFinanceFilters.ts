/**
 * useFinanceFilters - 财务模块筛选状态管理
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3, FRONTEND_MODULE_SHELL_PATTERN v1.0
 */

'use client';

import { useState, useCallback, useMemo } from 'react';
import type { FinanceFiltersState, TopupStatus } from '../types';

const DEFAULT_FILTERS: FinanceFiltersState = {
  search: '',
  status: 'all',
  activeTab: 'overview',
};

export function useFinanceFilters(initialFilters: Partial<FinanceFiltersState> = {}) {
  const [filters, setFilters] = useState<FinanceFiltersState>({
    ...DEFAULT_FILTERS,
    ...initialFilters,
  });

  const setSearch = useCallback((search: string) => {
    setFilters((prev) => ({ ...prev, search }));
  }, []);

  const setStatus = useCallback((status: TopupStatus | 'all') => {
    setFilters((prev) => ({ ...prev, status }));
  }, []);

  const setActiveTab = useCallback(
    (activeTab: FinanceFiltersState['activeTab']) => {
      setFilters((prev) => ({ ...prev, activeTab }));
    },
    []
  );

  const resetFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
  }, []);

  const hasActiveFilters = useMemo(() => {
    return filters.search !== '' || filters.status !== 'all';
  }, [filters.search, filters.status]);

  return {
    filters,
    setFilters,
    setSearch,
    setStatus,
    setActiveTab,
    resetFilters,
    hasActiveFilters,
  };
}
