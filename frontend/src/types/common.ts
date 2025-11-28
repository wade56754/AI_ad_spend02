/**
 * Common Types - Shared across all modules
 *
 * Aligned with DATA_SCHEMA.md v5.2
 */

// === UUID Types ===

export type UUID = string;

// === Timestamp Types ===

export type ISODateString = string; // "2025-01-15T10:30:00Z"
export type DateString = string; // "2025-01-15"

// === Money Types ===

/**
 * Money representation aligned with LEDGER_SOT.md v1.1
 * All amounts stored as integers (cents/分)
 */
export interface Money {
  amount: number; // Integer cents
  currency: 'CNY' | 'USD';
}

// === Pagination Types ===

export interface PaginationParams {
  page?: number;
  page_size?: number;
}

export interface SortParams {
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface DateRangeParams {
  start_date?: DateString;
  end_date?: DateString;
}

export interface ListParams extends PaginationParams, SortParams, DateRangeParams {
  search?: string;
}

// === Status Badge Types ===

export type StatusVariant = 'default' | 'success' | 'warning' | 'error' | 'info';

export interface StatusConfig {
  label: string;
  variant: StatusVariant;
  description?: string;
}

// === Form Types ===

export interface SelectOption<T = string> {
  value: T;
  label: string;
  disabled?: boolean;
}

// === Table Types ===

export interface TableColumn<T> {
  key: keyof T | string;
  header: string;
  width?: string | number;
  sortable?: boolean;
  render?: (value: unknown, row: T) => React.ReactNode;
}

// === Action Result Types ===

export interface ActionResult<T = void> {
  success: boolean;
  data?: T;
  error?: string;
}
