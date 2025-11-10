import { redirect } from "next/navigation";

import { apiFetch } from "@/lib/api";
import { createClient } from "@/lib/supabase/server";

import TopupsClient from "./topups-client";

type AdAccountRow = {
  id: string;
  name: string;
  project_id: string;
  channel_id: string;
};

type ProjectRow = {
  id: string;
  name: string;
};

type ChannelRow = {
  id: string;
  name: string;
};

export default async function TopupsPage() {
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

  const [accountsResponse, projectsResponse, channelsResponse] = await Promise.all([
    apiFetch<AdAccountRow[]>("/api/ad-accounts?page=1&page_size=200", {
      headers,
    }),
    apiFetch<ProjectRow[]>("/api/projects?page=1&page_size=200", {
      headers,
    }),
    apiFetch<ChannelRow[]>("/api/channels?page=1&page_size=200", {
      headers,
    }),
  ]);

  if (accountsResponse.error?.message || projectsResponse.error?.message || channelsResponse.error?.message) {
    redirect("/protected");
  }

  const accountOptions =
    accountsResponse.data?.map((item) => ({
      id: item.id,
      name: item.name,
      project_id: item.project_id,
      channel_id: item.channel_id,
    })) ?? [];

  const projectOptions = projectsResponse.data?.map((item) => ({ id: item.id, name: item.name })) ?? [];
  const channelOptions = channelsResponse.data?.map((item) => ({ id: item.id, name: item.name })) ?? [];

  return (
    <TopupsClient
      accountOptions={accountOptions}
      projectOptions={projectOptions}
      channelOptions={channelOptions}
      currentUserId={user.id}
      accessToken={accessToken}
    />
  );
}
