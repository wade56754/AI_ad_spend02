/**
 * Global Hooks
 *
 * Export all global hooks from this file
 */

export { useTheme } from './use-theme';
export { useIsMounted, useDeferredRender } from './useIsMounted';
export { useTableParams, serializeTableParams } from './use-table-params';
export type { TableParams, SortOrder } from './use-table-params';

// 权限检查 Hook (TASK-FE-COMMON-002)
export {
  usePermission,
  usePermissionGuard,
  useRoleCheck,
} from './usePermission';
export type { UsePermissionReturn } from './usePermission';

// 列表查询 Hook (TASK-FE-COMMON-005)
export { useListQuery } from './useListQuery';
export type {
  ListParams,
  UseListQueryOptions,
  UseListQueryReturn,
} from './useListQuery';
// 注意: PaginatedResponse 从 @/lib/api 重新导出
export type { PaginatedResponse } from '@/lib/api';
