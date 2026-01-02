/**
 * Topup Types Tests
 *
 * Tests for state transitions and role-based permissions
 * SoT: STATE_MACHINE.md v2.6 Section 9
 */

import {
  TOPUP_STATUS_CONFIG,
  TOPUP_TRANSITIONS,
  TOPUP_ACTION_ROLES,
  type TopupStatus,
  type TopupAction,
} from '@/features/topups/types';
import {
  canTransition,
  canPerformAction,
  getAvailableActions,
} from '@/features/topups/hooks/useTopupActions';

describe('Topup Types', () => {
  describe('TOPUP_STATUS_CONFIG', () => {
    const ALL_STATUSES: TopupStatus[] = [
      'draft',
      'pending_review',
      'finance_approve',
      'paid',
      'completed',
      'rejected',
      'cancelled',
    ];

    it('should have config for all 7 statuses', () => {
      expect(Object.keys(TOPUP_STATUS_CONFIG)).toHaveLength(7);
      ALL_STATUSES.forEach((status) => {
        expect(TOPUP_STATUS_CONFIG[status]).toBeDefined();
      });
    });

    it('should have required properties for each status', () => {
      ALL_STATUSES.forEach((status) => {
        const config = TOPUP_STATUS_CONFIG[status];
        expect(config).toHaveProperty('label');
        expect(config).toHaveProperty('variant');
        expect(config).toHaveProperty('description');
        expect(config).toHaveProperty('step');
      });
    });

    it('should have correct step values for normal flow', () => {
      expect(TOPUP_STATUS_CONFIG['draft'].step).toBe(1);
      expect(TOPUP_STATUS_CONFIG['pending_review'].step).toBe(2);
      expect(TOPUP_STATUS_CONFIG['finance_approve'].step).toBe(3);
      expect(TOPUP_STATUS_CONFIG['paid'].step).toBe(4);
      expect(TOPUP_STATUS_CONFIG['completed'].step).toBe(5);
    });

    it('should mark terminal states with step -1', () => {
      expect(TOPUP_STATUS_CONFIG['rejected'].step).toBe(-1);
      expect(TOPUP_STATUS_CONFIG['cancelled'].step).toBe(-1);
    });

    it('should have appropriate variants', () => {
      expect(TOPUP_STATUS_CONFIG['draft'].variant).toBe('secondary');
      expect(TOPUP_STATUS_CONFIG['pending_review'].variant).toBe('warning');
      expect(TOPUP_STATUS_CONFIG['finance_approve'].variant).toBe('info');
      expect(TOPUP_STATUS_CONFIG['paid'].variant).toBe('info');
      expect(TOPUP_STATUS_CONFIG['completed'].variant).toBe('success');
      expect(TOPUP_STATUS_CONFIG['rejected'].variant).toBe('error');
      expect(TOPUP_STATUS_CONFIG['cancelled'].variant).toBe('default');
    });
  });

  describe('TOPUP_TRANSITIONS', () => {
    describe('draft status transitions', () => {
      it('can transition to pending_review', () => {
        expect(TOPUP_TRANSITIONS['draft']).toContain('pending_review');
      });

      it('can transition to cancelled', () => {
        expect(TOPUP_TRANSITIONS['draft']).toContain('cancelled');
      });

      it('cannot transition to completed directly', () => {
        expect(TOPUP_TRANSITIONS['draft']).not.toContain('completed');
      });
    });

    describe('pending_review status transitions', () => {
      it('can transition to finance_approve', () => {
        expect(TOPUP_TRANSITIONS['pending_review']).toContain('finance_approve');
      });

      it('can transition to rejected', () => {
        expect(TOPUP_TRANSITIONS['pending_review']).toContain('rejected');
      });

      it('can transition to cancelled', () => {
        expect(TOPUP_TRANSITIONS['pending_review']).toContain('cancelled');
      });
    });

    describe('finance_approve status transitions', () => {
      it('can transition to paid', () => {
        expect(TOPUP_TRANSITIONS['finance_approve']).toContain('paid');
      });

      it('can transition to rejected', () => {
        expect(TOPUP_TRANSITIONS['finance_approve']).toContain('rejected');
      });

      it('can transition to cancelled', () => {
        expect(TOPUP_TRANSITIONS['finance_approve']).toContain('cancelled');
      });
    });

    describe('paid status transitions', () => {
      it('can only transition to completed', () => {
        expect(TOPUP_TRANSITIONS['paid']).toHaveLength(1);
        expect(TOPUP_TRANSITIONS['paid']).toContain('completed');
      });
    });

    describe('terminal states', () => {
      it('completed has no transitions', () => {
        expect(TOPUP_TRANSITIONS['completed']).toHaveLength(0);
      });

      it('rejected has no transitions', () => {
        expect(TOPUP_TRANSITIONS['rejected']).toHaveLength(0);
      });

      it('cancelled has no transitions', () => {
        expect(TOPUP_TRANSITIONS['cancelled']).toHaveLength(0);
      });
    });
  });

  describe('TOPUP_ACTION_ROLES', () => {
    const ALL_ACTIONS: TopupAction[] = [
      'create',
      'submit',
      'data_review_approve',
      'data_review_reject',
      'finance_approve',
      'finance_reject',
      'mark_paid',
      'complete',
      'cancel',
    ];

    it('should have roles defined for all actions', () => {
      ALL_ACTIONS.forEach((action) => {
        expect(TOPUP_ACTION_ROLES[action]).toBeDefined();
        expect(Array.isArray(TOPUP_ACTION_ROLES[action])).toBe(true);
      });
    });

    describe('create action', () => {
      it('should be allowed for pitcher', () => {
        expect(TOPUP_ACTION_ROLES['create']).toContain('pitcher');
      });

      it('should be allowed for account_manager', () => {
        expect(TOPUP_ACTION_ROLES['create']).toContain('account_manager');
      });

      it('should be allowed for admin', () => {
        expect(TOPUP_ACTION_ROLES['create']).toContain('admin');
      });
    });

    describe('data_review actions', () => {
      it('data_review_approve should be allowed for project_owner', () => {
        expect(TOPUP_ACTION_ROLES['data_review_approve']).toContain('project_owner');
      });

      it('data_review_reject should be allowed for project_owner', () => {
        expect(TOPUP_ACTION_ROLES['data_review_reject']).toContain('project_owner');
      });

      it('data_review_approve should be allowed for admin', () => {
        expect(TOPUP_ACTION_ROLES['data_review_approve']).toContain('admin');
      });
    });

    describe('finance actions', () => {
      it('finance_approve should be allowed for finance', () => {
        expect(TOPUP_ACTION_ROLES['finance_approve']).toContain('finance');
      });

      it('finance_reject should be allowed for finance', () => {
        expect(TOPUP_ACTION_ROLES['finance_reject']).toContain('finance');
      });

      it('mark_paid should be allowed for finance', () => {
        expect(TOPUP_ACTION_ROLES['mark_paid']).toContain('finance');
      });

      it('finance_approve should be allowed for admin', () => {
        expect(TOPUP_ACTION_ROLES['finance_approve']).toContain('admin');
      });
    });

    describe('complete action', () => {
      it('should be allowed for finance', () => {
        expect(TOPUP_ACTION_ROLES['complete']).toContain('finance');
      });

      it('should be allowed for system', () => {
        expect(TOPUP_ACTION_ROLES['complete']).toContain('system');
      });

      it('should be allowed for admin', () => {
        expect(TOPUP_ACTION_ROLES['complete']).toContain('admin');
      });
    });

    describe('cancel action', () => {
      it('should be allowed for pitcher', () => {
        expect(TOPUP_ACTION_ROLES['cancel']).toContain('pitcher');
      });

      it('should be allowed for account_manager', () => {
        expect(TOPUP_ACTION_ROLES['cancel']).toContain('account_manager');
      });

      it('should be allowed for admin', () => {
        expect(TOPUP_ACTION_ROLES['cancel']).toContain('admin');
      });
    });
  });

  describe('canTransition helper', () => {
    it('should return true for valid transitions', () => {
      expect(canTransition('draft', 'pending_review')).toBe(true);
      expect(canTransition('pending_review', 'finance_approve')).toBe(true);
      expect(canTransition('finance_approve', 'paid')).toBe(true);
      expect(canTransition('paid', 'completed')).toBe(true);
    });

    it('should return false for invalid transitions', () => {
      expect(canTransition('draft', 'completed')).toBe(false);
      expect(canTransition('draft', 'paid')).toBe(false);
      expect(canTransition('completed', 'draft')).toBe(false);
      expect(canTransition('rejected', 'pending_review')).toBe(false);
    });

    it('should return true for rejection from non-terminal states', () => {
      expect(canTransition('pending_review', 'rejected')).toBe(true);
      expect(canTransition('finance_approve', 'rejected')).toBe(true);
    });

    it('should return true for cancellation from non-paid states', () => {
      expect(canTransition('draft', 'cancelled')).toBe(true);
      expect(canTransition('pending_review', 'cancelled')).toBe(true);
      expect(canTransition('finance_approve', 'cancelled')).toBe(true);
    });
  });

  describe('canPerformAction helper', () => {
    describe('pitcher role', () => {
      const role = 'pitcher';

      it('can create topup', () => {
        expect(canPerformAction('create', role)).toBe(true);
      });

      it('can submit topup', () => {
        expect(canPerformAction('submit', role)).toBe(true);
      });

      it('can cancel topup', () => {
        expect(canPerformAction('cancel', role)).toBe(true);
      });

      it('cannot data review', () => {
        expect(canPerformAction('data_review_approve', role)).toBe(false);
        expect(canPerformAction('data_review_reject', role)).toBe(false);
      });

      it('cannot finance approve', () => {
        expect(canPerformAction('finance_approve', role)).toBe(false);
        expect(canPerformAction('finance_reject', role)).toBe(false);
      });
    });

    describe('project_owner role', () => {
      const role = 'project_owner';

      it('can data review approve', () => {
        expect(canPerformAction('data_review_approve', role)).toBe(true);
      });

      it('can data review reject', () => {
        expect(canPerformAction('data_review_reject', role)).toBe(true);
      });

      it('cannot create topup', () => {
        expect(canPerformAction('create', role)).toBe(false);
      });

      it('cannot finance approve', () => {
        expect(canPerformAction('finance_approve', role)).toBe(false);
      });
    });

    describe('finance role', () => {
      const role = 'finance';

      it('can finance approve', () => {
        expect(canPerformAction('finance_approve', role)).toBe(true);
      });

      it('can finance reject', () => {
        expect(canPerformAction('finance_reject', role)).toBe(true);
      });

      it('can mark paid', () => {
        expect(canPerformAction('mark_paid', role)).toBe(true);
      });

      it('can complete', () => {
        expect(canPerformAction('complete', role)).toBe(true);
      });

      it('can data review (finance has data_review permission)', () => {
        expect(canPerformAction('data_review_approve', role)).toBe(true);
      });
    });

    describe('admin role', () => {
      const role = 'admin';

      it('can perform all actions', () => {
        expect(canPerformAction('create', role)).toBe(true);
        expect(canPerformAction('submit', role)).toBe(true);
        expect(canPerformAction('data_review_approve', role)).toBe(true);
        expect(canPerformAction('data_review_reject', role)).toBe(true);
        expect(canPerformAction('finance_approve', role)).toBe(true);
        expect(canPerformAction('finance_reject', role)).toBe(true);
        expect(canPerformAction('mark_paid', role)).toBe(true);
        expect(canPerformAction('complete', role)).toBe(true);
        expect(canPerformAction('cancel', role)).toBe(true);
      });
    });
  });

  describe('getAvailableActions helper', () => {
    describe('draft status', () => {
      it('pitcher can submit and cancel', () => {
        const actions = getAvailableActions('draft', 'pitcher');
        expect(actions.map((a) => a.action)).toContain('submit');
        expect(actions.map((a) => a.action)).toContain('cancel');
      });

      it('project_owner has no actions on draft', () => {
        const actions = getAvailableActions('draft', 'project_owner');
        expect(actions).toHaveLength(0);
      });

      it('submit targets pending_review', () => {
        const actions = getAvailableActions('draft', 'pitcher');
        const submitAction = actions.find((a) => a.action === 'submit');
        expect(submitAction?.targetStatus).toBe('pending_review');
      });
    });

    describe('pending_review status', () => {
      it('project_owner can approve and reject', () => {
        const actions = getAvailableActions('pending_review', 'project_owner');
        expect(actions.map((a) => a.action)).toContain('data_review_approve');
        expect(actions.map((a) => a.action)).toContain('data_review_reject');
      });

      it('pitcher can only cancel', () => {
        const actions = getAvailableActions('pending_review', 'pitcher');
        expect(actions).toHaveLength(1);
        expect(actions[0].action).toBe('cancel');
      });
    });

    describe('finance_approve status', () => {
      it('finance can approve and reject', () => {
        const actions = getAvailableActions('finance_approve', 'finance');
        expect(actions.map((a) => a.action)).toContain('finance_approve');
        expect(actions.map((a) => a.action)).toContain('finance_reject');
      });
    });

    describe('paid status', () => {
      it('finance can complete', () => {
        const actions = getAvailableActions('paid', 'finance');
        expect(actions.map((a) => a.action)).toContain('complete');
      });

      it('pitcher cannot complete', () => {
        const actions = getAvailableActions('paid', 'pitcher');
        expect(actions).toHaveLength(0);
      });
    });

    describe('terminal states', () => {
      it('completed has no actions', () => {
        const actions = getAvailableActions('completed', 'admin');
        expect(actions).toHaveLength(0);
      });

      it('rejected has no actions', () => {
        const actions = getAvailableActions('rejected', 'admin');
        expect(actions).toHaveLength(0);
      });

      it('cancelled has no actions', () => {
        const actions = getAvailableActions('cancelled', 'admin');
        expect(actions).toHaveLength(0);
      });
    });
  });
});
