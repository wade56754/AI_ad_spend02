/**
 * Edit Weekly Brief Page
 *
 * @sot docs/10.module-specs/B3-weekly-brief.md §3.2
 * @permission project_owner (draft only), admin
 */

'use client';

import { use } from 'react';
import { WeeklyBriefForm } from '@/features/weekly-briefs';

interface EditWeeklyBriefRouteProps {
  params: Promise<{ id: string }>;
}

export default function EditWeeklyBriefRoute({ params }: EditWeeklyBriefRouteProps) {
  const { id } = use(params);
  const briefId = parseInt(id, 10);

  if (isNaN(briefId)) {
    return <div>无效的周报 ID</div>;
  }

  return <WeeklyBriefForm briefId={briefId} mode="edit" />;
}
