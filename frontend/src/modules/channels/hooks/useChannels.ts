/**
 * Channels React Query Hooks
 *
 * TanStack Query v5 hooks for channel management
 * SoT 对齐: DATA_SCHEMA.md v5.2
 */

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
  type UseMutationOptions,
} from '@tanstack/react-query';
import { queryKeys } from '@/lib/api';
import {
  getChannels,
  getChannel,
  createChannel,
  updateChannel,
  activateChannel,
  deactivateChannel,
} from '../services';
import type {
  Channel,
  ChannelListParams,
  ChannelCreateInput,
  ChannelUpdateInput,
  ChannelListResponse,
} from '../types';

// ========== Query Hooks ==========

/**
 * Fetch paginated channel list
 */
export function useChannels(
  params: ChannelListParams = {},
  options?: Omit<UseQueryOptions<ChannelListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.channels.list(params),
    queryFn: () => getChannels(params),
    ...options,
  });
}

/**
 * Fetch single channel by ID
 */
export function useChannel(
  id: string,
  options?: Omit<UseQueryOptions<{ data: Channel }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.channels.detail(id),
    queryFn: () => getChannel(id),
    enabled: !!id,
    ...options,
  });
}

// ========== Mutation Hooks ==========

/**
 * Create channel mutation
 */
export function useCreateChannel(
  options?: UseMutationOptions<{ data: Channel }, Error, ChannelCreateInput>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createChannel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.channels.all });
    },
    ...options,
  });
}

/**
 * Update channel mutation
 */
export function useUpdateChannel(
  options?: UseMutationOptions<{ data: Channel }, Error, { id: string; input: ChannelUpdateInput }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }) => updateChannel(id, input),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.channels.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.channels.lists() });
    },
    ...options,
  });
}

/**
 * Activate channel mutation
 */
export function useActivateChannel(
  options?: UseMutationOptions<{ data: Channel }, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: activateChannel,
    onSuccess: (data, id) => {
      queryClient.setQueryData(queryKeys.channels.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.channels.lists() });
    },
    ...options,
  });
}

/**
 * Deactivate channel mutation
 */
export function useDeactivateChannel(
  options?: UseMutationOptions<{ data: Channel }, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deactivateChannel,
    onSuccess: (data, id) => {
      queryClient.setQueryData(queryKeys.channels.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.channels.lists() });
    },
    ...options,
  });
}
