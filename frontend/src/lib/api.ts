/**
 * API Client for the AI Ad Spend System
 *
 * Aligned with:
 * - API_SOT.md v9.0 (API endpoints)
 * - ERROR_CODES_SOT.md v2.1 (error handling)
 * - AUTH_SPEC.md v2.0 (authentication)
 *
 * @module lib/api
 */

// ============================================================================
// Types
// ============================================================================

/**
 * Pagination metadata
 */
export interface PaginationMeta {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  // Nested pagination for some components
  pagination?: {
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  };
}

/**
 * Paginated response structure (supports both formats)
 * - New format: { items, total, page, page_size, total_pages }
 * - Legacy format: { data, meta: { total, page, ... } }
 */
export interface PaginatedResponse<T> {
  // New format
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  // Legacy format (for backward compatibility)
  data: T[];
  meta: PaginationMeta;
}

/**
 * Standard API error response (aligned with ERROR_CODES_SOT.md)
 */
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

/**
 * Standard API response envelope
 */
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  message?: string;
}

/**
 * Fetch options with body serialization
 */
export interface ApiFetchOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
}

// ============================================================================
// Configuration
// ============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * Get authentication token from storage
 *
 * Note: 与 useAuth.ts 中的 AUTH_TOKEN_KEY 保持一致
 */
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;

  // 优先使用 auth-token (与 useAuth.ts 一致)，然后尝试旧的 access_token
  return (
    localStorage.getItem('auth-token') ||
    localStorage.getItem('access_token') ||
    sessionStorage.getItem('access_token')
  );
}

// ============================================================================
// Error Handling
// ============================================================================

/**
 * Custom API error class
 */
export class ApiRequestError extends Error {
  public readonly code: string;
  public readonly status: number;
  public readonly details?: Record<string, unknown>;

