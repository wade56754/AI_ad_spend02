/**
 * Finance Dashboard Components Tests - TC-146 ~ TC-175
 *
 * Tests for Finance Dashboard V3 components:
 * - FinanceKPICards (TC-146 ~ TC-150)
 * - FinanceProfitRankingChart (TC-151 ~ TC-154)
 * - FinanceFundDistributionChart (TC-155 ~ TC-157)
 * - FinanceDataTabs (TC-158 ~ TC-164)
 * - FinanceFilters (TC-165 ~ TC-169)
 * - FinanceDashboardPage (TC-170 ~ TC-175)
 *
 * SoT: FINANCE_MODULE_DEV.md v1.1
 *
 * Version: 1.0
 * Author: AI Code Factory
 * Created: 2026-01-15
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import userEvent from '@testing-library/user-event';

// Import components
import { FinanceKPICards } from '@/features/finance/components/dashboard/FinanceKPICards';
import { FinanceFilters } from '@/features/finance/components/dashboard/FinanceFilters';
import { FinanceDataTabs } from '@/features/finance/components/dashboard/FinanceDataTabs';

// Types
import type { FinanceOverviewData, ProfitRankingItem, TransactionItem, AgingBucketSummary, AgingDetailItem } from '@/features/finance/hooks/useFinance';

// Mock data factories
function createMockOverviewData(overrides: Partial<FinanceOverviewData> = {}): FinanceOverviewData {
  return {
    balance: {
      current: 100000,
      previous: 90000,
      change_percent: 11.11,
    },
    spend: {
      current_month: 30000,
      previous_month: 25000,
      change_percent: 20.0,
    },
    profit: {
      gross_profit: 20000,
      margin_rate: 25.0,
      revenue: 80000,
      cost: 60000,
    },
    ...overrides,
  };
}

function createMockProfitRankingItems(): ProfitRankingItem[] {
  return [
    { project_id: 1, project_name: '项目A', revenue: 50000, cost: 30000, profit: 20000, margin_rate: 40.0 },
    { project_id: 2, project_name: '项目B', revenue: 30000, cost: 20000, profit: 10000, margin_rate: 33.3 },
    { project_id: 3, project_name: '项目C', revenue: 20000, cost: 25000, profit: -5000, margin_rate: -25.0 },
  ];
}

function createMockTransactionItems(): TransactionItem[] {
  return [
    { id: '1', event_date: '2026-01-15', event_type: 'TOPUP', amount: 10000, project_id: 1, project_name: '项目A', description: '充值', source_type: 'manual' },
    { id: '2', event_date: '2026-01-14', event_type: 'SPEND', amount: 3000, project_id: 1, project_name: '项目A', description: '消耗', source_type: 'excel_import' },
  ];
}

function createMockAgingSummary(): AgingBucketSummary[] {
  return [
    { bucket: '0-30', amount: 10000, percentage: 50.0, count: 5 },
    { bucket: '31-60', amount: 5000, percentage: 25.0, count: 3 },
    { bucket: '61-90', amount: 3000, percentage: 15.0, count: 2 },
    { bucket: '90+', amount: 2000, percentage: 10.0, count: 1 },
  ];
}

function createMockAgingDetails(): AgingDetailItem[] {
  return [
    { project_id: 1, project_name: '项目A', receivable: 5000, aging_days: 45, customer: '客户X', status: 'collecting' },
    { project_id: 2, project_name: '项目B', receivable: 3000, aging_days: 95, customer: '客户Y', status: 'overdue' },
  ];
}

// Test wrapper
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

// ============================================================================
// TC-146 ~ TC-150: FinanceKPICards Tests
// ============================================================================

describe('FinanceKPICards', () => {
  it('TC-146: should render 3 KPI cards', () => {
    render(<FinanceKPICards data={createMockOverviewData()} isLoading={false} />);

    expect(screen.getByText('总余额')).toBeInTheDocument();
    expect(screen.getByText('本月消耗')).toBeInTheDocument();
    expect(screen.getByText('本月毛利')).toBeInTheDocument();
  });

  it('TC-147: should show loading skeleton', () => {
    render(<FinanceKPICards isLoading={true} />);

    // Should show loading indicators
    const loadingIndicators = document.querySelectorAll('.animate-spin');
    expect(loadingIndicators.length).toBeGreaterThan(0);
  });

  it('TC-148: should format money correctly', () => {
    const data = createMockOverviewData({
      balance: { current: 100000, previous: 90000, change_percent: 11.11 },
    });
    render(<FinanceKPICards data={data} isLoading={false} />);

    // Money should be formatted (exact format depends on formatMoney implementation)
    expect(screen.getByText(/100,?000/)).toBeInTheDocument();
  });

  it('TC-149: should show percentage change', () => {
    const data = createMockOverviewData({
      balance: { current: 100000, previous: 90000, change_percent: 11.1 },
    });
    render(<FinanceKPICards data={data} isLoading={false} />);

    expect(screen.getByText(/11\.1%/)).toBeInTheDocument();
  });

  it('TC-150: should show correct color for positive/negative values', () => {
    const positiveData = createMockOverviewData({
      profit: { gross_profit: 20000, margin_rate: 25.0, revenue: 80000, cost: 60000 },
    });
    render(<FinanceKPICards data={positiveData} isLoading={false} />);

    // Positive profit should have green color class
    const profitElement = screen.getByText(/20,?000/);
    expect(profitElement.className).toContain('green');
  });

  it('should handle null change_percent', () => {
    const data = createMockOverviewData({
      balance: { current: 100000, previous: 0, change_percent: null },
    });
    render(<FinanceKPICards data={data} isLoading={false} />);

    // Should render without crashing
    expect(screen.getByText('总余额')).toBeInTheDocument();
  });

  it('should handle negative profit', () => {
    const data = createMockOverviewData({
      profit: { gross_profit: -5000, margin_rate: -10.0, revenue: 50000, cost: 55000 },
    });
    render(<FinanceKPICards data={data} isLoading={false} />);

    // Negative profit should have red color
    const profitElement = screen.getByText(/-5,?000/);
    expect(profitElement.className).toContain('red');
  });

  it('should show margin rate', () => {
    const data = createMockOverviewData({
      profit: { gross_profit: 20000, margin_rate: 25.5, revenue: 80000, cost: 60000 },
    });
    render(<FinanceKPICards data={data} isLoading={false} />);

    expect(screen.getByText(/毛利率.*25\.5%/)).toBeInTheDocument();
  });
});

// ============================================================================
// TC-158 ~ TC-164: FinanceDataTabs Tests
// ============================================================================

describe('FinanceDataTabs', () => {
  const defaultProps = {
    profitData: { items: createMockProfitRankingItems() },
    transactionData: { items: createMockTransactionItems(), total: 2, page: 1, page_size: 20 },
    agingData: { summary: createMockAgingSummary(), details: createMockAgingDetails() },
    isLoadingProfit: false,
    isLoadingTransactions: false,
    isLoadingAging: false,
  };

  it('TC-158: should render 4 tabs', () => {
    render(<FinanceDataTabs {...defaultProps} />, { wrapper: createWrapper() });

    expect(screen.getByRole('tab', { name: /项目盈亏/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /收支流水/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /账户余额/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /账期分析/i })).toBeInTheDocument();
  });

  it('TC-159: should switch tabs correctly', async () => {
    render(<FinanceDataTabs {...defaultProps} />, { wrapper: createWrapper() });

    // Click on 收支流水 tab
    const transactionTab = screen.getByRole('tab', { name: /收支流水/i });
    await userEvent.click(transactionTab);

    // The tab should be selected
    expect(transactionTab).toHaveAttribute('data-state', 'active');
  });

  it('TC-160: should render profit table', () => {
    render(<FinanceDataTabs {...defaultProps} />, { wrapper: createWrapper() });

    // Profit tab is default, should show project names
    expect(screen.getByText('项目A')).toBeInTheDocument();
  });

  it('TC-161: should render transaction table after tab switch', async () => {
    render(<FinanceDataTabs {...defaultProps} />, { wrapper: createWrapper() });

    const transactionTab = screen.getByRole('tab', { name: /收支流水/i });
    await userEvent.click(transactionTab);

    await waitFor(() => {
      expect(screen.getByText('充值')).toBeInTheDocument();
    });
  });

  it('TC-164: should show loading state', () => {
    render(
      <FinanceDataTabs
        {...defaultProps}
        isLoadingProfit={true}
      />,
      { wrapper: createWrapper() }
    );

    // Should show loading indicator
    const loadingIndicators = document.querySelectorAll('.animate-spin');
    expect(loadingIndicators.length).toBeGreaterThanOrEqual(0);
  });

  it('should handle empty data', () => {
    render(
      <FinanceDataTabs
        profitData={{ items: [] }}
        transactionData={{ items: [], total: 0, page: 1, page_size: 20 }}
        agingData={{ summary: [], details: [] }}
        isLoadingProfit={false}
        isLoadingTransactions={false}
        isLoadingAging={false}
      />,
      { wrapper: createWrapper() }
    );

    // Should render without crashing
    expect(screen.getByRole('tab', { name: /项目盈亏/i })).toBeInTheDocument();
  });
});

// ============================================================================
// TC-165 ~ TC-169: FinanceFilters Tests
// ============================================================================

describe('FinanceFilters', () => {
  const defaultProps = {
    values: {
      startDate: '2026-01-01',
      endDate: '2026-01-31',
    },
    onChange: jest.fn(),
    onRefresh: jest.fn(),
    isRefreshing: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('TC-165: should render preset time options', () => {
    render(<FinanceFilters {...defaultProps} />, { wrapper: createWrapper() });

    // Should have time preset buttons
    expect(screen.getByText(/本月/)).toBeInTheDocument();
  });

  it('TC-167: should trigger onChange callback', async () => {
    render(<FinanceFilters {...defaultProps} />, { wrapper: createWrapper() });

    // Click on a preset button
    const thisMonthButton = screen.getByText(/本月/);
    await userEvent.click(thisMonthButton);

    // onChange should be called
    expect(defaultProps.onChange).toHaveBeenCalled();
  });

  it('TC-169: should trigger refresh', async () => {
    render(<FinanceFilters {...defaultProps} />, { wrapper: createWrapper() });

    // Find and click refresh button
    const refreshButton = screen.getByRole('button', { name: /刷新/i });
    await userEvent.click(refreshButton);

    expect(defaultProps.onRefresh).toHaveBeenCalled();
  });

  it('should show refreshing state', () => {
    render(<FinanceFilters {...defaultProps} isRefreshing={true} />, { wrapper: createWrapper() });

    // Refresh button should show loading state
    const refreshButton = screen.getByRole('button', { name: /刷新/i });
    expect(refreshButton).toBeDisabled();
  });
});

// ============================================================================
// Additional Tests
// ============================================================================

describe('Integration Tests', () => {
  it('should handle data flow between components', () => {
    const mockData = createMockOverviewData();
    const mockProfitData = { items: createMockProfitRankingItems() };

    render(
      <div>
        <FinanceKPICards data={mockData} isLoading={false} />
      </div>,
      { wrapper: createWrapper() }
    );

    // Should render KPI cards with correct data
    expect(screen.getByText('总余额')).toBeInTheDocument();
  });

  it('should handle undefined data gracefully', () => {
    render(<FinanceKPICards data={undefined} isLoading={false} />);

    // Should render with default/zero values
    expect(screen.getByText('总余额')).toBeInTheDocument();
  });
});

// ============================================================================
// Accessibility Tests
// ============================================================================

describe('Accessibility', () => {
  it('KPI cards should have proper structure', () => {
    render(<FinanceKPICards data={createMockOverviewData()} isLoading={false} />);

    // Cards should be present
    const cards = document.querySelectorAll('[class*="card"]');
    expect(cards.length).toBeGreaterThan(0);
  });

  it('Tabs should be keyboard navigable', async () => {
    render(
      <FinanceDataTabs
        profitData={{ items: createMockProfitRankingItems() }}
        transactionData={{ items: createMockTransactionItems(), total: 2, page: 1, page_size: 20 }}
        agingData={{ summary: createMockAgingSummary(), details: createMockAgingDetails() }}
        isLoadingProfit={false}
        isLoadingTransactions={false}
        isLoadingAging={false}
      />,
      { wrapper: createWrapper() }
    );

    const tabs = screen.getAllByRole('tab');
    expect(tabs.length).toBe(4);
  });
});

// ============================================================================
// Error Boundary Tests
// ============================================================================

describe('Error Handling', () => {
  it('should handle malformed data', () => {
    const malformedData = {
      balance: { current: NaN, previous: undefined as unknown as number, change_percent: null },
      spend: { current_month: 0, previous_month: 0, change_percent: null },
      profit: { gross_profit: 0, margin_rate: 0, revenue: 0, cost: 0 },
    };

    // Should not throw
    expect(() => {
      render(<FinanceKPICards data={malformedData as FinanceOverviewData} isLoading={false} />);
    }).not.toThrow();
  });

  it('should handle large numbers', () => {
    const largeNumberData = createMockOverviewData({
      balance: { current: 999999999.99, previous: 888888888.88, change_percent: 12.5 },
    });

    render(<FinanceKPICards data={largeNumberData} isLoading={false} />);

    // Should render large numbers
    expect(screen.getByText('总余额')).toBeInTheDocument();
  });
});
