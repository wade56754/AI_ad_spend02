'use client';

import React from 'react';
import {
  FileX,
  Inbox,
  Search,
  FolderOpen,
  Users,
  ShoppingCart,
  Calendar,
  AlertCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '../button';

// 空状态类型
export type EmptyStateType =
  | 'no-data'
  | 'no-results'
  | 'no-items'
  | 'no-projects'
  | 'no-users'
  | 'no-orders'
  | 'no-events'
  | 'not-found'
  | 'custom';

// 空状态组件 Props
export interface EmptyStateProps {
  type?: EmptyStateType;
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  illustration?: string; // 图片URL
}

/**
 * 预定义的空状态配置
 */
const EMPTY_STATE_CONFIG = {
  'no-data': {
    defaultTitle: '暂无数据',
    defaultDescription: '当前页面没有可显示的数据',
    icon: <FileX className="w-12 h-12 text-gray-400" />
  },
  'no-results': {
    defaultTitle: '没有搜索结果',
    defaultDescription: '尝试调整搜索条件或筛选器',
    icon: <Search className="w-12 h-12 text-gray-400" />
  },
  'no-items': {
    defaultTitle: '暂无项目',
    defaultDescription: '列表中没有任何项目',
    icon: <Inbox className="w-12 h-12 text-gray-400" />
  },
  'no-projects': {
    defaultTitle: '暂无项目',
    defaultDescription: '还没有创建任何项目',
    icon: <FolderOpen className="w-12 h-12 text-gray-400" />
  },
  'no-users': {
    defaultTitle: '暂无用户',
    defaultDescription: '还没有任何用户注册',
    icon: <Users className="w-12 h-12 text-gray-400" />
  },
  'no-orders': {
    defaultTitle: '暂无订单',
    defaultDescription: '还没有任何订单记录',
    icon: <ShoppingCart className="w-12 h-12 text-gray-400" />
  },
  'no-events': {
    defaultTitle: '暂无事件',
    defaultDescription: '还没有任何事件记录',
    icon: <Calendar className="w-12 h-12 text-gray-400" />
  },
  'not-found': {
    defaultTitle: '页面未找到',
    defaultDescription: '您访问的页面不存在或已被移除',
    icon: <AlertCircle className="w-12 h-12 text-gray-400" />
  },
  'custom': {
    defaultTitle: '暂无内容',
    defaultDescription: '当前没有可显示的内容',
    icon: <Inbox className="w-12 h-12 text-gray-400" />
  }
};

/**
 * 空状态组件
 * 用于显示数据为空时的占位界面
 */
export function EmptyState({
  type = 'no-data',
  title,
  description,
  icon,
  actions,
  className,
  size = 'md',
  illustration
}: EmptyStateProps) {
  const config = EMPTY_STATE_CONFIG[type];

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'p-4 text-center';
      case 'md':
        return 'p-8 text-center';
      case 'lg':
        return 'p-12 text-center';
      case 'xl':
        return 'p-16 text-center';
      default:
        return 'p-8 text-center';
    }
  };

  const getIconSize = () => {
    switch (size) {
      case 'sm':
        return 'w-8 h-8';
      case 'md':
        return 'w-12 h-12';
      case 'lg':
        return 'w-16 h-16';
      case 'xl':
        return 'w-20 h-20';
      default:
        return 'w-12 h-12';
    }
  };

  const getTitleSize = () => {
    switch (size) {
      case 'sm':
        return 'text-base font-medium';
      case 'md':
        return 'text-lg font-medium';
      case 'lg':
        return 'text-xl font-semibold';
      case 'xl':
        return 'text-2xl font-semibold';
      default:
        return 'text-lg font-medium';
    }
  };

  const getDescriptionSize = () => {
    switch (size) {
      case 'sm':
        return 'text-sm';
      case 'md':
        return 'text-base';
      case 'lg':
        return 'text-lg';
      case 'xl':
        return 'text-xl';
      default:
        return 'text-base';
    }
  };

  const displayIcon = icon || (React.cloneElement(config.icon as React.ReactElement, {
    className: cn(getIconSize(), 'text-gray-400')
  }));

  return (
    <div className={cn('flex flex-col items-center justify-center', getSizeClasses(), className)}>
      {illustration ? (
        <img
          src={illustration}
          alt="空状态插图"
          className={cn('mb-4 max-w-full h-auto', size === 'sm' ? 'w-16 h-16' : size === 'lg' ? 'w-32 h-32' : size === 'xl' ? 'w-40 h-40' : 'w-24 h-24')}
        />
      ) : (
        <div className="mb-4">
          {displayIcon}
        </div>
      )}

      <h3 className={cn(
        'text-gray-900 dark:text-gray-100 mb-2',
        getTitleSize()
      )}>
        {title || config.defaultTitle}
      </h3>

      <p className={cn(
        'text-gray-500 dark:text-gray-400 mb-6 max-w-md',
        getDescriptionSize()
      )}>
        {description || config.defaultDescription}
      </p>

      {actions && (
        <div className="flex flex-col sm:flex-row gap-3 items-center justify-center">
          {actions}
        </div>
      )}
    </div>
  );
}

