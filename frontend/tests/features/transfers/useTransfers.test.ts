/**
 * useTransfers Hooks Tests
 *
 * Tests for frontend/src/features/transfers/hooks/useTransfers.ts
 * SoT: STATE_MACHINE.md v2.6 第12章
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useTransfers,
  useTransfer,
  useCreateTransfer,
  useSubmitTransfer,
  useApproveTransfer,
  useRejectTransfer,
  useCompleteTransfer,
} from '@/features/transfers/hooks/useTransfers';
import * as transfersApi from '@/features/transfers/services';
import type { Transfer, TransferStatus } from '@/features/transfers/types';

// Mock the transfers API - must match the import path in useTransfers.ts
jest.mock('@/features/transfers/services', () => ({
  getTransfers: jest.fn(),
  getTransfer: jest.fn(),
  createTransfer: jest.fn(),
  submitTransfer: jest.fn(),
  approveTransfer: jest.fn(),
  rejectTransfer: jest.fn(),
  completeTransfer: jest.fn(),
}));

// Test wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

// Mock transfer data factory
function createMockTransfer(overrides: Partial<Transfer> = {}): Transfer {
  return {
    id: 1,
    request_no: 'TR-2025-0001',
    source_ad_account_id: 100,
    source_ad_account_name: 'Source Account',
    target_ad_account_id: 200,
    target_ad_account_name: 'Target Account',
    transfer_amount: '1000.00',
    status: 'draft' as TransferStatus,
    reason: 'Test transfer',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('useTransfers Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ========== Query Hooks ==========

  describe('useTransfers', () => {
    it('should fetch transfer list successfully', async () => {
      const mockTransfers = [
        createMockTransfer({ id: 1 }),
        createMockTransfer({ id: 2, request_no: 'TR-2025-0002' }),
      ];
      const mockResponse = {
        items: mockTransfers,
        total: 2,
        page: 1,
        page_size: 10,
        total_pages: 1,
      };

      (transfersApi.getTransfers as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useTransfers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.items).toHaveLength(2);
      expect(result.current.data?.total).toBe(2);
      expect(transfersApi.getTransfers).toHaveBeenCalled();
    });

    it('should fetch with status filter', async () => {
      const mockResponse = {
        items: [createMockTransfer({ status: 'pending_approval' })],
        total: 1,
        page: 1,
        page_size: 10,
        total_pages: 1,
      };

      (transfersApi.getTransfers as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useTransfers({ status: 'pending_approval' }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.items[0]?.status).toBe('pending_approval');
    });

    it('should handle fetch error', async () => {
      (transfersApi.getTransfers as jest.Mock).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useTransfers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error?.message).toBe('Network error');
    });
  });

  describe('useTransfer', () => {
    it('should fetch single transfer by id', async () => {
      const mockTransfer = createMockTransfer({ id: 123 });
      (transfersApi.getTransfer as jest.Mock).mockResolvedValue(mockTransfer);

      const { result } = renderHook(() => useTransfer(123), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.id).toBe(123);
      expect(transfersApi.getTransfer).toHaveBeenCalledWith(123);
    });

    it('should not fetch when id is 0', async () => {
      const { result } = renderHook(() => useTransfer(0), {
        wrapper: createWrapper(),
      });

      // Should remain in initial state since enabled: false
      expect(result.current.isFetching).toBe(false);
      expect(transfersApi.getTransfer).not.toHaveBeenCalled();
    });
  });

  // ========== Mutation Hooks ==========

  describe('useCreateTransfer', () => {
    it('should have correct mutation function', () => {
      const { result } = renderHook(() => useCreateTransfer(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
      expect(result.current.isPending).toBe(false);
    });
  });

  describe('useSubmitTransfer', () => {
    it('should have correct mutation function', () => {
      const { result } = renderHook(() => useSubmitTransfer(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useApproveTransfer', () => {
    it('should have correct mutation function', () => {
      const { result } = renderHook(() => useApproveTransfer(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useRejectTransfer', () => {
    it('should have correct mutation function', () => {
      const { result } = renderHook(() => useRejectTransfer(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useCompleteTransfer', () => {
    it('should have correct mutation function', () => {
      const { result } = renderHook(() => useCompleteTransfer(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  // ========== State Machine Transitions (Type Safety) ==========

  describe('State Machine Transitions', () => {
    it('should define valid transfer statuses', () => {
      const validStatuses: TransferStatus[] = [
        'draft',
        'pending_approval',
        'approved',
        'completed',
        'rejected',
      ];

      const mockTransfer = createMockTransfer();
      expect(validStatuses).toContain(mockTransfer.status);
    });

    it('should allow state transition mock data', () => {
      // Test data creation for state transitions
      const draft = createMockTransfer({ status: 'draft' });
      const pending = createMockTransfer({ status: 'pending_approval' });
      const approved = createMockTransfer({ status: 'approved' });
      const completed = createMockTransfer({ status: 'completed' });
      const rejected = createMockTransfer({ status: 'rejected' });

      expect(draft.status).toBe('draft');
      expect(pending.status).toBe('pending_approval');
      expect(approved.status).toBe('approved');
      expect(completed.status).toBe('completed');
      expect(rejected.status).toBe('rejected');
    });
  });

  // ========== Hook Structure ==========

  describe('Hook Structure', () => {
    it('should export all required hooks', () => {
      expect(useTransfers).toBeDefined();
      expect(useTransfer).toBeDefined();
      expect(useCreateTransfer).toBeDefined();
      expect(useSubmitTransfer).toBeDefined();
      expect(useApproveTransfer).toBeDefined();
      expect(useRejectTransfer).toBeDefined();
      expect(useCompleteTransfer).toBeDefined();
    });
  });
});
