/**
 * 常量统一导出
 *
 * SoT 引用:
 * - STATE_MACHINE.md v2.9
 * - MASTER.md v4.9
 */

// 角色常量
export {
  ROLE_CONFIG,
  TECH_ROLE_CONFIG,
  TECH_ROLE_OPTIONS,
  BUSINESS_ROLE_OPTIONS,
  type RoleConfig,
} from './roles';

// 状态配置
export {
  // 配置对象
  DAILY_REPORT_STATUS_CONFIG,
  ACCOUNT_STATUS_CONFIG,
  TOPUP_STATUS_CONFIG,
  PROJECT_STATUS_CONFIG,
  CHANNEL_STATUS_CONFIG,
  // 选项列表
  DAILY_REPORT_STATUS_OPTIONS,
  ACCOUNT_STATUS_OPTIONS,
  TOPUP_STATUS_OPTIONS,
  PROJECT_STATUS_OPTIONS,
  CHANNEL_STATUS_OPTIONS,
  // 类型
  type StatusConfig,
} from './status-config';

// 权限矩阵 (TASK-FE-COMMON-002)
export {
  ROLE_PERMISSIONS,
  PERMISSION_LABELS,
  type Permission,
} from './permission-matrix';

// 状态变体 (TASK-FE-COMMON-003)
export {
  STATUS_VARIANT_COLORS,
  STATUS_VARIANT_LABELS,
  COMMON_STATUS_VARIANTS,
  getVariantClasses,
  getVariantFromStatus,
} from './status-variants';
