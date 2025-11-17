/**
 * 项目管理模块类型定义
 */

export type ProjectStatus = 'planning' | 'active' | 'paused' | 'completed';

export type ProjectPriority = 'low' | 'medium' | 'high';

export type ProjectSortBy =
  | 'name'
  | 'created_at'
  | 'updated_at'
  | 'budget'
  | 'current_spend'
  | 'roi'
  | 'start_date';

export type SortOrder = 'asc' | 'desc';

export interface Project {
  id: number;
  name: string;
  description?: string;
  client_name: string;
  client_id?: number;
  status: ProjectStatus;
  priority: ProjectPriority;
  budget: number;
  current_spend: number;
  remaining_budget: number;
  budget_utilization: number; // 预算使用率 (0-100)
  team_lead: string;
  team_lead_id?: number;
  team_size?: number;
  start_date: string;
  end_date: string;
  actual_end_date?: string;
  roi: number;
  total_conversions?: number;
  total_impressions?: number;
  total_clicks?: number;
  cpc?: number;
  cpm?: number;
  ctr?: number;
  created_at: string;
  updated_at: string;
  created_by: string;
  notes?: string;
  tags?: string[];
  platforms?: Platform[];
  industry?: string;
  region?: string;
}

export type Platform =
  | 'facebook'
  | 'google'
  | 'tiktok'
  | 'instagram'
  | 'youtube'
  | 'twitter'
  | 'linkedin';

export interface ProjectStats {
  total_projects: number;
  active_projects: number;
  completed_projects: number;
  planning_projects: number;
  paused_projects: number;
  total_budget: number;
  total_spend: number;
  remaining_budget: number;
  average_roi: number;
  total_conversions: number;
  total_impressions: number;
  total_clicks: number;
  average_ctr: number;
  average_cpc: number;
  high_priority_projects: number;
  overdue_projects: number;
  projects_this_month: number;
  completion_rate: number;
}

export interface ProjectFilters {
  search_term: string;
  status: ProjectStatus | 'all';
  priority: ProjectPriority | 'all';
  client_id?: number | 'all';
  team_lead_id?: number | 'all';
  platform: Platform | 'all';
  date_range: {
    start?: string;
    end?: string;
  };
  budget_range: {
    min?: number;
    max?: number;
  };
  roi_range: {
    min?: number;
    max?: number;
  };
  has_overdue: boolean | null;
  tags: string[];
  sort_by: ProjectSortBy;
  sort_order: SortOrder;
}

export interface ProjectCreateRequest {
  name: string;
  description?: string;
  client_name: string;
  client_id?: number;
  priority: ProjectPriority;
  budget: number;
  team_lead_id: number;
  start_date: string;
  end_date: string;
  platforms: Platform[];
  industry?: string;
  region?: string;
  notes?: string;
  tags?: string[];
}

export interface ProjectUpdateRequest {
  name?: string;
  description?: string;
  status?: ProjectStatus;
  priority?: ProjectPriority;
  budget?: number;
  team_lead_id?: number;
  end_date?: string;
  notes?: string;
  tags?: string[];
  platforms?: Platform[];
}

export interface ProjectDetail extends Project {
  team_members?: TeamMember[];
  milestones?: Milestone[];
  recent_activities?: Activity[];
  performance_data?: PerformanceData;
  budget_breakdown?: BudgetBreakdown;
  client_info?: ClientInfo;
}

export interface TeamMember {
  id: number;
  name: string;
  role: string;
  email: string;
  avatar?: string;
  join_date: string;
  is_active: boolean;
  responsibilities: string[];
}

export interface Milestone {
  id: number;
  title: string;
  description?: string;
  due_date: string;
  completed_date?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'overdue';
  progress: number; // 0-100
  assignee?: string;
  priority: 'low' | 'medium' | 'high';
}

export interface Activity {
  id: number;
  type: 'created' | 'updated' | 'status_changed' | 'budget_updated' | 'team_changed' | 'milestone_completed';
  description: string;
  actor: string;
  actor_role: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface PerformanceData {
  daily_spend: number[];
  daily_conversions: number[];
  daily_impressions: number[];
  daily_clicks: number[];
  ctr_trend: number[];
  cpc_trend: number[];
  roi_trend: number[];
  last_updated: string;
}

export interface BudgetBreakdown {
  ad_spend: number;
  creative_cost: number;
  tool_cost: number;
  service_fee: number;
  other_costs: number;
  total: number;
}

export interface ClientInfo {
  id: number;
  name: string;
  industry: string;
  contact_person: string;
  email: string;
  phone?: string;
  address?: string;
  created_at: string;
}

export interface KPICardConfig {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: 'primary' | 'success' | 'warning' | 'destructive' | 'info' | 'default';
  icon?: React.ComponentType<{ className?: string }>;
  trend?: {
    type: 'up' | 'down' | 'neutral';
    value: number;
    period?: string;
  };
}

export interface ProjectTableRow {
  project: Project;
  isSelected: boolean;
}

export interface ProjectTableColumn {
  key: string;
  title: string;
  width?: string;
  sortable?: boolean;
  align?: 'left' | 'center' | 'right';
  render?: (value: any, record: Project) => React.ReactNode;
}

export interface BatchOperation {
  type: 'status_change' | 'priority_update' | 'delete' | 'export' | 'assign';
  targetIds: number[];
  payload?: any;
}

export interface ProjectFormData {
  name: string;
  description?: string;
  client_name: string;
  priority: ProjectPriority;
  budget: string;
  team_lead_id: number;
  start_date: string;
  end_date: string;
  platforms: Platform[];
  industry?: string;
  region?: string;
  notes?: string;
  tags: string[];
}