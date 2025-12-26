---
version: v1.0
status: ready_for_production
layer: architecture
owner: wade
last_reviewed: 2025-11-28
baseline: MASTER.md v4.4, SoT Freeze v2.6, Dev-Guides Freeze vFinal
---

# Frontend Structure Specification

## 1. Purpose

Define the authoritative frontend project structure for the AI Ad Spend Management System, ensuring:

- **Domain-Driven Design**: Feature-based modular architecture aligned with backend domains
- **SoT Compliance**: UI components strictly follow STATE_MACHINE.md v2.7 and ERROR_CODES_SOT.md v2.1
- **Type Safety**: Full TypeScript coverage with Zod runtime validation
- **Maintainability**: Clear separation of concerns with colocated feature code
- **Testability**: Built-in testing infrastructure at all levels

## 2. Scope

### 2.1 In Scope

- Complete folder structure specification
- API client architecture (apiFetch pattern)
- Error handling flow mapped to ERROR_CODES_SOT.md v2.1
- Data fetching strategy with TanStack Query
- UI state mapping to 8-state daily report machine (STATE_MACHINE.md v2.7)
- Module organization for core domains (topups, daily_reports, ledger, reconciliation)
- Shared components and hooks library

### 2.2 Out of Scope

- Visual design system (see UI_DESIGN_SYSTEM.md)
- Backend API implementation (see API_DEVELOPMENT_FLOW.md)
- Deployment configuration (see Infrastructure Layer)

## 3. Technology Stack

### 3.1 Core Dependencies

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Framework | React | ^18.2.0 | UI framework |
| Language | TypeScript | ^5.3.0 | Type safety |
| Build Tool | Vite | ^5.0.0 | Fast development & build |
| Routing | React Router | ^6.20.0 | Client-side routing |
| State (Server) | TanStack Query | ^5.0.0 | Server state management |
| State (Client) | Zustand | ^4.4.0 | Client state management |
| Validation | Zod | ^3.22.0 | Runtime type validation |
| Auth | Supabase Client | ^2.38.0 | Authentication |
| Styling | Tailwind CSS | ^3.4.0 | Utility-first CSS |
| UI Components | shadcn/ui | latest | Component library |

### 3.2 Dev Dependencies

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Testing | Vitest | ^1.0.0 | Unit/integration tests |
| Testing | Testing Library | ^14.1.0 | Component testing |
| E2E Testing | Playwright | ^1.40.0 | End-to-end tests |
| Linting | ESLint | ^8.55.0 | Code quality |
| Formatting | Prettier | ^3.1.0 | Code formatting |

## 4. Project Structure

### 4.1 Root Directory Layout

