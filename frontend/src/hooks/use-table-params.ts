/**
 * useTableParams Hook
 *
 * URL state management for table pagination, filtering, and sorting
 * Uses nuqs for type-safe URL search params
 *
 * @example
 * ```tsx
 * const [params, setParams] = useTableParams();
 *
 * // Read values
 * console.log(params.page, params.pageSize, params.search);
 *
 * // Update values
 * setParams({ page: 2 });
 * setParams({ search: 'query', page: 1 }); // Reset page on search
 * ```
 */

'use client';

import {
  parseAsInteger,
  parseAsString,
  parseAsStringEnum,
  useQueryStates,
  createSerializer,
} from 'nuqs';

// Sort order enum
export type SortOrder = 'asc' | 'desc';

// Default values
const DEFAULT_PAGE = 1;
const DEFAULT_PAGE_SIZE = 20;
const DEFAULT_SORT_ORDER: SortOrder = 'desc';

// Parser definitions
const tableParamsParsers = {
  page: parseAsInteger.withDefault(DEFAULT_PAGE),
  pageSize: parseAsInteger.withDefault(DEFAULT_PAGE_SIZE),
  search: parseAsString.withDefault(''),
  sortBy: parseAsString,
  sortOrder: parseAsStringEnum<SortOrder>(['asc', 'desc']).withDefault(DEFAULT_SORT_ORDER),
};

// Type for table params
export interface TableParams {
  page: number;
  pageSize: number;
  search: string;
  sortBy: string | null;
  sortOrder: SortOrder;
}

// Serializer for building URLs
export const serializeTableParams = createSerializer(tableParamsParsers);

/**
 * Hook for managing table URL state
 */
export function useTableParams() {
  const [params, setParams] = useQueryStates(tableParamsParsers, {
    history: 'push',
    shallow: true,
  });

  // Helper to reset to first page when filters change
  const setParamsWithPageReset = (
    newParams: Partial<TableParams>,
    options?: { resetPage?: boolean }
  ) => {
    const shouldResetPage = options?.resetPage ?? ('search' in newParams || 'sortBy' in newParams);

    if (shouldResetPage && !('page' in newParams)) {
      return setParams({ ...newParams, page: DEFAULT_PAGE });
    }
    return setParams(newParams);
  };

  // Helper to clear all filters
  const clearFilters = () => {
    return setParams({
      page: DEFAULT_PAGE,
      pageSize: DEFAULT_PAGE_SIZE,
      search: '',
      sortBy: null,
      sortOrder: DEFAULT_SORT_ORDER,
    });
  };

  // Helper to check if any filters are active
  const hasActiveFilters = Boolean(
    params.search ||
    params.sortBy ||
    params.page !== DEFAULT_PAGE ||
    params.pageSize !== DEFAULT_PAGE_SIZE
  );

  return {
    params,
    setParams: setParamsWithPageReset,
    clearFilters,
    hasActiveFilters,
    // Pagination helpers
    pagination: {
      page: params.page,
      pageSize: params.pageSize,
      offset: (params.page - 1) * params.pageSize,
    },
    // Sorting helpers
    sorting: {
      sortBy: params.sortBy,
      sortOrder: params.sortOrder,
      toggleSort: (column: string) => {
        if (params.sortBy === column) {
          // Toggle order or clear
          if (params.sortOrder === 'asc') {
            setParams({ sortBy: column, sortOrder: 'desc' });
          } else {
            setParams({ sortBy: null, sortOrder: DEFAULT_SORT_ORDER });
          }
        } else {
          // New column, default to desc
          setParams({ sortBy: column, sortOrder: 'desc', page: DEFAULT_PAGE });
        }
      },
    },
  };
}

export default useTableParams;
