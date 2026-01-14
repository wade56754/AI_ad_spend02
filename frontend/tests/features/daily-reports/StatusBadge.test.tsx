/**
 * StatusBadge Component Tests
 *
 * Tests for StatusBadge component rendering
 * SoT: STATE_MACHINE.md v2.6 § 8
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { StatusBadge, StatusLegend } from '@/features/daily-reports/components/StatusBadge';
import { STATUS_CONFIG } from '@/features/daily-reports/types';
import type { DailyReportStatus } from '@/features/daily-reports/types';

describe('StatusBadge', () => {
  const allStatuses: DailyReportStatus[] = [
    'raw_submitted',
    'trend_pending',
    'trend_ok',
    'trend_flagged',
    'trend_resolved',
    'final_pending',
    'final_confirmed',
    'final_locked',
  ];

  // 测试 8 状态模式 (phase1={false})
  it.each(allStatuses)('renders correct label for %s status (8-state mode)', (status) => {
    render(<StatusBadge status={status} phase1={false} />);
    const config = STATUS_CONFIG[status];
    expect(screen.getByText(config.label)).toBeInTheDocument();
  });

  it('renders with icon by default (8-state mode)', () => {
    render(<StatusBadge status="raw_submitted" phase1={false} />);
    // Icon should be present (SVG element)
    const badge = screen.getByText('原始提交').closest('div');
    expect(badge?.querySelector('svg')).toBeInTheDocument();
  });

  it('hides icon when showIcon is false (8-state mode)', () => {
    render(<StatusBadge status="raw_submitted" showIcon={false} phase1={false} />);
    const badge = screen.getByText('原始提交').closest('div');
    expect(badge?.querySelector('svg')).not.toBeInTheDocument();
  });

  it('applies size classes correctly (8-state mode)', () => {
    const { rerender } = render(<StatusBadge status="raw_submitted" size="sm" phase1={false} />);
    // Size class is on the Badge container, not the text span
    const badge = screen.getByText('原始提交').closest('[class*="text-"]');
    expect(badge).toHaveClass('text-xs');

    rerender(<StatusBadge status="raw_submitted" size="lg" phase1={false} />);
    const badgeLg = screen.getByText('原始提交').closest('[class*="text-"]');
    expect(badgeLg).toHaveClass('text-base');
  });

  it('applies custom className (8-state mode)', () => {
    render(<StatusBadge status="raw_submitted" className="custom-class" phase1={false} />);
    const badge = screen.getByText('原始提交').closest('div');
    expect(badge).toHaveClass('custom-class');
  });
});

describe('StatusLegend', () => {
  it('renders all 8 status badges (8-state mode)', () => {
    render(<StatusLegend phase1={false} />);

    Object.values(STATUS_CONFIG).forEach((config) => {
      expect(screen.getByText(config.label)).toBeInTheDocument();
    });
  });

  it('renders exactly 8 badges (8-state mode)', () => {
    render(<StatusLegend phase1={false} />);
    // Count badge elements by their text content
    const statusLabels = Object.values(STATUS_CONFIG).map((config) => config.label);
    const badges = statusLabels.map((label) => screen.getByText(label));
    expect(badges).toHaveLength(8);
  });
});

describe('STATUS_CONFIG', () => {
  it('has configuration for all 8 statuses', () => {
    expect(Object.keys(STATUS_CONFIG)).toHaveLength(8);
  });

  it('has valid variant for each status', () => {
    const validVariants = ['default', 'success', 'warning', 'error', 'info'];
    Object.values(STATUS_CONFIG).forEach((config) => {
      expect(validVariants).toContain(config.variant);
    });
  });

  it('has non-empty label for each status', () => {
    Object.values(STATUS_CONFIG).forEach((config) => {
      expect(config.label).toBeTruthy();
      expect(config.label.length).toBeGreaterThan(0);
    });
  });
});
