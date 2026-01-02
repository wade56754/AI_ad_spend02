/**
 * Settlement Rules React Query Hooks
 *
 * TanStack Query v5 hooks for settlement rule (pricing configuration) management
 *
 * SoT: DATA_SCHEMA.md v5.6 §3.5.7 (settlement_rules entity)
 * SoT: BR-PROJ.md v1.0 (定价规则)
 *
 * @module features/settlement-rules/hooks
 */

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
  type UseMutationOptions,
} from '@tanstack/react-query';
import { queryKeys, type PaginatedResponse } from '@/lib/api';
import {
  getSettlementRules,
  getSettlementRule,
  getEffectiveSettlementRules,
  createSettlementRule,
  updateSettlementRule,
  deleteSettlementRule,
} from '../services';
import type {
  SettlementRule,
  SettlementRuleListParams,
  SettlementRuleCreateInput,
  SettlementRuleUpdateInput,
} from '../types';

// ========== Query Hooks ==========

/**
 * 获取结算规则列表
 */
export function useSettlementRules(
  params: SettlementRuleListParams = {},
  options?: Omit<UseQueryOptions<PaginatedResponse<SettlementRule>>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.settlementRules.list(params),
    queryFn: () => getSettlementRules(params),
    ...options,
  });
}

/**
 * 获取结算规则详情
 */
export function useSettlementRule(
  id: number,
  options?: Omit<UseQueryOptions<SettlementRule>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.settlementRules.detail(id),
    queryFn: () => getSettlementRule(id),
    enabled: !!id,
    ...options,
  });
}

/**
 * 获取当前生效的结算规则列表 (用于下拉选择)
 */
export function useEffectiveSettlementRules(
  options?: Omit<UseQueryOptions<SettlementRule[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.settlementRules.effective(),
    queryFn: getEffectiveSettlementRules,
    staleTime: 5 * 60 * 1000, // 5 minutes - rules don't change often
    ...options,
  });
}

// ========== Mutation Hooks ==========

/**
 * 创建结算规则
 */
export function useCreateSettlementRule(
  options?: UseMutationOptions<SettlementRule, Error, SettlementRuleCreateInput>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createSettlementRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settlementRules.all });
    },
    ...options,
  });
}

/**
 * 更新结算规则
 */
export function useUpdateSettlementRule(
  options?: UseMutationOptions<
    SettlementRule,
    Error,
    { id: number; input: SettlementRuleUpdateInput }
  >
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => updateSettlementRule(id, input),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settlementRules.detail(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.settlementRules.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.settlementRules.effective() });
    },
    ...options,
  });
}

/**
 * 删除结算规则
 */
export function useDeleteSettlementRule(options?: UseMutationOptions<void, Error, number>) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteSettlementRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settlementRules.all });
    },
    ...options,
  });
}

// ========== Refresh Hook ==========

/**
 * 刷新结算规则数据
 *
 * @example
 * ```tsx
 * const { refreshAll, refreshList, refreshEffective } = useRefreshSettlementRules();
 * // 刷新所有数据
 * refreshAll();
 * // 仅刷新列表
 * refreshList();
 * ```
 */
export function useRefreshSettlementRules() {
  const queryClient = useQueryClient();

  return {
    /** 刷新所有结算规则数据 */
    refreshAll: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settlementRules.all });
    },
    /** 刷新结算规则列表 */
    refreshList: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settlementRules.lists() });
    },
    /** 刷新生效规则列表 */
    refreshEffective: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settlementRules.effective() });
    },
    /** 刷新单个规则详情 */
    refreshDetail: (id: number) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settlementRules.detail(id) });
    },
  };
}