```
frontend/
├── public/                    # Static assets
│   ├── favicon.ico
│   └── manifest.json
├── src/
│   ├── app/                   # App-level configuration
│   │   ├── App.tsx           # Root component
│   │   ├── routes.tsx        # Route definitions
│   │   └── providers.tsx     # Context providers
│   ├── lib/                   # Core libraries
│   │   ├── api/              # API client layer
│   │   ├── auth/             # Auth utilities
│   │   ├── validation/       # Zod schemas
│   │   └── utils/            # Helper functions
│   ├── modules/               # Feature modules (domain-driven)
│   │   ├── auth/             # Authentication module
│   │   ├── dashboard/        # Dashboard module
│   │   ├── projects/         # Projects module
│   │   ├── ad-accounts/      # Ad accounts module
│   │   ├── daily-reports/    # Daily reports module (8-state machine)
│   │   ├── topups/           # Topup requests module
│   │   ├── ledger/           # Ledger transactions module
│   │   ├── reconciliation/   # Reconciliation module
│   │   └── shared/           # Shared components & hooks
│   ├── stores/                # Global Zustand stores
│   ├── types/                 # Global TypeScript types
│   └── main.tsx              # Entry point
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .env.example
├── .eslintrc.cjs
├── .prettierrc
├── index.html
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

### 4.2 Module Structure (Feature-Based)

Each feature module follows this structure:

```
modules/{feature}/
├── components/           # Feature-specific components
│   ├── {Feature}List.tsx
│   ├── {Feature}Form.tsx
│   ├── {Feature}Card.tsx
│   └── {Feature}StatusBadge.tsx
├── hooks/                # Feature-specific hooks
│   ├── use{Feature}Query.ts
│   ├── use{Feature}Mutation.ts
│   └── use{Feature}Store.ts
├── pages/                # Route pages
│   ├── {Feature}ListPage.tsx
│   ├── {Feature}DetailPage.tsx
│   └── {Feature}CreatePage.tsx
├── services/             # API service functions
│   └── {feature}Api.ts
├── stores/               # Feature Zustand stores
│   └── {feature}Store.ts
├── types/                # Feature types
│   └── {feature}.types.ts
├── utils/                # Feature utilities
│   └── {feature}Utils.ts
└── index.ts              # Public exports
```

### 4.3 Shared Module Structure

```
modules/shared/
├── components/
│   ├── ui/               # Base UI components (shadcn/ui wrappers)
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Select.tsx
│   │   ├── Table.tsx
│   │   ├── Modal.tsx
│   │   ├── Toast.tsx
│   │   └── index.ts
│   ├── layout/           # Layout components
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   ├── PageContainer.tsx
│   │   └── index.ts
│   ├── feedback/         # Feedback components
│   │   ├── LoadingSpinner.tsx
│   │   ├── ErrorBoundary.tsx
│   │   ├── EmptyState.tsx
│   │   └── index.ts
│   └── data-display/     # Data display components
│       ├── StatusBadge.tsx
│       ├── DataTable.tsx
│       ├── Pagination.tsx
│       └── index.ts
├── hooks/
│   ├── useAuth.ts
│   ├── usePermission.ts
│   ├── usePagination.ts
│   ├── useDebounce.ts
│   └── index.ts
└── index.ts
```

## 5. API Client Architecture

### 5.1 apiFetch Pattern

All API calls MUST use the centralized `apiFetch` function (API_SOT.md v9.3 Section 2.4).

**Location**: `src/lib/api/apiFetch.ts`

```typescript
// Type definitions aligned with API_SOT.md v9.3 Section 4
interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  message: string;
  code: string;
  request_id: string;
  timestamp: string;
}

interface ApiError {
  success: false;
  error: {
    code: string;      // ERROR_CODES_SOT.md v2.1
    message: string;
    details?: Record<string, unknown>;
  };
  request_id: string;
  timestamp: string;
}

interface PaginatedResponse<T> {
  success: true;
  data: {
    items: T[];
    meta: {
      pagination: {
        page: number;
        page_size: number;
        total: number;
        total_pages: number;
        has_next: boolean;
        has_prev: boolean;
      };
    };
  };
  message: string;
  code: string;
}
```

### 5.2 API Client Structure

```
lib/api/
├── apiFetch.ts           # Core fetch wrapper
├── apiClient.ts          # Configured axios/fetch instance
├── apiErrors.ts          # Error handling utilities
├── apiTypes.ts           # API response types
├── endpoints/            # Endpoint definitions
│   ├── auth.ts
│   ├── projects.ts
│   ├── adAccounts.ts
│   ├── dailyReports.ts
│   ├── topups.ts
│   ├── ledger.ts
│   └── reconciliation.ts
└── index.ts
```

### 5.3 Module API Services

Each module has its own API service file:

**Location**: `modules/{feature}/services/{feature}Api.ts`

```typescript
// Example: modules/daily-reports/services/dailyReportsApi.ts
import { apiFetch } from '@/lib/api';
import type { DailyReport, DailyReportCreateRequest } from '../types';

