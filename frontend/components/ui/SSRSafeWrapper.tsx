/**
 * SSR安全的组件包装器
 *
 * 黄金规则13实现：
 * - 确保服务器和客户端渲染一致
 * - 延迟渲染依赖客户端环境的内容
 * - 防止水合失败
 */

import React, { ReactNode } from 'react';
import { useIsMounted, useDeferredRender } from '@/hooks/useIsMounted';

interface SSRSafeWrapperProps {
  children: ReactNode;
  fallback?: ReactNode;
  delay?: number;
}

/**
 * 基础SSR安全包装器
 * 确保内容只在客户端渲染
 */
export const SSRSafeWrapper: React.FC<SSRSafeWrapperProps> = ({
  children,
  fallback = null,
  delay = 0
}) => {
  const isMounted = useIsMounted();
  const shouldRender = useDeferredRender(delay);

  if (!isMounted || !shouldRender) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

/**
 * 客户端专用组件包装器
 */
interface ClientOnlyProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export const ClientOnly: React.FC<ClientOnlyProps> = ({
  children,
  fallback = null
}) => {
  const isMounted = useIsMounted();

  if (!isMounted) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

/**
 * 延迟渲染组件
 */
interface DelayedRenderProps {
  children: ReactNode;
  delay: number;
  fallback?: ReactNode;
}

export const DelayedRender: React.FC<DelayedRenderProps> = ({
  children,
  delay,
  fallback = null
}) => {
  const shouldRender = useDeferredRender(delay);

  if (!shouldRender) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

/**
 * 环境检测组件
 */
interface EnvironmentAwareProps {
  children: (isClient: boolean) => ReactNode;
  serverFallback?: ReactNode;
}

export const EnvironmentAware: React.FC<EnvironmentAwareProps> = ({
  children,
  serverFallback = null
}) => {
  const isMounted = useIsMounted();

  if (!isMounted) {
    return <>{serverFallback}</>;
  }

  return <>{children(true)}</>;
};

/**
 * 动态内容包装器
 * 用于包装任何依赖动态数据的组件
 */
interface DynamicContentProps {
  children: ReactNode;
  loadingFallback?: ReactNode;
  errorFallback?: ReactNode;
  delay?: number;
}

export const DynamicContent: React.FC<DynamicContentProps> = ({
  children,
  loadingFallback = <div className="animate-pulse">加载中...</div>,
  errorFallback = <div className="text-red-500">加载失败</div>,
  delay = 0
}) => {
  const isMounted = useIsMounted();
  const shouldRender = useDeferredRender(delay);

  if (!isMounted || !shouldRender) {
    return <>{loadingFallback}</>;
  }

  return (
    <React.Suspense fallback={loadingFallback}>
      {children}
    </React.Suspense>
  );
};

/**
 * NoSSR组件
 * 完全跳过SSR的组件
 */
export const NoSSR: React.FC<{ children: ReactNode; fallback?: ReactNode }> = ({
  children,
  fallback = null
}) => {
  const [isClient, setIsClient] = React.useState(false);

  React.useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};