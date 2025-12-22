/**
 * Cost Analysis Types
 */

export interface CostBreakdown {
  category: string;
  amount: number;
  percentage: number;
  trend: number;
}

export interface CostSummary {
  total_cost: number;
  media_cost: number;
  service_fee: number;
  other_cost: number;
  period_start: string;
  period_end: string;
}

export interface CostTrend {
  date: string;
  cost: number;
  revenue: number;
  profit: number;
}

export interface CostAnalysisData {
  summary: CostSummary;
  breakdown: CostBreakdown[];
  trends: CostTrend[];
}
