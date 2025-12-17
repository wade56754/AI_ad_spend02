/**
 * Project Actions Hook Tests
 *
 * Tests for useProjectActions hook and helper functions
 * SoT: STATE_MACHINE.md v2.6 § 5
 */

import {
  getAvailableActions,
  canTransition,
  ALLOWED_TRANSITIONS,
} from '@/features/projects/hooks/useProjectActions';

describe('getAvailableActions', () => {
  it('returns pause, complete, and cancel actions for active status', () => {
    const actions = getAvailableActions('active');
    expect(actions).toHaveLength(3);
    expect(actions.map((a) => a.action)).toContain('pause');
    expect(actions.map((a) => a.action)).toContain('complete');
    expect(actions.map((a) => a.action)).toContain('cancel');
  });

  it('returns resume and cancel actions for paused status', () => {
    const actions = getAvailableActions('paused');
    expect(actions).toHaveLength(2);
    expect(actions.map((a) => a.action)).toContain('resume');
    expect(actions.map((a) => a.action)).toContain('cancel');
  });

  it('returns no actions for completed status', () => {
    const actions = getAvailableActions('completed');
    expect(actions).toHaveLength(0);
  });

  it('returns no actions for cancelled status', () => {
    const actions = getAvailableActions('cancelled');
    expect(actions).toHaveLength(0);
  });

  it('pause action targets paused status', () => {
    const actions = getAvailableActions('active');
    const pauseAction = actions.find((a) => a.action === 'pause');
    expect(pauseAction?.targetStatus).toBe('paused');
    expect(pauseAction?.variant).toBe('outline');
  });

  it('complete action requires confirmation', () => {
    const actions = getAvailableActions('active');
    const completeAction = actions.find((a) => a.action === 'complete');
    expect(completeAction?.requiresConfirm).toBe(true);
    expect(completeAction?.targetStatus).toBe('completed');
  });

  it('cancel action has destructive variant', () => {
    const actions = getAvailableActions('active');
    const cancelAction = actions.find((a) => a.action === 'cancel');
    expect(cancelAction?.variant).toBe('destructive');
    expect(cancelAction?.requiresConfirm).toBe(true);
  });
});

describe('canTransition', () => {
  it('allows active to paused transition', () => {
    expect(canTransition('active', 'paused')).toBe(true);
  });

  it('allows active to completed transition', () => {
    expect(canTransition('active', 'completed')).toBe(true);
  });

  it('allows active to cancelled transition', () => {
    expect(canTransition('active', 'cancelled')).toBe(true);
  });

  it('allows paused to active transition', () => {
    expect(canTransition('paused', 'active')).toBe(true);
  });

  it('allows paused to cancelled transition', () => {
    expect(canTransition('paused', 'cancelled')).toBe(true);
  });

  it('denies completed to active transition', () => {
    expect(canTransition('completed', 'active')).toBe(false);
  });

  it('denies cancelled to active transition', () => {
    expect(canTransition('cancelled', 'active')).toBe(false);
  });

  it('denies paused to completed transition', () => {
    expect(canTransition('paused', 'completed')).toBe(false);
  });
});

describe('ALLOWED_TRANSITIONS', () => {
  it('has correct number of transitions', () => {
    expect(ALLOWED_TRANSITIONS.length).toBe(5);
  });

  it('covers all valid state transitions', () => {
    const transitions = ALLOWED_TRANSITIONS.map((t) => `${t.from}->${t.to}`);
    expect(transitions).toContain('active->paused');
    expect(transitions).toContain('active->completed');
    expect(transitions).toContain('active->cancelled');
    expect(transitions).toContain('paused->active');
    expect(transitions).toContain('paused->cancelled');
  });
});
