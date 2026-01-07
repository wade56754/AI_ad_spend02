/**
 * Global Hooks
 *
 * Export all global hooks from this file
 */

export { useTheme } from './use-theme';
export { useIsMounted } from './useIsMounted';
export { useTableParams, serializeTableParams } from './use-table-params';
export type { TableParams, SortOrder } from './use-table-params';

// 权限检查 Hook (TASK-FE-COMMON-002)
export {
  usePermission,
  isCeo,
  getBusinessRole,
  getRolePermissions,
} from './usePermission';
export type { Permission, UsePermissionReturn } from './usePermission';

// 列表查询 Hook (TASK-FE-COMMON-005)
export { useListQuery } from './useListQuery';
export type {
  PaginatedResponse,
  ListQueryParams,
  UseListQueryOptions,
  UseListQueryReturn,
} from './useListQuery';
