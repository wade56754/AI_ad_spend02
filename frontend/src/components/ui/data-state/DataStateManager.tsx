'use client';

import React from 'react';
import { useDataState, DataStatus } from './DataStateProvider';
import { LoadingState, MetricCardSkeleton } from './LoadingState';
import { EmptyState } from './EmptyState';
import { ErrorState } from './ErrorState';
import { cn } from '@/lib/utils';

// 状态管理器组件 Props
export interface DataStateManagerProps<T = any> {
  // 状态相关
  status?: DataStatus;
  loading?: boolean;
  error?: Error | string;
  data?: T;

  // 内容渲染
  children: React.ReactNode | ((data: T) => React.ReactNode);
  loadingContent?: React.ReactNode;
  emptyContent?: React.ReactNode;
  errorContent?: React.ReactNode;

  // 自定义配置
  loadingType?: 'spinner' | 'skeleton' | 'dots' | 'progress';
  skeletonCount?: number;
  emptyType?: 'no-data' | 'no-results' | 'no-items' | 'not-found' | 'custom';
  errorType?: 'network' | 'server' | 'permission' | 'timeout' | 'unknown';

  // 操作回调
  onRetry?: () => void;
  onRefresh?: () => void;

  // 样式配置
  className?: string;
  minHeight?: string | number;
  overlay?: boolean;

  // 空数据判断
  isEmpty?: (data: T) => boolean;

  // 进度（用于progress类型的加载状态）
  progress?: number;
  showProgressPercentage?: boolean;
}

/**
 * 数据状态管理器组件
 * 统一管理加载、空状态、错误状态的显示
 */
export function DataStateManager<T = any>({
  status,
  loading,
  error,
  data,
  children,
  loadingContent,
  emptyContent,
  errorContent,
  loadingType = 'spinner',
  skeletonCount = 3,
  emptyType = 'no-data',
  errorType = 'unknown',
  onRetry,
  onRefresh,
  className,
  minHeight = '200px',
  overlay = false,
  isEmpty,
  progress,
  showProgressPercentage = false
}: DataStateManagerProps<T>) {
  // 优先使用传入的status，其次从context获取，最后基于props推断
  const { state: contextState } = useDataState();
  const actualStatus = status || contextState.status;
  const actualError = error || contextState.error;
  const actualData = data || contextState.data;

  // 判断是否为空状态
  const isEmptyData = React.useMemo(() => {
    if (isEmpty) {
      return isEmpty(actualData as T);
    }

    // 默认的空数据判断逻辑
    if (actualData === null || actualData === undefined) {
      return true;
    }

    if (Array.isArray(actualData)) {
      return actualData.length === 0;
    }

    if (typeof actualData === 'object') {
      return Object.keys(actualData).length === 0;
    }

    return false;
  }, [actualData, isEmpty]);

  // 判断是否为加载状态
  const isLoading = loading !== undefined ? loading : actualStatus === 'loading';

  // 判断是否为错误状态
  const hasError = actualError !== undefined || actualStatus === 'error';

  // 判断是否为空状态
  const showEmpty = !isLoading && !hasError && isEmptyData;

  // 判断是否显示成功内容
  const showContent = !isLoading && !hasError && !isEmptyData;

  const containerStyle: React.CSSProperties = {
    minHeight: typeof minHeight === 'number' ? `${minHeight}px` : minHeight,
    position: overlay ? 'relative' : undefined
  };

  // 渲染加载状态
  const renderLoading = () => {
    if (loadingContent) {
      return loadingContent;
    }

    const loadingProps = {
      type: loadingType,
      overlay,
      progress,
      showPercentage: showProgressPercentage
    };

    if (loadingType === 'skeleton' && typeof children === 'function') {
      return (
        <div className="space-y-4">
          {Array.from({ length: skeletonCount }, (_, i) => (
            <MetricCardSkeleton key={i} />
          ))}
        </div>
      );
    }

    return <LoadingState {...loadingProps} />;
  };

  // 渲染空状态
  const renderEmpty = () => {
    if (emptyContent) {
      return emptyContent;
    }

    const emptyProps = {
      type: emptyType,
      actions: onRefresh && (
        <button
          onClick={onRefresh}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          刷新数据
        </button>
      )
    };

    return <EmptyState {...emptyProps} />;
  };

  // 渲染错误状态
  const renderError = () => {
    if (errorContent) {
      return errorContent;
    }

    const errorProps = {
      type: errorType,
      error: actualError,
      onRetry,
      showDetails: true
    };

    return <ErrorState {...errorProps} />;
  };

  // 渲染内容
  const renderContent = () => {
    if (typeof children === 'function') {
      return (children as (data: T) => React.ReactNode)(actualData as T);
    }
    return children;
  };

  return (
    <div
      className={cn('relative w-full', className)}
      style={containerStyle}
    >
      {isLoading && renderLoading()}

      {!isLoading && hasError && renderError()}

      {!isLoading && !hasError && showEmpty && renderEmpty()}

      {showContent && renderContent()}
    </div>
  );
}

