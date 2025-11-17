'use client'

import { useState } from 'react'

interface SidebarProps {
  activeMenu: string
  onMenuChange: (menu: string) => void
}

const MENU_ITEMS = [
  { id: 'workbench', label: '工作台概览', icon: '📊' },
  { id: 'projects', label: '项目管理', icon: '📁' },
  { id: 'channels', label: '渠道账户', icon: '🔗' },
  { id: 'reports', label: '日报管理', icon: '📈', badge: 2 },
  { id: 'settings', label: '系统设置', icon: '⚙️' },
]

const BOTTOM_MENU_ITEMS = [
  { id: 'help', label: '帮助中心', icon: '❓' },
  { id: 'contact', label: '联系我们', icon: '💬' },
  { id: 'logout', label: '退出登录', icon: '🚪', highlight: true },
]

export default function Sidebar({ activeMenu, onMenuChange }: SidebarProps) {
  return (
    <aside className="flex w-[260px] flex-col bg-slate-900 text-white shadow-lg">
      {/* Logo */}
      <div className="border-b border-slate-700 p-5">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-orange-500 text-base font-bold">
            M
          </div>
          <div className="text-xs font-semibold">广告投放管理系统</div>
        </div>
      </div>

      {/* Main Menu */}
      <nav className="flex-1 space-y-1 px-3 py-5">
        {MENU_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => onMenuChange(item.id)}
            className={`relative flex w-full items-center justify-between px-6 py-2.5 text-left text-sm transition-colors ${
              activeMenu === item.id ? 'text-white' : 'text-slate-300 hover:text-white'
            }`}
          >
            {activeMenu === item.id && (
              <>
                <div className="absolute left-0 top-0 bottom-0 w-1 rounded-r-md bg-white" />
                <div className="absolute inset-0 -z-10 rounded-md bg-[#FF7A1A14]" />
              </>
            )}

            <div className="ml-1 flex items-center gap-2">
              <span className="text-base">{item.icon}</span>
              <span className="text-xs">{item.label}</span>
            </div>
            {item.badge && (
              <div className="flex h-5 w-5 items-center justify-center rounded-full bg-orange-400 text-xs font-bold text-white">
                {item.badge}
              </div>
            )}
          </button>
        ))}
      </nav>

      {/* Bottom Menu */}
      <div className="space-y-1 border-t border-slate-700 px-3 py-4">
        {BOTTOM_MENU_ITEMS.map((item) => (
          <button
            key={item.id}
            className={`flex w-full items-center gap-2 rounded-md px-6 py-2.5 text-left text-sm transition-colors ${
              item.highlight
                ? 'text-orange-500 hover:bg-slate-800'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-300'
            }`}
          >
            <span className="text-base">{item.icon}</span>
            <span className="text-xs">{item.label}</span>
          </button>
        ))}
      </div>
    </aside>
  )
}
