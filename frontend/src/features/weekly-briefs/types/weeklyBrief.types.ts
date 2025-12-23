/**
 * Weekly Brief Types
 *
 * SoT 对齐: B3-weekly-brief.md §2.2-2.5
 *
 * @module features/weekly-briefs/types
 */

// ========== 周报状态 ==========

/**
 * 周报状态
 * SoT 对齐: B3-weekly-brief.md §2.5
 */
export type WeeklyBriefStatus = 'draft' | 'submitted';

// ========== 核心类型 ==========

/**
 * 周报实体
 * SoT 对齐: B3-weekly-brief.md §2.2
 */
export interface WeeklyBrief {
  /** 周报 ID */
  id: number;
  /** 项目 ID */
  project_id: number;
  /** 项目名称 (JOIN) */
  project_name?: string;
  /** 周开始日期 (周一, ISO 格式) */
  week_start: string;
  /** 周结束日期 (周日, ISO 格式) */
  week_end: string;
  /** 周次标签 (如 "2025年第51周") */
  week_label?: string;
  /** 提交人 ID */
  submitter_id: string;
  /** 提交人姓名 (JOIN) */
  submitter_name?: string;
  /** 状态 */
  status: WeeklyBriefStatus;
  /** 周消耗 (自动汇总) */
  weekly_spend: number;
  /** 周进粉 (自动汇总) */
  weekly_conversions: number;
  /** 周 CPL (计算) */
  weekly_cpl: number;
  /** CPL 环比变化 (%) */
  cpl_trend?: number | null;
  /** 本周成果 */
  achievements?: string | null;
  /** 遇到问题 */
  issues?: string | null;
  /** 解决方案 */
  solutions?: string | null;
  /** 下周计划 */
  next_week_plan?: string | null;
  /** 提交时间 */
  submitted_at?: string | null;
  /** 创建时间 */
  created_at: string;
  /** 更新时间 */
  updated_at: string;
}

// ========== 统计类型 ==========

/**
 * 周报统计信息
 * SoT 对齐: B3-weekly-brief.md §4.2
 */
export interface WeeklyBriefStats {
  /** 本周项目总数 */
  total_projects: number;
  /** 已提交数 */
  submitted_count: number;
  /** 草稿数 */
  draft_count: number;
  /** 提交率 (%) */
  submission_rate: number;
  /** 本周总消耗 */
  total_weekly_spend: number;
}

/**
 * 周数据汇总
 * SoT 对齐: B3-weekly-brief.md §4.2 项目周数据汇总
 */
export interface WeeklySummary {
  /** 项目 ID */
  project_id: number;
  /** 项目名称 */
  project_name: string;
  /** 周开始日期 */
  week_start: string;
  /** 周结束日期 */
  week_end: string;
  /** 周消耗 */
  weekly_spend: number;
  /** 周进粉 */
  weekly_conversions: number;
  /** 周 CPL */
  weekly_cpl: number;
  /** 目标 CPL */
  target_cpl?: number | null;
  /** CPL vs 目标 (%) */
  cpl_vs_target?: number | null;
  /** 上周数据 */
  last_week?: {
    spend: number;
    conversions: number;
    cpl: number;
  } | null;
  /** 趋势 */
  trends?: {
    spend_change: number;
    conversions_change: number;
    cpl_change: number;
  } | null;
  /** 每日明细 */
  daily_breakdown?: Array<{
    date: string;
    spend: number;
    conversions: number;
  }>;
}

// ========== 请求类型 ==========

/**
 * 周报列表查询参数
 */
export interface WeeklyBriefListParams {
  /** 周次 (如 "2025-W51") */
  week?: string;
  /** 周开始日期 */
  week_start?: string;
  /** 项目 ID */
  project_id?: number;
  /** 状态筛选 */
  status?: WeeklyBriefStatus;
  /** 页码 */
  page?: number;
  /** 每页数量 */
  page_size?: number;
}

/**
 * 创建周报请求
 * SoT 对齐: B3-weekly-brief.md §4.2
 */
export interface CreateWeeklyBriefRequest {
  /** 项目 ID */
  project_id: number;
  /** 周开始日期 (周一) */
  week_start: string;
  /** 本周成果 */
  achievements?: string;
  /** 遇到问题 */
  issues?: string;
  /** 解决方案 */
  solutions?: string;
  /** 下周计划 */
  next_week_plan?: string;
}

/**
 * 更新周报请求
 */
export interface UpdateWeeklyBriefRequest {
  /** 本周成果 */
  achievements?: string;
  /** 遇到问题 */
  issues?: string;
  /** 解决方案 */
  solutions?: string;
  /** 下周计划 */
  next_week_plan?: string;
}

// ========== 响应类型 ==========

/**
 * 周报列表响应
 */
export interface WeeklyBriefListResponse {
  /** 周报列表 */
  items: WeeklyBrief[];
  /** 总数 */
  total: number;
  /** 当前页 */
  page: number;
  /** 每页数量 */
  page_size: number;
  /** 统计信息 */
  stats?: WeeklyBriefStats;
}

/**
 * 提交周报响应
 */
export interface SubmitWeeklyBriefResponse {
  /** 周报 ID */
  id: number;
  /** 状态 */
  status: WeeklyBriefStatus;
  /** 提交时间 */
  submitted_at: string;
}
