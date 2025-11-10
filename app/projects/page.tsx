import { notFound } from "next/navigation";

import { apiFetch } from "@/lib/api";
import { createClient } from "@/lib/supabase/server";

import ProjectsClient from "./projects-client";

type ProjectRow = {
  id: string;
  name: string;
  client_name: string | null;
  currency: string;
  status: string;
  created_by: string | null;
  updated_by: string | null;
  created_at: string;
  updated_at: string;
};

export default async function ProjectsPage() {
  const supabase = await createClient();

  const [{ data: userData }, { data: sessionData }] = await Promise.all([
    supabase.auth.getUser(),
    supabase.auth.getSession(),
  ]);

  const currentUserId = userData?.user?.id ?? null;
  const accessToken = sessionData.session?.access_token ?? null;

  const headers = accessToken
    ? {
        Authorization: `Bearer ${accessToken}`,
      }
    : undefined;

  const projectsResponse = await apiFetch<ProjectRow[]>("/api/projects?page=1&page_size=50", {
    headers,
  });

  const errorMessage = projectsResponse.error?.message;
  if (errorMessage) {
    notFound();
  }

  return (
    <ProjectsClient
      initialProjects={projectsResponse.data ?? []}
      currentUserId={currentUserId}
      accessToken={accessToken}
    />
  );
}
