/**
 * Project Types
 *
 * 项目管理模块类型定义
 * Aligned with DATA_SCHEMA.md v5.2 (projects table)
 */

import type { UUID, ISODateString, DateString, Money } from '@/types';

// === Status Enum ===

export type ProjectStatus = 'active' | 'paused' | 'completed' | 'archived';

// === Entity Types ===

export interface Project {
  id: UUID;
  name: string;
  description?: string;
  client_name: string;
  status: ProjectStatus;

  // 预算与消耗
  budget_total: Money;
  budget_daily?: Money;
  spent_total: Money;
  spent_today: Money;

  // 关联账户
  ad_account_count: number;

  // 时间信息
  start_date: DateString;
  end_date?: DateString;
  created_at: ISODateString;
  updated_at: ISODateString;
}

// === List/Filter Types ===

export interface ProjectFilters {
  status?: ProjectStatus | ProjectStatus[];
  client_name?: string;
  search?: string;
  start_date?: DateString;
  end_date?: DateString;
}

export interface ProjectListParams extends ProjectFilters {
  page?: number;
  page_size?: number;
  sort_by?: 'name' | 'status' | 'spent_total' | 'created_at';
  sort_order?: 'asc' | 'desc';
}

// === Form Types ===

export interface ProjectCreateInput {
  name: string;
  description?: string;
  client_name: string;
  budget_total: number;
  budget_daily?: number;
  start_date: DateString;
  end_date?: DateString;
}

export interface ProjectUpdateInput {
  name?: string;
  description?: string;
  status?: ProjectStatus;
  budget_total?: number;
  budget_daily?: number;
  end_date?: DateString;
}

// === Summary Types ===

export interface ProjectSummary {
  total_projects: number;
  active_projects: number;
  total_budget: Money;
  total_spent: Money;
  today_spent: Money;
}

// === Status Display Config ===

export const PROJECT_STATUS_CONFIG: Record<ProjectStatus, { label: string; variant: 'default' | 'success' | 'warning' | 'error' | 'info' }> = {
  active: { label: '投放中', variant: 'success' },
  paused: { label: '已暂停', variant: 'warning' },
  completed: { label: '已完成', variant: 'info' },
  archived: { label: '已归档', variant: 'default' },
};
