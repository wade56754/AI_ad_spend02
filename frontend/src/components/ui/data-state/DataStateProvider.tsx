'use client';

import React, { createContext, useContext, ReactNode } from 'react';

// 数据状态枚举
export type DataStatus = 'loading' | 'success' | 'error' | 'empty';

// 数据状态接口
export interface DataState<T = any> {
  status: DataStatus;
  data?: T;
  error?: string;
  lastUpdated?: Date;
}

// 数据状态上下文接口
export interface DataStateContextType<T = unknown> {
  state: DataState<T>;
  setLoading: () => void;
  setSuccess: (data: T) => void;
  setError: (error: string) => void;
  setEmpty: () => void;
  reset: () => void;
}

// 创建上下文
const DataStateContext = createContext<DataStateContextType | undefined>(undefined);

// 数据状态提供者组件 Props
export interface DataStateProviderProps {
  children: ReactNode;
  initialState?: Partial<DataState>;
  onDataUpdate?: (state: DataState) => void;
}

/**
 * 数据状态提供者组件
 * 提供统一的数据状态管理，包括加载、成功、错误、空状态
 */
export function DataStateProvider({
  children,
  initialState,
  onDataUpdate
}: DataStateProviderProps) {
  const [state, setState] = React.useState<DataState>({
    status: 'loading',
    ...initialState
  });

  const setLoading = React.useCallback(() => {
    setState(prev => {
      const newState = { ...prev, status: 'loading' as const, error: undefined };
      onDataUpdate?.(newState);
      return newState;
    });
  }, [onDataUpdate]);

  const setSuccess = React.useCallback(<T = unknown>(data: T) => {
    setState(prev => {
      const newState = {
        ...prev,
        status: 'success' as const,
        data,
        error: undefined,
        lastUpdated: new Date()
      };
      onDataUpdate?.(newState);
      return newState;
    });
  }, [onDataUpdate]);

  const setError = React.useCallback((error: string) => {
    setState(prev => {
      const newState = { ...prev, status: 'error' as const, error };
      onDataUpdate?.(newState);
      return newState;
    });
  }, [onDataUpdate]);

  const setEmpty = React.useCallback(() => {
    setState(prev => {
      const newState = {
        ...prev,
        status: 'empty' as const,
        data: undefined,
        error: undefined
      };
      onDataUpdate?.(newState);
      return newState;
    });
  }, [onDataUpdate]);

  const reset = React.useCallback(() => {
    setState(prev => {
      const newState = {
        status: 'loading' as const,
        data: undefined,
        error: undefined
      };
      onDataUpdate?.(newState);
      return newState;
    });
  }, [onDataUpdate]);

  const contextValue: DataStateContextType = {
    state,
    setLoading,
    setSuccess,
    setError,
    setEmpty,
    reset
  };

  return (
    <DataStateContext.Provider value={contextValue}>
      {children}
    </DataStateContext.Provider>
  );
}

/**
 * 使用数据状态的 Hook
 */
export function useDataState() {
  const context = useContext(DataStateContext);
  if (context === undefined) {
    throw new Error('useDataState must be used within a DataStateProvider');
  }
  return context;
}

/**
 * 异步数据操作 Hook
 * 自动处理加载状态、成功和错误状态
 */
export function useAsyncOperation<T = any>(
  operation: () => Promise<T>,
  options?: {
    onSuccess?: (data: T) => void;
    onError?: (error: Error) => void;
    immediate?: boolean;
  }
) {
  const { setLoading, setSuccess, setError } = useDataState();
  const [isLoading, setIsLoading] = React.useState(false);

  const execute = React.useCallback(async () => {
    try {
      setLoading();
      setIsLoading(true);
      const result = await operation();
      setSuccess(result);
      options?.onSuccess?.(result);
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '操作失败';
      setError(errorMessage);
      options?.onError?.(error as Error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [operation, setLoading, setSuccess, setError, options]);

  React.useEffect(() => {
    if (options?.immediate) {
      execute();
    }
  }, [execute, options?.immediate]);

  return {
    execute,
    isLoading
  };
}