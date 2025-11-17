// 导出所有数据状态管理相关的组件和类型

// 核心状态管理
export {
  DataStateProvider,
  useDataState,
  useAsyncOperation,
  type DataState,
  type DataStatus,
  type DataStateContextType,
  type DataStateProviderProps
} from './DataStateProvider';

// 加载状态
export {
  LoadingState,
  Skeleton,
  CardSkeleton,
  MetricCardSkeleton,
  TableSkeleton,
  type LoadingStateProps,
  type SkeletonProps
} from './LoadingState';

// 空状态
export {
  EmptyState,
  NoDataEmptyState,
  NoResultsEmptyState,
  NoProjectsEmptyState,
  NoUsersEmptyState,
  NotFoundEmptyState,
  CardEmptyState,
  InlineEmptyState,
  type EmptyStateProps,
  type EmptyStateType
} from './EmptyState';

// 错误状态
export {
  ErrorState,
  NetworkError,
  ServerError,
  PermissionError,
  TimeoutError,
  NotFoundError,
  InlineErrorState,
  WarningAlert,
  ErrorBoundary,
  type ErrorStateProps,
  type ErrorType,
  type ErrorSeverity,
  type ErrorBoundaryState
} from './ErrorState';

// 状态管理器
export {
  DataStateManager,
  StateContainer,
  useDataWithState,
  ListStateManager,
  type DataStateManagerProps,
  type StateContainerProps
} from './DataStateManager';