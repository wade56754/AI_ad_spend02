import ReportsClient from "./reports-client";

import { apiFetch } from "@/lib/api";

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
  const month = new Date().toISOString().slice(0, 7);

  const [projectsResponse, channelsResponse] = await Promise.all([
    apiFetch<ProjectReportRow[]>(`/api/reports/projects?month=${month}`),
    apiFetch<ChannelReportRow[]>(`/api/reports/channels?month=${month}`),
  ]);

  if (projectsResponse.error) {
    throw new Error(projectsResponse.error);
  }

  if (channelsResponse.error) {
    throw new Error(channelsResponse.error);
  }

  return (
    <ReportsClient
      month={month}
      projects={projectsResponse.data ?? []}
      channels={channelsResponse.data ?? []}
    />
  );
}


