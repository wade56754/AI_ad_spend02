import ReportsClient from "./reports-client";

import { apiFetch } from "@/lib/api";
import { createClient } from "@/lib/supabase/server";

type ProjectReportRow = {
  project_id: string;
  project_name: string;
  total_spend: string;
  total_leads: number;
  net_amount: string;
  profit: string;
};

type ChannelReportRow = {
  channel_id: string;
  channel_name: string;
  total_spend: string;
  account_count: number;
  total_topup: string;
  service_fee_amount: string;
};

export default async function ReportsPage() {
  const supabase = await createClient();
  const [{ data: sessionData }] = await Promise.all([supabase.auth.getSession()]);
  const accessToken = sessionData.session?.access_token ?? null;

  const month = new Date().toISOString().slice(0, 7);

  const authHeaders = accessToken
    ? {
        Authorization: `Bearer ${accessToken}`,
      }
    : undefined;

  const [projectsResponse, channelsResponse] = await Promise.all([
    apiFetch<ProjectReportRow[]>(`/api/reports/projects?month=${month}`, {
      headers: authHeaders,
    }),
    apiFetch<ChannelReportRow[]>(`/api/reports/channels?month=${month}`, {
      headers: authHeaders,
    }),
  ]);

  const projectsError = projectsResponse.error?.message;
  if (projectsError) {
    throw new Error(projectsError);
  }

  const channelsError = channelsResponse.error?.message;
  if (channelsError) {
    throw new Error(channelsError);
  }

  return (
    <ReportsClient
      month={month}
      projects={projectsResponse.data ?? []}
      channels={channelsResponse.data ?? []}
    />
  );
}