export const dailyReportsApi = {
  // GET /api/v1/daily-reports
  list: (params: ListParams) =>
    apiFetch<PaginatedResponse<DailyReport>>('/api/v1/daily-reports', { params }),

  // GET /api/v1/daily-reports/:id
  get: (id: number) =>
    apiFetch<DailyReport>(`/api/v1/daily-reports/${id}`),

  // POST /api/v1/daily-reports
  create: (data: DailyReportCreateRequest) =>
    apiFetch<DailyReport>('/api/v1/daily-reports', { method: 'POST', body: data }),

  // POST /api/v1/daily-reports/:id/submit (STATE_MACHINE.md v2.7 Section 8.2)
  submit: (id: number) =>
    apiFetch<DailyReport>(`/api/v1/daily-reports/${id}/submit`, { method: 'POST' }),
};
```

## 6. Error Handling Flow

### 6.1 Error Code Mapping (ERROR_CODES_SOT.md v2.1)

**Location**: `src/lib/api/apiErrors.ts`

```typescript
// Error code categories from ERROR_CODES_SOT.md v2.1
export const ERROR_CODE_PREFIXES = {
  AUTH: 'AUTH_',      // Authentication errors (401, 403)
  BIZ: 'BIZ_',        // Business logic errors (400, 404, 409)
  VALIDATION: 'VALIDATION_',  // Parameter validation (400)
  SYS: 'SYS_',        // System errors (500, 503)
  DB: 'DB_',          // Database errors (500)
  STATE: 'STATE_',    // State machine errors (400, 409)
  TREND: 'TREND_',    // Trend check errors (400)
} as const;

// Common error codes
export const ERROR_CODES = {
  // AUTH errors
  AUTH_001: '用户名或密码错误',
  AUTH_400: '未提供认证令牌',
  AUTH_401: '无效的认证令牌',
  AUTH_402: '认证令牌已过期',
  AUTH_500: '权限不足',

  // BIZ errors
  BIZ_001: '资源不存在',
  BIZ_301: '状态转换非法',
  BIZ_302: '操作冲突',

  // STATE errors (STATE_MACHINE.md v2.7)
  STATE_001: '非法状态转换',
  STATE_002: '终态不可修改',
  STATE_409: '并发冲突',

  // VALIDATION errors
  VALIDATION_001: '必填字段缺失',
  VALIDATION_010: '格式错误',
} as const;
```

### 6.2 Error Handling Strategy

```typescript
// Error handler in apiFetch.ts
export async function handleApiError(error: ApiError): Promise<never> {
  const { code, message, details } = error.error;

  // 1. Auth errors -> redirect to login
  if (code.startsWith('AUTH_4')) {
    authStore.getState().logout();
    window.location.href = '/login';
  }

  // 2. State machine errors -> show specific guidance
  if (code.startsWith('STATE_')) {
    toast.error(`状态错误: ${message}`, {
      description: '请参阅 STATE_MACHINE.md 了解合法状态转换',
    });
  }

  // 3. Validation errors -> show field-level errors
  if (code.startsWith('VALIDATION_')) {
    // Return errors for form to display
    throw new ValidationError(code, message, details);
  }

  // 4. Generic errors -> toast notification
  toast.error(message);
  throw new ApiError(code, message, details);
}
```

## 7. Data Fetching Strategy

### 7.1 TanStack Query Configuration

**Location**: `src/lib/api/queryClient.ts`

```typescript
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5 minutes
      gcTime: 30 * 60 * 1000,        // 30 minutes (formerly cacheTime)
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
});
```

### 7.2 Query Key Convention

```typescript
// Query key factory pattern
export const queryKeys = {
  // Daily Reports
  dailyReports: {
    all: ['daily-reports'] as const,
    lists: () => [...queryKeys.dailyReports.all, 'list'] as const,
    list: (filters: DailyReportFilters) =>
      [...queryKeys.dailyReports.lists(), filters] as const,
    details: () => [...queryKeys.dailyReports.all, 'detail'] as const,
    detail: (id: number) => [...queryKeys.dailyReports.details(), id] as const,
  },

  // Topups
  topups: {
    all: ['topups'] as const,
    lists: () => [...queryKeys.topups.all, 'list'] as const,
    list: (filters: TopupFilters) => [...queryKeys.topups.lists(), filters] as const,
    detail: (id: number) => [...queryKeys.topups.all, 'detail', id] as const,
  },

  // Ledger
  ledger: {
    all: ['ledger'] as const,
    entries: (accountId: number) => [...queryKeys.ledger.all, 'entries', accountId] as const,
    balance: (accountId: number) => [...queryKeys.ledger.all, 'balance', accountId] as const,
  },
};
```

### 7.3 Custom Query Hooks

**Location**: `modules/{feature}/hooks/use{Feature}Query.ts`

```typescript
// Example: useDailyReportsQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dailyReportsApi } from '../services/dailyReportsApi';
import { queryKeys } from '@/lib/api/queryKeys';

