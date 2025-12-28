/**
 * Dashboard Module
 * 
 * 注意: TrendDataPoint 从 types 导出，组件中使用 TrendDataPoint as MainTrendDataPoint
 */

// 类型优先导出
export * from './types';

// 组件导出 (排除重名类型)
export { 
  DashboardPage,
  DashboardHeader,
  StatCard,
  KpiCards,
  OpsStatusCards,
  QuickActions,
  PendingTasksCard,
  QuickActionsCard,
  AccountOverviewCard,
  SystemStatusCard,
  StatCardSkeleton,
  TrendChartSkeleton,
  CardSkeleton,
  GlobalDateFilter,
  getDateRangeFromPreset,
  AlertBanner,
  generateMockAlerts,
  MainTrendChart,
  generateSummary,
  TopLists,
  generateMockTopLists,
} from './components';

// 重新导出组件特定类型 (避免冲突)
export type { 
  DateRangePreset,
  MetricType,
  Alert,
  KpiData,
  Average7d,
  OpsStatusData,
} from './components';
