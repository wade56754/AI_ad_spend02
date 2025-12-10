import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  User,
  Settings,
  LogOut,
  CreditCard,
  Shield,
  HelpCircle,
  ChevronDown
} from 'lucide-react';

interface UserProfileDropdownProps {
  userName: string;
  userAvatar?: string;
  userEmail?: string;
  userRole?: string;
}

/**
 * 个人中心下拉菜单组件
 *
 * 提供用户信息展示和常用操作入口
 * 遵循设计系统规范，支持响应式设计
 */
export function UserProfileDropdown({
  userName,
  userAvatar,
  userEmail,
  userRole = "管理员"
}: UserProfileDropdownProps) {
  const handleLogout = () => {
    // 处理退出登录逻辑
    console.log('退出登录');
    // 清除用户信息、token等
    // 跳转到登录页
    window.location.href = '/login';
  };

  const handleProfile = () => {
    // 跳转到个人中心页面
    window.location.href = '/profile';
  };

  const handleSettings = () => {
    // 跳转到设置页面
    window.location.href = '/settings';
  };

  const handleBalance = () => {
    // 跳转到账户余额页面
    window.location.href = '/finance/balance';
  };

  const handleSecurity = () => {
    // 跳转到安全设置页面
    window.location.href = '/settings/security';
  };

  const handleHelp = () => {
    // 跳转到帮助中心页面
    window.location.href = '/help';
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="flex items-center gap-3 px-3 py-2 hover:bg-muted rounded-xl transition-colors h-auto"
        >
          <Avatar className="w-8 h-8">
            <AvatarImage src={userAvatar} alt={userName} />
            <AvatarFallback className="bg-primary/10 text-primary font-bold">
              {userName[0]?.toUpperCase()}
            </AvatarFallback>
          </Avatar>

          <div className="flex flex-col items-start">
            <span className="text-sm font-medium text-foreground">{userName}</span>
            <span className="text-xs text-muted-foreground">{userRole}</span>
          </div>

          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none text-foreground">{userName}</p>
            {userEmail && (
              <p className="text-xs leading-none text-muted-foreground">
                {userEmail}
              </p>
            )}
          </div>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        <DropdownMenuItem onClick={handleProfile} className="cursor-pointer">
          <User className="mr-2 h-4 w-4 text-muted-foreground" />
          个人中心
        </DropdownMenuItem>

        <DropdownMenuItem onClick={handleSettings} className="cursor-pointer">
          <Settings className="mr-2 h-4 w-4 text-muted-foreground" />
          账户设置
        </DropdownMenuItem>

        <DropdownMenuItem onClick={handleBalance} className="cursor-pointer">
          <CreditCard className="mr-2 h-4 w-4 text-muted-foreground" />
          账户余额
        </DropdownMenuItem>

        <DropdownMenuItem onClick={handleSecurity} className="cursor-pointer">
          <Shield className="mr-2 h-4 w-4 text-muted-foreground" />
          安全设置
        </DropdownMenuItem>

        <DropdownMenuItem onClick={handleHelp} className="cursor-pointer">
          <HelpCircle className="mr-2 h-4 w-4 text-muted-foreground" />
          帮助中心
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        <DropdownMenuItem
          onClick={handleLogout}
          className="cursor-pointer text-destructive focus:text-destructive"
        >
          <LogOut className="mr-2 h-4 w-4" />
          退出登录
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export default UserProfileDropdown;