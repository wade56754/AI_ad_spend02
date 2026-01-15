/**
 * Ad Account Status Transition Tests
 *
 * Tests for ad account state machine based on:
 * - STATE_MACHINE.md v2.6 Section 7
 * - DATA_SCHEMA.md v5.2 ad_accounts entity
 *
 * State Machine:
 * new → testing → active → suspended → dead → archived
 *                      ↓
 *                   dead
 *                      ↓
 *                   archived
 */

import {
  ALLOWED_TRANSITIONS,
  AD_ACCOUNT_STATUS_CONFIG,
  type AdAccountStatus,
} from '@/features/ad-accounts/types/adAccount.types';

describe('Ad Account Status Transitions', () => {
  // ========== State Machine Validation ==========

  describe('ALLOWED_TRANSITIONS', () => {
    it('should have all 6 statuses defined', () => {
      const expectedStatuses: AdAccountStatus[] = [
        'new',
        'testing',
        'active',
        'suspended',
        'dead',
        'archived',
      ];

      expectedStatuses.forEach((status) => {
        expect(ALLOWED_TRANSITIONS).toHaveProperty(status);
      });
    });

    it('new status can only transition to testing', () => {
      expect(ALLOWED_TRANSITIONS.new).toEqual(['testing']);
    });

    it('testing status can only transition to active', () => {
      expect(ALLOWED_TRANSITIONS.testing).toEqual(['active']);
    });

    it('active status can transition to suspended or dead', () => {
      expect(ALLOWED_TRANSITIONS.active).toContain('suspended');
      expect(ALLOWED_TRANSITIONS.active).toContain('dead');
      expect(ALLOWED_TRANSITIONS.active).toHaveLength(2);
    });

    it('suspended status can transition to dead or active', () => {
      expect(ALLOWED_TRANSITIONS.suspended).toContain('dead');
      expect(ALLOWED_TRANSITIONS.suspended).toContain('active');
      expect(ALLOWED_TRANSITIONS.suspended).toHaveLength(2);
    });

    it('dead status can only transition to archived', () => {
      expect(ALLOWED_TRANSITIONS.dead).toEqual(['archived']);
    });

    it('archived status has no valid transitions (terminal state)', () => {
      expect(ALLOWED_TRANSITIONS.archived).toEqual([]);
    });
  });

  // ========== Transition Validation Function ==========

  describe('canTransition', () => {
    function canTransition(from: AdAccountStatus, to: AdAccountStatus): boolean {
      return ALLOWED_TRANSITIONS[from].includes(to);
    }

    // Valid transitions
    it('allows new → testing transition', () => {
      expect(canTransition('new', 'testing')).toBe(true);
    });

    it('allows testing → active transition', () => {
      expect(canTransition('testing', 'active')).toBe(true);
    });

    it('allows active → suspended transition', () => {
      expect(canTransition('active', 'suspended')).toBe(true);
    });

    it('allows active → dead transition', () => {
      expect(canTransition('active', 'dead')).toBe(true);
    });

    it('allows suspended → dead transition', () => {
      expect(canTransition('suspended', 'dead')).toBe(true);
    });

    it('allows suspended → active transition (reactivate)', () => {
      expect(canTransition('suspended', 'active')).toBe(true);
    });

    it('allows dead → archived transition', () => {
      expect(canTransition('dead', 'archived')).toBe(true);
    });

    // Invalid transitions
    it('denies new → active transition (must go through testing)', () => {
      expect(canTransition('new', 'active')).toBe(false);
    });

    it('denies testing → suspended transition', () => {
      expect(canTransition('testing', 'suspended')).toBe(false);
    });

    it('denies active → new transition (cannot go backwards)', () => {
      expect(canTransition('active', 'new')).toBe(false);
    });

    it('denies dead → active transition (cannot resurrect)', () => {
      expect(canTransition('dead', 'active')).toBe(false);
    });

    it('denies archived → any transition (terminal state)', () => {
      expect(canTransition('archived', 'new')).toBe(false);
      expect(canTransition('archived', 'testing')).toBe(false);
      expect(canTransition('archived', 'active')).toBe(false);
      expect(canTransition('archived', 'suspended')).toBe(false);
      expect(canTransition('archived', 'dead')).toBe(false);
    });
  });

  // ========== Status Config Validation ==========

  describe('AD_ACCOUNT_STATUS_CONFIG', () => {
    it('should have config for all 6 statuses', () => {
      const expectedStatuses: AdAccountStatus[] = [
        'new',
        'testing',
        'active',
        'suspended',
        'dead',
        'archived',
      ];

      expectedStatuses.forEach((status) => {
        expect(AD_ACCOUNT_STATUS_CONFIG).toHaveProperty(status);
        expect(AD_ACCOUNT_STATUS_CONFIG[status]).toHaveProperty('label');
        expect(AD_ACCOUNT_STATUS_CONFIG[status]).toHaveProperty('variant');
      });
    });

    it('new status has correct display config', () => {
      expect(AD_ACCOUNT_STATUS_CONFIG.new.label).toBe('新建');
      expect(AD_ACCOUNT_STATUS_CONFIG.new.variant).toBe('default');
    });

    it('testing status has info variant', () => {
      expect(AD_ACCOUNT_STATUS_CONFIG.testing.label).toBe('测试中');
      expect(AD_ACCOUNT_STATUS_CONFIG.testing.variant).toBe('info');
    });

    it('active status has success variant', () => {
      expect(AD_ACCOUNT_STATUS_CONFIG.active.label).toBe('活跃');
      expect(AD_ACCOUNT_STATUS_CONFIG.active.variant).toBe('success');
    });

    it('suspended status has warning variant', () => {
      expect(AD_ACCOUNT_STATUS_CONFIG.suspended.label).toBe('暂停');
      expect(AD_ACCOUNT_STATUS_CONFIG.suspended.variant).toBe('warning');
    });

    it('dead status has error variant', () => {
      expect(AD_ACCOUNT_STATUS_CONFIG.dead.label).toBe('死号');
      expect(AD_ACCOUNT_STATUS_CONFIG.dead.variant).toBe('error');
    });

    it('archived status has default variant', () => {
      expect(AD_ACCOUNT_STATUS_CONFIG.archived.label).toBe('归档');
      expect(AD_ACCOUNT_STATUS_CONFIG.archived.variant).toBe('default');
    });
  });

  // ========== Business Logic Tests ==========

  describe('Business Rules', () => {
    it('account must complete testing before becoming active', () => {
      // Cannot skip testing phase
      expect(ALLOWED_TRANSITIONS.new).not.toContain('active');
      expect(ALLOWED_TRANSITIONS.new).toContain('testing');
      expect(ALLOWED_TRANSITIONS.testing).toContain('active');
    });

    it('suspended accounts can be reactivated', () => {
      // Business rule: suspended accounts can resume operation
      expect(ALLOWED_TRANSITIONS.suspended).toContain('active');
    });

    it('dead accounts cannot be reactivated', () => {
      // Business rule: dead accounts are permanently closed
      expect(ALLOWED_TRANSITIONS.dead).not.toContain('active');
      expect(ALLOWED_TRANSITIONS.dead).not.toContain('suspended');
    });

    it('only dead accounts can be archived', () => {
      // Business rule: must mark as dead before archiving
      expect(ALLOWED_TRANSITIONS.new).not.toContain('archived');
      expect(ALLOWED_TRANSITIONS.testing).not.toContain('archived');
      expect(ALLOWED_TRANSITIONS.active).not.toContain('archived');
      expect(ALLOWED_TRANSITIONS.suspended).not.toContain('archived');
      expect(ALLOWED_TRANSITIONS.dead).toContain('archived');
    });
  });

  // ========== State Flow Tests ==========

  describe('Complete State Flows', () => {
    function canFollowPath(path: AdAccountStatus[]): boolean {
      for (let i = 0; i < path.length - 1; i++) {
        if (!ALLOWED_TRANSITIONS[path[i]].includes(path[i + 1])) {
          return false;
        }
      }
      return true;
    }

    it('supports happy path: new → testing → active → dead → archived', () => {
      const happyPath: AdAccountStatus[] = ['new', 'testing', 'active', 'dead', 'archived'];
      expect(canFollowPath(happyPath)).toBe(true);
    });

    it('supports suspend flow: new → testing → active → suspended → active', () => {
      const suspendFlow: AdAccountStatus[] = ['new', 'testing', 'active', 'suspended', 'active'];
      expect(canFollowPath(suspendFlow)).toBe(true);
    });

    it('supports suspend to dead flow: active → suspended → dead → archived', () => {
      const suspendToDeadFlow: AdAccountStatus[] = ['active', 'suspended', 'dead', 'archived'];
      expect(canFollowPath(suspendToDeadFlow)).toBe(true);
    });

    it('rejects invalid path: new → active → archived', () => {
      const invalidPath: AdAccountStatus[] = ['new', 'active', 'archived'];
      expect(canFollowPath(invalidPath)).toBe(false);
    });

    it('rejects resurrection path: dead → active', () => {
      const resurrectionPath: AdAccountStatus[] = ['dead', 'active'];
      expect(canFollowPath(resurrectionPath)).toBe(false);
    });
  });
});
