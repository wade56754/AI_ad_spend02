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
 * Paginated response structure (aligned with backend paginated_response)
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
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
 */
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;

  // Try localStorage first, then sessionStorage
  return (
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
 * Handle API error response
 */
async function handleErrorResponse(response: Response): Promise<never> {
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

  // Handle 401 - redirect to login
  if (response.status === 401) {
    if (typeof window !== 'undefined') {
      // Clear tokens
      localStorage.removeItem('access_token');
      sessionStorage.removeItem('access_token');

      // Redirect to login (unless already on login page)
      if (!window.location.pathname.includes('/login')) {
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
    await handleErrorResponse(response);
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
 * @example
 * const { items, total, page } = await apiFetchPaginated<User>('/api/v1/users?page=1');
 */
export async function apiFetchPaginated<T>(
  url: string,
  options: ApiFetchOptions = {}
): Promise<PaginatedResponse<T>> {
  return apiFetch<PaginatedResponse<T>>(url, options);
}

// ============================================================================
// Convenience Functions
// ============================================================================

/**
 * GET request helper
 */
export async function apiGet<T>(url: string): Promise<T> {
  return apiFetch<T>(url, { method: 'GET' });
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
    await handleErrorResponse(response);
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
    await handleErrorResponse(response);
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
    list: (params?: Record<string, unknown>) =>
      [...queryKeys.users.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.users.all, 'detail', id] as const,
  },

  // Projects
  projects: {
    all: ['projects'] as const,
    list: (params?: Record<string, unknown>) =>
      [...queryKeys.projects.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.projects.all, 'detail', id] as const,
  },

  // Channels
  channels: {
    all: ['channels'] as const,
    list: (params?: Record<string, unknown>) =>
      [...queryKeys.channels.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.channels.all, 'detail', id] as const,
  },

  // Ad Accounts
  adAccounts: {
    all: ['adAccounts'] as const,
    list: (params?: Record<string, unknown>) =>
      [...queryKeys.adAccounts.all, 'list', params] as const,
    detail: (id: string) =>
      [...queryKeys.adAccounts.all, 'detail', id] as const,
  },

  // Daily Reports
  dailyReports: {
    all: ['dailyReports'] as const,
    list: (params?: Record<string, unknown>) =>
      [...queryKeys.dailyReports.all, 'list', params] as const,
    detail: (id: string) =>
      [...queryKeys.dailyReports.all, 'detail', id] as const,
    stats: (params?: Record<string, unknown>) =>
      [...queryKeys.dailyReports.all, 'stats', params] as const,
  },

  // Topups
  topups: {
    all: ['topups'] as const,
    list: (params?: Record<string, unknown>) =>
      [...queryKeys.topups.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.topups.all, 'detail', id] as const,
    stats: (params?: Record<string, unknown>) =>
      [...queryKeys.topups.all, 'stats', params] as const,
  },

  // Transfers
  transfers: {
    all: ['transfers'] as const,
    list: (params?: Record<string, unknown>) =>
      [...queryKeys.transfers.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.transfers.all, 'detail', id] as const,
  },

  // Ledger
  ledger: {
    all: ['ledger'] as const,
    list: (params?: Record<string, unknown>) =>
      [...queryKeys.ledger.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.ledger.all, 'detail', id] as const,
    balance: (accountId: string) =>
      [...queryKeys.ledger.all, 'balance', accountId] as const,
  },

  // Reconciliation
  reconciliation: {
    all: ['reconciliation'] as const,
    list: (params?: Record<string, unknown>) =>
      [...queryKeys.reconciliation.all, 'list', params] as const,
    detail: (id: string) =>
      [...queryKeys.reconciliation.all, 'detail', id] as const,
    batches: (params?: Record<string, unknown>) =>
      [...queryKeys.reconciliation.all, 'batches', params] as const,
  },

  // Settlements
  settlements: {
    all: ['settlements'] as const,
    list: (params?: Record<string, unknown>) =>
      [...queryKeys.settlements.all, 'list', params] as const,
    detail: (id: string) =>
      [...queryKeys.settlements.all, 'detail', id] as const,
  },

  // Suppliers
  suppliers: {
    all: ['suppliers'] as const,
    list: (params?: Record<string, unknown>) =>
      [...queryKeys.suppliers.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.suppliers.all, 'detail', id] as const,
  },

  // Reports
  reports: {
    all: ['reports'] as const,
    list: (params?: Record<string, unknown>) =>
      [...queryKeys.reports.all, 'list', params] as const,
    detail: (id: string) => [...queryKeys.reports.all, 'detail', id] as const,
  },

  // Import Jobs
  importJobs: {
    all: ['importJobs'] as const,
    list: (params?: Record<string, unknown>) =>
      [...queryKeys.importJobs.all, 'list', params] as const,
    detail: (id: string) =>
      [...queryKeys.importJobs.all, 'detail', id] as const,
  },

  // Finance Profit
  profit: {
    all: ['profit'] as const,
    list: (params?: Record<string, unknown>) =>
      [...queryKeys.profit.all, 'list', params] as const,
    summary: (params?: Record<string, unknown>) =>
      [...queryKeys.profit.all, 'summary', params] as const,
  },

  // Dashboard
  dashboard: {
    all: ['dashboard'] as const,
    stats: () => [...queryKeys.dashboard.all, 'stats'] as const,
    trends: (params?: Record<string, unknown>) =>
      [...queryKeys.dashboard.all, 'trends', params] as const,
  },
};
