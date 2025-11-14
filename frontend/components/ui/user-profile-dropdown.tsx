import React, { useState } from 'react';
import { Button } from './button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from './avatar';
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
    window.location.href = '/auth/login';
  };

  const handleProfile = () => {
    // 跳转到个人中心页面
    window.location.href = '/profile';
  };

  const handleSettings = () => {
    // 跳转到设置页面
    window.location.href = '/settings';
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="flex items-center gap-3 px-4 py-2 hover:bg-gray-100 rounded-xl transition-colors h-auto"
        >
          <Avatar className="w-10 h-10">
            <AvatarImage src={userAvatar} alt={userName} />
            <AvatarFallback className="bg-[#1E3A8A]/10 text-[#1E3A8A] font-bold">
              {userName[0]?.toUpperCase()}
            </AvatarFallback>
          </Avatar>

          <div className="flex flex-col items-start">
            <span className="text-sm font-medium text-gray-900">{userName}</span>
            <span className="text-xs text-gray-600">{userRole}</span>
          </div>

          <ChevronDown className="w-4 h-4 text-gray-600" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{userName}</p>
            {userEmail && (
              <p className="text-xs leading-none text-muted-foreground">
                {userEmail}
              </p>
            )}
          </div>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        <DropdownMenuItem onClick={handleProfile} className="cursor-pointer">
          <User className="mr-2 h-4 w-4" />
          个人中心
        </DropdownMenuItem>

        <DropdownMenuItem onClick={handleSettings} className="cursor-pointer">
          <Settings className="mr-2 h-4 w-4" />
          账户设置
        </DropdownMenuItem>

        <DropdownMenuItem className="cursor-pointer">
          <CreditCard className="mr-2 h-4 w-4" />
          账户余额
        </DropdownMenuItem>

        <DropdownMenuItem className="cursor-pointer">
          <Shield className="mr-2 h-4 w-4" />
          安全设置
        </DropdownMenuItem>

        <DropdownMenuItem className="cursor-pointer">
          <HelpCircle className="mr-2 h-4 w-4" />
          帮助中心
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        <DropdownMenuItem
          onClick={handleLogout}
          className="cursor-pointer text-red-600 focus:text-red-600"
        >
          <LogOut className="mr-2 h-4 w-4" />
          退出登录
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export default UserProfileDropdown;