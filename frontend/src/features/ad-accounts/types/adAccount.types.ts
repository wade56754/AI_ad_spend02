/**
 * Ad Account Types
 *
 * SoT 对齐:
 * - STATE_MACHINE.md v2.6 Section 7
 * - DATA_SCHEMA.md v5.2 (ad_accounts entity)
 * - init_schema.sql §5.1 ad_accounts 表
 */

// === Status Enum ===

export type AdAccountStatus =
  | 'new'
  | 'testing'
  | 'active'
  | 'suspended'
  | 'dead'
  | 'archived';

// === Entity Types ===

/**
 * AdAccount 实体 - 对齐 init_schema.sql §5.1
 *
 * 字段说明：
 * - id: BIGSERIAL 主键
 * - project_id: 项目ID
 * - channel_id: 渠道ID
 * - supplier_id: 供应商ID
 * - owner_id: 负责人ID
 * - name: 账户名称
 * - account_code: 账户代码
 * - status: 账户状态
 * - status_reason: 状态原因
 * - spend_limit: 消耗限额
 * - currency: 货币
 * - timezone: 时区
 */
export interface AdAccount {
  id: number; // BIGSERIAL
  project_id: number;
  channel_id?: string; // UUID
  supplier_id?: string; // UUID
  owner_id?: string; // UUID - 负责人
  name?: string; // 账户名称
  account_code?: string; // 账户代码
  status?: AdAccountStatus;
  status_reason?: string; // 状态原因
  spend_limit?: number; // DECIMAL(15,2)
  currency?: string; // 默认 CNY
  timezone?: string; // 默认 Asia/Shanghai
  created_by?: string;
  updated_by?: string;
  created_at: string;
  updated_at: string;

  // 聚合字段 (JOIN 查询时填充)
  project_name?: string;
  channel_name?: string;
  owner_name?: string;
}

// === List/Filter Types ===

export interface AdAccountListParams {
  page?: number;
  page_size?: number;
  status?: AdAccountStatus;
  project_id?: string;
  channel_id?: string;
}

// === Form Types ===

export interface AdAccountCreateInput {
  project_id: number;
  channel_id?: string;
  supplier_id?: string;
  owner_id?: string;
  name?: string;
  account_code?: string;
  status?: AdAccountStatus;
  spend_limit?: number;
  currency?: string;
  timezone?: string;
}

export interface AdAccountUpdateInput {
  name?: string;
  project_id?: number;
  channel_id?: string;
  supplier_id?: string;
  owner_id?: string;
  status?: AdAccountStatus;
  status_reason?: string;
  spend_limit?: number;
  currency?: string;
  timezone?: string;
}

export interface AdAccountStatusUpdateInput {
  status: AdAccountStatus;
  status_reason?: string;
  updated_by?: string;
}

// === State Transitions ===

export const ALLOWED_TRANSITIONS: Record<AdAccountStatus, AdAccountStatus[]> = {
  new: ['testing'],
  testing: ['active'],
  active: ['suspended', 'dead'],
  suspended: ['dead', 'active'],
  dead: ['archived'],
  archived: [],
};

// === Status Display Config ===

export const AD_ACCOUNT_STATUS_CONFIG: Record<AdAccountStatus, {
  label: string;
  variant: 'default' | 'success' | 'warning' | 'error' | 'info';
}> = {
  new: { label: '新建', variant: 'default' },
  testing: { label: '测试中', variant: 'info' },
  active: { label: '活跃', variant: 'success' },
  suspended: { label: '暂停', variant: 'warning' },
  dead: { label: '死号', variant: 'error' },
  archived: { label: '归档', variant: 'default' },
};

// === 向后兼容别名 ===

/** @deprecated 使用 owner_id */
export type AssignedUserId = string;

/** @deprecated 使用 status_reason */
export type DeadReason = string;
