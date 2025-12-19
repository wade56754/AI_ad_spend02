/**
 * Project Status Badge Component Tests
 *
 * Tests for ProjectStatusBadge, BudgetProgress, and related components
 * SoT: STATE_MACHINE.md v2.6 § 5
 */

import { render, screen } from '@testing-library/react';
import {
  ProjectStatusBadge,
  BudgetProgress,
  ProjectStatsCard,
  ProjectStatusLegend,
} from '@/features/projects/components/ProjectStatusBadge';
import { PROJECT_STATUS_CONFIG } from '@/features/projects/types';
import { FolderKanban } from 'lucide-react';

describe('ProjectStatusBadge', () => {
  it('renders active status correctly', () => {
    render(<ProjectStatusBadge status="active" showTooltip={false} />);
    expect(screen.getByText('进行中')).toBeInTheDocument();
  });

  it('renders paused status correctly', () => {
    render(<ProjectStatusBadge status="paused" showTooltip={false} />);
    expect(screen.getByText('已暂停')).toBeInTheDocument();
  });

  it('renders completed status correctly', () => {
    render(<ProjectStatusBadge status="completed" showTooltip={false} />);
    expect(screen.getByText('已完成')).toBeInTheDocument();
  });

  it('renders cancelled status correctly', () => {
    render(<ProjectStatusBadge status="cancelled" showTooltip={false} />);
    expect(screen.getByText('已取消')).toBeInTheDocument();
  });

  it('renders unknown status fallback', () => {
    // @ts-expect-error Testing invalid status
    render(<ProjectStatusBadge status="invalid" showTooltip={false} />);
    expect(screen.getByText('未知状态')).toBeInTheDocument();
  });

  it('renders with different sizes', () => {
    const { rerender } = render(
      <ProjectStatusBadge status="active" size="sm" showTooltip={false} />
    );
    expect(screen.getByText('进行中')).toBeInTheDocument();

    rerender(<ProjectStatusBadge status="active" size="lg" showTooltip={false} />);
    expect(screen.getByText('进行中')).toBeInTheDocument();
  });
});

describe('BudgetProgress', () => {
  it('renders budget and spent amounts', () => {
    render(<BudgetProgress budget={100000} spent={50000} />);
    expect(screen.getByText(/已消耗/)).toBeInTheDocument();
    expect(screen.getByText(/预算/)).toBeInTheDocument();
  });

  it('calculates percentage correctly', () => {
    render(<BudgetProgress budget={100000} spent={75000} />);
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('handles zero budget', () => {
    render(<BudgetProgress budget={0} spent={0} />);
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('caps percentage at 100%', () => {
    render(<BudgetProgress budget={100000} spent={150000} />);
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('formats large amounts with 万 suffix', () => {
    render(<BudgetProgress budget={100000} spent={50000} />);
    expect(screen.getByText(/¥5\.0万/)).toBeInTheDocument();
  });
});

describe('ProjectStatsCard', () => {
  it('renders title and value', () => {
    render(
      <ProjectStatsCard
        title="项目总数"
        value={42}
        icon={FolderKanban}
      />
    );
    expect(screen.getByText('项目总数')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('renders string value', () => {
    render(
      <ProjectStatsCard
        title="总预算"
        value="¥10万"
        icon={FolderKanban}
      />
    );
    expect(screen.getByText('¥10万')).toBeInTheDocument();
  });

  it('renders with different variants', () => {
    const { rerender } = render(
      <ProjectStatsCard
        title="Test"
        value={1}
        icon={FolderKanban}
        variant="success"
      />
    );
    expect(screen.getByText('Test')).toBeInTheDocument();

    rerender(
      <ProjectStatsCard
        title="Test"
        value={1}
        icon={FolderKanban}
        variant="error"
      />
    );
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
});

describe('ProjectStatusLegend', () => {
  it('renders all status labels', () => {
    render(<ProjectStatusLegend />);
    expect(screen.getByText('进行中')).toBeInTheDocument();
    expect(screen.getByText('已暂停')).toBeInTheDocument();
    expect(screen.getByText('已完成')).toBeInTheDocument();
    expect(screen.getByText('已取消')).toBeInTheDocument();
  });
});

describe('PROJECT_STATUS_CONFIG', () => {
  it('has configuration for all 4 statuses', () => {
    expect(Object.keys(PROJECT_STATUS_CONFIG)).toHaveLength(4);
    expect(PROJECT_STATUS_CONFIG.active).toBeDefined();
    expect(PROJECT_STATUS_CONFIG.paused).toBeDefined();
    expect(PROJECT_STATUS_CONFIG.completed).toBeDefined();
    expect(PROJECT_STATUS_CONFIG.cancelled).toBeDefined();
  });

  it('each status has required properties', () => {
    Object.values(PROJECT_STATUS_CONFIG).forEach((config: { label: string; variant: string }) => {
      expect(config.label).toBeDefined();
      expect(config.variant).toBeDefined();
    });
  });
});