  constructor(
    message: string,
    code: string,
    status: number,
    details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'ApiRequestError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

/**
 * Type guard to check if error is an API error
 */
export function isApiError(error: unknown): error is ApiRequestError {
  return error instanceof ApiRequestError;
}

/**
 * Alias for backward compatibility
 */
export const ApiError = ApiRequestError;

/**
 * Handle API error response
 * @param response - The fetch response object
 * @param requestUrl - The URL that was requested (used for context-aware error handling)
 */
async function handleErrorResponse(response: Response, requestUrl?: string): Promise<never> {
  let error: ApiError;

  try {
    const data = await response.json();
    // Handle both { error: {...} } and direct error format
    error = data.error || data;
  } catch {
    error = {
      code: 'SYS_001',
      message: response.statusText || 'Network error',
    };
  }

  // Handle 401 - clear ALL tokens and redirect to login
  // SoT Reference: AUTH_SPEC.md v2.0 §7.4
  if (response.status === 401) {
    if (typeof window !== 'undefined') {
      const path = window.location.pathname;
      const isAuthPage = path.includes('/login') || path.includes('/register');
      // Check if this is a login/register POST request
      const isLoginRequest = requestUrl?.includes('/auth/login') || requestUrl?.includes('/auth/register');

      // For login/register failures (wrong password), let the error pass through
      if (isLoginRequest) {
        // Don't clear tokens or redirect for login failures
      } else {
        // For all other 401 errors (expired token, invalid token), clear tokens
        localStorage.removeItem('auth-token');
        localStorage.removeItem('auth-user');
        localStorage.removeItem('refresh-token');
        localStorage.removeItem('access_token');
        sessionStorage.removeItem('access_token');
        // Clear cookie
        document.cookie = 'access_token=; path=/; max-age=0';

        // On auth pages, silently fail
        if (isAuthPage) {
          const silentError = new ApiRequestError(
            'Session expired',
            'AUTH_401',
            401
          );
          (silentError as ApiRequestError & { silent?: boolean }).silent = true;
          throw silentError;
        }

        // Redirect to login for protected pages
        window.location.href = '/login';
      }
    }
  }

  throw new ApiRequestError(
    error.message,
    error.code,
    response.status,
    error.details
  );
}

// ============================================================================
// Core Fetch Functions
// ============================================================================

/**
 * Core API fetch function with authentication and error handling
 *
 * @example
 * // GET request
 * const user = await apiFetch<User>('/api/v1/users/me');
 *
 * // POST request
 * const newUser = await apiFetch<User>('/api/v1/users', {
 *   method: 'POST',
 *   body: { name: 'John' }
 * });
 */
export async function apiFetch<T>(
  url: string,
  options: ApiFetchOptions = {}
): Promise<T> {
  const { body, headers: customHeaders, ...restOptions } = options;

  // Build headers
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...customHeaders,
  };

  // Add auth token if available
  const token = getAuthToken();
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  // Build full URL
  const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;

  // Make request
  const response = await fetch(fullUrl, {
    ...restOptions,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  // Handle errors
  if (!response.ok) {
    await handleErrorResponse(response, fullUrl);
  }

  // Handle empty response (204 No Content)
  if (response.status === 204) {
    return undefined as T;
  }

  // Parse response
  const data: ApiResponse<T> = await response.json();

  // Handle envelope format { success, data, error }
  if ('success' in data) {
    if (!data.success && data.error) {
      throw new ApiRequestError(
        data.error.message,
        data.error.code,
        response.status,
        data.error.details
      );
    }
    return data.data as T;
  }

  // Handle direct data format
  return data as T;
}

/**
 * Fetch paginated data
 *
 * Normalizes response to support both formats:
 * - Backend format: { items, total, page, page_size, total_pages }
 * - Legacy format: { data, meta: { total, page, page_size, total_pages } }
 *
 * @example
 * const { items, data, meta } = await apiFetchPaginated<User>('/api/v1/users?page=1');
 */
export async function apiFetchPaginated<T>(
  url: string,
  options: ApiFetchOptions = {}
): Promise<PaginatedResponse<T>> {
  // For paginated endpoints, we need to handle the full envelope
  const { body, headers: customHeaders, ...restOptions } = options;

  const reqHeaders: HeadersInit = {
    'Content-Type': 'application/json',
    ...customHeaders,
  };

  const token = getAuthToken();
  if (token) {
    (reqHeaders as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;

  const response = await fetch(fullUrl, {
    ...restOptions,
    headers: reqHeaders,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    await handleErrorResponse(response, fullUrl);
  }

  const envelope = await response.json();

  // Handle envelope format { success, data, meta }
  if ('success' in envelope && !envelope.success && envelope.error) {
    throw new ApiRequestError(
      envelope.error.message,
      envelope.error.code,
      response.status,
      envelope.error.details
    );
  }

  // Extract items from envelope.data (which is an array)
  const items = Array.isArray(envelope.data) ? envelope.data : (envelope.data?.items || []);

  // Extract meta from envelope.meta
  const meta = envelope.meta?.pagination || envelope.meta || {
    total: envelope.total || items.length,
    page: envelope.page || 1,
    page_size: envelope.page_size || 20,
    total_pages: envelope.total_pages || 1,
  };

  return {
    // New format
    items,
    total: meta.total,
    page: meta.page,
    page_size: meta.page_size,
    total_pages: meta.total_pages,
    // Legacy format
    data: items,
    meta,
  };
}

// ============================================================================
// Convenience Functions
// ============================================================================

/**
 * GET request helper with optional query params
 */
export async function apiGet<T>(
  url: string,
  params?: Record<string, string | number | boolean | undefined>
): Promise<T> {
  let fullUrl = url;
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.set(key, String(value));
      }
    });
    const query = searchParams.toString();
    if (query) {
      fullUrl += (url.includes('?') ? '&' : '?') + query;
    }
  }
  return apiFetch<T>(fullUrl, { method: 'GET' });
}

/**
 * POST request helper
 */
export async function apiPost<T>(url: string, body?: unknown): Promise<T> {
  return apiFetch<T>(url, { method: 'POST', body });
}

/**
 * PATCH request helper
 */
export async function apiPatch<T>(url: string, body?: unknown): Promise<T> {
  return apiFetch<T>(url, { method: 'PATCH', body });
}

/**
 * DELETE request helper
 */
export async function apiDelete<T>(url: string): Promise<T> {
  return apiFetch<T>(url, { method: 'DELETE' });
}

/**
 * PUT request helper
 */
export async function apiPut<T>(url: string, body?: unknown): Promise<T> {
  return apiFetch<T>(url, { method: 'PUT', body });
}

/**
 * Generic request helper (alias for apiFetch)
 */
export const apiRequest = apiFetch;

/**
 * Upload file helper
 *
 * @example
 * const result = await apiUpload<ImportJob>('/api/v1/import-jobs/upload', file, {
 *   onProgress: (percent) => console.log(percent)
 * });
 */
export async function apiUpload<T>(
  url: string,
  file: File,
  options: {
    fieldName?: string;
    additionalData?: Record<string, string>;
    onProgress?: (percent: number) => void;
  } = {}
): Promise<T> {
  const { fieldName = 'file', additionalData = {} } = options;

  const formData = new FormData();
  formData.append(fieldName, file);

  // Add additional data
  Object.entries(additionalData).forEach(([key, value]) => {
    formData.append(key, value);
  });

  // Build headers (without Content-Type - browser sets it with boundary)
  const headers: HeadersInit = {};
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;

  const response = await fetch(fullUrl, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    await handleErrorResponse(response, fullUrl);
  }

  const data = await response.json();
  return 'data' in data ? data.data : data;
}

/**
 * Download file helper
 *
 * @example
 * const blob = await apiDownload('/api/v1/reports/123/export');
 * // Or with filename
 * await apiDownload('/api/v1/reports/123/export', { saveAs: 'report.xlsx' });
 */
export async function apiDownload(
  url: string,
  options: {
    saveAs?: string;
  } = {}
): Promise<Blob> {
  const headers: HeadersInit = {};
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;

  const response = await fetch(fullUrl, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    await handleErrorResponse(response, fullUrl);
  }

  const blob = await response.blob();

  // Auto-save if filename provided
  if (options.saveAs && typeof window !== 'undefined') {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = options.saveAs;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  }

  return blob;
}

// ============================================================================
// Query Keys Factory (for TanStack Query)
// ============================================================================

/**
 * Query key factory for consistent cache key generation
 *
 * @example
 * // In hooks
 * queryKey: queryKeys.users.list({ page: 1 })
 * queryKey: queryKeys.users.detail(userId)
 */
export const queryKeys = {
  // Auth
  auth: {
    all: ['auth'] as const,
    me: () => [...queryKeys.auth.all, 'me'] as const,
  },

  // Users
  users: {
    all: ['users'] as const,
    list: (params?: Record<string, any>) =>
      [...queryKeys.users.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.users.all, 'detail', id] as const,
  },

  // Projects
  projects: {
    all: ['projects'] as const,
    list: (params?: Record<string, any>) =>
      [...queryKeys.projects.all, 'list', params] as const,
    lists: (params?: Record<string, any>) =>
      [...queryKeys.projects.all, 'list', params] as const,
    detail: (id: string | number) =>
      [...queryKeys.projects.all, 'detail', String(id)] as const,
    members: (projectId: string | number) =>
      [...queryKeys.projects.all, 'members', String(projectId)] as const,
  },

  // Channels
  channels: {
    all: ['channels'] as const,
    list: (params?: Record<string, any>) =>
      [...queryKeys.channels.all, 'list', params] as const,
    lists: (params?: Record<string, any>) =>
      [...queryKeys.channels.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.channels.all, 'detail', id] as const,
  },

  // Ad Accounts
  adAccounts: {
    all: ['adAccounts'] as const,
    list: (params?: Record<string, any>) =>
      [...queryKeys.adAccounts.all, 'list', params] as const,
    detail: (id: string) =>
      [...queryKeys.adAccounts.all, 'detail', id] as const,
  },

  // Daily Reports
  dailyReports: {
    all: ['dailyReports'] as const,
    list: (params?: Record<string, any>) =>
      [...queryKeys.dailyReports.all, 'list', params] as const,
    lists: (params?: Record<string, any>) =>
      [...queryKeys.dailyReports.all, 'list', params] as const,
    detail: (id: string) =>
      [...queryKeys.dailyReports.all, 'detail', id] as const,
    stats: (params?: Record<string, any>) =>
      [...queryKeys.dailyReports.all, 'stats', params] as const,
    byProject: (projectId: string | number, params?: Record<string, any>) =>
      [...queryKeys.dailyReports.all, 'byProject', String(projectId), params] as const,
  },

  // Topups
  topups: {
    all: ['topups'] as const,
    list: (params?: Record<string, any>) =>
      [...queryKeys.topups.all, 'list', params] as const,
    lists: (params?: Record<string, any>) =>
      [...queryKeys.topups.all, 'list', params] as const,
    detail: (id: string | number) =>
      [...queryKeys.topups.all, 'detail', String(id)] as const,
    stats: (params?: Record<string, any>) =>
      [...queryKeys.topups.all, 'stats', params] as const,
    byProject: (projectId: string | number, params?: Record<string, any>) =>
      [...queryKeys.topups.all, 'byProject', String(projectId), params] as const,
  },

  // Transfers
  transfers: {
    all: ['transfers'] as const,
    list: (params?: Record<string, any>) =>
      [...queryKeys.transfers.all, 'list', params] as const,
    lists: (params?: Record<string, any>) =>
      [...queryKeys.transfers.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.transfers.all, 'detail', id] as const,
  },

  // Ledger
  ledger: {
    all: ['ledger'] as const,
    list: (params?: Record<string, any>) =>
      [...queryKeys.ledger.all, 'list', params] as const,
    lists: (params?: Record<string, any>) =>
      [...queryKeys.ledger.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.ledger.all, 'detail', id] as const,
    balance: (accountId: string) =>
      [...queryKeys.ledger.all, 'balance', accountId] as const,
    tenantBalance: (tenantId?: string) =>
      [...queryKeys.ledger.all, 'tenantBalance', tenantId] as const,
    projectBalance: (projectId?: string) =>
      [...queryKeys.ledger.all, 'projectBalance', projectId] as const,
  },

  // Reconciliation
  reconciliation: {
    all: ['reconciliation'] as const,
    list: (params?: Record<string, any>) =>
      [...queryKeys.reconciliation.all, 'list', params] as const,
    lists: (params?: Record<string, any>) =>
      [...queryKeys.reconciliation.all, 'list', params] as const,
    detail: (id: string) =>
      [...queryKeys.reconciliation.all, 'detail', id] as const,
    batches: (params?: Record<string, any>) =>
      [...queryKeys.reconciliation.all, 'batches', params] as const,
    byProject: (projectId: string | number, params?: Record<string, any>) =>
      [...queryKeys.reconciliation.all, 'byProject', String(projectId), params] as const,
  },

  // Settlements
  settlements: {
    all: ['settlements'] as const,
    list: (params?: Record<string, any>) =>
      [...queryKeys.settlements.all, 'list', params] as const,
    lists: (params?: Record<string, any>) =>
      [...queryKeys.settlements.all, 'list', params] as const,
    detail: (id: string | number) =>
      [...queryKeys.settlements.all, 'detail', String(id)] as const,
    statistics: (params?: Record<string, any>) =>
      [...queryKeys.settlements.all, 'statistics', params] as const,
    overdue: (params?: Record<string, any>) =>
      [...queryKeys.settlements.all, 'overdue', params] as const,
    payments: (settlementId: string | number) =>
      [...queryKeys.settlements.all, 'payments', String(settlementId)] as const,
  },

  // Suppliers
  suppliers: {
    all: ['suppliers'] as const,
    list: (params?: Record<string, any>) =>
      [...queryKeys.suppliers.all, 'list', params] as const,
    lists: (params?: Record<string, any>) =>
      [...queryKeys.suppliers.all, 'list', params] as const,
    detail: (id: string | number) =>
      [...queryKeys.suppliers.all, 'detail', String(id)] as const,
    statistics: (params?: Record<string, any>) =>
      [...queryKeys.suppliers.all, 'statistics', params] as const,
    accounts: (supplierId: string | number) =>
      [...queryKeys.suppliers.all, 'accounts', String(supplierId)] as const,
    ledgerSummary: (supplierId: string | number) =>
      [...queryKeys.suppliers.all, 'ledgerSummary', String(supplierId)] as const,
  },

  // Reports
  reports: {
    all: ['reports'] as const,
    list: (params?: Record<string, any>) =>
      [...queryKeys.reports.all, 'list', params] as const,
    lists: (params?: Record<string, any>) =>
      [...queryKeys.reports.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.reports.all, 'detail', id] as const,
    dashboard: (params?: Record<string, any>) =>
      [...queryKeys.reports.all, 'dashboard', params] as const,
    performance: (params?: Record<string, any>) =>
      [...queryKeys.reports.all, 'performance', params] as const,
    profit: (params?: Record<string, any>) =>
      [...queryKeys.reports.all, 'profit', params] as const,
    reconciliation: (params?: Record<string, any>) =>
      [...queryKeys.reports.all, 'reconciliation', params] as const,
    financial: (params?: Record<string, any>) =>
      [...queryKeys.reports.all, 'financial', params] as const,
    trends: (params?: Record<string, any>) =>
      [...queryKeys.reports.all, 'trends', params] as const,
  },

  // Import Jobs
  importJobs: {
    all: ['importJobs'] as const,
    list: (params?: Record<string, any>) =>
      [...queryKeys.importJobs.all, 'list', params] as const,
    lists: (params?: Record<string, any>) =>
      [...queryKeys.importJobs.all, 'list', params] as const,
    detail: (id: string) =>
      [...queryKeys.importJobs.all, 'detail', id] as const,
    progress: (id: string) =>
      [...queryKeys.importJobs.all, 'progress', id] as const,
    statistics: () =>
      [...queryKeys.importJobs.all, 'statistics'] as const,
  },

  // Finance Profit
  profit: {
    all: ['profit'] as const,
    list: (params?: Record<string, any>) =>
      [...queryKeys.profit.all, 'list', params] as const,
    lists: (params?: Record<string, any>) =>
      [...queryKeys.profit.all, 'list', params] as const,
    summary: (params?: Record<string, any>) =>
      [...queryKeys.profit.all, 'summary', params] as const,
  },

  // Finance Profit (alias for backward compatibility)
  financeProfit: {
    all: ['financeProfit'] as const,
    list: (params?: Record<string, any>) =>
      ['financeProfit', 'list', params] as const,
    lists: (params?: Record<string, any>) =>
      ['financeProfit', 'list', params] as const,
    detail: (id: string) => ['financeProfit', 'detail', id] as const,
    summary: (params?: Record<string, any>) =>
      ['financeProfit', 'summary', params] as const,
    overview: (params?: Record<string, any>) =>
      ['financeProfit', 'overview', params] as const,
    byProject: (params?: string | number | Record<string, unknown>) =>
      ['financeProfit', 'byProject', params] as const,
    byAccount: (params?: string | number | Record<string, unknown>) =>
      ['financeProfit', 'byAccount', params] as const,
    byChannel: (params?: string | number | Record<string, unknown>) =>
      ['financeProfit', 'byChannel', params] as const,
    trend: (params?: Record<string, any>) =>
      ['financeProfit', 'trend', params] as const,
  },

  // Dashboard
  dashboard: {
    all: ['dashboard'] as const,
    stats: () => [...queryKeys.dashboard.all, 'stats'] as const,
    trends: (params?: Record<string, any>) =>
      [...queryKeys.dashboard.all, 'trends', params] as const,
  },

  // Fund Overview (资金总览)
  fund: {
    all: ['fund'] as const,
    overview: (params?: Record<string, any>) =>
      [...queryKeys.fund.all, 'overview', params] as const,
    byProject: (params?: Record<string, any>) =>
      [...queryKeys.fund.all, 'byProject', params] as const,
    byChannel: (params?: Record<string, any>) =>
      [...queryKeys.fund.all, 'byChannel', params] as const,
    receivables: () => [...queryKeys.fund.all, 'receivables'] as const,
    payments: () => [...queryKeys.fund.all, 'payments'] as const,
  },

  // Ad Spend (消耗明细) - C3-spend-detail.md
  adSpend: {
    all: ['adSpend'] as const,
    list: (params?: Record<string, any>) =>
      [...queryKeys.adSpend.all, 'list', params] as const,
    summary: (params?: Record<string, any>) =>
      [...queryKeys.adSpend.all, 'summary', params] as const,
    trend: (params?: Record<string, any>) =>
      [...queryKeys.adSpend.all, 'trend', params] as const,
    byProject: (params?: Record<string, any>) =>
      [...queryKeys.adSpend.all, 'byProject', params] as const,
    byAccount: (params?: Record<string, any>) =>
      [...queryKeys.adSpend.all, 'byAccount', params] as const,
  },

  // Weekly Briefs (周度简报) - B3-weekly-brief.md
  weeklyBriefs: {
    all: ['weeklyBriefs'] as const,
    list: (params?: Record<string, any>) =>
      [...queryKeys.weeklyBriefs.all, 'list', params] as const,
    detail: (id: number) =>
      [...queryKeys.weeklyBriefs.all, 'detail', id] as const,
    stats: (params?: Record<string, any>) =>
      [...queryKeys.weeklyBriefs.all, 'stats', params] as const,
    projectSummary: (projectId: number, weekStart: string) =>
      [...queryKeys.weeklyBriefs.all, 'projectSummary', projectId, weekStart] as const,
  },
};
