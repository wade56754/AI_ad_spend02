'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useTheme } from '@/hooks/useTheme';
import {
  LayoutDashboard,
  FolderKanban,
  CreditCard,
  Users,
  FileText,
  DollarSign,
  Settings,
  Menu,
  X,
  Bell,
  HelpCircle,
  BarChart3,
  Target,
  TrendingUp
} from 'lucide-react';

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<any>;
  badge?: number;
}

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  className?: string;
}

const navigation: NavigationItem[] = [
  { name: '项目管理', href: '/projects', icon: LayoutDashboard, badge: 8 },
  { name: '渠道账户', href: '/ad-accounts', icon: Users, badge: 5 },
  { name: '日报管理', href: '/reports', icon: FileText, badge: 12 },
  { name: '财务管理', href: '/finance', icon: DollarSign },
  { name: '数据统计', href: '/analytics', icon: BarChart3 },
  { name: '广告投放', href: '/campaigns', icon: Target },
  { name: 'AI监控', href: '/ai-monitoring', icon: TrendingUp },
  { name: '系统设置', href: '/settings', icon: Settings },
];

export default function Sidebar({ isOpen, onToggle, className = '' }: SidebarProps) {
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();

  return (
    <>
      {/* 移动端遮罩层 */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-900 bg-opacity-50 lg:hidden"
          onClick={onToggle}
          aria-hidden="true"
        />
      )}

      {/* 侧边栏 */}
      <div
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-72 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 ease-in-out transform lg:translate-x-0 lg:static lg:inset-0 flex flex-col',
          isOpen ? 'translate-x-0' : '-translate-x-full',
          className
        )}
      >
        {/* Logo区域 */}
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200 dark:border-gray-700">
          <Link href="/" className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
              <Target className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">AI广告系统</h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">智能代投管理平台</p>
            </div>
          </Link>

          {/* 移动端关闭按钮 */}
          <button
            type="button"
            className="lg:hidden p-2 rounded-md text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
            onClick={onToggle}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 导航菜单 */}
        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          <div className="mb-8">
            <h3 className="px-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
              主要功能
            </h3>
            {navigation.slice(0, 4).map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'group flex items-center justify-between px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 mb-1',
                    isActive
                      ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 border-l-4 border-blue-600'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white'
                  )}
                >
                  <div className="flex items-center">
                    <item.icon className={cn(
                      'mr-3 h-5 w-5 transition-colors duration-200',
                      isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400 dark:text-gray-500 group-hover:text-gray-600 dark:group-hover:text-gray-300'
                    )} />
                    {item.name}
                  </div>
                  {item.badge && (
                    <span className={cn(
                      'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
                      isActive
                        ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                    )}>
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>

          <div>
            <h3 className="px-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
              分析监控
            </h3>
            {navigation.slice(4).map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'group flex items-center justify-between px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 mb-1',
                    isActive
                      ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 border-l-4 border-blue-600'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white'
                  )}
                >
                  <div className="flex items-center">
                    <item.icon className={cn(
                      'mr-3 h-5 w-5 transition-colors duration-200',
                      isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400 dark:text-gray-500 group-hover:text-gray-600 dark:group-hover:text-gray-300'
                    )} />
                    {item.name}
                  </div>
                  {item.badge && (
                    <span className={cn(
                      'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
                      isActive
                        ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                    )}>
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        </nav>

        {/* 底部操作区域 */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="space-y-2">
            <Link
              href="/help"
              className="flex items-center px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
            >
              <HelpCircle className="w-4 h-4 mr-3 text-gray-400 dark:text-gray-500" />
              帮助中心
            </Link>

            <Link
              href="/notifications"
              className="flex items-center justify-between px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
            >
              <div className="flex items-center">
                <Bell className="w-4 h-4 mr-3 text-gray-400 dark:text-gray-500" />
                通知中心
              </div>
              <span className="w-2 h-2 bg-red-500 rounded-full" aria-label="有新通知" />
            </Link>

            <button
              type="button"
              onClick={toggleTheme}
              className="w-full flex items-center px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
            >
              {theme === 'dark' ? (
                <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
              {theme === 'dark' ? '浅色模式' : '深色模式'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}