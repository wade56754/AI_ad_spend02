/**
 * TopupsTable Component Tests
 *
 * Tests for the main topups table component
 * SoT: STATE_MACHINE.md v2.6 Section 9
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TopupsTable } from '@/features/topups/components/TopupsTable';
import {
  setupFetchMock,
  resetFetchMock,
  mockFetchSuccess,
  mockFetchError,
  mockPaginatedResponse,
} from '../../../tests/mocks/api';
import { topupRequestFactory } from '../../../tests/factories';

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
    ...render(
      <QueryClientProvider client={queryClient}>
        {ui}
      </QueryClientProvider>
    ),
    queryClient,
  };
}

describe('TopupsTable', () => {
  beforeEach(() => {
    setupFetchMock();
  });

  afterEach(() => {
    resetFetchMock();
  });

  describe('loading state', () => {
    it('shows loading indicator while fetching data', async () => {
      // Don't resolve the fetch immediately
      (global.fetch as jest.Mock).mockReturnValueOnce(new Promise(() => {}));

      renderWithProviders(<TopupsTable />);

      expect(screen.getByText('加载中...')).toBeInTheDocument();
    });
  });

  describe('error state', () => {
    it('shows error message when fetch fails', async () => {
      mockFetchError('NET-001', 'Network error', 500);

      renderWithProviders(<TopupsTable />);

      await waitFor(() => {
        expect(screen.getByText(/加载失败/)).toBeInTheDocument();
      });
    });
  });

  describe('empty state', () => {
    it('shows empty message when no topups', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            data: [],
            meta: {
              pagination: {
                page: 1,
                page_size: 20,
                total: 0,
                total_pages: 0,
              },
            },
          },
        }),
      });

      renderWithProviders(<TopupsTable />);

      await waitFor(() => {
        expect(screen.getByText('暂无充值申请')).toBeInTheDocument();
      });
    });
  });

  describe('data display', () => {
    it('displays topup data correctly', async () => {
      const topups = [
        topupRequestFactory.buildWithStatus('draft', {
          project_name: '测试项目A',
          ad_account_name: '账户1',
          amount: 1000000, // ¥10,000
        }),
        topupRequestFactory.buildWithStatus('pending_review', {
          project_name: '测试项目B',
          ad_account_name: '账户2',
          amount: 2500000, // ¥25,000
        }),
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            data: topups,
            meta: {
              pagination: {
                page: 1,
                page_size: 20,
                total: 2,
                total_pages: 1,
              },
            },
          },
        }),
      });

      renderWithProviders(<TopupsTable />);

      await waitFor(() => {
        expect(screen.getByText('测试项目A')).toBeInTheDocument();
        expect(screen.getByText('测试项目B')).toBeInTheDocument();
      });
    });

    it('displays all table headers', async () => {
      const topups = [topupRequestFactory.build()];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            data: topups,
            meta: {
              pagination: { page: 1, page_size: 20, total: 1, total_pages: 1 },
            },
          },
        }),
      });

      renderWithProviders(<TopupsTable />);

      await waitFor(() => {
        expect(screen.getByText('申请时间')).toBeInTheDocument();
        expect(screen.getByText('项目')).toBeInTheDocument();
        expect(screen.getByText('广告账户')).toBeInTheDocument();
        expect(screen.getByText('金额')).toBeInTheDocument();
        expect(screen.getByText('状态')).toBeInTheDocument();
        expect(screen.getByText('申请人')).toBeInTheDocument();
        expect(screen.getByText('操作')).toBeInTheDocument();
      });
    });

    it('displays status badge for each status', async () => {
      const topups = [
        topupRequestFactory.buildWithStatus('draft'),
        topupRequestFactory.buildWithStatus('pending_review'),
        topupRequestFactory.buildWithStatus('completed'),
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            data: topups,
            meta: {
              pagination: { page: 1, page_size: 20, total: 3, total_pages: 1 },
            },
          },
        }),
      });

      renderWithProviders(<TopupsTable />);

      await waitFor(() => {
        expect(screen.getByText('草稿')).toBeInTheDocument();
        expect(screen.getByText('待数据复核')).toBeInTheDocument();
        expect(screen.getByText('已完成')).toBeInTheDocument();
      });
    });
  });

  describe('row interactions', () => {
    it('calls onViewDetail when row is clicked', async () => {
      const onViewDetail = jest.fn();
      const topup = topupRequestFactory.build({ project_name: '点击测试项目' });

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            data: [topup],
            meta: {
              pagination: { page: 1, page_size: 20, total: 1, total_pages: 1 },
            },
          },
        }),
      });

      renderWithProviders(<TopupsTable onViewDetail={onViewDetail} />);

      await waitFor(() => {
        expect(screen.getByText('点击测试项目')).toBeInTheDocument();
      });

      const row = screen.getByText('点击测试项目').closest('tr');
      fireEvent.click(row!);

      expect(onViewDetail).toHaveBeenCalledWith(topup);
    });

    it('opens dropdown menu when actions button is clicked', async () => {
      const topup = topupRequestFactory.build();

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            data: [topup],
            meta: {
              pagination: { page: 1, page_size: 20, total: 1, total_pages: 1 },
            },
          },
        }),
      });

      renderWithProviders(<TopupsTable />);

      await waitFor(() => {
        const moreButton = screen.getByRole('button');
        expect(moreButton).toBeInTheDocument();
      });

      const moreButton = screen.getByRole('button');
      fireEvent.click(moreButton);

      await waitFor(() => {
        expect(screen.getByText('查看详情')).toBeInTheDocument();
      });
    });

    it('shows quick actions based on status', async () => {
      const topup = topupRequestFactory.buildWithStatus('draft');

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            data: [topup],
            meta: {
              pagination: { page: 1, page_size: 20, total: 1, total_pages: 1 },
            },
          },
        }),
      });

      renderWithProviders(<TopupsTable />);

      await waitFor(() => {
        const moreButton = screen.getByRole('button');
        fireEvent.click(moreButton);
      });

      await waitFor(() => {
        expect(screen.getByText('提交审批')).toBeInTheDocument();
        expect(screen.getByText('取消申请')).toBeInTheDocument();
      });
    });
  });

  describe('pagination', () => {
    it('shows pagination when there are multiple pages', async () => {
      const topups = topupRequestFactory.buildMany(5);

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            data: topups,
            meta: {
              pagination: {
                page: 1,
                page_size: 20,
                total: 100,
                total_pages: 5,
              },
            },
          },
        }),
      });

      renderWithProviders(<TopupsTable />);

      await waitFor(() => {
        expect(screen.getByText(/共 100 条/)).toBeInTheDocument();
        expect(screen.getByText(/第 1 \/ 5 页/)).toBeInTheDocument();
      });
    });

    it('hides pagination when there is only one page', async () => {
      const topups = topupRequestFactory.buildMany(5);

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            data: topups,
            meta: {
              pagination: {
                page: 1,
                page_size: 20,
                total: 5,
                total_pages: 1,
              },
            },
          },
        }),
      });

      renderWithProviders(<TopupsTable />);

      await waitFor(() => {
        expect(screen.queryByText('上一页')).not.toBeInTheDocument();
      });
    });

    it('disables previous button on first page', async () => {
      const topups = topupRequestFactory.buildMany(5);

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            data: topups,
            meta: {
              pagination: {
                page: 1,
                page_size: 20,
                total: 100,
                total_pages: 5,
              },
            },
          },
        }),
      });

      renderWithProviders(<TopupsTable />);

      await waitFor(() => {
        const prevButton = screen.getByText('上一页');
        expect(prevButton).toBeDisabled();
      });
    });

    it('disables next button on last page', async () => {
      const topups = topupRequestFactory.buildMany(5);

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            data: topups,
            meta: {
              pagination: {
                page: 5,
                page_size: 20,
                total: 100,
                total_pages: 5,
              },
            },
          },
        }),
      });

      renderWithProviders(<TopupsTable />);

      await waitFor(() => {
        const nextButton = screen.getByText('下一页');
        expect(nextButton).toBeDisabled();
      });
    });

    it('fetches next page when next button is clicked', async () => {
      const topups = topupRequestFactory.buildMany(5);

      // First page
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            data: topups,
            meta: {
              pagination: {
                page: 1,
                page_size: 20,
                total: 100,
                total_pages: 5,
              },
            },
          },
        }),
      });

      renderWithProviders(<TopupsTable />);

      await waitFor(() => {
        expect(screen.getByText('下一页')).toBeInTheDocument();
      });

      // Mock second page
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            data: topups,
            meta: {
              pagination: {
                page: 2,
                page_size: 20,
                total: 100,
                total_pages: 5,
              },
            },
          },
        }),
      });

      fireEvent.click(screen.getByText('下一页'));

      await waitFor(() => {
        expect(screen.getByText(/第 2 \/ 5 页/)).toBeInTheDocument();
      });
    });
  });

  describe('quick actions by status', () => {
    const statusActions = [
      { status: 'draft' as const, expectedActions: ['提交审批', '取消申请'] },
      { status: 'pending_review' as const, expectedActions: ['数据复核', '取消申请'] },
      { status: 'finance_approve' as const, expectedActions: ['财务终审', '取消申请'] },
      { status: 'paid' as const, expectedActions: ['确认到账'] },
      { status: 'completed' as const, expectedActions: [] },
      { status: 'rejected' as const, expectedActions: [] },
      { status: 'cancelled' as const, expectedActions: [] },
    ];

    statusActions.forEach(({ status, expectedActions }) => {
      it(`shows correct actions for ${status} status`, async () => {
        const topup = topupRequestFactory.buildWithStatus(status);

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({
            success: true,
            data: {
              data: [topup],
              meta: {
                pagination: { page: 1, page_size: 20, total: 1, total_pages: 1 },
              },
            },
          }),
        });

        renderWithProviders(<TopupsTable />);

        await waitFor(() => {
          const moreButton = screen.getByRole('button');
          fireEvent.click(moreButton);
        });

        await waitFor(() => {
          // Always show 查看详情
          expect(screen.getByText('查看详情')).toBeInTheDocument();

          // Check expected quick actions
          expectedActions.forEach((action) => {
            expect(screen.getByText(action)).toBeInTheDocument();
          });
        });
      });
    });
  });

  describe('amount display', () => {
    it('handles number amount', async () => {
      const topup = topupRequestFactory.build({ amount: 5000000 }); // ¥50,000

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            data: [topup],
            meta: {
              pagination: { page: 1, page_size: 20, total: 1, total_pages: 1 },
            },
          },
        }),
      });

      renderWithProviders(<TopupsTable />);

      await waitFor(() => {
        // ¥50,000 should display as ¥5.00万
        expect(screen.getByText(/¥5\.00万/)).toBeInTheDocument();
      });
    });

    it('handles object amount with value property', async () => {
      const topup = {
        ...topupRequestFactory.build(),
        amount: { value: 3000000, currency: 'CNY' },
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            data: [topup],
            meta: {
              pagination: { page: 1, page_size: 20, total: 1, total_pages: 1 },
            },
          },
        }),
      });

      renderWithProviders(<TopupsTable />);

      await waitFor(() => {
        expect(screen.getByText(/¥3\.00万/)).toBeInTheDocument();
      });
    });
  });
});