// 预设的空状态组件
export function NoDataEmptyState({
  title,
  description,
  onRefresh
}: {
  title?: string;
  description?: string;
  onRefresh?: () => void;
}) {
  return (
    <EmptyState
      type="no-data"
      title={title}
      description={description}
      actions={
        onRefresh && (
          <Button onClick={onRefresh} variant="outline">
            刷新数据
          </Button>
        )
      }
    />
  );
}

export function NoResultsEmptyState({
  onClearSearch
}: {
  onClearSearch?: () => void;
}) {
  return (
    <EmptyState
      type="no-results"
      actions={
        onClearSearch && (
          <Button onClick={onClearSearch} variant="outline">
            清除搜索条件
          </Button>
        )
      }
    />
  );
}

export function NoProjectsEmptyState({
  onCreateProject
}: {
  onCreateProject?: () => void;
}) {
  return (
    <EmptyState
      type="no-projects"
      description="创建第一个项目开始管理您的广告投放"
      actions={
        onCreateProject && (
          <Button onClick={onCreateProject}>
            创建项目
          </Button>
        )
      }
    />
  );
}

export function NoUsersEmptyState({
  onInviteUser
}: {
  onInviteUser?: () => void;
}) {
  return (
    <EmptyState
      type="no-users"
      description="邀请团队成员加入项目"
      actions={
        onInviteUser && (
          <Button onClick={onInviteUser}>
            邀请用户
          </Button>
        )
      }
    />
  );
}

export function NotFoundEmptyState({
  onGoHome
}: {
  onGoHome?: () => void;
}) {
  return (
    <EmptyState
      type="not-found"
      size="lg"
      actions={
        onGoHome && (
          <Button onClick={onGoHome}>
            返回首页
          </Button>
        )
      }
    />
  );
}

// 卡片样式的空状态
export function CardEmptyState({
  type = 'no-data',
  title,
  description,
  className
}: {
  type?: EmptyStateType;
  title?: string;
  description?: string;
  className?: string;
}) {
  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8', className)}>
      <EmptyState
        type={type}
        title={title}
        description={description}
        size="sm"
      />
    </div>
  );
}

// 内联空状态（用于表格、列表中的空行）
export function InlineEmptyState({
  message,
  colSpan,
  className
}: {
  message: string;
  colSpan?: number;
  className?: string;
}) {
  return (
    <tr className={className}>
      <td colSpan={colSpan || 1} className="px-4 py-8 text-center">
        <div className="flex items-center justify-center space-x-2 text-gray-500 dark:text-gray-400">
          <Inbox className="w-4 h-4" />
          <span>{message}</span>
        </div>
      </td>
    </tr>
  );
}