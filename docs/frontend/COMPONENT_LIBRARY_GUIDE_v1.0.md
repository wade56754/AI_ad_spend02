# 前端组件库使用指南 v1.1

> 本文档描述了 AI_ad_spend02 项目前端基础组件库的使用方法、最佳实践和迁移指南。
>
> **更新日期**: 2025-12-05
> **基准**: FRONTEND_STYLE_GUIDE v2.3

## 📚 目录

- [组件分类](#组件分类)
- [Dashboard 专用组件](#dashboard-专用组件)
- [基础 UI 组件](#基础-ui-组件)
- [数据状态组件](#数据状态组件)
- [布局组件](#布局组件)
- [已废弃组件](#已废弃组件)
- [使用示例](#使用示例)

---

## 组件分类

### 1. 基础 UI 组件 (`frontend/components/ui/`)

标准的基础 UI 组件，基于 Radix UI + Tailwind CSS 实现。

#### 布局类
- `card` - 卡片容器
- `separator` - 分隔符
- `scroll-area` - 滚动区域
- `sheet` - 侧边抽屉
- `sidebar` - 侧边栏

#### 表单类
- `button` - 按钮 ⭐ **推荐使用标准 Button**
- `input` - 输入框
- `textarea` - 文本域
- `select` - 选择器
- `checkbox` - 复选框
- `switch` - 开关
- `label` - 标签
- `calendar` - 日历

#### 反馈类
- `alert` - 警告提示
- `alert-dialog` - 确认对话框 ⭐ **新增组件**
- `dialog` - 对话框
- `popover` - 弹出框
- `tooltip` - 工具提示
- `progress` - 进度条
- `skeleton` - 骨架屏

#### 导航类
- `tabs` - 标签页
- `breadcrumb` - 面包屑
- `dropdown-menu` - 下拉菜单

#### 数据展示类
- `table` - 表格
- `badge` - 徽章
- `avatar` - 头像
- `collapsible` - 折叠面板

### 2. 数据状态组件 (`frontend/components/ui/data-state/`)

统一的数据状态管理组件族，用于处理加载、成功、错误、空状态。

#### 核心组件
- `DataStateProvider` - 数据状态上下文提供者
- `DataStateManager` - 数据状态管理器
- `LoadingState` - 加载状态组件
- `EmptyState` - 空状态组件
- `ErrorState` - 错误状态组件

#### 使用场景

**列表页**:
```tsx
import { DataStateProvider, useDataState } from '@/components/ui/data-state';

function ListPage() {
  const { state, setLoading, setSuccess, setError } = useDataState();
  
  // 加载数据
  useEffect(() => {
    setLoading();
    fetchData().then(setSuccess).catch(setError);
  }, []);
  
  if (state.status === 'loading') return <LoadingState />;
  if (state.status === 'error') return <ErrorState error={state.error} />;
  if (state.status === 'empty') return <EmptyState />;
  
  return <DataList data={state.data} />;
}
```

**详情页**:
```tsx
function DetailPage({ id }) {
  const { state } = useDataState();
  
  // 使用 DataStateManager 自动处理状态
  return (
    <DataStateManager
      fetchFn={() => fetchDetail(id)}
      renderSuccess={(data) => <DetailContent data={data} />}
      renderLoading={() => <LoadingState />}
      renderError={(error) => <ErrorState error={error} />}
    />
  );
}
```

**Dashboard 页**:
```tsx
function DashboardPage() {
  return (
    <DataStateProvider>
      <KpiCards /> {/* 使用 MetricCard 显示指标 */}
      <TrendSection /> {/* 使用图表组件 */}
      <TodayTasksCard /> {/* 使用卡片组件 */}
    </DataStateProvider>
  );
}
```

### 3. 布局组件 (`frontend/components/layout/`)

- `app-sidebar` - 应用侧边栏
- `Header` - 页面头部
- `page-container` - 页面容器
- `providers` - 全局 Provider 配置

### 4. Dashboard 专用组件 (`frontend/src/modules/dashboard/`)

Dashboard 首页使用模块化组件架构，位于 `src/modules/dashboard/` 目录：

```
frontend/src/modules/dashboard/
├── components/
│   ├── index.ts                    # Barrel export
│   ├── DashboardKpiRow.tsx         # KPI 指标卡片行
│   ├── DashboardTrendSection.tsx   # 趋势图表区（组合图）
│   ├── DashboardRiskPanel.tsx      # 风险预警面板
│   ├── DashboardTodayTasks.tsx     # 今日待办列表
│   └── DashboardFundsOverview.tsx  # 资金概览卡片
├── data/
│   └── mock-data.ts                # 模拟数据
└── types/
    └── index.ts                    # 类型定义
```

---

## Dashboard 专用组件

### DashboardKpiRow - KPI 指标行 ⭐ 新增

用于 Dashboard 顶部显示关键业务指标，支持 Primary/Secondary 两级优先级。

#### 导入方式

```tsx
import { DashboardKpiRow } from '@/modules/dashboard/components';
```

#### 基本用法

```tsx
import { DollarSign, TrendingUp, AlertTriangle, FileText } from 'lucide-react';

const metrics: KpiMetric[] = [
  {
    id: 'total_spend',
    title: '今日消耗',
    value: '$12,345',
    change: 12.5,
    changeType: 'up',
    icon: DollarSign,
    priority: 'primary',
  },
  {
    id: 'pending_reports',
    title: '待处理日报',
    value: '3',
    icon: FileText,
    priority: 'secondary',
  },
];

<DashboardKpiRow metrics={metrics} />
```

#### Props

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `metrics` | `KpiMetric[]` | 是 | KPI 指标数组 |
| `className` | `string` | 否 | 自定义类名 |

#### KpiMetric 类型

```tsx
interface KpiMetric {
  id: string;
  title: string;
  value: string;
  change?: number;           // 变化百分比
  changeType?: 'up' | 'down' | 'neutral';
  icon: LucideIcon;
  description?: string;
  priority: 'primary' | 'secondary';
}
```

### DashboardTrendSection - 趋势图表 ⭐ 新增

显示消耗与 ROI 的双轴组合图（柱状图 + 折线图），支持时间范围切换。

```tsx
import { DashboardTrendSection } from '@/modules/dashboard/components';

<DashboardTrendSection data={chartData} />
```

#### Props

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `data` | `TrendChartData[]` | 是 | 图表数据 |
| `className` | `string` | 否 | 自定义类名 |

#### 颜色配置

图表颜色使用 `@/lib/theme-colors.ts` 中的 `TOKENS` 对象：

```tsx
import { TOKENS, CHART_COLORS } from '@/lib/theme-colors';

// 图表中使用
<CartesianGrid stroke={CHART_COLORS.grid} />
<Bar fill={TOKENS.accent.primary} />
<Line stroke={TOKENS.status.success} />
```

### DashboardRiskPanel - 风险预警面板 ⭐ 新增

紧凑列表展示风险预警，支持 critical/warning 两级优先级。

```tsx
import { DashboardRiskPanel } from '@/modules/dashboard/components';

<DashboardRiskPanel
  alerts={alerts}
  onViewAll={() => navigate('/alerts')}
  onAlertClick={(alert) => handleAlert(alert)}
/>
```

#### 视觉特征

- 左侧彩色边框标识优先级（`border-l-4 border-danger` 或 `border-warning`）
- P0/P1 Badge 标签
- 悬停效果 `hover:bg-elevated/80`

### DashboardTodayTasks - 今日待办 ⭐ 新增

双列布局展示待办任务，包含进度条和快捷操作按钮。

```tsx
import { DashboardTodayTasks } from '@/modules/dashboard/components';

<DashboardTodayTasks
  tasks={tasks}
  onTaskClick={(task) => viewTask(task)}
  onHandleTask={(task) => handleTask(task)}
/>
```

#### 视觉特征

- 双列网格 `grid-cols-1 md:grid-cols-2`
- 优先级指示点（red/warning/gray）
- 顶部进度条显示完成度

### DashboardFundsOverview - 资金概览 ⭐ 新增

嵌套卡片布局展示资金池状态，包含余额、待审核充值等信息。

```tsx
import { DashboardFundsOverview } from '@/modules/dashboard/components';

<DashboardFundsOverview
  data={fundsData}
  onTopupClick={() => navigate('/topups')}
/>
```

---

## 基础 UI 组件

### AlertDialog - 确认对话框 ⭐ 新增

用于需要用户确认的操作，如删除、重要操作等。

#### 安装依赖

```bash
pnpm add @radix-ui/react-alert-dialog
```

#### 基本用法

```tsx
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

function DeleteButton() {
  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="destructive">删除</Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>确认删除</AlertDialogTitle>
          <AlertDialogDescription>
            此操作无法撤销。这将永久删除该账户及其所有数据。
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>取消</AlertDialogCancel>
          <AlertDialogAction onClick={handleDelete}>确认删除</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
```

#### 完整示例（AdAccountTable 使用场景）

```tsx
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

function AccountActions({ accountId }) {
  const [open, setOpen] = useState(false);
  
  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>确认删除账户</AlertDialogTitle>
          <AlertDialogDescription>
            删除后无法恢复，请谨慎操作。
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>取消</AlertDialogCancel>
          <AlertDialogAction
            onClick={() => {
              handleDelete(accountId);
              setOpen(false);
            }}
          >
            确认删除
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
```

### Button - 按钮 ⭐ 推荐使用

标准按钮组件，支持多种变体和尺寸。

```tsx
import { Button } from "@/components/ui/button";

// 基础用法
<Button>点击我</Button>

// 变体
<Button variant="default">默认</Button>
<Button variant="destructive">危险操作</Button>
<Button variant="outline">轮廓</Button>
<Button variant="secondary">次要</Button>
<Button variant="ghost">幽灵</Button>
<Button variant="link">链接</Button>

// 尺寸
<Button size="sm">小</Button>
<Button size="default">默认</Button>
<Button size="lg">大</Button>
<Button size="icon">图标</Button>
```

### MetricCard - 指标卡片

用于 Dashboard 显示关键指标。

```tsx
import { MetricCard } from "@/components/ui/MetricCard";

<MetricCard
  title="总消费"
  value="¥12,345"
  change={12.5}
  trend="up"
  icon={<DollarSign />}
/>
```

---

## 已废弃组件

以下组件已被标记为 `@deprecated`，请使用推荐的替代方案：

### ❌ OptimizedButton

**状态**: Deprecated
**文件位置**: `frontend/components/ui/optimized-button.tsx`
**替代**: `Button` from `@/components/ui/button`

**迁移**:
```tsx
// ❌ 旧代码
import { OptimizedButton } from '@/components/ui/optimized-button';
<OptimizedButton variant="primary">点击</OptimizedButton>

// ✅ 新代码
import { Button } from '@/components/ui/button';
<Button variant="default">点击</Button>
```

### ❌ OptimizedMetricCard

**状态**: Deprecated
**文件位置**: `frontend/components/ui/optimized-metric-card.tsx`
**替代**: `DashboardKpiRow` from `@/modules/dashboard/components`

**迁移**:
```tsx
// ❌ 旧代码
import { OptimizedMetricCard } from '@/components/ui/optimized-metric-card';
<OptimizedMetricCard title="消耗" value="$12,345" />

// ✅ 新代码
import { DashboardKpiRow } from '@/modules/dashboard/components';
<DashboardKpiRow metrics={[{ id: 'spend', title: '消耗', value: '$12,345', ... }]} />
```

### ❌ ModernDashboard

**状态**: Deprecated
**文件位置**: `frontend/components/ui/modern-dashboard.tsx`
**替代**: 使用 Dashboard 模块化组件

**迁移**:
```tsx
// ❌ 旧代码
import { ModernDashboard } from '@/components/ui/modern-dashboard';
<ModernDashboard data={dashboardData} />

// ✅ 新代码
import {
  DashboardKpiRow,
  DashboardTrendSection,
  DashboardRiskPanel,
  DashboardTodayTasks,
  DashboardFundsOverview
} from '@/modules/dashboard/components';

// 组合使用各模块化组件
<DashboardKpiRow metrics={kpiMetrics} />
<DashboardTrendSection data={chartData} />
<DashboardRiskPanel alerts={alerts} />
```

### ❌ OptimizedDashboard

**状态**: Deprecated
**文件位置**: `frontend/components/ui/optimized-dashboard.tsx`
**替代**: 与 ModernDashboard 相同，使用 `@/modules/dashboard` 中的模块化组件

### ❌ MetricCard (components/ui/)

**状态**: Deprecated（仅限 `components/ui/MetricCard.tsx`）
**文件位置**: `frontend/components/ui/MetricCard.tsx`
**替代**: `DashboardKpiRow` from `@/modules/dashboard/components`

**说明**: 旧版 MetricCard 是单独的指标卡片组件。新版 Dashboard 使用 `DashboardKpiRow` 统一管理 KPI 卡片的布局和样式。

### ❌ TodayTasksCard

**状态**: Deprecated
**文件位置**: `frontend/components/dashboard/TodayTasksCard.tsx`
**替代**: `DashboardTodayTasks` from `@/modules/dashboard/components`

### 废弃组件清理计划

| 组件 | 当前状态 | 计划删除版本 |
|------|----------|--------------|
| `optimized-button.tsx` | Deprecated | v2.0 |
| `optimized-metric-card.tsx` | Deprecated | v2.0 |
| `modern-dashboard.tsx` | Deprecated | v2.0 |
| `optimized-dashboard.tsx` | Deprecated | v2.0 |
| `MetricCard.tsx` | Deprecated | v2.0 |
| `TodayTasksCard.tsx` | Deprecated | v2.0 |

> **注意**: 在删除前请确保所有页面已迁移到新组件。使用 `git grep` 检查组件引用。

---

## 使用示例

### 完整的列表页示例

```tsx
'use client';

import { useState, useEffect } from 'react';
import { DataStateProvider, useDataState, LoadingState, ErrorState, EmptyState } from '@/components/ui/data-state';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

function AccountList() {
  const { state, setLoading, setSuccess, setError } = useDataState();
  const [deleteId, setDeleteId] = useState<string | null>(null);

  useEffect(() => {
    setLoading();
    fetchAccounts()
      .then(setSuccess)
      .catch(setError);
  }, []);

  if (state.status === 'loading') return <LoadingState />;
  if (state.status === 'error') return <ErrorState error={state.error} />;
  if (state.status === 'empty') return <EmptyState message="暂无账户" />;

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>账户名称</TableHead>
            <TableHead>操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {state.data.map((account) => (
            <TableRow key={account.id}>
              <TableCell>{account.name}</TableCell>
              <TableCell>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setDeleteId(account.id)}
                >
                  删除
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              此操作无法撤销。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={() => handleDelete(deleteId)}>
              确认删除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

export default function AccountListPage() {
  return (
    <DataStateProvider>
      <AccountList />
    </DataStateProvider>
  );
}
```

---

## 最佳实践

### 1. 组件导入

统一使用命名导入：
```tsx
// ✅ 推荐
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';

// ❌ 不推荐
import Button from '@/components/ui/button';
```

### 2. 数据状态管理

- 列表页：使用 `DataStateProvider` + `useDataState` Hook
- 详情页：使用 `DataStateManager` 组件
- Dashboard：直接使用 `MetricCard`、`KpiCards` 等组件

### 3. 错误处理

使用统一的 `ErrorState` 组件，而不是自定义错误 UI：
```tsx
// ✅ 推荐
if (state.status === 'error') {
  return <ErrorState error={state.error} />;
}

// ❌ 不推荐
if (error) {
  return <div>出错了: {error}</div>;
}
```

### 4. 加载状态

使用 `LoadingState` 或 `Skeleton` 组件：
```tsx
// ✅ 推荐
if (loading) return <LoadingState />;
// 或
if (loading) return <Skeleton className="h-10 w-full" />;

// ❌ 不推荐
if (loading) return <div>加载中...</div>;
```

---

## 组件版本

- **v1.1.0** (2025-12-05): Dashboard 组件重构
  - 新增 Dashboard 专用组件节（5 个模块化组件）
  - 新增 `DashboardKpiRow` 组件及类型定义
  - 新增 `DashboardTrendSection` 组件（Recharts 集成）
  - 新增 `DashboardRiskPanel` 组件（风险预警）
  - 新增 `DashboardTodayTasks` 组件（今日待办）
  - 新增 `DashboardFundsOverview` 组件（资金概览）
  - 扩展已废弃组件列表（6 个组件）
  - 新增废弃组件清理计划表
  - 对齐 FRONTEND_STYLE_GUIDE v2.3

- **v1.0.0** (2025-01-XX): 初始版本
  - 新增 `alert-dialog` 组件
  - 标记废弃组件
  - 完善文档

---

## 参考资源

- [shadcn/ui 组件库](https://ui.shadcn.com/)
- [Radix UI 文档](https://www.radix-ui.com/)
- [Tailwind CSS 文档](https://tailwindcss.com/)
- [FRONTEND_STYLE_GUIDE v2.3](../3.dev-guides/FRONTEND_STYLE_GUIDE_v2.3.md)
- [FRONTEND_MODULE_SHELL_PATTERN v1.0](./FRONTEND_MODULE_SHELL_PATTERN_v1.0.md)