export function useDailyReportsList(filters: DailyReportFilters) {
  return useQuery({
    queryKey: queryKeys.dailyReports.list(filters),
    queryFn: () => dailyReportsApi.list(filters),
  });
}

export function useDailyReportSubmit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => dailyReportsApi.submit(id),
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.dailyReports.all });
    },
  });
}
```

## 8. UI State Mapping (STATE_MACHINE.md v2.7)

### 8.1 Daily Report 8-State Machine

**Reference**: STATE_MACHINE.md v2.7 Section 8

```typescript
// Location: modules/daily-reports/types/dailyReport.types.ts

// 8-state machine (STATE_MACHINE.md v2.7 Section 8.1)
export type DailyReportStatus =
  | 'raw_submitted'      // 投手提交原始粉数
  | 'trend_pending'      // 等待趋势风控检查
  | 'trend_ok'           // 趋势正常
  | 'trend_flagged'      // 趋势异常,需人工复核
  | 'trend_resolved'     // 运营确认异常已解决
  | 'final_pending'      // 等待最终粉数确认
  | 'final_confirmed'    // 最终粉数已确认
  | 'final_locked';      // 终态: 已进入计费,锁定

// Status display configuration
export const DAILY_REPORT_STATUS_CONFIG: Record<DailyReportStatus, {
  label: string;
  color: 'blue' | 'yellow' | 'green' | 'orange' | 'red' | 'gray';
  icon: string;
  allowedActions: string[];
}> = {
  raw_submitted: {
    label: '已提交',
    color: 'blue',
    icon: 'FileCheck',
    allowedActions: [],
  },
  trend_pending: {
    label: '趋势检查中',
    color: 'yellow',
    icon: 'Clock',
    allowedActions: [],
  },
  trend_ok: {
    label: '趋势正常',
    color: 'green',
    icon: 'CheckCircle',
    allowedActions: ['input_real_spend'],
  },
  trend_flagged: {
    label: '趋势异常',
    color: 'orange',
    icon: 'AlertTriangle',
    allowedActions: ['resolve', 'request_resubmit'],
  },
  trend_resolved: {
    label: '异常已解决',
    color: 'green',
    icon: 'CheckCircle2',
    allowedActions: ['input_real_spend'],
  },
  final_pending: {
    label: '待确认',
    color: 'yellow',
    icon: 'FileQuestion',
    allowedActions: ['confirm_final'],
  },
  final_confirmed: {
    label: '已确认',
    color: 'green',
    icon: 'FileCheck2',
    allowedActions: [],
  },
  final_locked: {
    label: '已锁定',
    color: 'gray',
    icon: 'Lock',
    allowedActions: ['reversal'],  // Only red-flush allowed
  },
};
```

### 8.2 Status Badge Component

**Location**: `modules/daily-reports/components/DailyReportStatusBadge.tsx`

```typescript
import { Badge } from '@/modules/shared/components/ui';
import { DAILY_REPORT_STATUS_CONFIG, type DailyReportStatus } from '../types';

