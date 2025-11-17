'use client';

import React from 'react';
import {
  AlertTriangle,
  XCircle,
  RefreshCw,
  WifiOff,
  Server,
  Shield,
  Clock,
  HelpCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '../button';

// 错误类型
export type ErrorType =
  | 'network'
  | 'server'
  | 'permission'
  | 'timeout'
  | 'not-found'
  | 'validation'
  | 'unknown'
  | 'custom';

// 错误严重程度
export type ErrorSeverity = 'low' | 'medium' | 'high' | 'critical';

// 错误状态组件 Props
export interface ErrorStateProps {
  type?: ErrorType;
  severity?: ErrorSeverity;
  title?: string;
  description?: string;
  error?: Error | string;
  actions?: React.ReactNode;
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showDetails?: boolean;
  onRetry?: () => void;
  onDismiss?: () => void;
}

/**
 * 预定义的错误状态配置
 */
const ERROR_STATE_CONFIG = {
  network: {
    defaultTitle: '网络连接错误',
    defaultDescription: '请检查您的网络连接后重试',
    icon: <WifiOff className="w-12 h-12 text-red-500" />,
    severity: 'medium' as ErrorSeverity
  },
  server: {
    defaultTitle: '服务器错误',
    defaultDescription: '服务器暂时无法响应，请稍后重试',
    icon: <Server className="w-12 h-12 text-red-500" />,
    severity: 'high' as ErrorSeverity
  },
  permission: {
    defaultTitle: '权限不足',
    defaultDescription: '您没有权限执行此操作',
    icon: <Shield className="w-12 h-12 text-orange-500" />,
    severity: 'medium' as ErrorSeverity
  },
  timeout: {
    defaultTitle: '请求超时',
    defaultDescription: '网络响应超时，请检查连接后重试',
    icon: <Clock className="w-12 h-12 text-orange-500" />,
    severity: 'medium' as ErrorSeverity
  },
  'not-found': {
    defaultTitle: '内容未找到',
    defaultDescription: '请求的资源不存在或已被删除',
    icon: <AlertTriangle className="w-12 h-12 text-yellow-500" />,
    severity: 'low' as ErrorSeverity
  },
  validation: {
    defaultTitle: '数据验证失败',
    defaultDescription: '提交的数据格式不正确',
    icon: <XCircle className="w-12 h-12 text-orange-500" />,
    severity: 'medium' as ErrorSeverity
  },
  unknown: {
    defaultTitle: '未知错误',
    defaultDescription: '发生了未知错误，请联系技术支持',
    icon: <AlertTriangle className="w-12 h-12 text-red-500" />,
    severity: 'high' as ErrorSeverity
  },
  custom: {
    defaultTitle: '操作失败',
    defaultDescription: '操作未能完成，请重试',
    icon: <AlertTriangle className="w-12 h-12 text-red-500" />,
    severity: 'medium' as ErrorSeverity
  }
};

/**
 * 获取错误严重程度的颜色类
 */
function getSeverityColorClasses(severity: ErrorSeverity) {
  switch (severity) {
    case 'low':
      return 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-900/20';
    case 'medium':
      return 'border-orange-200 bg-orange-50 dark:border-orange-800 dark:bg-orange-900/20';
    case 'high':
      return 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20';
    case 'critical':
      return 'border-red-300 bg-red-100 dark:border-red-700 dark:bg-red-900/30';
    default:
      return 'border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900/20';
  }
}

/**
 * 获取错误消息
 */
function getErrorMessage(error?: Error | string): string {
  if (!error) return '';
  if (typeof error === 'string') return error;
  return error.message || error.toString();
}

/**
 * 错误状态组件
 * 用于显示各种错误状态的界面
 */
export function ErrorState({
  type = 'unknown',
  severity,
  title,
  description,
  error,
  actions,
  className,
  size = 'md',
  showDetails = false,
  onRetry,
  onDismiss
}: ErrorStateProps) {
  const config = ERROR_STATE_CONFIG[type];
  const errorSeverity = severity || config.severity;
  const errorMessage = getErrorMessage(error);

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'p-4 text-center';
      case 'md':
        return 'p-6 text-center';
      case 'lg':
        return 'p-8 text-center';
      case 'xl':
        return 'p-10 text-center';
      default:
        return 'p-6 text-center';
    }
  };

  const getIconSize = () => {
    switch (size) {
      case 'sm':
        return 'w-6 h-6';
      case 'md':
        return 'w-10 h-10';
      case 'lg':
        return 'w-12 h-12';
      case 'xl':
        return 'w-16 h-16';
      default:
        return 'w-10 h-10';
    }
  };

  const getTitleSize = () => {
    switch (size) {
      case 'sm':
        return 'text-sm font-medium';
      case 'md':
        return 'text-base font-medium';
      case 'lg':
        return 'text-lg font-semibold';
      case 'xl':
        return 'text-xl font-semibold';
      default:
        return 'text-base font-medium';
    }
  };

  const getDescriptionSize = () => {
    switch (size) {
      case 'sm':
        return 'text-xs';
      case 'md':
        return 'text-sm';
      case 'lg':
        return 'text-base';
      case 'xl':
        return 'text-lg';
      default:
        return 'text-sm';
    }
  };

  const displayIcon = React.cloneElement(config.icon as React.ReactElement, {
    className: cn(getIconSize(), 'mx-auto mb-3')
  });

  const defaultActions = (
    <div className="flex flex-col sm:flex-row gap-3 items-center justify-center">
      {onRetry && (
        <Button onClick={onRetry} variant="outline" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" />
          重试
        </Button>
      )}
      {onDismiss && (
        <Button onClick={onDismiss} variant="ghost" size="sm">
          关闭
        </Button>
      )}
    </div>
  );

  return (
    <div className={cn(
      'rounded-lg border',
      getSeverityColorClasses(errorSeverity),
      getSizeClasses(),
      className
    )}>
      {displayIcon}

      <h3 className={cn(
        'text-gray-900 dark:text-gray-100 mb-2',
        getTitleSize()
      )}>
        {title || config.defaultTitle}
      </h3>

      <p className={cn(
        'text-gray-600 dark:text-gray-400 mb-4 max-w-md mx-auto',
        getDescriptionSize()
      )}>
        {description || config.defaultDescription}
      </p>

      {showDetails && errorMessage && (
        <div className="mb-4">
          <details className="text-left">
            <summary className="cursor-pointer text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300">
              错误详情
            </summary>
            <pre className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs text-gray-700 dark:text-gray-300 overflow-x-auto">
              {errorMessage}
            </pre>
          </details>
        </div>
      )}

      <div className="flex flex-col gap-2">
        {actions || defaultActions}
      </div>
    </div>
  );
}

