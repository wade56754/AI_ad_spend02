/**
 * Ledger Mutation Hooks
 *
 * TanStack Query v5 mutation hooks for ledger write operations
 *
 * @permission admin, finance only
 *
 * SoT References:
 * - LEDGER_SOT.md v1.1 (Double-entry bookkeeping rules)
 * - BR-FIN.md v1.1 (Financial business rules)
 * - MASTER.md v4.9 §2.4 (Role permissions)
 *
 * @module features/ledger/hooks
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/api';
import {
  createTransaction,
  updateTransactionStatus,
  createReversal,
  type CreateTransactionRequest,
  type TransactionResponse,
} from '../services/ledgerApi';

// === Create Transaction Mutation ===

/**
 * Hook for creating a new transaction
 *
 * Automatically invalidates:
 * - Ledger entries list
 * - Ledger stats
 * - Related balance queries
 *
 * @permission admin, finance
 */
export function useCreateTransaction() {
  const queryClient = useQueryClient();

  return useMutation<TransactionResponse, Error, CreateTransactionRequest>({
    mutationFn: createTransaction,
    onSuccess: (data) => {
      // Invalidate ledger entries list
      queryClient.invalidateQueries({
        queryKey: queryKeys.ledger.all,
      });

      // Invalidate stats
      queryClient.invalidateQueries({
        queryKey: [...queryKeys.ledger.all, 'stats'],
      });

      // If project-specific, invalidate project balance
      if (data.project_id) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.ledger.projectBalance(data.project_id),
        });
      }
    },
  });
}

// === Update Transaction Status Mutation ===

interface UpdateStatusParams {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  note?: string;
}

/**
 * Hook for updating transaction status
 *
 * @permission admin, finance
 */
export function useUpdateTransactionStatus() {
  const queryClient = useQueryClient();

  return useMutation<TransactionResponse, Error, UpdateStatusParams>({
    mutationFn: ({ id, ...data }) => updateTransactionStatus(id, data),
    onSuccess: (data) => {
      // Invalidate the specific transaction
      queryClient.invalidateQueries({
        queryKey: queryKeys.ledger.detail(data.id),
      });

      // Invalidate list
      queryClient.invalidateQueries({
        queryKey: queryKeys.ledger.all,
      });
    },
  });
}

// === Create Reversal (红冲) Mutation ===

interface CreateReversalParams {
  transactionId: string;
  reason: string;
}

/**
 * Hook for creating a reversal (红冲) transaction
 *
 * Creates an opposite transaction to cancel out an incorrect entry.
 *
 * @permission admin, finance
 * @sot BR-FIN.md v1.1 §BR-FIN-007 红冲规则
 */
export function useCreateReversal() {
  const queryClient = useQueryClient();

  return useMutation<TransactionResponse, Error, CreateReversalParams>({
    mutationFn: ({ transactionId, reason }) =>
      createReversal(transactionId, { reason }),
    onSuccess: () => {
      // Invalidate all ledger queries
      queryClient.invalidateQueries({
        queryKey: queryKeys.ledger.all,
      });

      // Invalidate stats
      queryClient.invalidateQueries({
        queryKey: [...queryKeys.ledger.all, 'stats'],
      });
    },
  });
}
