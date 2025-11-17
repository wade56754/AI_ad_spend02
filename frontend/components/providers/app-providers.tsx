'use client';

import { DataStateProvider } from '@/components/ui/data-state';

interface AppProvidersProps {
  children: React.ReactNode;
}

/**
 * 应用级Provider组件
 *
 * 将所有状态Provider集中在这个client组件中，
 * 保持根layout.tsx为SSR组件
 */
export function AppProviders({ children }: AppProvidersProps) {
  return (
    <DataStateProvider>
      {children}
    </DataStateProvider>
  );
}