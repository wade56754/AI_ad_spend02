// Page component
export { FinancePage } from './FinancePage';

// Supporting components
export { FinanceOverviewCards } from './FinanceOverviewCards';
export { FinanceTrendChart } from './FinanceTrendChart';
export { FinanceTodoList } from './FinanceTodoList';
export { FinanceTransactions } from './FinanceTransactions';
export { FinanceQuickActions } from './FinanceQuickActions';

// V2 Pages (Task Spec Refactor)
export { FundOverviewPage } from './FundOverviewPage';
export { ProfitAnalysisPage } from './ProfitAnalysisPage';

// V2 Components - Fund Overview
export * from './FundOverview';

// V2 Components - Profit Analysis
export * from './ProfitAnalysis';

// TASK-FE-FIN-005: 权限守卫
// Note: LedgerPage is at @/features/ledger, ReconciliationPage is at @/features/reconciliation
export { FinanceGuard, useFinanceAccess } from './FinanceGuard';
export * from './FinanceAnalysisDashboard';
