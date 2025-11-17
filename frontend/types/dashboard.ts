// Dashboard相关类型定义

export interface KPIData {
  title: string;
  value: string;
  subtitle?: string;
  color?: 'blue' | 'green' | 'orange' | 'purple';
  trend?: {
    value: string;
    direction: 'up' | 'down' | 'neutral';
  };
}

export interface TrendDataPoint {
  date: string;
  value: number;
  label?: string;
}

export interface ChartSegment {
  name: string;
  value: number;
  color: string;
}

export interface Project {
  id: string;
  name: string;
  client: string;
  manager: string;
  status: 'active' | 'pending' | 'completed' | 'paused';
  budget: {
    total: number;
    spent: number;
  };
  roi: number;
  createdAt: string;
}

export interface DashboardData {
  kpis: KPIData[];
  trendData: TrendDataPoint[];
  distributionData: ChartSegment[];
  projects: Project[];
}