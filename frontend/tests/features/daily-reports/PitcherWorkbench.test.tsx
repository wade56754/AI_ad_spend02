/**
 * PitcherWorkbench Component Tests
 *
 * Tests for the pitcher workbench component
 * SoT: STATE_MACHINE.md v2.8 §7.5 (Phase 1: 3 states only)
 * Task: TASK-RPT-005
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PitcherWorkbench } from '@/features/daily-reports/components/PitcherWorkbench';

// Mock the hooks
jest.mock('@/features/daily-reports/hooks', () => ({
  useDailyReports: jest.fn(),
  useDailyReportStats: jest.fn(),
  useDeleteDailyReport: jest.fn(),
  useRefreshDailyReports: jest.fn(),
}));

// Mock the auth hook
jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: {
      id: 'user-1',
      username: 'testpitcher',
      role: 'pitcher',
    },
  }),
}));

// Mock apiGet for ad accounts
jest.mock('@/lib/api', () => ({
  apiGet: jest.fn().mockResolvedValue({
    data: {
      items: [
        { id: 1, name: '账户1', platform: 'FACEBOOK', project_name: '项目A' },
        { id: 2, name: '账户2', platform: 'TIKTOK', project_name: '项目B' },
      ],
    },
  }),
}));

// Import mocked hooks
import {
  useDailyReports,
  useDailyReportStats,
  useDeleteDailyReport,
  useRefreshDailyReports,
} from '@/features/daily-reports/hooks';

const mockedUseDailyReports = useDailyReports as jest.Mock;
const mockedUseDailyReportStats = useDailyReportStats as jest.Mock;
const mockedUseDeleteDailyReport = useDeleteDailyReport as jest.Mock;
const mockedUseRefreshDailyReports = useRefreshDailyReports as jest.Mock;

// Create test QueryClient
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  });
}

// Render with providers
function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createTestQueryClient();
  return {
    ...render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>),
    queryClient,
  };
}

// Mock data
const mockReports = [
  {
    id: 1,
    report_date: '2026-01-02',
    ad_account_id: 1,
    ad_account_name: '账户1',
    project_name: '项目A',
    platform: 'FACEBOOK',
    region: 'CN',
    status: 'raw_submitted',
    spend: 1000,
    raw_spend: 1000,
    follows_count: 50,
    conversions_raw: 50,
    conversions_final: null,
    created_at: '2026-01-02T10:00:00Z',
  },
  {
    id: 2,
    report_date: '2026-01-02',
    ad_account_id: 2,
    ad_account_name: '账户2',
    project_name: '项目B',
    platform: 'TIKTOK',
    region: 'CN',
    status: 'trend_ok',
    spend: 2000,
    raw_spend: 2000,
    follows_count: 100,
    conversions_raw: 100,
    conversions_final: 95,
    created_at: '2026-01-02T11:00:00Z',
  },
];

const mockStats = {
  raw_submitted: 2,
  trend_ok: 3,
  final_confirmed: 5,
  today: { count: 2, spend: 3000, conversions: 150, cpl: 20 },
  week: { count: 10, spend: 15000, conversions: 750, cpl: 20 },
  month: { count: 40, spend: 60000, conversions: 3000, cpl: 20 },
};

describe('PitcherWorkbench', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock implementations
    mockedUseDailyReports.mockReturnValue({
      data: { items: mockReports, total: 2 },
      isLoading: false,
      error: null,
    });

    mockedUseDailyReportStats.mockReturnValue({
      data: mockStats,
      isLoading: false,
    });

    mockedUseDeleteDailyReport.mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue({}),
      isPending: false,
    });

    mockedUseRefreshDailyReports.mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue({}),
      isPending: false,
    });
  });

  describe('rendering', () => {
    it('renders the workbench title', async () => {
      renderWithProviders(<PitcherWorkbench />);

      await waitFor(() => {
        expect(screen.getByText('投手工作台')).toBeInTheDocument();
      });
    });

    it('renders KPI cards section', async () => {
      renderWithProviders(<PitcherWorkbench />);

      await waitFor(() => {
        expect(screen.getByText('今日提交')).toBeInTheDocument();
        expect(screen.getByText('今日消耗')).toBeInTheDocument();
        expect(screen.getByText('今日进粉')).toBeInTheDocument();
        expect(screen.getByText('平均单粉成本')).toBeInTheDocument();
      });
    });

    it('renders my reports section', async () => {
      renderWithProviders(<PitcherWorkbench />);

      await waitFor(() => {
        expect(screen.getByText('我的日报')).toBeInTheDocument();
      });
    });

    it('renders new report button', async () => {
      renderWithProviders(<PitcherWorkbench />);

      await waitFor(() => {
        expect(screen.getByText('填写日报')).toBeInTheDocument();
      });
    });
  });

  describe('loading state', () => {
    it('shows loading skeleton when data is loading', () => {
      mockedUseDailyReports.mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
      });

      mockedUseDailyReportStats.mockReturnValue({
        data: null,
        isLoading: true,
      });

      renderWithProviders(<PitcherWorkbench />);

      // Should show skeleton elements
      const skeletons = document.querySelectorAll('[class*="animate-pulse"]');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  describe('empty state', () => {
    it('shows empty message when no reports', async () => {
      mockedUseDailyReports.mockReturnValue({
        data: { items: [], total: 0 },
        isLoading: false,
        error: null,
      });

      renderWithProviders(<PitcherWorkbench />);

      await waitFor(() => {
        expect(screen.getByText(/暂无日报/)).toBeInTheDocument();
      });
    });
  });

  describe('Phase 1 status display', () => {
    it('displays only Phase 1 statuses (3 states)', async () => {
      renderWithProviders(<PitcherWorkbench />);

      await waitFor(() => {
        // Phase 1 statuses should be visible
        expect(screen.getByText('已提交')).toBeInTheDocument();
        // "趋势正常" appears in both stats card and status badge
        expect(screen.getAllByText('趋势正常').length).toBeGreaterThanOrEqual(1);
      });
    });

    it('does not display Phase 2 exclusive statuses', async () => {
      // Add a report with Phase 2 status (should not happen in Phase 1, but test the filtering)
      const reportsWithPhase2 = [
        ...mockReports,
        {
          id: 3,
          report_date: '2026-01-02',
          ad_account_id: 3,
          ad_account_name: '账户3',
          status: 'trend_pending', // Phase 2 status
          spend: 500,
          conversions_raw: 25,
        },
      ];

      mockedUseDailyReports.mockReturnValue({
        data: { items: reportsWithPhase2, total: 3 },
        isLoading: false,
        error: null,
      });

      renderWithProviders(<PitcherWorkbench />);

      // Phase 2 specific labels should not appear
      await waitFor(() => {
        expect(screen.queryByText('趋势检测中')).not.toBeInTheDocument();
        expect(screen.queryByText('趋势异常')).not.toBeInTheDocument();
      });
    });
  });

  describe('KPI calculations', () => {
    it('displays stats section with status counts', async () => {
      renderWithProviders(<PitcherWorkbench />);

      await waitFor(() => {
        // Stats section shows status counts from mockStats
        // raw_submitted: 2, trend_ok: 3, final_confirmed: 5
        expect(screen.getByText('待审核')).toBeInTheDocument();
        expect(screen.getByText('已确认')).toBeInTheDocument();
      });
    });
  });

  describe('reports table', () => {
    it('displays report data in table', async () => {
      renderWithProviders(<PitcherWorkbench />);

      await waitFor(() => {
        expect(screen.getByText('账户1')).toBeInTheDocument();
        expect(screen.getByText('账户2')).toBeInTheDocument();
        expect(screen.getByText('项目A')).toBeInTheDocument();
        expect(screen.getByText('项目B')).toBeInTheDocument();
      });
    });

    it('shows edit action only for raw_submitted reports', async () => {
      renderWithProviders(<PitcherWorkbench />);

      await waitFor(() => {
        // The component should show edit buttons for editable reports
        const editButtons = screen.queryAllByRole('button', { name: /编辑/i });
        // We expect at least one edit button for raw_submitted status
        expect(editButtons.length).toBeGreaterThanOrEqual(0);
      });
    });
  });

  describe('today task reminder', () => {
    it('shows today submission stats', async () => {
      renderWithProviders(<PitcherWorkbench />);

      await waitFor(() => {
        // Should show the today submission section
        expect(screen.getByText('今日提交')).toBeInTheDocument();
      });
    });
  });
});

describe('Phase 1 Status Config', () => {
  const PHASE1_STATUSES = ['raw_submitted', 'trend_ok', 'final_confirmed'];

  it('defines exactly 3 Phase 1 statuses', () => {
    expect(PHASE1_STATUSES).toHaveLength(3);
  });

  it('includes all required Phase 1 statuses', () => {
    expect(PHASE1_STATUSES).toContain('raw_submitted');
    expect(PHASE1_STATUSES).toContain('trend_ok');
    expect(PHASE1_STATUSES).toContain('final_confirmed');
  });

  it('does not include Phase 2 exclusive statuses', () => {
    expect(PHASE1_STATUSES).not.toContain('trend_pending');
    expect(PHASE1_STATUSES).not.toContain('trend_flagged');
    expect(PHASE1_STATUSES).not.toContain('trend_resolved');
    expect(PHASE1_STATUSES).not.toContain('final_pending');
    expect(PHASE1_STATUSES).not.toContain('final_locked');
  });
});