interface DailyReportStatusBadgeProps {
  status: DailyReportStatus;
}

export function DailyReportStatusBadge({ status }: DailyReportStatusBadgeProps) {
  const config = DAILY_REPORT_STATUS_CONFIG[status];

  return (
    <Badge variant={config.color} icon={config.icon}>
      {config.label}
    </Badge>
  );
}
```

### 8.3 State Transition Validation

```typescript
// Location: modules/daily-reports/utils/stateTransitions.ts

// Valid transitions per STATE_MACHINE.md v2.7 Section 8.2
const VALID_TRANSITIONS: Record<DailyReportStatus, DailyReportStatus[]> = {
  raw_submitted: ['trend_pending'],
  trend_pending: ['trend_ok', 'trend_flagged'],
  trend_ok: ['final_pending'],
  trend_flagged: ['trend_resolved', 'raw_submitted'],
  trend_resolved: ['final_pending'],
  final_pending: ['final_confirmed'],
  final_confirmed: ['final_locked'],
  final_locked: [],  // Terminal state - only reversal allowed
};

export function canTransition(from: DailyReportStatus, to: DailyReportStatus): boolean {
  return VALID_TRANSITIONS[from]?.includes(to) ?? false;
}

export function getAvailableTransitions(current: DailyReportStatus): DailyReportStatus[] {
  return VALID_TRANSITIONS[current] ?? [];
}
```

## 9. Module Specifications

### 9.1 Daily Reports Module

```
modules/daily-reports/
├── components/
│   ├── DailyReportList.tsx
│   ├── DailyReportForm.tsx
│   ├── DailyReportCard.tsx
│   ├── DailyReportStatusBadge.tsx
│   ├── DailyReportTimeline.tsx       # 8-state workflow timeline
│   ├── TrendCheckAlert.tsx           # trend_flagged handling
│   └── FinalConfirmDialog.tsx
├── hooks/
│   ├── useDailyReportQuery.ts
│   ├── useDailyReportMutation.ts
│   └── useDailyReportFilters.ts
├── pages/
│   ├── DailyReportListPage.tsx
│   ├── DailyReportDetailPage.tsx
│   └── DailyReportCreatePage.tsx
├── services/
│   └── dailyReportsApi.ts
├── types/
│   └── dailyReport.types.ts
├── utils/
│   └── stateTransitions.ts
└── index.ts
```

### 9.2 Topups Module

```
modules/topups/
├── components/
│   ├── TopupRequestList.tsx
│   ├── TopupRequestForm.tsx
│   ├── TopupStatusBadge.tsx
│   ├── TopupApprovalDialog.tsx
│   └── TopupReceiptUpload.tsx
├── hooks/
│   ├── useTopupQuery.ts
│   ├── useTopupMutation.ts
│   └── useTopupApproval.ts
├── pages/
│   ├── TopupListPage.tsx
│   ├── TopupDetailPage.tsx
│   └── TopupCreatePage.tsx
├── services/
│   └── topupsApi.ts
├── types/
│   └── topup.types.ts
└── index.ts
```

### 9.3 Ledger Module

```
modules/ledger/
├── components/
│   ├── LedgerEntryList.tsx
│   ├── LedgerEntryCard.tsx
│   ├── AccountBalanceCard.tsx
│   ├── LedgerTimeline.tsx
│   └── BalanceHistoryChart.tsx
├── hooks/
│   ├── useLedgerQuery.ts
│   └── useAccountBalance.ts
├── pages/
│   ├── LedgerListPage.tsx
│   └── AccountBalancePage.tsx
├── services/
│   └── ledgerApi.ts
├── types/
│   └── ledger.types.ts
└── index.ts
```

### 9.4 Reconciliation Module

```
modules/reconciliation/
├── components/
│   ├── ReconciliationBatchList.tsx
│   ├── ReconciliationDetailTable.tsx
│   ├── ReconciliationStatusBadge.tsx
│   ├── AdjustmentForm.tsx
│   └── ReconciliationSummary.tsx
├── hooks/
│   ├── useReconciliationQuery.ts
│   └── useReconciliationMutation.ts
├── pages/
│   ├── ReconciliationListPage.tsx
│   ├── ReconciliationDetailPage.tsx
│   └── ReconciliationCreatePage.tsx
├── services/
│   └── reconciliationApi.ts
├── types/
│   └── reconciliation.types.ts
└── index.ts
```

## 10. Naming Conventions

### 10.1 File Naming

| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `DailyReportCard.tsx` |
| Hooks | camelCase with `use` prefix | `useDailyReportQuery.ts` |
| Services | camelCase with `Api` suffix | `dailyReportsApi.ts` |
| Types | camelCase with `.types.ts` | `dailyReport.types.ts` |
| Utils | camelCase | `stateTransitions.ts` |
| Stores | camelCase with `Store` suffix | `authStore.ts` |
| Pages | PascalCase with `Page` suffix | `DailyReportListPage.tsx` |

### 10.2 Component Naming

```typescript
// Feature components: {Feature}{Descriptor}.tsx
DailyReportCard.tsx
DailyReportList.tsx
DailyReportStatusBadge.tsx

