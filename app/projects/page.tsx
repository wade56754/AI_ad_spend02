import { notFound } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

import ProjectsClient from "./projects-client";

export default async function ProjectsPage() {
  const supabase = await createClient();

  const [{ data: userData }, { data: projectsData, error: projectsError }] = await Promise.all([
    supabase.auth.getUser(),
    supabase.from("projects").select("*").order("created_at", { ascending: false }),
  ]);

  if (projectsError) {
    notFound();
  }

  return (
    <ProjectsClient
      initialProjects={projectsData ?? []}
      currentUserId={userData?.user?.id ?? null}
    />
  );
}


