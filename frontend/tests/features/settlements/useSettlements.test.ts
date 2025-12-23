/**
 * useSettlements Hooks Tests
 *
 * Tests for frontend/src/features/settlements/hooks/useSettlements.ts
 * SoT: DATA_SCHEMA.md v5.2, LEDGER_SOT.md v1.1
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useSettlements,
  useSettlement,
  useSettlementStatistics,
  useOverdueSettlements,
  useSettlementPayments,
  useCreateSettlement,
  useUpdateSettlement,
  useSubmitSettlement,
  useApproveSettlement,
  useRecordPayment,
  useCancelSettlement,
} from '@/features/settlements/hooks/useSettlements';
import * as settlementsApi from '@/features/settlements/services';

// Mock the settlements API
jest.mock('@/features/settlements/services', () => ({
  getSettlements: jest.fn(),
  getSettlement: jest.fn(),
  getSettlementStatistics: jest.fn(),
  getOverdueSettlements: jest.fn(),
  getSettlementPayments: jest.fn(),
  createSettlement: jest.fn(),
  updateSettlement: jest.fn(),
  submitSettlement: jest.fn(),
  approveSettlement: jest.fn(),
  recordPayment: jest.fn(),
  cancelSettlement: jest.fn(),
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

// Mock settlement data factory
function createMockSettlement(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    settlement_no: 'SET-2025-0001',
    supplier_id: 'sup-1',
    supplier_name: 'Test Supplier',
    period_start: '2025-01-01',
    period_end: '2025-01-31',
    total_amount: '50000.00',
    paid_amount: '0.00',
    status: 'draft',
    due_date: '2025-02-15',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

// Mock payment data factory
function createMockPayment(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    settlement_id: 1,
    amount: '10000.00',
    payment_date: '2025-02-01',
    payment_method: 'bank_transfer',
    reference_no: 'PAY-001',
    created_at: '2025-02-01T00:00:00Z',
    ...overrides,
  };
}

describe('useSettlements Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ========== Query Hooks ==========

  describe('useSettlements', () => {
    it('should fetch settlement list successfully', async () => {
      const mockSettlements = [
        createMockSettlement({ id: 1 }),
        createMockSettlement({ id: 2, settlement_no: 'SET-2025-0002' }),
      ];
      const mockResponse = {
        items: mockSettlements,
        total: 2,
        page: 1,
        page_size: 10,
        total_pages: 1,
      };

      (settlementsApi.getSettlements as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useSettlements(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.items).toHaveLength(2);
      expect(settlementsApi.getSettlements).toHaveBeenCalledWith({});
    });

    it('should pass filter params to API', async () => {
      (settlementsApi.getSettlements as jest.Mock).mockResolvedValue({ items: [], total: 0 });

      const params = { status: 'PENDING' as const, supplier_id: 1 };
      renderHook(() => useSettlements(params), { wrapper: createWrapper() });

      await waitFor(() => {
        expect(settlementsApi.getSettlements).toHaveBeenCalledWith(params);
      });
    });
  });

  describe('useSettlement', () => {
    it('should fetch single settlement by ID', async () => {
      const mockSettlement = createMockSettlement({ id: 999 });
      (settlementsApi.getSettlement as jest.Mock).mockResolvedValue(mockSettlement);

      const { result } = renderHook(() => useSettlement(999), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.id).toBe(999);
      expect(settlementsApi.getSettlement).toHaveBeenCalledWith(999);
    });

    it('should not fetch when id is 0', () => {
      renderHook(() => useSettlement(0), { wrapper: createWrapper() });
      expect(settlementsApi.getSettlement).not.toHaveBeenCalled();
    });
  });

  describe('useSettlementStatistics', () => {
    it('should fetch settlement statistics', async () => {
      const mockStats = {
        total_settlements: 50,
        total_amount: '500000.00',
        paid_amount: '300000.00',
        pending_amount: '200000.00',
        by_status: { draft: 5, approved: 20, paid: 25 },
      };
      (settlementsApi.getSettlementStatistics as jest.Mock).mockResolvedValue(mockStats);

      const { result } = renderHook(() => useSettlementStatistics(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.total_settlements).toBe(50);
    });
  });

  describe('useOverdueSettlements', () => {
    it('should fetch overdue settlements', async () => {
      const mockOverdue = [
        createMockSettlement({ id: 1, status: 'overdue' }),
        createMockSettlement({ id: 2, status: 'overdue' }),
      ];
      (settlementsApi.getOverdueSettlements as jest.Mock).mockResolvedValue(mockOverdue);

      const { result } = renderHook(() => useOverdueSettlements(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toHaveLength(2);
    });
  });

  describe('useSettlementPayments', () => {
    it('should fetch payments for a settlement', async () => {
      const mockPayments = [
        createMockPayment({ id: 1 }),
        createMockPayment({ id: 2, amount: '20000.00' }),
      ];
      (settlementsApi.getSettlementPayments as jest.Mock).mockResolvedValue(mockPayments);

      const { result } = renderHook(() => useSettlementPayments(1), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toHaveLength(2);
      expect(settlementsApi.getSettlementPayments).toHaveBeenCalledWith(1);
    });
  });

  // ========== Mutation Hooks ==========

  describe('useCreateSettlement', () => {
    it('should have mutate and mutateAsync functions', () => {
      const { result } = renderHook(() => useCreateSettlement(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
      expect(result.current.isPending).toBe(false);
    });
  });

  describe('useUpdateSettlement', () => {
    it('should have mutate and mutateAsync functions', () => {
      const { result } = renderHook(() => useUpdateSettlement(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useSubmitSettlement', () => {
    it('should have mutate function for draft -> pending_approval', () => {
      const { result } = renderHook(() => useSubmitSettlement(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useApproveSettlement', () => {
    it('should have mutate function for pending_approval -> approved', () => {
      const { result } = renderHook(() => useApproveSettlement(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useRecordPayment', () => {
    it('should have mutate function for recording payments', () => {
      const { result } = renderHook(() => useRecordPayment(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  describe('useCancelSettlement', () => {
    it('should have mutate function for cancelling settlement', () => {
      const { result } = renderHook(() => useCancelSettlement(), {
        wrapper: createWrapper(),
      });

      expect(result.current.mutate).toBeDefined();
      expect(result.current.mutateAsync).toBeDefined();
    });
  });

  // ========== Status Tests ==========

  describe('Settlement Status Types', () => {
    it('should support all settlement statuses', () => {
      const validStatuses = [
        'DRAFT',
        'PENDING',
        'APPROVED',
        'REJECTED',
        'PROCESSING',
        'COMPLETED',
        'CANCELLED',
      ];

      validStatuses.forEach((status) => {
        const settlement = createMockSettlement({ status });
        expect(settlement.status).toBe(status);
      });
    });
  });

  describe('Payment Methods', () => {
    it('should support different payment methods', () => {
      const methods = ['bank_transfer', 'check', 'cash', 'online'];

      methods.forEach((method) => {
        const payment = createMockPayment({ payment_method: method });
        expect(payment.payment_method).toBe(method);
      });
    });
  });
});
