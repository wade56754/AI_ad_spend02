import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

import TopupsClient from "./topups-client";

export default async function TopupsPage() {
  const supabase = await createClient();

  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser();

  if (userError || !user) {
    redirect("/auth/login");
  }

  const { data: accountMap } = await supabase
    .from("ad_accounts")
    .select("id, name, project_id, channel_id")
    .order("name", { ascending: true });

  const { data: projectsData } = await supabase.from("projects").select("id, name");
  const { data: channelsData } = await supabase.from("channels").select("id, name");

  return (
    <TopupsClient
      accountOptions={accountMap ?? []}
      projectOptions={projectsData ?? []}
      channelOptions={channelsData ?? []}
      currentUserId={user.id}
    />
  );
}


