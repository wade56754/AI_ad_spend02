/**
 * OpsStatusCards Component
 *
 * SoT: docs/10.module-specs/A1-dashboard.md
 * SoT: MASTER.md v4.4 §6.5 核心页面最小字段集
 * CodeBlock: CB-FE-002 (StatCard)
 *
 * 功能: 运营状态指标卡片
 * - 活跃项目数
 * - 异常项目数
 * - 待审批充值
 */

'use client';

import React from 'react';
import { Target, BarChart3, Wallet } from 'lucide-react';
import { StatCard } from './StatCard';

export interface OpsStatusData {
  active_projects: number;
  abnormal_projects: number;
  pending_topups: number;
}

export interface OpsStatusCardsProps {
  data: OpsStatusData;
}

/**
 * 运营状态卡片组件
 * 展示项目运营状态和待处理事项
 */
export function OpsStatusCards({ data }: OpsStatusCardsProps) {
  return (
    <section data-testid="ops-status">
      <h2 className="text-2xl font-semibold text-foreground mb-4">运营状态</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* 活跃项目数 */}
        <StatCard
          title="活跃项目数"
          value={data.active_projects.toString()}
          icon={<Target className="h-6 w-6" />}
          color="blue"
          testId="active-projects"
        />

        {/* 异常项目数 */}
        <StatCard
          title="异常项目数"
          value={data.abnormal_projects.toString()}
          target="CPL 超标 30%+"
          icon={<BarChart3 className="h-6 w-6" />}
          color={data.abnormal_projects > 0 ? 'red' : 'green'}
          href="/projects?filter=abnormal"
          isWarning={data.abnormal_projects > 0}
          testId="abnormal-projects"
        />

        {/* 待审批充值 */}
        <StatCard
          title="待审批充值"
          value={data.pending_topups.toString()}
          target="需老板审批"
          icon={<Wallet className="h-6 w-6" />}
          color={data.pending_topups > 0 ? 'orange' : 'green'}
          href="/topups?status=pending"
          isWarning={data.pending_topups > 0}
          testId="pending-topups"
        />
      </div>
    </section>
  );
}

export default OpsStatusCards;
