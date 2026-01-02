/**
 * Topup Actions Aggregated Hook
 *
 * Centralized hook for all topup actions and state transitions
 * SoT: STATE_MACHINE.md v2.9 Section 9
 * SoT: API_SOT.md v9.7 Section 10
 */

import { useCallback } from 'react';
import {
  useCreateTopup,
  useSubmitTopup,
  useReviewTopup,
  useApproveTopup,
  useRejectTopup,
  useConfirmPaidTopup,
  useCancelTopup,
} from './useTopups';
import type { TopupStatus, TopupAction, TopupRejectInput } from '../types';
import { TOPUP_TRANSITIONS, TOPUP_ACTION_ROLES } from '../types';

// === State Transition Helpers ===

/**
 * Check if a status transition is allowed
 */
export function canTransition(from: TopupStatus, to: TopupStatus): boolean {
  const allowedTransitions = TOPUP_TRANSITIONS[from];
  return allowedTransitions?.includes(to) ?? false;
}

/**
 * Check if user role can perform action
 */
export function canPerformAction(action: TopupAction, userRole: string): boolean {
  const allowedRoles = TOPUP_ACTION_ROLES[action];
  return allowedRoles?.includes(userRole) ?? false;
}

/**
 * Get available actions for a given status and user role
 */
export function getAvailableActions(
  status: TopupStatus,
  userRole: string
): Array<{
  action: TopupAction;
  label: string;
  targetStatus?: TopupStatus;
  variant?: 'default' | 'outline' | 'destructive';
  requiresInput?: boolean;
  requiresConfirm?: boolean;
}> {
  const actions: Array<{
    action: TopupAction;
    label: string;
    targetStatus?: TopupStatus;
    variant?: 'default' | 'outline' | 'destructive';
    requiresInput?: boolean;
    requiresConfirm?: boolean;
  }> = [];

  switch (status) {
    case 'draft':
      if (canPerformAction('submit', userRole)) {
        actions.push({
          action: 'submit',
          label: '提交审批',
          targetStatus: 'pending_review',
          variant: 'default',
          requiresConfirm: true,
        });
      }
      if (canPerformAction('cancel', userRole)) {
        actions.push({
          action: 'cancel',
          label: '取消申请',
          targetStatus: 'cancelled',
          variant: 'destructive',
          requiresConfirm: true,
        });
      }
      break;

    case 'pending_review':
      if (canPerformAction('data_review_approve', userRole)) {
        actions.push({
          action: 'data_review_approve',
          label: '数据复核通过',
          targetStatus: 'finance_approve',
          variant: 'default',
          requiresInput: true,
        });
      }
      if (canPerformAction('data_review_reject', userRole)) {
        actions.push({
          action: 'data_review_reject',
          label: '数据复核拒绝',
          targetStatus: 'rejected',
          variant: 'destructive',
          requiresInput: true,
        });
      }
      if (canPerformAction('cancel', userRole)) {
        actions.push({
          action: 'cancel',
          label: '取消申请',
          targetStatus: 'cancelled',
          variant: 'outline',
          requiresConfirm: true,
        });
      }
      break;

    case 'finance_approve':
      if (canPerformAction('finance_approve', userRole)) {
        actions.push({
          action: 'finance_approve',
          label: '财务批准',
          targetStatus: 'paid',
          variant: 'default',
          requiresInput: true,
        });
      }
      if (canPerformAction('finance_reject', userRole)) {
        actions.push({
          action: 'finance_reject',
          label: '财务拒绝',
          targetStatus: 'rejected',
          variant: 'destructive',
          requiresInput: true,
        });
      }
      if (canPerformAction('cancel', userRole)) {
        actions.push({
          action: 'cancel',
          label: '取消申请',
          targetStatus: 'cancelled',
          variant: 'outline',
          requiresConfirm: true,
        });
      }
      break;

    case 'paid':
      if (canPerformAction('complete', userRole)) {
        actions.push({
          action: 'complete',
          label: '确认到账',
          targetStatus: 'completed',
          variant: 'default',
          requiresConfirm: true,
        });
      }
      break;

    case 'completed':
    case 'rejected':
    case 'cancelled':
      // Terminal states - no actions available
      break;
  }

  return actions;
}

// === Main Hook ===

export interface UseTopupActionsOptions {
  onSuccess?: (action: TopupAction) => void;
  onError?: (action: TopupAction, error: Error) => void;
}

