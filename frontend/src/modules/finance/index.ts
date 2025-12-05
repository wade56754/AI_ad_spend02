/**
 * Finance 模块入口
 *
 * 对齐：FRONTEND_MODULE_SHELL_PATTERN v1.0
 */

// Shell 组件 (主入口)
export { FinancePageShell } from './components';

// 子组件
export {
  FinanceKpiRow,
  FinanceTopupTable,
  SpendingTrendChart,
  PlatformPieChart,
  PlatformBarChart,
  MonthlyComparison,
  BudgetProjection,
  TeamBudgetList,
} from './components';

// Hooks
export { useFinanceFilters, useFinanceData } from './hooks';
export type { DataStatus } from './hooks';

// Types
export type {
  TopupStatus,
  FinanceFiltersState,
  TopupRequest,
  FinancialSummary,
  SpendingTrend,
  PlatformSpending,
  TeamSpending,
  FinanceDataState,
} from './types';
