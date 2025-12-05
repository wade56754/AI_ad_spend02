import AppSidebar from '@/components/layout/app-sidebar';
import Header from '@/components/layout/Header';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
import type { Metadata } from 'next';
import { cookies } from 'next/headers';

export const metadata: Metadata = {
  title: 'Dashboard - AI广告代投系统',
  description: 'AI广告代投系统管理后台'
};

export default async function DashboardLayout({
  children
}: {
  children: React.ReactNode;
}) {
  const cookieStore = await cookies();
  // Default to expanded (true) when no cookie or cookie is not 'false'
  const sidebarCookie = cookieStore.get('sidebar_state')?.value;
  const defaultOpen = sidebarCookie !== 'false';

  return (
    <SidebarProvider defaultOpen={defaultOpen}>
      <AppSidebar />
      <SidebarInset>
        <Header />
        {children}
      </SidebarInset>
    </SidebarProvider>
  );
}
