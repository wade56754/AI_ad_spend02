/**
 * TopupStatusBadge Component Tests
 *
 * Tests for status badge, progress, and amount components
 * SoT: STATE_MACHINE.md v2.6 Section 9
 */

import { render, screen } from '@testing-library/react';
import {
  TopupStatusBadge,
  TopupProgress,
  TopupStatsCard,
  TopupStatusLegend,
  TopupAmount,
} from '@/features/topups/components/TopupStatusBadge';
import { TOPUP_STATUS_CONFIG, type TopupStatus } from '@/features/topups/types';
import { Wallet } from 'lucide-react';

describe('TopupStatusBadge', () => {
  const ALL_STATUSES: TopupStatus[] = [
    'draft',
    'pending_review',
    'finance_approve',
    'paid',
    'completed',
    'rejected',
    'cancelled',
  ];

  describe('rendering', () => {
    ALL_STATUSES.forEach((status) => {
      it(`renders ${status} status correctly`, () => {
        render(<TopupStatusBadge status={status} />);
        expect(screen.getByText(TOPUP_STATUS_CONFIG[status].label)).toBeInTheDocument();
      });
    });
  });

  describe('showIcon prop', () => {
    it('shows icon by default', () => {
      const { container } = render(<TopupStatusBadge status="draft" />);
      // Icon should be an SVG element
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('hides icon when showIcon is false', () => {
      const { container } = render(<TopupStatusBadge status="draft" showIcon={false} />);
      // No SVG inside the badge (there might be one in tooltip)
      const badge = container.querySelector('[class*="badge"]');
      expect(badge?.querySelector('svg')).not.toBeInTheDocument();
    });
  });

  describe('showTooltip prop', () => {
    it('renders tooltip by default', () => {
      render(<TopupStatusBadge status="draft" />);
      // With tooltip enabled, there should be a TooltipTrigger wrapper
      expect(screen.getByText('草稿')).toBeInTheDocument();
    });

    it('renders without tooltip when showTooltip is false', () => {
      render(<TopupStatusBadge status="draft" showTooltip={false} />);
      expect(screen.getByText('草稿')).toBeInTheDocument();
    });
  });

  describe('size prop', () => {
    it('renders small size', () => {
      const { container } = render(<TopupStatusBadge status="draft" size="sm" />);
      const badge = container.querySelector('[class*="badge"]');
      expect(badge).toHaveClass('text-xs');
    });

    it('renders default size', () => {
      const { container } = render(<TopupStatusBadge status="draft" size="default" />);
      const badge = container.querySelector('[class*="badge"]');
      expect(badge).toHaveClass('text-sm');
    });

    it('renders large size', () => {
      const { container } = render(<TopupStatusBadge status="draft" size="lg" />);
      const badge = container.querySelector('[class*="badge"]');
      expect(badge).toHaveClass('text-base');
    });
  });

  describe('status-specific styles', () => {
    it('renders draft with gray colors', () => {
      const { container } = render(<TopupStatusBadge status="draft" showTooltip={false} />);
      const badge = container.querySelector('[class*="badge"]');
      expect(badge).toHaveClass('bg-gray-50');
    });

    it('renders pending_review with amber colors', () => {
      const { container } = render(<TopupStatusBadge status="pending_review" showTooltip={false} />);
      const badge = container.querySelector('[class*="badge"]');
      expect(badge).toHaveClass('bg-amber-50');
    });

    it('renders completed with green colors', () => {
      const { container } = render(<TopupStatusBadge status="completed" showTooltip={false} />);
      const badge = container.querySelector('[class*="badge"]');
      expect(badge).toHaveClass('bg-green-50');
    });

    it('renders rejected with red colors', () => {
      const { container } = render(<TopupStatusBadge status="rejected" showTooltip={false} />);
      const badge = container.querySelector('[class*="badge"]');
      expect(badge).toHaveClass('bg-red-50');
    });
  });

  describe('unknown status handling', () => {
    it('renders fallback for unknown status', () => {
      // @ts-expect-error Testing unknown status
      render(<TopupStatusBadge status="unknown_status" />);
      expect(screen.getByText('未知状态')).toBeInTheDocument();
    });
  });
});

describe('TopupProgress', () => {
  describe('normal flow', () => {
    it('renders all progress steps', () => {
      render(<TopupProgress status="draft" />);
      expect(screen.getByText('草稿')).toBeInTheDocument();
      expect(screen.getByText('数据复核')).toBeInTheDocument();
      expect(screen.getByText('财务终审')).toBeInTheDocument();
      expect(screen.getByText('已支付')).toBeInTheDocument();
      expect(screen.getByText('已完成')).toBeInTheDocument();
    });

    it('highlights current step for draft', () => {
      const { container } = render(<TopupProgress status="draft" />);
      const steps = container.querySelectorAll('[class*="rounded-full"]');
      // First step should be active (ring effect)
      expect(steps[0]).toHaveClass('ring-4');
    });

    it('shows completed steps as green', () => {
      const { container } = render(<TopupProgress status="paid" />);
      const steps = container.querySelectorAll('[class*="rounded-full"]');
      // First 3 steps should be completed (green)
      expect(steps[0]).toHaveClass('bg-green-500');
      expect(steps[1]).toHaveClass('bg-green-500');
      expect(steps[2]).toHaveClass('bg-green-500');
    });
  });

  describe('terminal states', () => {
    it('shows special message for rejected status', () => {
      render(<TopupProgress status="rejected" />);
      expect(screen.getByText('审批流程已终止')).toBeInTheDocument();
    });

    it('shows special message for cancelled status', () => {
      render(<TopupProgress status="cancelled" />);
      expect(screen.getByText('申请已取消')).toBeInTheDocument();
    });
  });

  describe('showLabels prop', () => {
    it('shows labels by default', () => {
      render(<TopupProgress status="draft" />);
      expect(screen.getByText('草稿')).toBeInTheDocument();
    });

    it('hides labels when showLabels is false', () => {
      render(<TopupProgress status="draft" showLabels={false} />);
      // The step dots should still exist but labels shouldn't
      expect(screen.queryByText('草稿')).not.toBeInTheDocument();
    });
  });

  describe('size prop', () => {
    it('renders smaller dots for sm size', () => {
      const { container } = render(<TopupProgress status="draft" size="sm" />);
      const dots = container.querySelectorAll('[class*="h-2"]');
      expect(dots.length).toBeGreaterThan(0);
    });
  });
});

describe('TopupAmount', () => {
  describe('CNY currency', () => {
    it('renders small amounts correctly', () => {
      // Amount in cents
      render(<TopupAmount amount={100000} currency="CNY" />);
      // 100000 cents = 1000 yuan
      expect(screen.getByText(/¥1,000\.00/)).toBeInTheDocument();
    });

    it('renders large amounts with 万 suffix', () => {
      // Amount in cents >= 10000 yuan
      render(<TopupAmount amount={10000000} currency="CNY" />);
      // 10000000 cents = 100000 yuan = 10 万
      expect(screen.getByText(/¥10\.00万/)).toBeInTheDocument();
    });

    it('renders zero correctly', () => {
      render(<TopupAmount amount={0} currency="CNY" />);
      expect(screen.getByText(/¥0\.00/)).toBeInTheDocument();
    });
  });

  describe('other currencies', () => {
    it('renders USD correctly', () => {
      render(<TopupAmount amount={100000} currency="USD" />);
      expect(screen.getByText(/USD 1,000\.00/)).toBeInTheDocument();
    });
  });

  describe('size prop', () => {
    it('renders small size', () => {
      const { container } = render(<TopupAmount amount={100000} currency="CNY" size="sm" />);
      expect(container.firstChild).toHaveClass('text-sm');
    });

    it('renders default size', () => {
      const { container } = render(<TopupAmount amount={100000} currency="CNY" size="default" />);
      expect(container.firstChild).toHaveClass('text-base');
    });

    it('renders large size', () => {
      const { container } = render(<TopupAmount amount={100000} currency="CNY" size="lg" />);
      expect(container.firstChild).toHaveClass('text-xl');
    });
  });

  describe('showSign prop', () => {
    it('does not show sign by default', () => {
      render(<TopupAmount amount={100000} currency="CNY" />);
      expect(screen.queryByText(/\+/)).not.toBeInTheDocument();
    });

    it('shows plus sign when showSign is true', () => {
      render(<TopupAmount amount={100000} currency="CNY" showSign />);
      expect(screen.getByText(/\+/)).toBeInTheDocument();
    });
  });
});

describe('TopupStatsCard', () => {
  const defaultProps = {
    title: '待审批',
    value: 10,
    icon: Wallet,
  };

  it('renders title and value', () => {
    render(<TopupStatsCard {...defaultProps} />);
    expect(screen.getByText('待审批')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
  });

  it('renders formatted large numbers', () => {
    render(<TopupStatsCard {...defaultProps} value={1000000} />);
    expect(screen.getByText('1,000,000')).toBeInTheDocument();
  });

  it('renders string values', () => {
    render(<TopupStatsCard {...defaultProps} value="¥100,000" />);
    expect(screen.getByText('¥100,000')).toBeInTheDocument();
  });

  describe('trend', () => {
    it('shows positive trend', () => {
      render(<TopupStatsCard {...defaultProps} trend={{ value: 10, isPositive: true }} />);
      expect(screen.getByText(/↑ 10%/)).toBeInTheDocument();
    });

    it('shows negative trend', () => {
      render(<TopupStatsCard {...defaultProps} trend={{ value: 5, isPositive: false }} />);
      expect(screen.getByText(/↓ 5%/)).toBeInTheDocument();
    });
  });

  describe('variant styles', () => {
    it('applies success variant', () => {
      const { container } = render(<TopupStatsCard {...defaultProps} variant="success" />);
      expect(container.querySelector('[class*="bg-green-50"]')).toBeInTheDocument();
    });

    it('applies warning variant', () => {
      const { container } = render(<TopupStatsCard {...defaultProps} variant="warning" />);
      expect(container.querySelector('[class*="bg-amber-50"]')).toBeInTheDocument();
    });

    it('applies error variant', () => {
      const { container } = render(<TopupStatsCard {...defaultProps} variant="error" />);
      expect(container.querySelector('[class*="bg-red-50"]')).toBeInTheDocument();
    });
  });

  describe('onClick', () => {
    it('calls onClick when clicked', () => {
      const onClick = jest.fn();
      render(<TopupStatsCard {...defaultProps} onClick={onClick} />);

      const card = screen.getByText('待审批').closest('div[class*="rounded"]');
      card?.click();

      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it('adds cursor-pointer class when onClick is provided', () => {
      const { container } = render(<TopupStatsCard {...defaultProps} onClick={jest.fn()} />);
      expect(container.firstChild).toHaveClass('cursor-pointer');
    });
  });
});

describe('TopupStatusLegend', () => {
  it('renders all status labels', () => {
    render(<TopupStatusLegend />);

    expect(screen.getByText('草稿')).toBeInTheDocument();
    expect(screen.getByText('待数据复核')).toBeInTheDocument();
    expect(screen.getByText('待财务终审')).toBeInTheDocument();
    expect(screen.getByText('已支付')).toBeInTheDocument();
    expect(screen.getByText('已完成')).toBeInTheDocument();
    expect(screen.getByText('已拒绝')).toBeInTheDocument();
    expect(screen.getByText('已取消')).toBeInTheDocument();
  });

  it('renders icons for each status', () => {
    const { container } = render(<TopupStatusLegend />);
    const icons = container.querySelectorAll('svg');
    expect(icons.length).toBe(7); // One for each status
  });
});
