/**
 * Daily Report Status Actions Hook
 *
 * Aggregates all state transition mutations for daily reports
 * SoT: STATE_MACHINE.md v2.6 § 8 (8-state machine)
 *
 * State flow:
 * raw_submitted → trend_pending → trend_ok/trend_flagged
 * → trend_resolved → final_pending → final_confirmed → final_locked
 */

import {
  useSubmitForTrend,
  useApproveTrend,
  useFlagTrend,
  useResolveFlag,
  useSubmitForFinal,
  useConfirmFinal,
  useLockReport,
  useBulkSubmitForTrend,
} from './useDailyReports';
import type {
  DailyReport,
  DailyReportStatus,
  TrendResolveInput,
  FinalConfirmInput,
} from '../types';
import { ALLOWED_TRANSITIONS } from '../types';

/**
 * Available actions for a given status
 */
export interface AvailableAction {
  action: string;
  label: string;
  description: string;
  variant: 'default' | 'success' | 'warning' | 'destructive';
  requiresInput: boolean;
  allowedRoles: string[];
}

/**
 * Get available actions for current status
 */
export function getAvailableActions(status: DailyReportStatus): AvailableAction[] {
  const actions: AvailableAction[] = [];

  switch (status) {
    case 'raw_submitted':
      actions.push({
        action: 'submit_for_trend',
        label: '提交趋势审核',
        description: '提交日报进行趋势分析检查',
        variant: 'default',
        requiresInput: false,
        allowedRoles: ['pitcher', 'project_owner', 'admin'],
      });
      break;

    case 'trend_pending':
      actions.push({
        action: 'approve_trend',
        label: '趋势通过',
        description: '确认趋势数据正常',
        variant: 'success',
        requiresInput: false,
        allowedRoles: ['project_owner', 'admin'],
      });
      actions.push({
        action: 'flag_trend',
        label: '标记异常',
        description: '标记趋势数据异常需要处理',
        variant: 'warning',
        requiresInput: true,
        allowedRoles: ['project_owner', 'admin'],
      });
      break;

    case 'trend_ok':
      actions.push({
        action: 'submit_for_final',
        label: '提交终审',
        description: '提交日报进行最终确认',
        variant: 'default',
        requiresInput: false,
        allowedRoles: ['project_owner', 'admin'],
      });
      break;

    case 'trend_flagged':
      actions.push({
        action: 'resolve_flag',
        label: '处理异常',
        description: '处理趋势异常问题',
        variant: 'warning',
        requiresInput: true,
        allowedRoles: ['project_owner', 'admin'],
      });
      break;

    case 'trend_resolved':
      actions.push({
        action: 'submit_for_final',
        label: '提交终审',
        description: '提交日报进行最终确认',
        variant: 'default',
        requiresInput: false,
        allowedRoles: ['project_owner', 'admin'],
      });
      break;

    case 'final_pending':
      actions.push({
        action: 'confirm_final',
        label: '确认终审',
        description: '确认最终数据并提交',
        variant: 'success',
        requiresInput: true,
        allowedRoles: ['admin'],
      });
      break;

    case 'final_confirmed':
      actions.push({
        action: 'lock',
        label: '锁定日报',
        description: '锁定日报数据，不可修改',
        variant: 'destructive',
        requiresInput: false,
        allowedRoles: ['admin'],
      });
      break;

    case 'final_locked':
      // No actions available for locked status
      break;
  }

  return actions;
}

/**
 * Check if a transition is allowed
 */
export function canTransition(
  from: DailyReportStatus,
  to: DailyReportStatus,
  userRole: string
): boolean {
  const transition = ALLOWED_TRANSITIONS.find(
    (t) => t.from === from && t.to === to
  );

  if (!transition) return false;
  return transition.allowed_roles.includes(userRole);
}

/**
 * Aggregated hook for all daily report actions
 */
export function useDailyReportActions(reportId?: string) {
  const submitForTrend = useSubmitForTrend();
  const approveTrend = useApproveTrend();
  const flagTrend = useFlagTrend();
  const resolveFlag = useResolveFlag();
  const submitForFinal = useSubmitForFinal();
  const confirmFinal = useConfirmFinal();
  const lockReport = useLockReport();
  const bulkSubmitForTrend = useBulkSubmitForTrend();

  return {
    // Individual mutations
    submitForTrend,
    approveTrend,
    flagTrend,
    resolveFlag,
    submitForFinal,
    confirmFinal,
    lockReport,
    bulkSubmitForTrend,

    // Computed loading state
    isLoading:
      submitForTrend.isPending ||
      approveTrend.isPending ||
      flagTrend.isPending ||
      resolveFlag.isPending ||
      submitForFinal.isPending ||
      confirmFinal.isPending ||
      lockReport.isPending ||
      bulkSubmitForTrend.isPending,

    // Execute action by name
    executeAction: async (
      action: string,
      id: string,
      input?: TrendResolveInput | FinalConfirmInput | { notes: string }
    ) => {
      switch (action) {
        case 'submit_for_trend':
          return submitForTrend.mutateAsync(id);
        case 'approve_trend':
          return approveTrend.mutateAsync(id);
        case 'flag_trend':
          if (!input || !('notes' in input)) {
            throw new Error('Flag trend requires notes');
          }
          return flagTrend.mutateAsync({ id, notes: input.notes });
        case 'resolve_flag':
          if (!input) {
            throw new Error('Resolve flag requires input');
          }
          return resolveFlag.mutateAsync({ id, input: input as TrendResolveInput });
        case 'submit_for_final':
          return submitForFinal.mutateAsync(id);
        case 'confirm_final':
          if (!input) {
            throw new Error('Confirm final requires input');
          }
          return confirmFinal.mutateAsync({ id, input: input as FinalConfirmInput });
        case 'lock':
          return lockReport.mutateAsync(id);
        default:
          throw new Error(`Unknown action: ${action}`);
      }
    },

    // Helper functions
    getAvailableActions,
    canTransition,
  };
}

export type { TrendResolveInput, FinalConfirmInput } from '../types';
