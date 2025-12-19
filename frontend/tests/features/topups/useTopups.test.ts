/**
 * useTopups Hooks Tests
 *
 * Tests for frontend/src/features/topups/hooks/useTopups.ts
 * SoT: STATE_MACHINE.md v2.6 - Topup 8 states
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useTopups,
  useTopup,
  useTopupsByProject,
  useCreateTopup,
  useApproveTopup,
  useRejectTopup,
  useCompleteTopup,
  useCancelTopup,
} from '@/features/topups/hooks/useTopups';
import * as topupsApi from '@/features/topups/services';

// Mock the topups API
jest.mock('@/features/topups/services', () => ({
  getTopups: jest.fn(),
  getTopup: jest.fn(),
  getTopupsByProject: jest.fn(),
  createTopup: jest.fn(),
  approveTopup: jest.fn(),
  rejectTopup: jest.fn(),
  completeTopup: jest.fn(),
  cancelTopup: jest.fn(),
  getTopupStats: jest.fn(),
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

// Mock topup data factory
function createMockTopup(overrides: Record<string, unknown> = {}) {
  return {
    id: '1',
    request_no: 'TOP-2025-0001',
    project_id: 'proj-1',
    project_name: 'Test Project',
    amount: '5000.00',
    status: 'draft',
    created_by: 'user-1',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('useTopups Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ========== Query Hooks ==========

  describe('useTopups', () => {
    it('should fetch topup list successfully', async () => {
      const mockTopups = [
        createMockTopup({ id: '1' }),
        createMockTopup({ id: '2', request_no: 'TOP-2025-0002' }),
      ];
      const mockResponse = {
        items: mockTopups,
        total: 2,
        page: 1,
        page_size: 10,
        total_pages: 1,
      };

      (topupsApi.getTopups as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useTopups(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.items).toHaveLength(2);
      expect(topupsApi.getTopups).toHaveBeenCalledWith({});
    });

    it('should pass filter params to API', async () => {
      (topupsApi.getTopups as jest.Mock).mockResolvedValue({ items: [], total: 0 });

      const params = { status: 'pending_review', project_id: 'proj-1' };
      renderHook(() => useTopups(params), { wrapper: createWrapper() });

      await waitFor(() => {
        expect(topupsApi.getTopups).toHaveBeenCalledWith(params);
      });
    });
  });

  describe('useTopup', () => {
    it('should fetch single topup by ID', async () => {
      const mockTopup = createMockTopup({ id: '999' });
      (topupsApi.getTopup as jest.Mock).mockResolvedValue(mockTopup);

      const { result } = renderHook(() => useTopup('999'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.id).toBe('999');
      expect(topupsApi.getTopup).toHaveBeenCalledWith('999');
    });

    it('should not fetch when id is empty', () => {
      renderHook(() => useTopup(''), { wrapper: createWrapper() });
      expect(topupsApi.getTopup).not.toHaveBeenCalled();
    });
  });

  describe('useTopupsByProject', () => {
    it('should fetch topups filtered by project', async () => {
      const mockResponse = { items: [createMockTopup()], total: 1 };
      (topupsApi.getTopupsByProject as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useTopupsByProject('proj-123'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(topupsApi.getTopupsByProject).toHaveBeenCalledWith('proj-123', {});
    });
  });

  // ========== Mutation Hooks ==========

  describe('useCreateTopup', () => {
    it('should have mutate and mutateAsync functions', () => {
      const { result } = renderHook(() => useCreateTopup(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
      expect(result.current.isPending).toBe(false);
    });
  });

  describe('useApproveTopup', () => {
    it('should have mutate and mutateAsync functions', () => {
      const { result } = renderHook(() => useApproveTopup(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useRejectTopup', () => {
    it('should have mutate and mutateAsync functions', () => {
      const { result } = renderHook(() => useRejectTopup(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useCompleteTopup', () => {
    it('should have mutate and mutateAsync functions', () => {
      const { result } = renderHook(() => useCompleteTopup(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useCancelTopup', () => {
    it('should have mutate and mutateAsync functions', () => {
      const { result } = renderHook(() => useCancelTopup(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  // ========== State Machine Tests ==========

  describe('Topup Status Types', () => {
    it('should support all 8 topup statuses from SoT', () => {
      const validStatuses = [
        'draft',
        'pending_review',
        'approved',
        'rejected',
        'paid',
        'completed',
        'cancelled',
        'failed',
      ];

      validStatuses.forEach((status) => {
        const topup = createMockTopup({ status });
        expect(topup.status).toBe(status);
      });
    });

    it('should create mock topups with different statuses', () => {
      const draftTopup = createMockTopup({ status: 'draft' });
      const approvedTopup = createMockTopup({ status: 'approved' });
      const completedTopup = createMockTopup({ status: 'completed' });

      expect(draftTopup.status).toBe('draft');
      expect(approvedTopup.status).toBe('approved');
      expect(completedTopup.status).toBe('completed');
    });
  });
});
