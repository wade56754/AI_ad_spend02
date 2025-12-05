/**
 * Dashboard 模块组件导出
 */

// 页面级组件
export { DashboardHeader } from './DashboardHeader';

// 功能组件
export { DashboardKpiRow } from './DashboardKpiRow';
export { DashboardTrendSection } from './DashboardTrendSection';
export { DashboardRiskPanel } from './DashboardRiskPanel';
export { DashboardTodayTasks } from './DashboardTodayTasks';
export { DashboardFundsOverview } from './DashboardFundsOverview';

// 旧组件（保留向后兼容）
export { DashboardFilters } from './DashboardFilters';
export { KpiCards } from './KpiCards';
export { TrendSection } from './TrendSection';

// Re-export shared dashboard components
export { TodayTasksCard } from '@/components/dashboard/TodayTasksCard';
