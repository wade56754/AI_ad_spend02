/**
 * Create Weekly Brief Page
 *
 * @sot docs/10.module-specs/B3-weekly-brief.md §3.2
 * @permission project_owner, admin
 */

import { WeeklyBriefForm } from '@/features/weekly-briefs';

export default function CreateWeeklyBriefRoute() {
  return <WeeklyBriefForm mode="create" />;
}
