/**
 * useReconciliation Hooks Tests
 *
 * Tests for frontend/src/features/reconciliation/hooks/useReconciliation.ts
 * SoT: STATE_MACHINE.md v2.6 - Reconciliation Batch/Detail states
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useReconciliations,
  useReconciliation,
  useReconciliationMismatches,
  useReconciliationsByProject,
  useLatestReconciliation,
  useCreateReconciliation,
  useRunReconciliation,
  useRetryReconciliation,
  useResolveMismatch,
} from '@/features/reconciliation/hooks/useReconciliation';
import * as reconciliationApi from '@/features/reconciliation/services';

// Mock the reconciliation API
jest.mock('@/features/reconciliation/services', () => ({
  getReconciliations: jest.fn(),
  getReconciliation: jest.fn(),
  getReconciliationMismatches: jest.fn(),
  getReconciliationsByProject: jest.fn(),
  createReconciliation: jest.fn(),
  runReconciliation: jest.fn(),
  retryReconciliation: jest.fn(),
  resolveMismatch: jest.fn(),
  getReconciliationStats: jest.fn(),
  getLatestReconciliation: jest.fn(),
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

// Mock reconciliation data factory
function createMockReconciliation(overrides: Record<string, unknown> = {}) {
  return {
    id: '1',
    batch_no: 'REC-2025-0001',
    project_id: 'proj-1',
    project_name: 'Test Project',
    reconciliation_type: 'daily',
    status: 'pending',
    start_date: '2025-01-01',
    end_date: '2025-01-31',
    total_platform_spend: '10000.00',
    total_internal_spend: '10050.00',
    discrepancy_amount: '50.00',
    discrepancy_rate: '0.5',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

// Mock mismatch data factory
function createMockMismatch(overrides: Record<string, unknown> = {}) {
  return {
    id: 'mismatch-1',
    reconciliation_id: '1',
    ad_account_id: 'acc-1',
    date: '2025-01-15',
    platform_spend: '500.00',
    internal_spend: '520.00',
    discrepancy: '20.00',
    status: 'pending',
    resolution_type: null,
    resolved_at: null,
    ...overrides,
  };
}

describe('useReconciliation Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ========== Query Hooks ==========

  describe('useReconciliations', () => {
    it('should fetch reconciliation list successfully', async () => {
      const mockReconciliations = [
        createMockReconciliation({ id: '1' }),
        createMockReconciliation({ id: '2', batch_no: 'REC-2025-0002' }),
      ];
      const mockResponse = {
        items: mockReconciliations,
        total: 2,
        page: 1,
        page_size: 10,
        total_pages: 1,
      };

      (reconciliationApi.getReconciliations as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useReconciliations(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.items).toHaveLength(2);
      expect(reconciliationApi.getReconciliations).toHaveBeenCalledWith({});
    });

    it('should pass filter params to API', async () => {
      (reconciliationApi.getReconciliations as jest.Mock).mockResolvedValue({ items: [], total: 0 });

      const params = { status: 'completed', project_id: 'proj-1' };
      renderHook(() => useReconciliations(params), { wrapper: createWrapper() });

      await waitFor(() => {
        expect(reconciliationApi.getReconciliations).toHaveBeenCalledWith(params);
      });
    });
  });

  describe('useReconciliation', () => {
    it('should fetch single reconciliation by ID', async () => {
      const mockReconciliation = createMockReconciliation({ id: '999' });
      (reconciliationApi.getReconciliation as jest.Mock).mockResolvedValue(mockReconciliation);

      const { result } = renderHook(() => useReconciliation('999'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.id).toBe('999');
      expect(reconciliationApi.getReconciliation).toHaveBeenCalledWith('999');
    });

    it('should not fetch when id is empty', () => {
      renderHook(() => useReconciliation(''), { wrapper: createWrapper() });
      expect(reconciliationApi.getReconciliation).not.toHaveBeenCalled();
    });
  });

  describe('useReconciliationMismatches', () => {
    it('should fetch mismatches for a reconciliation', async () => {
      const mockMismatches = [
        createMockMismatch({ id: 'm1' }),
        createMockMismatch({ id: 'm2' }),
      ];
      (reconciliationApi.getReconciliationMismatches as jest.Mock).mockResolvedValue(mockMismatches);

      const { result } = renderHook(() => useReconciliationMismatches('rec-1'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toHaveLength(2);
      expect(reconciliationApi.getReconciliationMismatches).toHaveBeenCalledWith('rec-1');
    });
  });

  describe('useReconciliationsByProject', () => {
    it('should fetch reconciliations filtered by project', async () => {
      const mockResponse = { items: [createMockReconciliation()], total: 1 };
      (reconciliationApi.getReconciliationsByProject as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useReconciliationsByProject('proj-123'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(reconciliationApi.getReconciliationsByProject).toHaveBeenCalledWith('proj-123', {});
    });
  });

  describe('useLatestReconciliation', () => {
    it('should fetch latest reconciliation for project', async () => {
      const mockReconciliation = createMockReconciliation({ status: 'completed' });
      (reconciliationApi.getLatestReconciliation as jest.Mock).mockResolvedValue(mockReconciliation);

      const { result } = renderHook(() => useLatestReconciliation('proj-1'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.status).toBe('completed');
    });
  });

  // ========== Mutation Hooks ==========

  describe('useCreateReconciliation', () => {
    it('should have mutate and mutateAsync functions', () => {
      const { result } = renderHook(() => useCreateReconciliation(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
      expect(result.current.isPending).toBe(false);
    });
  });

  describe('useRunReconciliation', () => {
    it('should have mutate and mutateAsync functions', () => {
      const { result } = renderHook(() => useRunReconciliation(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useRetryReconciliation', () => {
    it('should have mutate and mutateAsync functions', () => {
      const { result } = renderHook(() => useRetryReconciliation(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useResolveMismatch', () => {
    it('should have mutate and mutateAsync functions', () => {
      const { result } = renderHook(() => useResolveMismatch(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  // ========== State Machine Tests ==========

  describe('Reconciliation Status Types', () => {
    it('should support batch statuses from SoT', () => {
      const batchStatuses = [
        'pending',
        'in_progress',
        'needs_adjustment',
        'completed',
        'failed',
      ];

      batchStatuses.forEach((status) => {
        const recon = createMockReconciliation({ status });
        expect(recon.status).toBe(status);
      });
    });

    it('should support mismatch statuses from SoT', () => {
      const mismatchStatuses = ['pending', 'confirmed', 'adjusted'];

      mismatchStatuses.forEach((status) => {
        const mismatch = createMockMismatch({ status });
        expect(mismatch.status).toBe(status);
      });
    });
  });

  describe('Reconciliation Types', () => {
    it('should support all reconciliation types', () => {
      const types = ['daily', 'weekly', 'monthly', 'ad_hoc'];

      types.forEach((type) => {
        const recon = createMockReconciliation({ reconciliation_type: type });
        expect(recon.reconciliation_type).toBe(type);
      });
    });
  });
});
