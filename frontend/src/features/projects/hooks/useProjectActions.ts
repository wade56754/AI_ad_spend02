/**
 * Project Actions Aggregated Hook
 *
 * Centralized hook for all project actions and state transitions
 * SoT: STATE_MACHINE.md v2.6 Section 5
 */

import { useCallback } from 'react';
import {
  useCreateProject,
  useUpdateProject,
  useDeleteProject,
  useAssignMember,
  useRemoveMember,
} from './useProjects';
import type {
  ProjectStatus,
  ProjectCreateInput,
  ProjectUpdateInput,
  ProjectMemberAssignInput,
} from '../types';

// === Status Transition Definitions ===

export type ProjectAction =
  | 'create'
  | 'update'
  | 'delete'
  | 'pause'
  | 'resume'
  | 'complete'
  | 'cancel'
  | 'assign_member'
  | 'remove_member';

/**
 * Allowed status transitions based on STATE_MACHINE.md v2.6 Section 5
 */
export const ALLOWED_TRANSITIONS: Array<{
  from: ProjectStatus;
  to: ProjectStatus;
  action: string;
}> = [
  { from: 'active', to: 'paused', action: 'pause' },
  { from: 'active', to: 'completed', action: 'complete' },
  { from: 'active', to: 'cancelled', action: 'cancel' },
  { from: 'paused', to: 'active', action: 'resume' },
  { from: 'paused', to: 'cancelled', action: 'cancel' },
];

/**
 * Check if a status transition is allowed
 */
export function canTransition(
  from: ProjectStatus,
  to: ProjectStatus
): boolean {
  return ALLOWED_TRANSITIONS.some(
    (t) => t.from === from && t.to === to
  );
}

/**
 * Get available actions for a given status
 */
export function getAvailableActions(status: ProjectStatus): Array<{
  action: ProjectAction;
  label: string;
  targetStatus?: ProjectStatus;
  variant?: 'default' | 'outline' | 'destructive';
  requiresConfirm?: boolean;
}> {
  const actions: Array<{
    action: ProjectAction;
    label: string;
    targetStatus?: ProjectStatus;
    variant?: 'default' | 'outline' | 'destructive';
    requiresConfirm?: boolean;
  }> = [];

  switch (status) {
    case 'active':
      actions.push(
        { action: 'pause', label: '暂停项目', targetStatus: 'paused', variant: 'outline' },
        { action: 'complete', label: '完成项目', targetStatus: 'completed', variant: 'default', requiresConfirm: true },
        { action: 'cancel', label: '取消项目', targetStatus: 'cancelled', variant: 'destructive', requiresConfirm: true }
      );
      break;

    case 'paused':
      actions.push(
        { action: 'resume', label: '恢复项目', targetStatus: 'active', variant: 'default' },
        { action: 'cancel', label: '取消项目', targetStatus: 'cancelled', variant: 'destructive', requiresConfirm: true }
      );
      break;

    case 'completed':
      // No actions for completed projects
      break;

    case 'cancelled':
      // No actions for cancelled projects
      break;
  }

  return actions;
}

// === Action Input Types ===

export interface ActionInput {
  create?: ProjectCreateInput;
  update?: { id: number; input: ProjectUpdateInput };
  delete?: number;
  pause?: number;
  resume?: number;
  complete?: number;
  cancel?: number;
  assign_member?: { projectId: number; input: ProjectMemberAssignInput };
  remove_member?: { projectId: number; userId: string };
}

// === Main Hook ===

export interface UseProjectActionsOptions {
  onSuccess?: (action: ProjectAction) => void;
  onError?: (action: ProjectAction, error: Error) => void;
}

export function useProjectActions(options: UseProjectActionsOptions = {}) {
  const { onSuccess, onError } = options;

  // CRUD mutations
  const createProject = useCreateProject({
    onSuccess: () => onSuccess?.('create'),
    onError: (error) => onError?.('create', error),
  });

  const updateProject = useUpdateProject({
    onSuccess: () => onSuccess?.('update'),
    onError: (error) => onError?.('update', error),
  });

  const deleteProject = useDeleteProject({
    onSuccess: () => onSuccess?.('delete'),
    onError: (error) => onError?.('delete', error),
  });

  // Member mutations
  const assignMember = useAssignMember({
    onSuccess: () => onSuccess?.('assign_member'),
    onError: (error) => onError?.('assign_member', error),
  });

  const removeMember = useRemoveMember({
    onSuccess: () => onSuccess?.('remove_member'),
    onError: (error) => onError?.('remove_member', error),
  });

  // Status change helpers
  const pauseProject = useCallback(
    (id: number) => {
      return updateProject.mutateAsync({
        id,
        input: { status: 'paused' },
      });
    },
    [updateProject]
  );

  const resumeProject = useCallback(
    (id: number) => {
      return updateProject.mutateAsync({
        id,
        input: { status: 'active' },
      });
    },
    [updateProject]
  );

  const completeProject = useCallback(
    (id: number) => {
      return updateProject.mutateAsync({
        id,
        input: { status: 'completed' },
      });
    },
    [updateProject]
  );

  const cancelProject = useCallback(
    (id: number) => {
      return updateProject.mutateAsync({
        id,
        input: { status: 'cancelled' },
      });
    },
    [updateProject]
  );

  // Combined loading state
  const isLoading =
    createProject.isPending ||
    updateProject.isPending ||
    deleteProject.isPending ||
    assignMember.isPending ||
    removeMember.isPending;

  // Execute action by name
  const executeAction = useCallback(
    async (action: ProjectAction, input: ActionInput) => {
      switch (action) {
        case 'create':
          if (input.create) {
            return createProject.mutateAsync(input.create);
          }
          break;

        case 'update':
          if (input.update) {
            return updateProject.mutateAsync(input.update);
          }
          break;

        case 'delete':
          if (input.delete !== undefined) {
            return deleteProject.mutateAsync(input.delete);
          }
          break;

        case 'pause':
          if (input.pause !== undefined) {
            return pauseProject(input.pause);
          }
          break;

        case 'resume':
          if (input.resume !== undefined) {
            return resumeProject(input.resume);
          }
          break;

        case 'complete':
          if (input.complete !== undefined) {
            return completeProject(input.complete);
          }
          break;

        case 'cancel':
          if (input.cancel !== undefined) {
            return cancelProject(input.cancel);
          }
          break;

        case 'assign_member':
          if (input.assign_member) {
            return assignMember.mutateAsync(input.assign_member);
          }
          break;

        case 'remove_member':
          if (input.remove_member) {
            return removeMember.mutateAsync(input.remove_member);
          }
          break;
      }
    },
    [
      createProject,
      updateProject,
      deleteProject,
      pauseProject,
      resumeProject,
      completeProject,
      cancelProject,
      assignMember,
      removeMember,
    ]
  );

  return {
    // Mutations
    createProject,
    updateProject,
    deleteProject,
    assignMember,
    removeMember,

    // Status change helpers
    pauseProject,
    resumeProject,
    completeProject,
    cancelProject,

    // State
    isLoading,

    // Utilities
    executeAction,
    getAvailableActions,
    canTransition,
  };
}

export default useProjectActions;
