'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import { Search, Bell, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Breadcrumb } from '@/components/ui/breadcrumb';
import { UserProfileDropdown } from '@/components/ui/user-profile-dropdown';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface HeaderProps {
  userName: string;
  userAvatar?: string;
  userEmail?: string;
  userRole?: string;
}

// 面包屑导航映射
const breadcrumbMap: Record<string, { label: string; href?: string; icon?: React.ReactNode }> = {
  '/': { label: '工作台概览' },
  '/projects': { label: '项目管理', href: '/projects' },
  '/ad-accounts': { label: '渠道账户', href: '/ad-accounts' },
  '/daily-reports': { label: '日报管理', href: '/daily-reports' },
  '/reconciliation': { label: '对账管理', href: '/reconciliation' },
  '/topup': { label: '充值管理', href: '/topup' },
  '/reports': { label: '数据报表', href: '/reports' },
  '/cost-analysis': { label: '成本分析', href: '/cost-analysis' },
  '/data-import': { label: '数据导入', href: '/data-import' },
  '/users': { label: '用户管理', href: '/users' },
  '/audit': { label: '审计日志', href: '/audit' },
  '/settings': { label: '系统设置', href: '/settings' },
  '/profile': { label: '个人中心', href: '/profile' },
};

export function Header({
  userName,
  userAvatar,
  userEmail,
  userRole
}: HeaderProps) {
  const pathname = usePathname();

  // 生成面包屑导航项
  const generateBreadcrumbItems = () => {
    // 移除开头的斜杠并分割路径
    const pathSegments = pathname.split('/').filter(Boolean);
    const items: { label: string; href?: string; icon?: React.ReactNode }[] = [];

    if (pathSegments.length === 0) {
      // 首页
      return items;
    }

    // 构建层级路径
    let currentPath = '';
    for (const segment of pathSegments) {
      currentPath += `/${segment}`;
      const breadcrumbInfo = breadcrumbMap[currentPath];

      if (breadcrumbInfo) {
        items.push({
          ...breadcrumbInfo,
          href: currentPath !== pathname ? currentPath : undefined,
        });
      } else {
        // 如果没有预定义的映射，使用路径名作为标签
        items.push({
          label: segment.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          href: currentPath !== pathname ? currentPath : undefined,
        });
      }
    }

    return items;
  };

  const breadcrumbItems = generateBreadcrumbItems();

  return (
    <header className="bg-white border-b border-[#ECECEC] px-8 py-6">
      <div className="flex items-center justify-between">
        {/* Left Section: 面包屑导航 */}
        <div className="flex-1">
          <Breadcrumb items={breadcrumbItems} />
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-3">
          {/* Search */}
          <Button variant="ghost" size="sm" className="p-3 hover:bg-gray-100 rounded-xl transition-colors">
            <Search className="w-5 h-5 text-gray-600" />
          </Button>

          {/* Notifications */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="p-3 hover:bg-gray-100 rounded-xl transition-colors relative"
              >
                <Bell className="w-5 h-5 text-gray-600" />
                <div className="absolute top-2 right-2 w-2 h-2 bg-[#EF4444] rounded-full"></div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-80">
              <DropdownMenuLabel className="font-normal">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium">通知</p>
                  <Button variant="ghost" size="sm" className="text-xs">
                    全部标记已读
                  </Button>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="cursor-pointer">
                <div className="flex flex-col space-y-1">
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-1"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">新账户待审核</p>
                      <p className="text-xs text-muted-foreground">
                        3个新账户需要您审核
                      </p>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">5分钟前</p>
                </div>
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer">
                <div className="flex flex-col space-y-1">
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full mt-1"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">日报提交成功</p>
                      <p className="text-xs text-muted-foreground">
                        张三提交了今日日报
                      </p>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">30分钟前</p>
                </div>
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer">
                <div className="flex flex-col space-y-1">
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-orange-500 rounded-full mt-1"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">账户异常提醒</p>
                      <p className="text-xs text-muted-foreground">
                        检测到2个账户有异常消耗
                      </p>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">1小时前</p>
                </div>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="cursor-pointer justify-center">
                查看所有通知
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* User Profile Dropdown */}
          <UserProfileDropdown
            userName={userName}
            userAvatar={userAvatar}
            userEmail={userEmail}
            userRole={userRole}
          />
        </div>
      </div>
    </header>
  );
}

export default Header;