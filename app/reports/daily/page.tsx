import { redirect } from "next/navigation";

import { apiFetch } from "@/lib/api";
import { createClient } from "@/lib/supabase/server";

import DailyReportsClient from "./reports-client";

type AccountRow = {
  id: string;
  name: string;
};

type ReportRow = {
  id: string;
  ad_account_id: string;
  date: string;
  spend: string;
  leads_count: number;
  note: string | null;
  created_at: string;
};

export default async function DailyReportsPage() {
  const supabase = await createClient();

  const [{ data: userData, error: userError }, { data: sessionData }] = await Promise.all([
    supabase.auth.getUser(),
    supabase.auth.getSession(),
  ]);

  const user = userData.user;

  if (userError || !user) {
    redirect("/auth/login");
  }

  const accessToken = sessionData.session?.access_token ?? null;
  const headers = accessToken
    ? {
        Authorization: `Bearer ${accessToken}`,
      }
    : undefined;

  const [accountsResponse, reportsResponse] = await Promise.all([
    apiFetch<AccountRow[]>("/api/ad-accounts?page=1&page_size=200", {
      headers,
    }),
    apiFetch<ReportRow[]>(`/api/ad-spend?page=1&page_size=50&user_id=${encodeURIComponent(user.id)}`, {
      headers,
    }),
  ]);

  if (accountsResponse.error?.message || reportsResponse.error?.message) {
    redirect("/protected");
  }

  const accounts =
    accountsResponse.data?.map((item) => ({
      id: item.id,
      name: item.name,
    })) ?? [];

  const reports = reportsResponse.data ?? [];

  return (
    <DailyReportsClient
      accounts={accounts}
      initialReports={reports}
      currentUserId={user.id}
      accessToken={accessToken}
    />
  );
}
