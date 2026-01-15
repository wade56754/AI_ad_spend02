'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Menu, Bell, Search, User, Settings, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

interface HeaderProps {
  onSidebarToggle: () => void;
  title?: string;
  subtitle?: string;
  className?: string;
}

export default function Header({
  onSidebarToggle,
  title = '控制台',
  subtitle = '欢迎使用AI广告代投系统',
  className = '',
}: HeaderProps) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 点击外部关闭下拉菜单
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsDropdownOpen(false);
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isDropdownOpen]);
  return (
    <header
      className={cn(
        'bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm',
        className
      )}
    >
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* 左侧：移动端菜单按钮 + 页面标题 */}
          <div className="flex items-center">
            {/* 移动端菜单按钮 */}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="lg:hidden mr-3 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700"
              onClick={onSidebarToggle}
              aria-label="打开侧边栏"
            >
              <Menu className="w-6 h-6" />
            </Button>

            {/* 页面标题 */}
            <div>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">{title}</h1>
              {subtitle && (
                <p className="text-sm text-gray-500 dark:text-gray-400 hidden sm:block">
                  {subtitle}
                </p>
              )}
            </div>
          </div>

          {/* 右侧：搜索框 + 通知 + 用户菜单 */}
          <div className="flex items-center space-x-4">
            {/* 搜索框 */}
            <div className="hidden md:block">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-4 w-4 text-gray-400" />
                </div>
                <Input
                  type="text"
                  className="w-64 pl-10 pr-3 border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white focus-visible:ring-blue-500 focus-visible:border-blue-500"
                  placeholder="搜索项目、账户..."
                />
              </div>
            </div>

            {/* 通知按钮 */}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="relative text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              aria-label="查看通知"
            >
              <Bell className="w-5 h-5" />
              <span
                className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full"
                aria-hidden="true"
              />
            </Button>

            {/* 用户菜单 */}
            <div className="relative" ref={dropdownRef}>
              <Button
                type="button"
                variant="ghost"
                className="flex items-center space-x-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                aria-label="用户菜单"
                data-testid="user-menu"
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                aria-expanded={isDropdownOpen}
                aria-haspopup="true"
              >
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
                <div className="hidden lg:block text-left">
                  <div className="text-sm font-medium text-gray-900 dark:text-white">管理员</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">admin@example.com</div>
                </div>
              </Button>

              {/* 下拉菜单 */}
              <div
                className={cn(
                  'absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-50 transition-all duration-200',
                  isDropdownOpen
                    ? 'opacity-100 scale-100 translate-y-0'
                    : 'opacity-0 scale-95 translate-y-[-10px] pointer-events-none'
                )}
              >
                <a
                  href="#"
                  className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <User className="w-4 h-4 mr-3" />
                  个人资料
                </a>
                <a
                  href="#"
                  className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <Settings className="w-4 h-4 mr-3" />
                  账户设置
                </a>
                <hr className="my-1 border-gray-200 dark:border-gray-700" />
                <Button
                  onClick={() => {
                    localStorage.removeItem('auth-token');
                    localStorage.removeItem('refresh-token');
                    localStorage.removeItem('token-expiry');
                    window.location.href = '/login';
                  }}
                  data-testid="logout-button"
                  variant="ghost"
                  className="w-full justify-start px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <LogOut className="w-4 h-4 mr-3" />
                  退出登录
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
