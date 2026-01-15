/**
 * useProfit Hooks Tests
 *
 * Tests for frontend/src/features/finance-profit/hooks/useProfit.ts
 * SoT: BUSINESS_RULES.md v3.2 - 利润计算公式
 * SoT: MASTER.md v4.4 §6.5 页面 3 项目盈亏字段集
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useProfitOverview,
  useProfitSummary,
  useProfitByProject,
  useProfitByAccount,
  useProfitByChannel,
  useProfitTrend,
  useCompareProfits,
  useRefreshProfit,
} from '@/features/finance-profit/hooks/useProfit';
import * as profitApi from '@/features/finance-profit/services';

// Mock the profit API
jest.mock('@/features/finance-profit/services', () => ({
  getProfitOverview: jest.fn(),
  getProfitSummary: jest.fn(),
  getProfitByProject: jest.fn(),
  getProfitByAccount: jest.fn(),
  getProfitByChannel: jest.fn(),
  getProfitTrend: jest.fn(),
  compareProfits: jest.fn(),
}));

// Test wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe('useProfit Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ========== Profit Overview ==========

  describe('useProfitOverview', () => {
    it('should fetch profit overview successfully', async () => {
      const mockData = {
        today_revenue: 10000,
        today_cost: 8500,
        today_profit: 1500,
        today_profit_margin: 15.0,
        week_revenue: 50000,
        week_cost: 42500,
        week_profit: 7500,
        week_profit_margin: 15.0,
        month_revenue: 200000,
        month_cost: 170000,
        month_profit: 30000,
        month_profit_margin: 15.0,
        profit_change_from_yesterday: 10.5,
        profit_change_from_last_week: 8.2,
        profit_change_from_last_month: 12.0,
        top_profit_projects: [
          { project_id: 1, project_name: 'Project A', profit: 10000 },
          { project_id: 2, project_name: 'Project B', profit: 8000 },
        ],
      };

      (profitApi.getProfitOverview as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useProfitOverview(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.today_profit).toBe(1500);
      expect(result.current.data?.top_profit_projects).toHaveLength(2);
    });
  });

  // ========== Profit Summary ==========

  describe('useProfitSummary', () => {
    it('should fetch profit summary for specific month', async () => {
      const mockData = {
        items: [
          {
            report_date: '2025-01-15',
            project_id: 1,
            project_name: 'Project A',
            conversions_final: 100,
            unit_price: 200,
            revenue: 20000,
            real_spend: 15000,
            fee: 500,
            cost: 15500,
            profit: 4500,
            profit_margin: 22.5,
          },
        ],
        total_conversions: 100,
        total_revenue: 20000,
        total_cost: 15500,
        total_profit: 4500,
        overall_profit_margin: 22.5,
      };

      (profitApi.getProfitSummary as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useProfitSummary({ year: 2025, month: 1 }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.items).toHaveLength(1);
      expect(result.current.data?.overall_profit_margin).toBe(22.5);
      expect(profitApi.getProfitSummary).toHaveBeenCalledWith({ year: 2025, month: 1 });
    });
  });

  // ========== Profit By Project ==========

  describe('useProfitByProject', () => {
    it('should fetch profit by project successfully', async () => {
      const mockData = {
        items: [
          {
            project_id: 1,
            project_name: 'Project A',
            owner_id: 1,
            owner_name: 'Owner A',
            cpl: 150,
            cpl_target: 200,
            is_abnormal: false,
            total_conversions: 200,
            avg_unit_price: 200,
            total_revenue: 40000,
            total_spend: 30000,
            total_fee: 1000,
            total_cost: 31000,
            total_profit: 9000,
            profit_margin: 22.5,
            report_count: 10,
          },
        ],
        total_projects: 1,
        total_conversions: 200,
        total_revenue: 40000,
        total_cost: 31000,
        total_profit: 9000,
        overall_profit_margin: 22.5,
        abnormal_count: 0,
      };

      (profitApi.getProfitByProject as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useProfitByProject(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.items).toHaveLength(1);
      expect(result.current.data?.items[0].is_abnormal).toBe(false);
      expect(result.current.data?.abnormal_count).toBe(0);
    });

    it('should pass filter params to API', async () => {
      (profitApi.getProfitByProject as jest.Mock).mockResolvedValue({ items: [] });

      const params = { project_id: 1, start_date: '2025-01-01', end_date: '2025-01-31' };
      renderHook(() => useProfitByProject(params), { wrapper: createWrapper() });

      await waitFor(() => {
        expect(profitApi.getProfitByProject).toHaveBeenCalledWith(params);
      });
    });
  });

  // ========== Profit By Account ==========

  describe('useProfitByAccount', () => {
    it('should fetch profit by account successfully', async () => {
      const mockData = {
        items: [
          {
            ad_account_id: 1,
            ad_account_name: 'Account A',
            project_id: 1,
            project_name: 'Project A',
            total_conversions: 100,
            total_revenue: 20000,
            total_spend: 15000,
            total_cost: 15500,
            total_profit: 4500,
            profit_margin: 22.5,
          },
        ],
        total_accounts: 1,
        total_conversions: 100,
        total_revenue: 20000,
        total_cost: 15500,
        total_profit: 4500,
        overall_profit_margin: 22.5,
      };

      (profitApi.getProfitByAccount as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useProfitByAccount(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.items).toHaveLength(1);
      expect(result.current.data?.total_accounts).toBe(1);
    });
  });

  // ========== Profit By Channel ==========

  describe('useProfitByChannel', () => {
    it('should fetch profit by channel successfully', async () => {
      const mockData = {
        items: [
          {
            channel_id: 1,
            channel_name: 'Facebook',
            total_accounts: 10,
            total_conversions: 500,
            total_revenue: 100000,
            total_spend: 75000,
            total_cost: 77500,
            total_profit: 22500,
            profit_margin: 22.5,
          },
        ],
        total_channels: 1,
        total_conversions: 500,
        total_revenue: 100000,
        total_cost: 77500,
        total_profit: 22500,
        overall_profit_margin: 22.5,
      };

      (profitApi.getProfitByChannel as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useProfitByChannel(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.items).toHaveLength(1);
      expect(result.current.data?.items[0].channel_name).toBe('Facebook');
    });
  });

  // ========== Profit Trend ==========

  describe('useProfitTrend', () => {
    it('should fetch profit trend successfully', async () => {
      const mockData = {
        items: [
          {
            period: '2025-01',
            period_start: '2025-01-01',
            period_end: '2025-01-31',
            total_conversions: 1000,
            total_revenue: 200000,
            total_cost: 170000,
            total_profit: 30000,
            profit_margin: 15.0,
            profit_change: 5000,
            profit_change_rate: 20.0,
          },
        ],
        granularity: 'monthly',
        period_count: 1,
        avg_profit: 30000,
        max_profit: 30000,
        min_profit: 30000,
        profit_volatility: 0,
      };

      (profitApi.getProfitTrend as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useProfitTrend(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.items).toHaveLength(1);
      expect(result.current.data?.granularity).toBe('monthly');
    });

    it('should support granularity parameter', async () => {
      (profitApi.getProfitTrend as jest.Mock).mockResolvedValue({
        items: [],
        granularity: 'daily',
      });

      renderHook(() => useProfitTrend({ granularity: 'daily' as any }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(profitApi.getProfitTrend).toHaveBeenCalledWith({ granularity: 'daily' });
      });
    });
  });

  // ========== Compare Profits Mutation ==========

  describe('useCompareProfits', () => {
    it('should have mutate and mutateAsync functions', () => {
      const { result } = renderHook(() => useCompareProfits(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
      expect(result.current.isPending).toBe(false);
    });

    it('should call compareProfits on mutate', async () => {
      const mockData = {
        items: [
          {
            project_id: 1,
            project_name: 'Project A',
            total_profit: 10000,
            profit_margin: 20,
            rank_by_profit: 1,
            rank_by_margin: 1,
          },
          {
            project_id: 2,
            project_name: 'Project B',
            total_profit: 8000,
            profit_margin: 15,
            rank_by_profit: 2,
            rank_by_margin: 2,
          },
        ],
        compare_count: 2,
        best_profit_project: 'Project A',
        best_margin_project: 'Project A',
        total_profit: 18000,
        avg_profit_margin: 17.5,
      };

      (profitApi.compareProfits as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useCompareProfits(), {
        wrapper: createWrapper(),
      });

      const params = { project_ids: [1, 2] };
      result.current.mutate(params);

      await waitFor(() => {
        expect(profitApi.compareProfits).toHaveBeenCalledWith(params);
      });
    });
  });

  // ========== Refresh Hook ==========

  describe('useRefreshProfit', () => {
    it('should provide refresh functions', () => {
      const { result } = renderHook(() => useRefreshProfit(), {
        wrapper: createWrapper(),
      });

      expect(result.current.refreshAll).toBeDefined();
      expect(result.current.refreshOverview).toBeDefined();
      expect(result.current.refreshByProject).toBeDefined();
      expect(result.current.refreshByAccount).toBeDefined();
      expect(result.current.refreshByChannel).toBeDefined();
      expect(result.current.refreshTrend).toBeDefined();
    });

    it('should call invalidateQueries on refreshAll', async () => {
      const queryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      });

      const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

      const wrapper = ({ children }: { children: React.ReactNode }) =>
        React.createElement(QueryClientProvider, { client: queryClient }, children);

      const { result } = renderHook(() => useRefreshProfit(), { wrapper });

      act(() => {
        result.current.refreshAll();
      });

      expect(invalidateSpy).toHaveBeenCalled();
    });
  });
});

describe('Profit Formula Tests', () => {
  /**
   * SoT: BUSINESS_RULES.md v3.2 利润计算公式
   * - revenue = conversions_final × unit_price
   * - cost = real_spend + fee
   * - profit = revenue - cost
   * - profit_margin = profit / revenue × 100
   */

  interface ProfitCalculation {
    revenue: number;
    cost: number;
    profit: number;
    profitMargin: number;
  }

  function calculateProfit(
    conversions: number,
    unitPrice: number,
    realSpend: number,
    fee: number
  ): ProfitCalculation {
    const revenue = conversions * unitPrice;
    const cost = realSpend + fee;
    const profit = revenue - cost;
    const profitMargin = revenue > 0 ? (profit / revenue) * 100 : 0;

    return { revenue, cost, profit, profitMargin };
  }

  it('should calculate profit correctly for standard case', () => {
    // 100 conversions × ¥200 = ¥20,000 revenue
    // ¥15,000 spend + ¥500 fee = ¥15,500 cost
    // profit = ¥4,500
    // margin = 22.5%
    const result = calculateProfit(100, 200, 15000, 500);

    expect(result.revenue).toBe(20000);
    expect(result.cost).toBe(15500);
    expect(result.profit).toBe(4500);
    expect(result.profitMargin).toBe(22.5);
  });

  it('should calculate negative profit for loss', () => {
    // 50 conversions × ¥200 = ¥10,000 revenue
    // ¥12,000 spend + ¥500 fee = ¥12,500 cost
    // profit = -¥2,500
    const result = calculateProfit(50, 200, 12000, 500);

    expect(result.revenue).toBe(10000);
    expect(result.cost).toBe(12500);
    expect(result.profit).toBe(-2500);
    expect(result.profitMargin).toBe(-25);
  });

  it('should handle zero conversions', () => {
    const result = calculateProfit(0, 200, 1000, 50);

    expect(result.revenue).toBe(0);
    expect(result.profit).toBe(-1050);
    expect(result.profitMargin).toBe(0); // division by zero protection
  });
});

describe('CPL Abnormal Detection', () => {
  /**
   * SoT: MASTER.md §6.5
   * is_abnormal = CPL > cpl_target × 1.3
   */

  function isAbnormalCPL(cpl: number, cplTarget: number): boolean {
    return cpl > cplTarget * 1.3;
  }

  it('should not flag normal CPL', () => {
    expect(isAbnormalCPL(150, 200)).toBe(false); // 150 < 200 × 1.3 = 260
    expect(isAbnormalCPL(200, 200)).toBe(false);
    expect(isAbnormalCPL(250, 200)).toBe(false);
  });

  it('should flag abnormal CPL when exceeds 130% of target', () => {
    expect(isAbnormalCPL(261, 200)).toBe(true); // 261 > 260
    expect(isAbnormalCPL(300, 200)).toBe(true);
    expect(isAbnormalCPL(400, 200)).toBe(true);
  });

  it('should handle boundary case exactly at 130%', () => {
    expect(isAbnormalCPL(260, 200)).toBe(false); // exactly at threshold
  });
});
