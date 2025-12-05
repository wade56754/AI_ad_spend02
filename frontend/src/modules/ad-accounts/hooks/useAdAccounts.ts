/**
 * useAdAccounts Hook
 *
 * Ad accounts list data fetching and state management.
 * Integrates with API layer and supports client-side filtering.
 *
 * @see API_SOT.md v9.0 Section 10 - Ad Accounts API
 * @see STATE_MACHINE.md v2.6 Section 7 - Ad Account States
 */

'use client';

import { useState, useCallback, useMemo, useEffect } from 'react';
import { adAccountsApi } from '@/lib/api';
import type { AdAccount, AdAccountFilters, AdAccountSummary, AdAccountListParams } from '../types';

// Default summary for initial state
const DEFAULT_SUMMARY: AdAccountSummary = {
  total_accounts: 0,
  active_accounts: 0,
  total_balance: 0,
  total_spent_today: 0,
  high_risk_count: 0,
};

interface UseAdAccountsResult {
  // Data
  accounts: AdAccount[];
  filteredAccounts: AdAccount[];
  summary: AdAccountSummary;

  // State
  loading: boolean;
  error: Error | null;
  isEmpty: boolean;

  // Filters
  filters: AdAccountFilters;
  setFilters: (filters: AdAccountFilters) => void;
  clearFilters: () => void;

  // Actions
  refresh: () => Promise<void>;
}

/**
 * Apply client-side filters to accounts list
 */
function applyFilters(accounts: AdAccount[], filters: AdAccountFilters): AdAccount[] {
  let result = [...accounts];

  // Filter by status
  if (filters.status) {
    const statuses = Array.isArray(filters.status) ? filters.status : [filters.status];
    result = result.filter((a) => statuses.includes(a.status));
  }

  // Filter by platform
  if (filters.platform) {
    const platforms = Array.isArray(filters.platform) ? filters.platform : [filters.platform];
    result = result.filter((a) => platforms.includes(a.platform));
  }

  // Filter by risk level
  if (filters.risk_level) {
    result = result.filter((a) => a.risk_level === filters.risk_level);
  }

  // Filter by project
  if (filters.project_id) {
    result = result.filter((a) => a.project_id === filters.project_id);
  }

  // Search filter
  if (filters.search) {
    const search = filters.search.toLowerCase().trim();
    if (search) {
      result = result.filter(
        (a) =>
          a.account_name.toLowerCase().includes(search) ||
          a.account_id.toLowerCase().includes(search) ||
          (a.project_name && a.project_name.toLowerCase().includes(search))
      );
    }
  }

  return result;
}

export function useAdAccounts(initialFilters: AdAccountFilters = {}): UseAdAccountsResult {
  // State
  const [accounts, setAccounts] = useState<AdAccount[]>([]);
  const [summary, setSummary] = useState<AdAccountSummary>(DEFAULT_SUMMARY);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [filters, setFilters] = useState<AdAccountFilters>(initialFilters);

  // Refresh data from API
  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch accounts list and summary in parallel
      const [listResponse, summaryResponse] = await Promise.all([
        adAccountsApi.fetchList({} as AdAccountListParams),
        adAccountsApi.fetchSummary({}),
      ]);

      setAccounts(listResponse.items || []);
      setSummary(summaryResponse);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '加载广告账户失败';
      setError(new Error(errorMessage));
      console.error('[useAdAccounts] Error fetching accounts:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Apply client-side filters using useMemo
  const filteredAccounts = useMemo(() => {
    return applyFilters(accounts, filters);
  }, [accounts, filters]);

  // Check if data is empty
  const isEmpty = useMemo(() => {
    return !loading && !error && filteredAccounts.length === 0;
  }, [loading, error, filteredAccounts.length]);

  // Clear all filters
  const clearFilters = useCallback(() => {
    setFilters({});
  }, []);

  // Initial fetch
  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    accounts,
    filteredAccounts,
    summary,
    loading,
    error,
    isEmpty,
    filters,
    setFilters,
    clearFilters,
    refresh,
  };
}

export default useAdAccounts;
