'use client';

import { Component, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

/**
 * 错误边界组件
 * 捕获子组件树中的 JavaScript 错误，记录错误并显示备用 UI
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // 记录错误信息
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ errorInfo });

    // 这里可以发送错误到监控服务
    // reportError(error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
    this.props.onReset?.();
  };

  render() {
    if (this.state.hasError) {
      // 如果提供了自定义 fallback，使用它
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 默认错误 UI
      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex items-center justify-center w-16 h-16 rounded-full bg-red-100 mb-6">
            <AlertTriangle className="h-8 w-8 text-red-600" />
          </div>

          <h2 className="text-xl font-semibold text-gray-900 mb-2">出错了</h2>

          <p className="text-gray-600 text-center max-w-md mb-6">
            {this.state.error?.message || '发生了未知错误，请刷新页面重试'}
          </p>

          {process.env.NODE_ENV === 'development' && this.state.error && (
            <details className="w-full max-w-lg mb-6">
              <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                查看错误详情
              </summary>
              <pre className="mt-2 p-4 bg-gray-100 rounded text-xs overflow-auto max-h-48 text-red-600">
                {this.state.error.stack}
              </pre>
            </details>
          )}

          <div className="flex gap-4">
            <Button onClick={this.handleReset} variant="default">
              <RefreshCw className="h-4 w-4 mr-2" />
              重试
            </Button>
            <Button onClick={() => window.location.reload()} variant="outline">
              刷新页面
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * 带 React Query 重置的错误边界 Hook 封装
 */
export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  fallback?: ReactNode
) {
  return function WithErrorBoundary(props: P) {
    return (
      <ErrorBoundary fallback={fallback}>
        <WrappedComponent {...props} />
      </ErrorBoundary>
    );
  };
}

export default ErrorBoundary;
