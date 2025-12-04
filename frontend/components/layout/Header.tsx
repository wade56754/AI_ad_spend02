import React from 'react';
import { SidebarTrigger } from '@/components/ui/sidebar';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';

interface HeaderProps {
  className?: string;
  children?: React.ReactNode;
}

export default function Header({ className, children }: HeaderProps) {
  return (
    <header
      className={cn(
        'flex h-16 shrink-0 items-center justify-between gap-2 transition-[width,height] ease-linear',
        'group-has-data-[collapsible=icon]/sidebar-wrapper:h-12',
        className
      )}
    >
      <div className="flex items-center gap-2 px-4">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mr-2 h-4" />
        {children}
      </div>

      <div className="flex items-center gap-2 px-4">
        {/* 预留右侧区域，可用于用户菜单、主题切换等 */}
      </div>
    </header>
  );
}
