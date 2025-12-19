/**
 * Library exports
 *
 * @module lib
 */

// Utilities
export { cn } from './utils';

// API Client
export {
  apiFetch,
  apiFetchPaginated,
  apiGet,
  apiPost,
  apiPatch,
  apiPut,
  apiDelete,
  apiUpload,
  apiDownload,
  apiRequest,
  queryKeys,
  ApiRequestError,
  ApiError,
  isApiError,
} from './api';

export type {
  PaginatedResponse,
  ApiError as ApiErrorType,
  ApiResponse,
  ApiFetchOptions,
  PaginationMeta,
} from './api';
