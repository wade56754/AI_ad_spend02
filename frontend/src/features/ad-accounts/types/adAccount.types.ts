/**
 * Ad Account Types
 *
 * SoT 对齐:
 * - STATE_MACHINE.md v2.6 Section 7
 * - DATA_SCHEMA.md v5.2 (ad_accounts entity)
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

export interface AdAccount {
  id: string; // UUID
  name: string;
  project_id: string;
  channel_id: string;
  assigned_user_id?: string;
  status: AdAccountStatus;
  dead_reason?: string;
  created_by?: string;
  updated_by?: string;
  created_at: string;
  updated_at: string;
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
  name: string;
  project_id: string;
  channel_id: string;
  assigned_user_id?: string;
  status?: AdAccountStatus;
}

export interface AdAccountStatusUpdateInput {
  status: AdAccountStatus;
  dead_reason?: string;
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
