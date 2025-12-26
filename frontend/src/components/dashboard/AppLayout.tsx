'use client';

import React, { useMemo, useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  FolderKanban,
  Users,
  FileText,
  CalendarDays,
  DollarSign,
  UserCog,
  Settings,
  LogOut,
  type LucideIcon,
} from 'lucide-react';
import Sidebar from './sidebar';
import Header from './header';

interface AppLayoutProps {
  children: React.ReactNode;
  userName?: string;
  userAvatar?: string;
  userEmail?: string;
  userRole?: string;
}

interface MenuItem {
  id: string;
  label: string;
  icon: LucideIcon;
  path?: string;
  badge?: number;
  highlight?: boolean;
}

interface MenuGroup {
  title: string;
  items: MenuItem[];
}

/**
 * 精简版侧边栏菜单配置 (6+2项)
 * 基于 UI_DESIGN_SYSTEM.md 和 FRONTEND_DASHBOARD_DESIGN_v1.2.md
 */
const MENU_GROUPS: MenuGroup[] = [
  {
    title: '业务管理',
    items: [
      { id: 'dashboard', label: '仪表盘', icon: LayoutDashboard, path: '/' },
      { id: 'projects', label: '项目管理', icon: FolderKanban, path: '/projects' },
      { id: 'ad-accounts', label: '广告账户', icon: Users, path: '/ad-accounts' },
      { id: 'daily-reports', label: '日报管理', icon: FileText, path: '/daily-reports' },
      { id: 'weekly-briefs', label: '周度简报', icon: CalendarDays, path: '/weekly-briefs' },
      { id: 'finance', label: '财务管理', icon: DollarSign, path: '/finance' },
    ],
  },
  {
    title: '系统管理',
    items: [
      { id: 'users', label: '用户管理', icon: UserCog, path: '/users' },
      { id: 'settings', label: '系统设置', icon: Settings, path: '/settings' },
    ],
  },
];

const BOTTOM_MENU_ITEMS: MenuItem[] = [
  { id: 'logout', label: '退出登录', icon: LogOut, highlight: true },
];

// 扁平化所有菜单项用于路由查找
const ALL_MENU_ITEMS = MENU_GROUPS.flatMap(group => group.items);

export function AppLayout({
  children,
  userName = "Anthony",
  userAvatar,
  userEmail,
  userRole = "管理员"
}: AppLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  // 初始化主题
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
    if (savedTheme) {
      setTheme(savedTheme);
      document.documentElement.classList.toggle('dark', savedTheme === 'dark');
    }
  }, []);

  // 切换主题
  const handleThemeToggle = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.classList.toggle('dark', newTheme === 'dark');
  };

  // 根据当前路径确定激活的菜单项
  const activeMenu = useMemo(() => {
    // 精确匹配
    const exactMatch = ALL_MENU_ITEMS.find(item => item.path === pathname);
    if (exactMatch) return exactMatch.id;

    // 前缀匹配 (如 /projects/123 应该高亮 projects)
    const prefixMatch = ALL_MENU_ITEMS.find(
      item => item.path && item.path !== '/' && pathname.startsWith(item.path)
    );
    if (prefixMatch) return prefixMatch.id;

    return 'dashboard';
  }, [pathname]);

  const handleMenuChange = (menuId: string) => {
    if (menuId === 'logout') {
      // TODO: 集成 useAuth().logout() 清除 token
      router.push('/login');
      return;
    }

    // 查找对应的路由
    const menuItem = [...ALL_MENU_ITEMS, ...BOTTOM_MENU_ITEMS].find(item => item.id === menuId);
    if (menuItem?.path) {
      router.push(menuItem.path);
    }
  };

  return (
    <div className="flex h-screen bg-[#F6F7FB] dark:bg-gray-900">
      <Sidebar
        activeMenu={activeMenu}
        onMenuChange={handleMenuChange}
        menuGroups={MENU_GROUPS}
        bottomMenuItems={BOTTOM_MENU_ITEMS}
        theme={theme}
        onThemeToggle={handleThemeToggle}
      />
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