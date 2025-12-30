/**
 * View Weekly Brief Page
 *
 * @sot docs/10.module-specs/B3-weekly-brief.md §3.2
 * @permission ceo, project_owner, finance, admin
 */

'use client';

import { use } from 'react';
import { WeeklyBriefForm } from '@/features/weekly-briefs';

interface ViewWeeklyBriefRouteProps {
  params: Promise<{ id: string }>;
}

export default function ViewWeeklyBriefRoute({ params }: ViewWeeklyBriefRouteProps) {
  const { id } = use(params);
  const briefId = parseInt(id, 10);

  if (isNaN(briefId)) {
    return <div>无效的周报 ID</div>;
  }

  return <WeeklyBriefForm briefId={briefId} mode="view" />;
}