export function useTopupActions(options: UseTopupActionsOptions = {}) {
  const { onSuccess, onError } = options;

  // Mutations
  const createTopupMutation = useCreateTopup({
    onSuccess: () => onSuccess?.('create'),
    onError: (error) => onError?.('create', error),
  });

  const submitTopupMutation = useSubmitTopup({
    onSuccess: () => onSuccess?.('submit'),
    onError: (error) => onError?.('submit', error),
  });

  const reviewTopupMutation = useReviewTopup({
    onSuccess: () => onSuccess?.('data_review_approve'),
    onError: (error) => onError?.('data_review_approve', error),
  });

  const approveTopupMutation = useApproveTopup({
    onSuccess: () => onSuccess?.('finance_approve'),
    onError: (error) => onError?.('finance_approve', error),
  });

  const rejectTopupMutation = useRejectTopup({
    onSuccess: () => onSuccess?.('data_review_reject'),
    onError: (error) => onError?.('data_review_reject', error),
  });

  const confirmPaidMutation = useConfirmPaidTopup({
    onSuccess: () => onSuccess?.('complete'),
    onError: (error) => onError?.('complete', error),
  });

  const cancelTopupMutation = useCancelTopup({
    onSuccess: () => onSuccess?.('cancel'),
    onError: (error) => onError?.('cancel', error),
  });

  // Action handlers
  const submitForReview = useCallback(
    (id: string) => {
      return submitTopupMutation.mutateAsync({ id });
    },
    [submitTopupMutation]
  );

  const dataReviewApprove = useCallback(
    (id: string, input?: { notes?: string }) => {
      return reviewTopupMutation.mutateAsync({
        id,
        input: { approved: true, version: 1, notes: input?.notes },
      });
    },
    [reviewTopupMutation]
  );

  const dataReviewReject = useCallback(
    (id: string, input: TopupRejectInput) => {
      return rejectTopupMutation.mutateAsync({ id, input });
    },
    [rejectTopupMutation]
  );

  const financeApprove = useCallback(
    (id: string, input?: { notes?: string }) => {
      return approveTopupMutation.mutateAsync({
        id,
        input: { approved: true, version: 1, notes: input?.notes },
      });
    },
    [approveTopupMutation]
  );

  const financeReject = useCallback(
    (id: string, input: TopupRejectInput) => {
      return rejectTopupMutation.mutateAsync({ id, input });
    },
    [rejectTopupMutation]
  );

  const markCompleted = useCallback(
    (id: string) => {
      return confirmPaidMutation.mutateAsync({ id });
    },
    [confirmPaidMutation]
  );

  const cancel = useCallback(
    (id: string) => {
      return cancelTopupMutation.mutateAsync(id);
    },
    [cancelTopupMutation]
  );

  // Combined loading state
  const isLoading =
    createTopupMutation.isPending ||
    submitTopupMutation.isPending ||
    reviewTopupMutation.isPending ||
    approveTopupMutation.isPending ||
    rejectTopupMutation.isPending ||
    confirmPaidMutation.isPending ||
    cancelTopupMutation.isPending;

  // Execute action by name
  const executeAction = useCallback(
    async (
      action: TopupAction,
      topupId: string,
      input?: {
        notes?: string;
        rejection_reason?: string;
        version?: number;
      }
    ) => {
      switch (action) {
        case 'submit':
          return submitForReview(topupId);

        case 'data_review_approve':
          return dataReviewApprove(topupId, { notes: input?.notes });

        case 'data_review_reject':
          if (!input?.rejection_reason) {
            throw new Error('拒绝原因是必填的');
          }
          return dataReviewReject(topupId, {
            rejection_reason: input.rejection_reason,
            version: input.version ?? 1,
          });

        case 'finance_approve':
          return financeApprove(topupId, { notes: input?.notes });

        case 'finance_reject':
          if (!input?.rejection_reason) {
            throw new Error('拒绝原因是必填的');
          }
          return financeReject(topupId, {
            rejection_reason: input.rejection_reason,
            version: input.version ?? 1,
          });

        case 'complete':
          return markCompleted(topupId);

        case 'cancel':
          return cancel(topupId);

        default:
          throw new Error(`未知操作: ${action}`);
      }
    },
    [
      submitForReview,
      dataReviewApprove,
      dataReviewReject,
      financeApprove,
      financeReject,
      markCompleted,
      cancel,
    ]
  );

  return {
    // Mutations
    createTopup: createTopupMutation,
    submitTopup: submitTopupMutation,
    reviewTopup: reviewTopupMutation,
    approveTopup: approveTopupMutation,
    rejectTopup: rejectTopupMutation,
    confirmPaid: confirmPaidMutation,
    cancelTopup: cancelTopupMutation,

    // Action helpers
    submitForReview,
    dataReviewApprove,
    dataReviewReject,
    financeApprove,
    financeReject,
    markCompleted,
    cancel,

    // State
    isLoading,

    // Utilities
    executeAction,
    getAvailableActions,
    canTransition,
    canPerformAction,
  };
}

export default useTopupActions;
