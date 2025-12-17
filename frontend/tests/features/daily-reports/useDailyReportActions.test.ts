/**
 * Daily Report Actions Hook Tests
 *
 * Tests for useDailyReportActions hook and helper functions
 * SoT: STATE_MACHINE.md v2.6 § 8
 */

import { getAvailableActions, canTransition } from '@/features/daily-reports/hooks/useDailyReportActions';
import { ALLOWED_TRANSITIONS } from '@/features/daily-reports/types';
import type { DailyReportStatus } from '@/features/daily-reports/types';

describe('getAvailableActions', () => {
  it('returns submit_for_trend action for raw_submitted status', () => {
    const actions = getAvailableActions('raw_submitted');
    expect(actions).toHaveLength(1);
    expect(actions[0].action).toBe('submit_for_trend');
    expect(actions[0].requiresInput).toBe(false);
  });

  it('returns approve_trend and flag_trend actions for trend_pending status', () => {
    const actions = getAvailableActions('trend_pending');
    expect(actions).toHaveLength(2);
    expect(actions.map(a => a.action)).toContain('approve_trend');
    expect(actions.map(a => a.action)).toContain('flag_trend');
  });

  it('returns submit_for_final action for trend_ok status', () => {
    const actions = getAvailableActions('trend_ok');
    expect(actions).toHaveLength(1);
    expect(actions[0].action).toBe('submit_for_final');
  });

  it('returns resolve_flag action for trend_flagged status', () => {
    const actions = getAvailableActions('trend_flagged');
    expect(actions).toHaveLength(1);
    expect(actions[0].action).toBe('resolve_flag');
    expect(actions[0].requiresInput).toBe(true);
  });

  it('returns submit_for_final action for trend_resolved status', () => {
    const actions = getAvailableActions('trend_resolved');
    expect(actions).toHaveLength(1);
    expect(actions[0].action).toBe('submit_for_final');
  });

  it('returns confirm_final action for final_pending status', () => {
    const actions = getAvailableActions('final_pending');
    expect(actions).toHaveLength(1);
    expect(actions[0].action).toBe('confirm_final');
    expect(actions[0].requiresInput).toBe(true);
  });

  it('returns lock action for final_confirmed status', () => {
    const actions = getAvailableActions('final_confirmed');
    expect(actions).toHaveLength(1);
    expect(actions[0].action).toBe('lock');
    expect(actions[0].variant).toBe('destructive');
  });

  it('returns no actions for final_locked status', () => {
    const actions = getAvailableActions('final_locked');
    expect(actions).toHaveLength(0);
  });
});

describe('canTransition', () => {
  it('allows admin to perform all transitions', () => {
    expect(canTransition('raw_submitted', 'trend_pending', 'admin')).toBe(true);
    expect(canTransition('trend_pending', 'trend_ok', 'admin')).toBe(true);
    expect(canTransition('trend_pending', 'trend_flagged', 'admin')).toBe(true);
    expect(canTransition('final_pending', 'final_confirmed', 'admin')).toBe(true);
    expect(canTransition('final_confirmed', 'final_locked', 'admin')).toBe(true);
  });

  it('allows operator to submit for trend', () => {
    expect(canTransition('raw_submitted', 'trend_pending', 'operator')).toBe(true);
  });

  it('allows manager to approve/flag trends', () => {
    expect(canTransition('trend_pending', 'trend_ok', 'manager')).toBe(true);
    expect(canTransition('trend_pending', 'trend_flagged', 'manager')).toBe(true);
  });

  it('denies invalid transitions', () => {
    expect(canTransition('raw_submitted', 'final_locked', 'admin')).toBe(false);
    expect(canTransition('trend_ok', 'raw_submitted', 'admin')).toBe(false);
    expect(canTransition('final_locked', 'raw_submitted', 'admin')).toBe(false);
  });

  it('denies transitions for unauthorized roles', () => {
    expect(canTransition('final_pending', 'final_confirmed', 'operator')).toBe(false);
    expect(canTransition('final_confirmed', 'final_locked', 'manager')).toBe(false);
  });
});

describe('ALLOWED_TRANSITIONS', () => {
  it('has correct number of transitions', () => {
    expect(ALLOWED_TRANSITIONS.length).toBe(8);
  });

  it('covers all 8 state transitions', () => {
    const transitions = ALLOWED_TRANSITIONS.map(t => `${t.from}->${t.to}`);
    expect(transitions).toContain('raw_submitted->trend_pending');
    expect(transitions).toContain('trend_pending->trend_ok');
    expect(transitions).toContain('trend_pending->trend_flagged');
    expect(transitions).toContain('trend_flagged->trend_resolved');
    expect(transitions).toContain('trend_ok->final_pending');
    expect(transitions).toContain('trend_resolved->final_pending');
    expect(transitions).toContain('final_pending->final_confirmed');
    expect(transitions).toContain('final_confirmed->final_locked');
  });
});
