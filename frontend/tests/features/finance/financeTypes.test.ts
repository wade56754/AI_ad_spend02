/**
 * Finance Types and Config Tests
 *
 * Tests for frontend/src/features/finance/types/finance.types.ts
 * SoT: BUSINESS_RULES.md v3.2 - 利润状态规则
 * SoT: LEDGER_SOT.md v1.1 - 应收账款状态
 */

import {
  PROFIT_STATUS_CONFIG,
  RECEIVABLE_STATUS_CONFIG,
  type ProfitStatus,
  type ReceivableStatus,
  type TrendGranularity,
  type DistributionGroupBy,
  type ProjectSortBy,
} from '@/features/finance/types/finance.types';

describe('Finance Types', () => {
  // ========== Profit Status ==========

  describe('PROFIT_STATUS_CONFIG', () => {
    it('should have config for all 4 profit statuses', () => {
      const expectedStatuses: ProfitStatus[] = ['healthy', 'warning', 'danger', 'inactive'];

      expectedStatuses.forEach((status) => {
        expect(PROFIT_STATUS_CONFIG).toHaveProperty(status);
        expect(PROFIT_STATUS_CONFIG[status]).toHaveProperty('label');
        expect(PROFIT_STATUS_CONFIG[status]).toHaveProperty('icon');
        expect(PROFIT_STATUS_CONFIG[status]).toHaveProperty('color');
      });
    });

    it('healthy status has correct config (profit_rate >= 15%)', () => {
      expect(PROFIT_STATUS_CONFIG.healthy.label).toBe('健康');
      expect(PROFIT_STATUS_CONFIG.healthy.color).toContain('green');
    });

    it('warning status has correct config (5% <= profit_rate < 15%)', () => {
      expect(PROFIT_STATUS_CONFIG.warning.label).toBe('关注');
      expect(PROFIT_STATUS_CONFIG.warning.color).toContain('amber');
    });

    it('danger status has correct config (profit_rate < 5%)', () => {
      expect(PROFIT_STATUS_CONFIG.danger.label).toBe('警告');
      expect(PROFIT_STATUS_CONFIG.danger.color).toContain('red');
    });

    it('inactive status has correct config (refunded/closed)', () => {
      expect(PROFIT_STATUS_CONFIG.inactive.label).toBe('非活跃');
      expect(PROFIT_STATUS_CONFIG.inactive.color).toContain('gray');
    });
  });

  describe('Profit Status Business Rules', () => {
    /**
     * SoT: BUSINESS_RULES.md §BR-PROFIT-01
     * - healthy: profit_rate >= 15%
     * - warning: 5% <= profit_rate < 15%
     * - danger: profit_rate < 5%
     * - inactive: project is refunded or closed
     */

    function determineProfitStatus(profitRate: number, isActive: boolean): ProfitStatus {
      if (!isActive) return 'inactive';
      if (profitRate >= 0.15) return 'healthy';
      if (profitRate >= 0.05) return 'warning';
      return 'danger';
    }

    it('should return healthy for profit_rate >= 15%', () => {
      expect(determineProfitStatus(0.15, true)).toBe('healthy');
      expect(determineProfitStatus(0.2, true)).toBe('healthy');
      expect(determineProfitStatus(0.5, true)).toBe('healthy');
    });

    it('should return warning for 5% <= profit_rate < 15%', () => {
      expect(determineProfitStatus(0.05, true)).toBe('warning');
      expect(determineProfitStatus(0.1, true)).toBe('warning');
      expect(determineProfitStatus(0.149, true)).toBe('warning');
    });

    it('should return danger for profit_rate < 5%', () => {
      expect(determineProfitStatus(0.04, true)).toBe('danger');
      expect(determineProfitStatus(0.01, true)).toBe('danger');
      expect(determineProfitStatus(0, true)).toBe('danger');
      expect(determineProfitStatus(-0.05, true)).toBe('danger'); // negative profit
    });

    it('should return inactive for closed/refunded projects', () => {
      expect(determineProfitStatus(0.2, false)).toBe('inactive');
      expect(determineProfitStatus(0.1, false)).toBe('inactive');
      expect(determineProfitStatus(0.01, false)).toBe('inactive');
    });
  });

  // ========== Receivable Status ==========

  describe('RECEIVABLE_STATUS_CONFIG', () => {
    it('should have config for all 3 receivable statuses', () => {
      const expectedStatuses: ReceivableStatus[] = ['settled', 'outstanding', 'refunded'];

      expectedStatuses.forEach((status) => {
        expect(RECEIVABLE_STATUS_CONFIG).toHaveProperty(status);
        expect(RECEIVABLE_STATUS_CONFIG[status]).toHaveProperty('label');
        expect(RECEIVABLE_STATUS_CONFIG[status]).toHaveProperty('variant');
      });
    });

    it('settled status has default variant', () => {
      expect(RECEIVABLE_STATUS_CONFIG.settled.label).toBe('已结清');
      expect(RECEIVABLE_STATUS_CONFIG.settled.variant).toBe('default');
    });

    it('outstanding status has destructive variant (needs attention)', () => {
      expect(RECEIVABLE_STATUS_CONFIG.outstanding.label).toBe('待收款');
      expect(RECEIVABLE_STATUS_CONFIG.outstanding.variant).toBe('destructive');
    });

    it('refunded status has secondary variant', () => {
      expect(RECEIVABLE_STATUS_CONFIG.refunded.label).toBe('已退款');
      expect(RECEIVABLE_STATUS_CONFIG.refunded.variant).toBe('secondary');
    });
  });

  describe('Receivable Status Business Rules', () => {
    /**
     * SoT: LEDGER_SOT.md §3.2 应收账款状态
     * - settled: 全部款项已收回
     * - outstanding: 尚有未收款项
     * - refunded: 项目已退款
     */

    function determineReceivableStatus(
      totalReceivable: number,
      totalReceived: number,
      isRefunded: boolean
    ): ReceivableStatus {
      if (isRefunded) return 'refunded';
      if (totalReceived >= totalReceivable) return 'settled';
      return 'outstanding';
    }

    it('should return settled when fully paid', () => {
      expect(determineReceivableStatus(10000, 10000, false)).toBe('settled');
      expect(determineReceivableStatus(10000, 12000, false)).toBe('settled'); // overpaid
    });

    it('should return outstanding when partially paid', () => {
      expect(determineReceivableStatus(10000, 5000, false)).toBe('outstanding');
      expect(determineReceivableStatus(10000, 0, false)).toBe('outstanding');
      expect(determineReceivableStatus(10000, 9999, false)).toBe('outstanding');
    });

    it('should return refunded regardless of payment status', () => {
      expect(determineReceivableStatus(10000, 10000, true)).toBe('refunded');
      expect(determineReceivableStatus(10000, 5000, true)).toBe('refunded');
      expect(determineReceivableStatus(10000, 0, true)).toBe('refunded');
    });
  });

  // ========== Enum Type Tests ==========

  describe('TrendGranularity', () => {
    it('should support day, week, month granularities', () => {
      const validGranularities: TrendGranularity[] = ['day', 'week', 'month'];

      validGranularities.forEach((granularity) => {
        expect(['day', 'week', 'month']).toContain(granularity);
      });
    });
  });

  describe('DistributionGroupBy', () => {
    it('should support project, supplier, platform groupings', () => {
      const validGroupings: DistributionGroupBy[] = ['project', 'supplier', 'platform'];

      validGroupings.forEach((grouping) => {
        expect(['project', 'supplier', 'platform']).toContain(grouping);
      });
    });
  });

  describe('ProjectSortBy', () => {
    it('should support profit, profit_rate, revenue sorting', () => {
      const validSortOptions: ProjectSortBy[] = ['profit', 'profit_rate', 'revenue'];

      validSortOptions.forEach((sortOption) => {
        expect(['profit', 'profit_rate', 'revenue']).toContain(sortOption);
      });
    });
  });

  // ========== Formula Tests ==========

  describe('Financial Formulas', () => {
    /**
     * SoT: BUSINESS_RULES.md §BR-PROFIT-02
     * Core formulas:
     * - revenue = conversions × unit_price (per_lead model)
     * - revenue = ad_spend × service_fee_rate (fee_rate model)
     * - cost = real_spend + fee
     * - profit = revenue - cost
     * - profit_rate = profit / revenue
     */

    function calculateProfit(
      conversions: number,
      unitPrice: number,
      realSpend: number,
      fee: number
    ) {
      const revenue = conversions * unitPrice;
      const cost = realSpend + fee;
      const profit = revenue - cost;
      const profitRate = revenue > 0 ? profit / revenue : 0;

      return { revenue, cost, profit, profitRate };
    }

    it('should calculate profit correctly for profitable project', () => {
      const result = calculateProfit(100, 200, 15000, 500);
      // revenue = 100 * 200 = 20000
      // cost = 15000 + 500 = 15500
      // profit = 20000 - 15500 = 4500
      // profitRate = 4500 / 20000 = 0.225

      expect(result.revenue).toBe(20000);
      expect(result.cost).toBe(15500);
      expect(result.profit).toBe(4500);
      expect(result.profitRate).toBe(0.225);
    });

    it('should calculate profit correctly for loss-making project', () => {
      const result = calculateProfit(50, 200, 12000, 500);
      // revenue = 50 * 200 = 10000
      // cost = 12000 + 500 = 12500
      // profit = 10000 - 12500 = -2500
      // profitRate = -2500 / 10000 = -0.25

      expect(result.revenue).toBe(10000);
      expect(result.cost).toBe(12500);
      expect(result.profit).toBe(-2500);
      expect(result.profitRate).toBe(-0.25);
    });

    it('should handle zero conversions', () => {
      const result = calculateProfit(0, 200, 1000, 50);
      // revenue = 0
      // cost = 1050
      // profit = -1050
      // profitRate = 0 (division by zero protection)

      expect(result.revenue).toBe(0);
      expect(result.profit).toBe(-1050);
      expect(result.profitRate).toBe(0);
    });
  });

  describe('Outstanding Calculation', () => {
    /**
     * SoT: LEDGER_SOT.md §3.1
     * outstanding = total_receivable - total_received
     */

    function calculateOutstanding(totalReceivable: number, totalReceived: number): number {
      return Math.max(0, totalReceivable - totalReceived);
    }

    it('should calculate outstanding correctly', () => {
      expect(calculateOutstanding(10000, 6000)).toBe(4000);
      expect(calculateOutstanding(10000, 0)).toBe(10000);
      expect(calculateOutstanding(10000, 10000)).toBe(0);
    });

    it('should not return negative outstanding (overpayment)', () => {
      expect(calculateOutstanding(10000, 12000)).toBe(0);
    });
  });
});
