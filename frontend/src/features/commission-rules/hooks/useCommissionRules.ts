/**
 * Commission Rules Hooks
 *
 * TASK-PRJ-003: 提成配置
 * TanStack Query v5 hooks for commission rules
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  getCommissionRules,
  getCommissionRule,
  getDefaultCommissionRule,
  getProjectEffectiveRule,
  createCommissionRule,
  updateCommissionRule,
  deleteCommissionRule,
  calculateCommission,
  setAsDefault,
} from '../services/commissionRulesApi';
import type {
  CommissionRuleListParams,
  CommissionRuleCreateInput,
  CommissionRuleUpdateInput,
} from '../types';

// ========== Query Keys ==========

export const commissionRuleKeys = {
  all: ['commission-rules'] as const,
  lists: () => [...commissionRuleKeys.all, 'list'] as const,
  list: (params: CommissionRuleListParams) => [...commissionRuleKeys.lists(), params] as const,
  details: () => [...commissionRuleKeys.all, 'detail'] as const,
  detail: (id: number) => [...commissionRuleKeys.details(), id] as const,
  default: () => [...commissionRuleKeys.all, 'default'] as const,
  projectEffective: (projectId: number, targetDate?: string) =>
    [...commissionRuleKeys.all, 'project', projectId, targetDate] as const,
  calculation: (ruleId: number, conversions: number) =>
    [...commissionRuleKeys.all, 'calculate', ruleId, conversions] as const,
};

// ========== Query Hooks ==========

/**
 * Hook to fetch commission rules list
 */
export function useCommissionRules(params: CommissionRuleListParams = {}) {
  return useQuery({
    queryKey: commissionRuleKeys.list(params),
    queryFn: () => getCommissionRules(params),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Hook to fetch single commission rule
 */
export function useCommissionRule(id: number | null) {
  return useQuery({
    queryKey: commissionRuleKeys.detail(id!),
    queryFn: () => getCommissionRule(id!),
    enabled: id !== null,
    staleTime: 2 * 60 * 1000,
  });
}

/**
 * Hook to fetch default commission rule
 */
export function useDefaultCommissionRule() {
  return useQuery({
    queryKey: commissionRuleKeys.default(),
    queryFn: getDefaultCommissionRule,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch effective commission rule for a project
 */
export function useProjectEffectiveRule(projectId: number | null, targetDate?: string) {
  return useQuery({
    queryKey: commissionRuleKeys.projectEffective(projectId!, targetDate),
    queryFn: () => getProjectEffectiveRule(projectId!, targetDate),
    enabled: projectId !== null,
    staleTime: 2 * 60 * 1000,
  });
}

/**
 * Hook to calculate commission
 */
export function useCalculateCommission(ruleId: number | null, conversions: number) {
  return useQuery({
    queryKey: commissionRuleKeys.calculation(ruleId!, conversions),
    queryFn: () => calculateCommission(ruleId!, conversions),
    enabled: ruleId !== null && conversions >= 0,
    staleTime: 60 * 1000, // 1 minute
  });
}

// ========== Mutation Hooks ==========

/**
 * Hook to create commission rule
 */
export function useCreateCommissionRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: CommissionRuleCreateInput) => createCommissionRule(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: commissionRuleKeys.all });
      toast.success('提成规则创建成功');
    },
    onError: (error: Error) => {
      toast.error(error.message || '创建失败');
    },
  });
}

/**
 * Hook to update commission rule
 */
export function useUpdateCommissionRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: CommissionRuleUpdateInput }) =>
      updateCommissionRule(id, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: commissionRuleKeys.all });
      toast.success('提成规则更新成功');
    },
    onError: (error: Error) => {
      toast.error(error.message || '更新失败');
    },
  });
}

/**
 * Hook to delete commission rule
 */
export function useDeleteCommissionRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => deleteCommissionRule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: commissionRuleKeys.all });
      toast.success('提成规则已删除');
    },
    onError: (error: Error) => {
      toast.error(error.message || '删除失败');
    },
  });
}

/**
 * Hook to set rule as default
 */
export function useSetAsDefault() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => setAsDefault(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: commissionRuleKeys.all });
      toast.success('已设为默认规则');
    },
    onError: (error: Error) => {
      toast.error(error.message || '设置失败');
    },
  });
}

/**
 * Hook to calculate commission (mutation version for on-demand calculation)
 */
export function useCalculateCommissionMutation() {
  return useMutation({
    mutationFn: ({ ruleId, conversions }: { ruleId: number; conversions: number }) =>
      calculateCommission(ruleId, conversions),
    onError: (error: Error) => {
      toast.error(error.message || '计算失败');
    },
  });
}