// Shared components: {Descriptor}.tsx
Button.tsx
Input.tsx
StatusBadge.tsx
DataTable.tsx
```

### 10.3 Type Naming

```typescript
// Entity types: PascalCase
interface DailyReport { ... }
interface TopupRequest { ... }

// Request/Response types: {Entity}{Action}Request/Response
interface DailyReportCreateRequest { ... }
interface DailyReportUpdateRequest { ... }
interface DailyReportResponse { ... }

// Status types: {Entity}Status
type DailyReportStatus = 'raw_submitted' | 'trend_pending' | ...;
type TopupRequestStatus = 'draft' | 'pending_review' | ...;
```

## 11. Relation to SoT

| SoT Document | Version | Usage in Frontend |
|--------------|---------|-------------------|
| `STATE_MACHINE.md` | v2.6 | Status types, transition validation, UI state mapping |
| `DATA_SCHEMA.md` | v5.2 | Entity types, field definitions |
| `API_SOT.md` | v9.0 | API endpoints, response formats, error codes |
| `ERROR_CODES_SOT.md` | v2.1 | Error handling, user feedback messages |
| `AUTH_SPEC.md` | v2.0 | Permission checks, role-based rendering |
| `BUSINESS_RULES.md` | v3.1 | Form validation rules, business logic |

## 12. References

### Internal Documents
- [FRONTEND_DEVELOPMENT_RULES.md](../../3.dev-guides/FRONTEND_DEVELOPMENT_RULES.md) v1.0
- [UI_FLOW_SPEC.md](../../3.dev-guides/UI_FLOW_SPEC.md) v1.0
- [UI_DESIGN_SYSTEM.md](../../3.dev-guides/UI_DESIGN_SYSTEM.md) v0.1
- [API_DEVELOPMENT_FLOW.md](../../3.dev-guides/API_DEVELOPMENT_FLOW.md) v0.1

### External References
- [React Documentation](https://react.dev/)
- [TanStack Query](https://tanstack.com/query)
- [Zustand](https://zustand-demo.pmnd.rs/)
- [shadcn/ui](https://ui.shadcn.com/)
- [Tailwind CSS](https://tailwindcss.com/)

---

**Document Summary**:
- **Version**: v1.0
- **Status**: ready_for_production
- **Sections**: 12 major sections
- **Modules Defined**: 4 core modules (daily-reports, topups, ledger, reconciliation)
- **SoT Alignment**: 6 SoT documents referenced with versions