// 预设的错误状态组件
export function NetworkError({ onRetry }: { onRetry?: () => void }) {
  return (
    <ErrorState
      type="network"
      onRetry={onRetry}
      showDetails
    />
  );
}

export function ServerError({ onRetry }: { onRetry?: () => void }) {
  return (
    <ErrorState
      type="server"
      severity="high"
      onRetry={onRetry}
      showDetails
    />
  );
}

export function PermissionError({ onRequestAccess }: { onRequestAccess?: () => void }) {
  return (
    <ErrorState
      type="permission"
      actions={
        onRequestAccess && (
          <Button onClick={onRequestAccess} variant="outline">
            申请权限
          </Button>
        )
      }
    />
  );
}

export function TimeoutError({ onRetry }: { onRetry?: () => void }) {
  return (
    <ErrorState
      type="timeout"
      onRetry={onRetry}
    />
  );
}

export function NotFoundError({ onGoHome }: { onGoHome?: () => void }) {
  return (
    <ErrorState
      type="not-found"
      severity="low"
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

// 内联错误状态（用于表格、列表中的错误行）
export function InlineErrorState({
  error,
  colSpan,
  onRetry
}: {
  error: string | Error;
  colSpan?: number;
  onRetry?: () => void;
}) {
  return (
    <tr>
      <td colSpan={colSpan || 1} className="px-4 py-4">
        <div className="flex items-center justify-center space-x-2 text-red-600 dark:text-red-400">
          <XCircle className="w-4 h-4" />
          <span className="text-sm">{getErrorMessage(error)}</span>
          {onRetry && (
            <Button
              onClick={onRetry}
              variant="ghost"
              size="sm"
              className="h-6 px-2"
            >
              <RefreshCw className="w-3 h-3" />
            </Button>
          )}
        </div>
      </td>
    </tr>
  );
}

// 警告提示组件
export function WarningAlert({
  title,
  message,
  onAction,
  actionText
}: {
  title: string;
  message?: string;
  onAction?: () => void;
  actionText?: string;
}) {
  return (
    <div className="flex items-start space-x-3 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
      <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
          {title}
        </h4>
        {message && (
          <p className="mt-1 text-sm text-yellow-700 dark:text-yellow-300">
            {message}
          </p>
        )}
        {onAction && (
          <div className="mt-2">
            <Button
              onClick={onAction}
              variant="outline"
              size="sm"
              className="text-yellow-700 border-yellow-300 hover:bg-yellow-100 dark:text-yellow-300 dark:border-yellow-600 dark:hover:bg-yellow-900/30"
            >
              {actionText || '了解更多'}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

// 错误边界组件
export interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<
  {
    children: React.ReactNode;
    fallback?: React.ComponentType<{ error: Error; retry: () => void }>;
    onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  },
  ErrorBoundaryState
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  retry = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      const FallbackComponent = this.props.fallback || DefaultErrorFallback;
      return <FallbackComponent error={this.state.error} retry={this.retry} />;
    }

    return this.props.children;
  }
}

// 默认错误回退组件
function DefaultErrorFallback({ error, retry }: { error: Error; retry: () => void }) {
  return (
    <div className="min-h-[400px] flex items-center justify-center p-4">
      <ErrorState
        error={error}
        title="页面加载失败"
        description="页面遇到了意外错误，您可以尝试刷新页面"
        onRetry={retry}
        showDetails
      />
    </div>
  );
}