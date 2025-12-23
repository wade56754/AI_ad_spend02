/**
 * Projects Route Page
 *
 * Route: /projects
 */

'use client';

import dynamic from 'next/dynamic';

// 动态导入以避免 SSR hydration 问题
const ProjectsPage = dynamic(
  () => import('@/features/projects').then(mod => ({ default: mod.ProjectsPage })),
  { ssr: false, loading: () => <ProjectsPageSkeleton /> }
);

function ProjectsPageSkeleton() {
  return (
    <div className="container mx-auto py-6 space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="h-8 w-32 bg-gray-200 rounded" />
        <div className="flex gap-2">
          <div className="h-9 w-20 bg-gray-200 rounded" />
          <div className="h-9 w-24 bg-gray-200 rounded" />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-24 bg-gray-200 rounded-lg" />
        ))}
      </div>
      <div className="h-64 bg-gray-200 rounded-lg" />
    </div>
  );
}

export default function Page() {
  return <ProjectsPage />;
}
