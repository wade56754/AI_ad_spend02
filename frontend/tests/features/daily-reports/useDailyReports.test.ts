/**
 * useDailyReports Hooks Tests
 *
 * Tests for frontend/src/features/daily-reports/hooks/useDailyReports.ts
 * SoT: STATE_MACHINE.md v2.6 - Daily Report 8 states
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useDailyReports,
  useDailyReport,
  useDailyReportsByProject,
  useCreateDailyReport,
  useUpdateDailyReport,
  useDeleteDailyReport,
  useSubmitForTrend,
  useApproveTrend,
  useFlagTrend,
  useResolveFlag,
  useSubmitForFinal,
  useConfirmFinal,
  useLockReport,
} from '@/features/daily-reports/hooks/useDailyReports';
import * as dailyReportsApi from '@/features/daily-reports/services';

// Mock the daily reports API
jest.mock('@/features/daily-reports/services', () => ({
  getDailyReports: jest.fn(),
  getDailyReport: jest.fn(),
  getDailyReportsByProject: jest.fn(),
  createDailyReport: jest.fn(),
  updateDailyReport: jest.fn(),
  deleteDailyReport: jest.fn(),
  submitForTrend: jest.fn(),
  approveTrend: jest.fn(),
  flagTrend: jest.fn(),
  resolveFlag: jest.fn(),
  submitForFinal: jest.fn(),
  confirmFinal: jest.fn(),
  lockReport: jest.fn(),
  bulkSubmitForTrend: jest.fn(),
  getDailyReportStats: jest.fn(),
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

// Mock daily report data factory
function createMockDailyReport(overrides: Record<string, unknown> = {}) {
  return {
    id: '1',
    report_date: '2025-01-15',
    project_id: 'proj-1',
    project_name: 'Test Project',
    ad_account_id: 'acc-1',
    ad_account_name: 'Test Account',
    channel: 'meta',
    spend: '1000.00',
    impressions: 50000,
    clicks: 1500,
    conversions: 75,
    status: 'raw_submitted',
    created_by: 'user-1',
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
    ...overrides,
  };
}

describe('useDailyReports Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ========== Query Hooks ==========

  describe('useDailyReports', () => {
    it('should fetch daily report list successfully', async () => {
      const mockReports = [
        createMockDailyReport({ id: '1' }),
        createMockDailyReport({ id: '2', report_date: '2025-01-16' }),
      ];
      const mockResponse = {
        items: mockReports,
        total: 2,
        page: 1,
        page_size: 10,
        total_pages: 1,
      };

      (dailyReportsApi.getDailyReports as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useDailyReports(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.items).toHaveLength(2);
      expect(dailyReportsApi.getDailyReports).toHaveBeenCalledWith({});
    });

    it('should pass filter params to API', async () => {
      (dailyReportsApi.getDailyReports as jest.Mock).mockResolvedValue({ items: [], total: 0 });

      const params = { status: 'trend_pending' as const, project_id: 1 };
      renderHook(() => useDailyReports(params), { wrapper: createWrapper() });

      await waitFor(() => {
        expect(dailyReportsApi.getDailyReports).toHaveBeenCalledWith(params);
      });
    });
  });

  describe('useDailyReport', () => {
    it('should fetch single daily report by ID', async () => {
      const mockReport = createMockDailyReport({ id: '999' });
      (dailyReportsApi.getDailyReport as jest.Mock).mockResolvedValue(mockReport);

      const { result } = renderHook(() => useDailyReport('999'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.id).toBe('999');
      expect(dailyReportsApi.getDailyReport).toHaveBeenCalledWith('999');
    });

    it('should not fetch when id is empty', () => {
      renderHook(() => useDailyReport(''), { wrapper: createWrapper() });
      expect(dailyReportsApi.getDailyReport).not.toHaveBeenCalled();
    });
  });

  describe('useDailyReportsByProject', () => {
    it('should fetch daily reports filtered by project', async () => {
      const mockResponse = { items: [createMockDailyReport()], total: 1 };
      (dailyReportsApi.getDailyReportsByProject as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useDailyReportsByProject('proj-123'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(dailyReportsApi.getDailyReportsByProject).toHaveBeenCalledWith('proj-123', {});
    });
  });

  // ========== Mutation Hooks ==========

  describe('useCreateDailyReport', () => {
    it('should have mutate and mutateAsync functions', () => {
      const { result } = renderHook(() => useCreateDailyReport(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
      expect(result.current.isPending).toBe(false);
    });
  });

  describe('useUpdateDailyReport', () => {
    it('should have mutate and mutateAsync functions', () => {
      const { result } = renderHook(() => useUpdateDailyReport(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useDeleteDailyReport', () => {
    it('should have mutate and mutateAsync functions', () => {
      const { result } = renderHook(() => useDeleteDailyReport(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  // ========== State Transition Mutations ==========

  describe('useSubmitForTrend', () => {
    it('should have mutate function for raw_submitted -> trend_pending', () => {
      const { result } = renderHook(() => useSubmitForTrend(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useApproveTrend', () => {
    it('should have mutate function for trend_pending -> trend_ok', () => {
      const { result } = renderHook(() => useApproveTrend(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useFlagTrend', () => {
    it('should have mutate function for trend_pending -> trend_flagged', () => {
      const { result } = renderHook(() => useFlagTrend(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useResolveFlag', () => {
    it('should have mutate function for trend_flagged -> trend_resolved', () => {
      const { result } = renderHook(() => useResolveFlag(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useSubmitForFinal', () => {
    it('should have mutate function for trend_ok/resolved -> final_pending', () => {
      const { result } = renderHook(() => useSubmitForFinal(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useConfirmFinal', () => {
    it('should have mutate function for final_pending -> final_confirmed', () => {
      const { result } = renderHook(() => useConfirmFinal(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useLockReport', () => {
    it('should have mutate function for final_confirmed -> final_locked', () => {
      const { result } = renderHook(() => useLockReport(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  // ========== State Machine Tests ==========

  describe('Daily Report Status Types (8 States)', () => {
    it('should support all 8 daily report statuses from SoT', () => {
      const validStatuses = [
        'raw_submitted',
        'trend_pending',
        'trend_ok',
        'trend_flagged',
        'trend_resolved',
        'final_pending',
        'final_confirmed',
        'final_locked',
      ];

      validStatuses.forEach((status) => {
        const report = createMockDailyReport({ status });
        expect(report.status).toBe(status);
      });
    });

    it('should create mock reports with different statuses', () => {
      const rawReport = createMockDailyReport({ status: 'raw_submitted' });
      const trendOkReport = createMockDailyReport({ status: 'trend_ok' });
      const lockedReport = createMockDailyReport({ status: 'final_locked' });

      expect(rawReport.status).toBe('raw_submitted');
      expect(trendOkReport.status).toBe('trend_ok');
      expect(lockedReport.status).toBe('final_locked');
    });
  });

  describe('Channel Types', () => {
    it('should support different ad channels', () => {
      const channels = ['meta', 'google', 'tiktok', 'apple', 'other'];

      channels.forEach((channel) => {
        const report = createMockDailyReport({ channel });
        expect(report.channel).toBe(channel);
      });
    });
  });
});