// 便捷的状态容器组件
export interface StateContainerProps<T = any> extends Omit<DataStateManagerProps<T>, 'children'> {
  children: React.ReactNode;
}

/**
 * 状态容器组件
 * 简化版本的DataStateManager，用于包裹现有组件
 */
export function StateContainer<T = any>({
  children,
  loading,
  error,
  data,
  loadingType = 'spinner',
  emptyType = 'no-data',
  errorType = 'unknown',
  onRetry,
  onRefresh,
  className,
  minHeight = '200px',
  isEmpty,
  ...props
}: StateContainerProps<T>) {
  return (
    <DataStateManager<T>
      loading={loading}
      error={error}
      data={data}
      loadingType={loadingType}
      emptyType={emptyType}
      errorType={errorType}
      onRetry={onRetry}
      onRefresh={onRefresh}
      className={className}
      minHeight={minHeight}
      isEmpty={isEmpty}
      {...props}
    >
      {children}
    </DataStateManager>
  );
}

/**
 * 带状态管理的数据获取Hook
 */
export function useDataWithState<T = any>(
  fetcher: () => Promise<T>,
  options?: {
    immediate?: boolean;
    onSuccess?: (data: T) => void;
    onError?: (error: Error) => void;
    retryCount?: number;
    retryDelay?: number;
  }
) {
  const { setLoading, setSuccess, setError, state } = useDataState();
  const [retryCount, setRetryCount] = React.useState(0);

  const execute = React.useCallback(async () => {
    try {
      setLoading();
      const result = await fetcher();
      setSuccess(result);
      setRetryCount(0);
      options?.onSuccess?.(result);
      return result;
    } catch (error) {
      const err = error as Error;

      // 自动重试逻辑
      if (options?.retryCount && retryCount < options.retryCount) {
        setTimeout(() => {
          setRetryCount(prev => prev + 1);
          execute();
        }, options.retryDelay || 1000);
        return;
      }

      setError(err.message || '请求失败');
      options?.onError?.(err);
      throw err;
    }
  }, [fetcher, setLoading, setSuccess, setError, retryCount, options]);

  React.useEffect(() => {
    if (options?.immediate) {
      execute();
    }
  }, [execute, options?.immediate]);

  const retry = React.useCallback(() => {
    setRetryCount(0);
    execute();
  }, [execute]);

  const reset = React.useCallback(() => {
    setRetryCount(0);
    setLoading();
  }, [setLoading]);

  return {
    data: state.data as T | undefined,
    loading: state.status === 'loading',
    error: state.error,
    execute,
    retry,
    reset,
    retryCount
  };
}

/**
 * 列表状态管理组件
 * 专门用于列表数据的显示
 */
export function ListStateManager<T = any>({
  items,
  loading,
  error,
  renderItem,
  loadingComponent,
  emptyMessage,
  errorComponent,
  className,
  itemClassName,
  containerClassName
}: {
  items?: T[];
  loading?: boolean;
  error?: Error | string;
  renderItem: (item: T, index: number) => React.ReactNode;
  loadingComponent?: React.ReactNode;
  emptyMessage?: string;
  errorComponent?: React.ReactNode;
  className?: string;
  itemClassName?: string;
  containerClassName?: string;
}) {
  return (
    <DataStateManager<T[]>
      loading={loading}
      error={error}
      data={items}
      emptyType="no-items"
      className={className}
      loadingContent={loadingComponent}
      emptyContent={
        <div className={cn('text-center py-8', containerClassName)}>
          <p className="text-gray-500 dark:text-gray-400">
            {emptyMessage || '列表中没有数据'}
          </p>
        </div>
      }
      errorContent={errorComponent}
    >
      {(data) => (
        <div className={cn('space-y-2', containerClassName)}>
          {data.map((item, index) => (
            <div key={index} className={itemClassName}>
              {renderItem(item, index)}
            </div>
          ))}
        </div>
      )}
    </DataStateManager>
  );
}