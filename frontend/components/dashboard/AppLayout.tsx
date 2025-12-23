'use client';

import React, { useState, useEffect } from 'react';
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
  { id: 'ad-accounts', label: '广告账号管理', icon: '🔗', path: '/ad-accounts' },
  { id: 'daily-reports', label: '日报管理', icon: '📈', path: '/daily-reports' },
  { id: 'reconciliation', label: '对账管理', icon: '💰', path: '/reconciliation' },
  { id: 'topup', label: '充值管理', icon: '💳', path: '/topup' },
  { id: 'reports', label: '数据报表', icon: '📊', path: '/reports' },
  { id: 'cost-analysis', label: '成本分析', icon: '📉', path: '/cost-analysis' },
  { id: 'data-import', label: '数据导入', icon: '📥', path: '/data-import' },
  { id: 'users', label: '用户管理', icon: '👥', path: '/users' },
  { id: 'audit', label: '审计日志', icon: '🔍', path: '/audit' },
  { id: 'settings', label: '系统设置', icon: '⚙️', path: '/settings' },
];

const BOTTOM_MENU_ITEMS = [
  { id: 'profile', label: '个人中心', icon: '👤', path: '/profile' },
  { id: 'help', label: '帮助中心', icon: '❓', path: '/help' },
  { id: 'contact', label: '联系我们', icon: '💬', path: '/contact' },
  { id: 'logout', label: '退出登录', icon: '🚪', highlight: true },
];

export function AppLayout({
  children,
  userName = "Anthony",
  userAvatar,
  userEmail,
  userRole = "管理员"
}: AppLayoutProps) {
  const [activeMenu, setActiveMenu] = useState('workbench');
  const router = useRouter();
  const pathname = usePathname();

  // 根据当前路径确定激活的菜单项
  const getCurrentActiveMenu = () => {
    const currentItem = MENU_ITEMS.find(item => item.path === pathname);
    return currentItem ? currentItem.id : 'workbench';
  };

  const handleMenuChange = (menuId: string) => {
    setActiveMenu(menuId);

    // 查找对应的路由
    const menuItem = [...MENU_ITEMS, ...BOTTOM_MENU_ITEMS].find(item => item.id === menuId);

    if (menuItem?.path) {
      router.push(menuItem.path);
    } else if (menuId === 'logout') {
      // 处理退出登录逻辑
      console.log('退出登录');
      // 这里可以添加清除用户信息、token等逻辑
      router.push('/auth/login');
    } else if (menuId === 'help') {
      // 打开帮助文档或新页面
      window.open('/docs', '_blank');
    } else if (menuId === 'contact') {
      // 打开联系方式或反馈页面
      router.push('/contact');
    }
  };

  // 初始化时设置当前激活的菜单
  useEffect(() => {
    setActiveMenu(getCurrentActiveMenu());
  }, [pathname]);

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