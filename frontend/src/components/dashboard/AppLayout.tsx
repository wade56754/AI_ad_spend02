'use client';

import React, { useMemo } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Sidebar from './sidebar';
import Header from './header';

interface AppLayoutProps {
  children: React.ReactNode;
  userName?: string;
  userAvatar?: string;
  userEmail?: string;
  userRole?: string;
}

const MENU_ITEMS = [
  { id: 'workbench', label: '工作台概览', icon: '📊', path: '/' },
  { id: 'projects', label: '项目管理', icon: '📁', path: '/projects' },
  { id: 'finance', label: '财务中心', icon: '💵', path: '/finance' },
  { id: 'ad-accounts', label: '广告账号管理', icon: '🔗', path: '/ad-accounts' },
  { id: 'daily-reports', label: '日报管理', icon: '📈', path: '/daily-reports' },
  { id: 'reconciliation', label: '对账管理', icon: '💰', path: '/reconciliation' },
  { id: 'topups', label: '充值管理', icon: '💳', path: '/topups' },
  { id: 'reports', label: '数据报表', icon: '📊', path: '/reports' },
  { id: 'suppliers', label: '供应商管理', icon: '🏢', path: '/suppliers' },
  { id: 'settlements', label: '结算管理', icon: '📋', path: '/settlements' },
  { id: 'import-jobs', label: '数据导入', icon: '📥', path: '/import-jobs' },
  { id: 'users', label: '用户管理', icon: '👥', path: '/users' },
  { id: 'cost-analysis', label: '成本分析', icon: '📉', path: '/cost-analysis' },
  { id: 'audit-logs', label: '审计日志', icon: '🔍', path: '/audit-logs' },
  { id: 'settings', label: '系统设置', icon: '⚙️', path: '/settings' },
];

const BOTTOM_MENU_ITEMS = [
  { id: 'profile', label: '个人中心', icon: '👤', path: '/profile' },
  { id: 'help', label: '帮助中心', icon: '❓', path: '/help' },
  { id: 'logout', label: '退出登录', icon: '🚪', highlight: true },
];

export function AppLayout({
  children,
  userName = "Anthony",
  userAvatar,
  userEmail,
  userRole = "管理员"
}: AppLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();

  // 根据当前路径确定激活的菜单项 - 使用 useMemo 替代 useState + useEffect
  // activeMenu 完全由 pathname 派生，不需要单独的状态
  const activeMenu = useMemo(() => {
    const currentItem = MENU_ITEMS.find(item => item.path === pathname);
    return currentItem ? currentItem.id : 'workbench';
  }, [pathname]);

  const handleMenuChange = (menuId: string) => {
    // 查找对应的路由
    const menuItem = [...MENU_ITEMS, ...BOTTOM_MENU_ITEMS].find(item => item.id === menuId);

    if (menuId === 'logout') {
      // TODO: 集成 useAuth().logout() 清除 token
      router.push('/login');
    } else if (menuItem?.path) {
      router.push(menuItem.path);
    }
  };

  // 为侧边栏提供完整的菜单项
  const SidebarWithMenu = () => {
    return <Sidebar
      activeMenu={activeMenu}
      onMenuChange={handleMenuChange}
      menuItems={MENU_ITEMS}
      bottomMenuItems={BOTTOM_MENU_ITEMS}
    />;
  };

  return (
    <div className="flex h-screen bg-[#F6F7FB]">
      <SidebarWithMenu />
      <div className="flex-1 overflow-auto">
        <Header
          userName={userName}
          userAvatar={userAvatar}
          userEmail={userEmail}
          userRole={userRole}
        />
        <main className="mx-auto flex max-w-[1200px] flex-col gap-8 px-8 pb-10 pt-8">
          {children}
        </main>
      </div>
    </div>
  );
}

export default AppLayout;