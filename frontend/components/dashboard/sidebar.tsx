'use client';

import React from 'react';

interface MenuItem {
  id: string;
  label: string;
  icon: string;
  path?: string;
  badge?: number;
  highlight?: boolean;
}

interface SidebarProps {
  activeMenu: string;
  onMenuChange: (menu: string) => void;
  menuItems?: MenuItem[];
  bottomMenuItems?: MenuItem[];
}

const DEFAULT_MENU_ITEMS = [
  { id: 'workbench', label: '工作台概览', icon: '📊', path: '/' },
  { id: 'projects', label: '项目管理', icon: '📁', path: '/projects' },
  { id: 'channels', label: '渠道账户', icon: '🔗', path: '/ad-accounts' },
  { id: 'reports', label: '日报管理', icon: '📈', badge: 2, path: '/daily-reports' },
  { id: 'settings', label: '系统设置', icon: '⚙️', path: '/settings' },
];

const DEFAULT_BOTTOM_MENU_ITEMS = [
  { id: 'help', label: '帮助中心', icon: '❓' },
  { id: 'contact', label: '联系我们', icon: '💬' },
  { id: 'logout', label: '退出登录', icon: '🚪', highlight: true },
];

export function Sidebar({
  activeMenu,
  onMenuChange,
  menuItems = DEFAULT_MENU_ITEMS,
  bottomMenuItems = DEFAULT_BOTTOM_MENU_ITEMS
}: SidebarProps) {
  return (
    <aside className="flex w-[280px] flex-col bg-[#0B1437] text-white">
      {/* Logo */}
      <div className="border-b border-gray-700/30 p-6">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#1E3A8A] text-lg font-bold">
            M
          </div>
          <div className="text-sm font-semibold">广告投放管理系统</div>
        </div>
      </div>

      {/* Main Menu */}
      <nav className="flex-1 px-4 py-6">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onMenuChange(item.id)}
            className={`relative flex w-full items-center justify-between px-4 py-3 text-left transition-all rounded-xl mb-1 ${
              activeMenu === item.id
                ? 'bg-[#1E3A8A] text-white'
                : 'text-gray-400 hover:bg-gray-700/30 hover:text-white'
            }`}
          >
            <div className="flex items-center gap-3">
              <span className="text-base">{item.icon}</span>
              <span className="text-sm font-medium">{item.label}</span>
            </div>
            {item.badge && (
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[#F59E0B] text-xs font-bold text-white">
                {item.badge}
              </div>
            )}
          </button>
        ))}
      </nav>

      {/* Bottom Menu */}
      <div className="border-t border-gray-700/30 px-4 py-4">
        {bottomMenuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onMenuChange(item.id)}
            className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left transition-all mb-1 ${
              item.highlight
                ? 'text-[#F59E0B] hover:bg-[#F59E0B]/10'
                : 'text-gray-400 hover:bg-gray-700/30 hover:text-white'
            }`}
          >
            <span className="text-base">{item.icon}</span>
            <span className="text-sm font-medium">{item.label}</span>
          </button>
        ))}
      </div>
    </aside>
  );
}

export default Sidebar;