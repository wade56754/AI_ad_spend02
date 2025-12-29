/**
 * useTopupActions Hook Tests
 *
 * Tests for the aggregated topup actions hook
 * SoT: STATE_MACHINE.md v2.6 Section 9
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useTopupActions } from '@/features/topups/hooks/useTopupActions';
import {
  setupFetchMock,
  resetFetchMock,
  mockFetchSuccess,
  mockFetchError,
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

// Wrapper component
function createWrapper() {
  const queryClient = createTestQueryClient();
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

describe('useTopupActions Hook', () => {
  beforeEach(() => {
    setupFetchMock();
  });

  afterEach(() => {
    resetFetchMock();
  });

  describe('initialization', () => {
    it('should return all action methods', () => {
      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      expect(result.current.submitForReview).toBeDefined();
      expect(result.current.dataReviewApprove).toBeDefined();
      expect(result.current.dataReviewReject).toBeDefined();
      expect(result.current.financeApprove).toBeDefined();
      expect(result.current.financeReject).toBeDefined();
      expect(result.current.markCompleted).toBeDefined();
      expect(result.current.cancel).toBeDefined();
    });

    it('should return utilities', () => {
      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      expect(result.current.executeAction).toBeDefined();
      expect(result.current.getAvailableActions).toBeDefined();
      expect(result.current.canTransition).toBeDefined();
      expect(result.current.canPerformAction).toBeDefined();
    });

    it('should not be loading initially', () => {
      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('callbacks', () => {
    it('should call onSuccess callback after successful action', async () => {
      const onSuccess = jest.fn();
      const topup = topupRequestFactory.buildWithStatus('paid');

      mockFetchSuccess(topup);

      const { result } = renderHook(() => useTopupActions({ onSuccess }), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.markCompleted(topup.id);
      });

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalledWith('complete');
      });
    });

    it('should call onError callback after failed action', async () => {
      const onError = jest.fn();
      const topup = topupRequestFactory.build();

      mockFetchError('VAL-001', 'Validation error', 400);

      const { result } = renderHook(() => useTopupActions({ onError }), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        try {
          await result.current.cancel(topup.id);
        } catch {
          // Expected to throw
        }
      });

      await waitFor(() => {
        expect(onError).toHaveBeenCalled();
      });
    });
  });

  describe('submitForReview', () => {
    it('should call API to submit topup for review', async () => {
      const topup = topupRequestFactory.buildWithStatus('pending_review');
      mockFetchSuccess(topup);

      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.submitForReview(topup.id);
      });

      expect(global.fetch).toHaveBeenCalled();
    });
  });

  describe('dataReviewApprove', () => {
    it('should call API with notes', async () => {
      const topup = topupRequestFactory.buildWithStatus('finance_approve');
      mockFetchSuccess(topup);

      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.dataReviewApprove(topup.id, { notes: '数据核实无误' });
      });

      expect(global.fetch).toHaveBeenCalled();
    });
  });

  describe('dataReviewReject', () => {
    it('should call API with rejection reason', async () => {
      const topup = topupRequestFactory.buildWithStatus('rejected');
      mockFetchSuccess(topup);

      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.dataReviewReject(topup.id, {
          rejection_reason: '数据有误',
          version: 1,
        });
      });

      expect(global.fetch).toHaveBeenCalled();
    });
  });

  describe('financeApprove', () => {
    it('should call API to approve financially', async () => {
      const topup = topupRequestFactory.buildWithStatus('paid');
      mockFetchSuccess(topup);

      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.financeApprove(topup.id);
      });

      expect(global.fetch).toHaveBeenCalled();
    });
  });

  describe('financeReject', () => {
    it('should call API with rejection reason', async () => {
      const topup = topupRequestFactory.buildWithStatus('rejected');
      mockFetchSuccess(topup);

      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.financeReject(topup.id, {
          rejection_reason: '预算不足',
          version: 1,
        });
      });

      expect(global.fetch).toHaveBeenCalled();
    });
  });

  describe('markCompleted', () => {
    it('should call API to mark as completed', async () => {
      const topup = topupRequestFactory.buildWithStatus('completed');
      mockFetchSuccess(topup);

      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.markCompleted(topup.id);
      });

      expect(global.fetch).toHaveBeenCalled();
    });
  });

  describe('cancel', () => {
    it('should call API to cancel topup', async () => {
      const topup = topupRequestFactory.buildWithStatus('cancelled');
      mockFetchSuccess(topup);

      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.cancel(topup.id);
      });

      expect(global.fetch).toHaveBeenCalled();
    });
  });

  describe('executeAction', () => {
    it('should execute submit action', async () => {
      const topup = topupRequestFactory.buildWithStatus('pending_review');
      mockFetchSuccess(topup);

      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.executeAction('submit', topup.id);
      });

      expect(global.fetch).toHaveBeenCalled();
    });

    it('should execute data_review_approve action', async () => {
      const topup = topupRequestFactory.buildWithStatus('finance_approve');
      mockFetchSuccess(topup);

      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.executeAction('data_review_approve', topup.id, {
          notes: '审核通过',
        });
      });

      expect(global.fetch).toHaveBeenCalled();
    });

    it('should throw error when data_review_reject without reason', async () => {
      const topup = topupRequestFactory.build();

      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      await expect(
        act(async () => {
          await result.current.executeAction('data_review_reject', topup.id, {});
        })
      ).rejects.toThrow('拒绝原因是必填的');
    });

    it('should execute data_review_reject with reason', async () => {
      const topup = topupRequestFactory.buildWithStatus('rejected');
      mockFetchSuccess(topup);

      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.executeAction('data_review_reject', topup.id, {
          rejection_reason: '数据不正确',
          version: 1,
        });
      });

      expect(global.fetch).toHaveBeenCalled();
    });

    it('should throw error when finance_reject without reason', async () => {
      const topup = topupRequestFactory.build();

      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      await expect(
        act(async () => {
          await result.current.executeAction('finance_reject', topup.id, {});
        })
      ).rejects.toThrow('拒绝原因是必填的');
    });

    it('should execute complete action', async () => {
      const topup = topupRequestFactory.buildWithStatus('completed');
      mockFetchSuccess(topup);

      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.executeAction('complete', topup.id);
      });

      expect(global.fetch).toHaveBeenCalled();
    });

    it('should execute cancel action', async () => {
      const topup = topupRequestFactory.buildWithStatus('cancelled');
      mockFetchSuccess(topup);

      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.executeAction('cancel', topup.id);
      });

      expect(global.fetch).toHaveBeenCalled();
    });

    it('should throw error for unknown action', async () => {
      const topup = topupRequestFactory.build();

      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      await expect(
        act(async () => {
          // @ts-expect-error Testing unknown action
          await result.current.executeAction('unknown_action', topup.id);
        })
      ).rejects.toThrow('未知操作');
    });
  });

  describe('isLoading state', () => {
    it('should be true while mutation is pending', async () => {
      const topup = topupRequestFactory.build();

      // Create a promise that we can control
      let resolvePromise: (value: any) => void;
      const controlledPromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      (global.fetch as jest.Mock).mockReturnValueOnce(controlledPromise);

      const { result } = renderHook(() => useTopupActions(), {
        wrapper: createWrapper(),
      });

      // Start the action but don't await it
      act(() => {
        result.current.cancelTopup.mutate(topup.id);
      });

      // Loading should be true while pending (wait for async state update)
      await waitFor(() => {
        expect(result.current.isLoading).toBe(true);
      });

      // Resolve the promise
      await act(async () => {
        resolvePromise!({
          ok: true,
          status: 200,
          json: async () => ({ success: true, data: topup }),
        });
      });

      // Loading should be false after completion
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });
  });
});
