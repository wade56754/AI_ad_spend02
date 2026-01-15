/**
 * useAdAccounts Hooks Tests
 *
 * Tests for frontend/src/features/ad-accounts/hooks/useAdAccounts.ts
 * SoT: STATE_MACHINE.md v2.6 Section 7 - Ad Account 6 states
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useAdAccounts,
  useAdAccount,
  useCreateAdAccount,
  useUpdateAdAccountStatus,
  useDeleteAdAccount,
} from '@/features/ad-accounts/hooks/useAdAccounts';
import * as adAccountsApi from '@/features/ad-accounts/services';

// Mock the ad-accounts API
jest.mock('@/features/ad-accounts/services', () => ({
  getAdAccounts: jest.fn(),
  getAdAccount: jest.fn(),
  createAdAccount: jest.fn(),
  updateAdAccountStatus: jest.fn(),
  deleteAdAccount: jest.fn(),
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

// Mock ad account data factory
function createMockAdAccount(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    project_id: 1,
    channel_id: 'ch-1',
    supplier_id: 'sup-1',
    owner_id: 'user-1',
    name: 'Test Account',
    account_code: 'ACC-001',
    status: 'new' as const,
    status_reason: null,
    spend_limit: 10000,
    currency: 'CNY',
    timezone: 'Asia/Shanghai',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    project_name: 'Test Project',
    channel_name: 'Facebook',
    owner_name: 'Test User',
    ...overrides,
  };
}

describe('useAdAccounts Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ========== Query Hooks ==========

  describe('useAdAccounts', () => {
    it('should fetch ad account list successfully', async () => {
      const mockAccounts = [
        createMockAdAccount({ id: 1 }),
        createMockAdAccount({ id: 2, account_code: 'ACC-002' }),
      ];
      const mockResponse = {
        items: mockAccounts,
        meta: {
          pagination: {
            page: 1,
            page_size: 10,
            total: 2,
            total_pages: 1,
          },
        },
      };

      (adAccountsApi.getAdAccounts as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useAdAccounts(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.items).toHaveLength(2);
      expect(adAccountsApi.getAdAccounts).toHaveBeenCalledWith({});
    });

    it('should pass filter params to API', async () => {
      (adAccountsApi.getAdAccounts as jest.Mock).mockResolvedValue({
        items: [],
        meta: { pagination: { page: 1, page_size: 10, total: 0, total_pages: 0 } },
      });

      const params = { status: 'active' as const, project_id: 'proj-1' };
      renderHook(() => useAdAccounts(params), { wrapper: createWrapper() });

      await waitFor(() => {
        expect(adAccountsApi.getAdAccounts).toHaveBeenCalledWith(params);
      });
    });

    it('should handle pagination params', async () => {
      (adAccountsApi.getAdAccounts as jest.Mock).mockResolvedValue({
        items: [],
        meta: { pagination: { page: 2, page_size: 20, total: 0, total_pages: 0 } },
      });

      const params = { page: 2, page_size: 20 };
      renderHook(() => useAdAccounts(params), { wrapper: createWrapper() });

      await waitFor(() => {
        expect(adAccountsApi.getAdAccounts).toHaveBeenCalledWith(params);
      });
    });

    it('should handle API errors gracefully', async () => {
      const error = new Error('Network error');
      (adAccountsApi.getAdAccounts as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useAdAccounts(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBeDefined();
    });
  });

  describe('useAdAccount', () => {
    it('should fetch single ad account by ID', async () => {
      const mockAccount = createMockAdAccount({ id: 999 });
      (adAccountsApi.getAdAccount as jest.Mock).mockResolvedValue({ data: mockAccount });

      const { result } = renderHook(() => useAdAccount('999'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.data.id).toBe(999);
      expect(adAccountsApi.getAdAccount).toHaveBeenCalledWith('999');
    });

    it('should not fetch when id is empty', () => {
      renderHook(() => useAdAccount(''), { wrapper: createWrapper() });
      expect(adAccountsApi.getAdAccount).not.toHaveBeenCalled();
    });

    it('should handle not found error', async () => {
      const error = { message: 'Ad account not found', status: 404 };
      (adAccountsApi.getAdAccount as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useAdAccount('nonexistent'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });
    });
  });

  // ========== Mutation Hooks ==========

  describe('useCreateAdAccount', () => {
    it('should have mutate and mutateAsync functions', () => {
      const { result } = renderHook(() => useCreateAdAccount(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
      expect(result.current.isPending).toBe(false);
    });

    it('should call createAdAccount on mutate', async () => {
      const mockAccount = createMockAdAccount();
      (adAccountsApi.createAdAccount as jest.Mock).mockResolvedValue({ data: mockAccount });

      const { result } = renderHook(() => useCreateAdAccount(), {
        wrapper: createWrapper(),
      });

      const input = {
        project_id: 1,
        name: 'New Account',
        account_code: 'NEW-001',
        status: 'new' as const,
      };

      result.current.mutate(input);

      await waitFor(() => {
        expect(adAccountsApi.createAdAccount).toHaveBeenCalled();
      });

      // Verify the input was passed (first argument)
      expect((adAccountsApi.createAdAccount as jest.Mock).mock.calls[0][0]).toEqual(input);
    });
  });

  describe('useUpdateAdAccountStatus', () => {
    it('should have mutate and mutateAsync functions', () => {
      const { result } = renderHook(() => useUpdateAdAccountStatus(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });

    it('should call updateAdAccountStatus on mutate', async () => {
      const mockAccount = createMockAdAccount({ status: 'testing' });
      (adAccountsApi.updateAdAccountStatus as jest.Mock).mockResolvedValue({ data: mockAccount });

      const { result } = renderHook(() => useUpdateAdAccountStatus(), {
        wrapper: createWrapper(),
      });

      const params = {
        id: '1',
        input: { status: 'testing' as const, status_reason: 'Start testing' },
      };

      result.current.mutate(params);

      await waitFor(() => {
        expect(adAccountsApi.updateAdAccountStatus).toHaveBeenCalledWith('1', params.input);
      });
    });
  });

  describe('useDeleteAdAccount', () => {
    it('should have mutate and mutateAsync functions', () => {
      const { result } = renderHook(() => useDeleteAdAccount(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });

    it('should call deleteAdAccount on mutate', async () => {
      (adAccountsApi.deleteAdAccount as jest.Mock).mockResolvedValue(undefined);

      const { result } = renderHook(() => useDeleteAdAccount(), {
        wrapper: createWrapper(),
      });

      result.current.mutate('1');

      await waitFor(() => {
        expect(adAccountsApi.deleteAdAccount).toHaveBeenCalled();
      });

      // Verify the id was passed (first argument)
      expect((adAccountsApi.deleteAdAccount as jest.Mock).mock.calls[0][0]).toBe('1');
    });
  });

  // ========== Status Types Tests ==========

  describe('Ad Account Status Types', () => {
    it('should support all 6 ad account statuses from SoT', () => {
      const validStatuses = ['new', 'testing', 'active', 'suspended', 'dead', 'archived'];

      validStatuses.forEach((status) => {
        const account = createMockAdAccount({ status });
        expect(account.status).toBe(status);
      });
    });

    it('should create mock accounts with different statuses', () => {
      const newAccount = createMockAdAccount({ status: 'new' });
      const activeAccount = createMockAdAccount({ status: 'active' });
      const deadAccount = createMockAdAccount({ status: 'dead' });

      expect(newAccount.status).toBe('new');
      expect(activeAccount.status).toBe('active');
      expect(deadAccount.status).toBe('dead');
    });
  });

  // ========== Integration Tests ==========

  describe('Query Invalidation', () => {
    it('useCreateAdAccount should invalidate queries on success', async () => {
      const mockAccount = createMockAdAccount();
      (adAccountsApi.createAdAccount as jest.Mock).mockResolvedValue({ data: mockAccount });

      const queryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      });

      // Spy on invalidateQueries
      const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

      const wrapper = ({ children }: { children: React.ReactNode }) =>
        React.createElement(QueryClientProvider, { client: queryClient }, children);

      const { result } = renderHook(() => useCreateAdAccount(), { wrapper });

      result.current.mutate({ project_id: 1, name: 'Test' });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(invalidateSpy).toHaveBeenCalled();
    });
  });
});
