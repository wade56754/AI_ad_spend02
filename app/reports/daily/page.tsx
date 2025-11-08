import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

import DailyReportsClient from "./reports-client";

export default async function DailyReportsPage() {
  const supabase = await createClient();

  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser();

  if (userError || !user) {
    redirect("/auth/login");
  }

  const [{ data: accounts }, { data: reports, error: reportsError }] = await Promise.all([
    supabase
      .from("ad_accounts")
      .select("id, name")
      .eq("assigned_user_id", user.id)
      .order("name", { ascending: true }),
    supabase
      .from("ad_spend_daily")
      .select("id, ad_account_id, date, spend, leads_count, note, created_at")
      .eq("user_id", user.id)
      .order("date", { ascending: false })
      .limit(50),
  ]);

  if (reportsError) {
    throw reportsError;
  }

  return (
    <DailyReportsClient
      accounts={accounts ?? []}
      initialReports={reports ?? []}
      currentUserId={user.id}
    />
  );
}


