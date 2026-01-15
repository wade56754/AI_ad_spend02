'use client';

import React from 'react';
import {
  LayoutDashboard,
  FolderKanban,
  Users,
  FileText,
  CalendarDays,
  DollarSign,
  UserCog,
  Settings,
  Sun,
  Moon,
  LogOut,
  Target,
  type LucideIcon,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

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

interface SidebarProps {
  activeMenu: string;
  onMenuChange: (menu: string) => void;
  menuGroups?: MenuGroup[];
  bottomMenuItems?: MenuItem[];
  theme?: 'light' | 'dark';
  onThemeToggle?: () => void;
}

const DEFAULT_MENU_GROUPS: MenuGroup[] = [
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

const DEFAULT_BOTTOM_MENU_ITEMS: MenuItem[] = [
  { id: 'logout', label: '退出登录', icon: LogOut, highlight: true },
];

export function Sidebar({
  activeMenu,
  onMenuChange,
  menuGroups = DEFAULT_MENU_GROUPS,
  bottomMenuItems = DEFAULT_BOTTOM_MENU_ITEMS,
  theme = 'light',
  onThemeToggle,
}: SidebarProps) {
  return (
    <aside className="flex w-[280px] flex-col bg-[#0B1437] text-white">
      {/* Logo */}
      <div className="border-b border-gray-700/30 p-6">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-r from-blue-600 to-purple-600">
            <Target className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="text-base font-bold">AI广告系统</div>
            <div className="text-xs text-gray-400">智能代投管理平台</div>
          </div>
        </div>
      </div>

      {/* Main Menu with Groups */}
      <nav className="flex-1 overflow-y-auto px-4 py-6">
        {menuGroups.map((group, groupIndex) => (
          <div key={group.title} className={groupIndex > 0 ? 'mt-6' : ''}>
            <h3 className="mb-3 px-4 text-xs font-semibold uppercase tracking-wider text-gray-500">
              {group.title}
            </h3>
            {group.items.map((item) => {
              const Icon = item.icon;
              const isActive = activeMenu === item.id;
              return (
                <Button
                  key={item.id}
                  onClick={() => onMenuChange(item.id)}
                  variant="ghost"
                  className={`relative w-full justify-between px-4 py-3 text-left transition-all rounded-xl mb-1 ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:bg-gray-700/30 hover:text-white'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`h-5 w-5 ${isActive ? 'text-white' : 'text-gray-500'}`} />
                    <span className="text-sm font-medium">{item.label}</span>
                  </div>
                  {item.badge && (
                    <div className="flex h-5 w-5 items-center justify-center rounded-full bg-amber-500 text-xs font-bold text-white">
                      {item.badge}
                    </div>
                  )}
                </Button>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Bottom Menu */}
      <div className="border-t border-gray-700/30 px-4 py-4">
        {/* Theme Toggle */}
        {onThemeToggle && (
          <Button
            onClick={onThemeToggle}
            variant="ghost"
            className="w-full justify-start gap-3 rounded-xl px-4 py-3 text-left text-gray-400 transition-all hover:bg-gray-700/30 hover:text-white mb-1"
          >
            {theme === 'dark' ? (
              <Sun className="h-5 w-5 text-gray-500" />
            ) : (
              <Moon className="h-5 w-5 text-gray-500" />
            )}
            <span className="text-sm font-medium">
              {theme === 'dark' ? '浅色模式' : '深色模式'}
            </span>
          </Button>
        )}

        {/* Other Bottom Items */}
        {bottomMenuItems.map((item) => {
          const Icon = item.icon;
          return (
            <Button
              key={item.id}
              onClick={() => onMenuChange(item.id)}
              variant="ghost"
              className={`w-full justify-start gap-3 rounded-xl px-4 py-3 text-left transition-all mb-1 ${
                item.highlight
                  ? 'text-amber-500 hover:bg-amber-500/10'
                  : 'text-gray-400 hover:bg-gray-700/30 hover:text-white'
              }`}
            >
              <Icon className={`h-5 w-5 ${item.highlight ? 'text-amber-500' : 'text-gray-500'}`} />
              <span className="text-sm font-medium">{item.label}</span>
            </Button>
          );
        })}
      </div>
    </aside>
  );
}

export default Sidebar;
