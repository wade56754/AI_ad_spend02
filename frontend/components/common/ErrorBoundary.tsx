'use client';

import { Component, type ErrorInfo, type ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorBoundaryProps {
  children: ReactNode;
  /** Custom fallback UI. If not provided, uses default error page */
  fallback?: ReactNode;
  /** Called when an error is caught */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error Boundary Component
 *
 * Catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI.
 *
 * Usage:
 * ```tsx
 * <ErrorBoundary>
 *   <MyComponent />
 * </ErrorBoundary>
 * ```
 *
 * With custom fallback:
 * ```tsx
 * <ErrorBoundary fallback={<CustomErrorPage />}>
 *   <MyComponent />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to console in development
    console.error('[ErrorBoundary] Caught error:', error);
    console.error('[ErrorBoundary] Component stack:', errorInfo.componentStack);

    // Call optional error handler
    this.props.onError?.(error, errorInfo);

    // TODO: In production, send error to monitoring service (e.g., Sentry)
    // if (process.env.NODE_ENV === 'production') {
    //   captureException(error, { extra: { componentStack: errorInfo.componentStack } });
    // }
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return <DefaultErrorFallback error={this.state.error} onReset={this.handleReset} onReload={this.handleReload} />;
    }

    return this.props.children;
  }
}

/**
 * Default error fallback UI
 */
function DefaultErrorFallback({
  error,
  onReset,
  onReload,
}: {
  error: Error | null;
  onReset: () => void;
  onReload: () => void;
}) {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center p-8">
      <div className="flex flex-col items-center gap-4 text-center">
        <div className="rounded-full bg-destructive/10 p-3">
          <AlertTriangle className="h-8 w-8 text-destructive" />
        </div>

        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-foreground">页面出错了</h2>
          <p className="max-w-md text-sm text-muted-foreground">
            抱歉，页面加载时发生错误。请尝试刷新页面或返回首页。
          </p>
        </div>

        {/* Show error details in development */}
        {process.env.NODE_ENV === 'development' && error && (
          <details className="mt-4 w-full max-w-lg rounded-lg border border-border bg-muted/50 p-4 text-left">
            <summary className="cursor-pointer text-sm font-medium text-foreground">
              错误详情 (仅开发环境显示)
            </summary>
            <pre className="mt-2 overflow-auto whitespace-pre-wrap text-xs text-muted-foreground">
              {error.message}
              {'\n\n'}
              {error.stack}
            </pre>
          </details>
        )}

        <div className="mt-4 flex gap-3">
          <Button variant="outline" onClick={onReset}>
            <RefreshCw className="mr-2 h-4 w-4" />
            重试
          </Button>
          <Button onClick={onReload}>刷新页面</Button>
        </div>
      </div>
    </div>
  );
}

export default ErrorBoundary;
