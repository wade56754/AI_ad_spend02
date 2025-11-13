# Bolt.new 页面开发指南

## 🎯 页面开发策略

基于日报管理模块的成功经验，我们采用以下页面开发策略：

### 1. 模板优先
### 2. 复用组件
### 3. 类型安全
### 4. 响应式设计

## 📱 在 Bolt.new 中开发页面

### 1. 页面模板创建

在 Bolt.new 中输入：

```
创建一个 Next.js 页面模板，要求：

1. 使用 App Router (src/app/)
2. TypeScript 类型安全
3. 响应式布局
4. 包含以下部分：
   - 页面标题和面包屑
   - 筛选和搜索栏
   - 操作按钮区域
   - 数据展示区域
   - 分页控制

命名为 PageTemplate，要支持动态标题、自定义操作、数据类型泛型
```

### 2. 生成基础模板

```typescript
// src/app/template/page.tsx
interface PageTemplateProps<T> {
  title: string;
  description?: string;
  breadcrumbs?: { label: string; href: string }[];
  children: React.ReactNode;
  actions?: React.ReactNode;
  filters?: React.ReactNode;
  loading?: boolean;
  error?: string;
}

export function PageTemplate<T>({
  title,
  description,
  breadcrumbs,
  children,
  actions,
  filters,
  loading = false,
  error,
}: PageTemplateProps<T>) {
  // Bolt.new 生成的实现
  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 页面头部 */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">{title}</h1>
          {description && (
            <p className="text-gray-600 mt-1">{description}</p>
          )}
          {breadcrumbs && (
            <nav className="flex mt-2 text-sm">
              {breadcrumbs.map((item, index) => (
                <React.Fragment key={index}>
                  <a href={item.href} className="text-blue-600 hover:text-blue-800">
                    {item.label}
                  </a>
                  {index < breadcrumbs.length - 1 && (
                    <span className="mx-2 text-gray-400">/</span>
                  )}
                </React.Fragment>
              ))}
            </nav>
          )}
        </div>
        {actions && <div className="flex gap-2">{actions}</div>}
      </div>

      {/* 筛选区域 */}
      {filters && (
        <Card>
          <CardContent className="p-4">{filters}</CardContent>
        </Card>
      )}

      {/* 主内容区域 */}
      {loading ? (
        <Card>
          <CardContent className="p-8">
            <div className="flex justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          </CardContent>
        </Card>
      ) : error ? (
        <Card>
          <CardContent className="p-8">
            <div className="text-center text-red-600">
              <p>{error}</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        children
      )}
    </div>
  );
}
```

## 🏠 业务页面开发

### 1. 广告账户管理页面

在 Bolt.new 中输入：

```
基于现有的日报管理页面和 PageTemplate，创建广告账户管理页面：

路由：/ad-accounts

功能要求：
1. 账户列表展示（表格视图 + 卡片视图切换）
2. 高级筛选（状态、项目、渠道、负责人）
3. 搜索功能
4. 批量操作（启用/禁用、分配、删除）
5. 新建/编辑账户弹窗
6. 账户详情页面（包含多个tab）
7. 导入/导出功能
8. 响应式设计

保持与日报管理相同的设计风格和交互模式
```

### 2. 页面结构示例

```typescript
// src/app/ad-accounts/page.tsx
'use client';

import { useState } from 'react';
import { PageTemplate } from '@/components/templates/PageTemplate';
import { AdAccountFilters } from '@/components/ad-accounts/AdAccountFilters';
import { AdAccountTable } from '@/components/ad-accounts/AdAccountTable';
import { Button } from '@/components/ui/button';
import { Plus, Download, Grid, List } from 'lucide-react';

export default function AdAccountsPage() {
  const [filters, setFilters] = useState({
    status: '',
    projectId: '',
    channelId: '',
    assignedUserId: '',
  });
  const [viewMode, setViewMode] = useState<'table' | 'grid'>('table');
  const [selectedItems, setSelectedItems] = useState<number[]>([]);

  return (
    <PageTemplate
      title="广告账户管理"
      description="管理和监控广告账户的状态和表现"
      breadcrumbs={[
        { label: '首页', href: '/dashboard' },
        { label: '广告账户', href: '/ad-accounts' }
      ]}
      actions={
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            导出
          </Button>
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            新建账户
          </Button>
        </div>
      }
      filters={
        <AdAccountFilters
          filters={filters}
          onFiltersChange={setFilters}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
        />
      }
    >
      <AdAccountTable
        filters={filters}
        viewMode={viewMode}
        selectedItems={selectedItems}
        onSelectionChange={setSelectedItems}
      />
    </PageTemplate>
  );
}
```

### 3. 详情页面开发

```typescript
// src/app/ad-accounts/[id]/page.tsx
'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PageTemplate } from '@/components/templates/PageTemplate';
import { AccountInfo } from '@/components/ad-accounts/AccountInfo';
import { AccountPerformance } from '@/components/ad-accounts/AccountPerformance';
import { AccountAlerts } from '@/components/ad-accounts/AccountAlerts';
import { AccountDocuments } from '@/components/ad-accounts/AccountDocuments';

interface PageProps {
  params: { id: string };
}

export default function AccountDetailPage({ params }: PageProps) {
  const accountId = params.id;

  return (
    <PageTemplate
      title={`账户详情 #${accountId}`}
      breadcrumbs={[
        { label: '首页', href: '/dashboard' },
        { label: '广告账户', href: '/ad-accounts' },
        { label: '详情', href: `/ad-accounts/${accountId}` }
      ]}
    >
      <Tabs defaultValue="info" className="space-y-4">
        <TabsList>
          <TabsTrigger value="info">基本信息</TabsTrigger>
          <TabsTrigger value="performance">表现数据</TabsTrigger>
          <TabsTrigger value="alerts">告警记录</TabsTrigger>
          <TabsTrigger value="documents">文档管理</TabsTrigger>
        </TabsList>

        <TabsContent value="info">
          <AccountInfo accountId={accountId} />
        </TabsContent>

        <TabsContent value="performance">
          <AccountPerformance accountId={accountId} />
        </TabsContent>

        <TabsContent value="alerts">
          <AccountAlerts accountId={accountId} />
        </TabsContent>

        <TabsContent value="documents">
          <AccountDocuments accountId={accountId} />
        </TabsContent>
      </Tabs>
    </PageTemplate>
  );
}
```

## 🔍 筛选和搜索组件

### 1. 通用筛选组件

在 Bolt.new 中输入：

```
创建一个通用筛选栏组件，要求：

1. 支持动态筛选条件
2. 支持多种输入类型（文本、选择、日期范围）
3. 支持搜索功能
4. 支持重置功能
5. 支持保存/加载预设
6. 响应式设计
7. TypeScript 类型安全

命名为 FilterBar，支持传入筛选配置数组
```

### 2. 筛选配置

```typescript
// src/components/common/FilterBar.tsx
interface FilterConfig {
  key: string;
  type: 'text' | 'select' | 'date' | 'daterange';
  label: string;
  placeholder?: string;
  options?: { value: string; label: string }[];
  defaultValue?: any;
}

interface FilterBarProps {
  configs: FilterConfig[];
  values: Record<string, any>;
  onChange: (values: Record<string, any>) => void;
  onSearch?: (search: string) => void;
  searchPlaceholder?: string;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  configs,
  values,
  onChange,
  onSearch,
  searchPlaceholder = "搜索...",
}) => {
  // Bolt.new 生成的实现
};
```

## 📱 表单页面

### 1. 表单页面模板

在 Bolt.new 中输入：

```
创建一个通用的表单页面模板：

1. 支持新建和编辑模式
2. 表单验证
3. 步骤指示器（可选）
4. 保存/取消/重置按钮
5. 错误处理
6. 加载状态
7. 成功提示

命名为 FormPage，支持传入表单配置和验证模式
```

### 2. 表单页面结构

```typescript
// src/app/ad-accounts/create/page.tsx
'use client';

import { FormPage } from '@/components/templates/FormPage';
import { AdAccountForm } from '@/components/ad-accounts/AdAccountForm';

export default function CreateAdAccountPage() {
  const handleSave = async (data: AdAccountFormData) => {
    // 保存逻辑
  };

  return (
    <FormPage
      title="新建广告账户"
      subtitle="填写广告账户的基本信息和配置"
      mode="create"
      onSave={handleSave}
    >
      <AdAccountForm mode="create" />
    </FormPage>
  );
}
```

## 📊 仪表板页面

### 1. 仪表板组件

在 Bolt.new 中输入：

```
创建一个仪表板页面组件：

1. 响应式网格布局
2. 关键指标卡片
3. 图表展示（多种类型）
4. 实时数据更新
5. 自定义时间范围
6. 数据导出功能
7. 快速操作

命名为 Dashboard，支持传入指标配置
```

## 🔧 页面开发最佳实践

### 1. 页面状态管理

```typescript
// 使用 Zustand 进行状态管理
interface PageState {
  loading: boolean;
  error: string | null;
  data: any;
  filters: Record<string, any>;
  pagination: {
    page: number;
    pageSize: number;
    total: number;
  };
}

const usePageState = () => {
  return useStore<PageState>((set) => ({
    loading: false,
    error: null,
    data: null,
    filters: {},
    pagination: { page: 1, pageSize: 10, total: 0 },
    setLoading: (loading) => set({ loading }),
    setError: (error) => set({ error }),
    setData: (data) => set({ data }),
    setFilters: (filters) => set({ filters }),
    setPagination: (pagination) => set({ pagination }),
  }));
};
```

### 2. 数据获取模式

```typescript
// 统一的数据获取Hook
const usePageData = <T>(
  endpoint: string,
  filters: Record<string, any> = {},
  pagination?: any
) => {
  return useQuery({
    queryKey: [endpoint, filters, pagination],
    queryFn: async () => {
      const params = new URLSearchParams({ ...filters, ...pagination });
      const response = await api.get(`${endpoint}?${params}`);
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5分钟
  });
};
```

### 3. 错误边界处理

```typescript
// src/components/ErrorBoundary.tsx
import { Component, ErrorInfo, ReactNode } from 'react';

export class ErrorBoundary extends Component<
  { children: ReactNode },
  { state: { hasError: false; error: null; errorInfo: null }
> {
  state = { hasError: false, error: null, errorInfo: null };

  static getDerivedStateFromError(error: Error, errorInfo: ErrorInfo) {
    return { hasError: true, error, errorInfo };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('页面错误:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900">页面出错了</h1>
            <p className="text-gray-600 mt-2">{this.state.error?.message}</p>
            <Button
              className="mt-4"
              onClick={() => window.location.reload()}
            >
              重新加载
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

## 📱 响应式设计模式

### 1. 断点设计

```typescript
// 使用 Tailwind CSS 响应式断点
const responsiveClasses = {
  // 移动端
  mobile: 'sm:hidden',
  // 平板
  tablet: 'hidden lg:block xl:hidden',
  // 桌面
  desktop: 'hidden lg:block'
};
```

### 2. 布局适配

```typescript
// 根据屏幕尺寸显示不同内容
const ResponsiveLayout = () => {
  return (
    <>
      {/* 移动端布局 */}
      <div className="block lg:hidden">
        <MobileLayout />
      </div>

      {/* 桌面端布局 */}
      <div className="hidden lg:block">
        <DesktopLayout />
      </div>
    </>
  );
};
```

## 🎯 下一步开发计划

### 第一周：P0页面
1. **广告账户管理** - 基于现有模板快速开发
2. **对账系统界面** - 复用表格组件
3. **财务管理页面** - 完善现有页面

### 第二周：P1功能
1. **仪表板页面** - 图表和数据可视化
2. **报表分析页面** - 高级分析功能

### 第三周：P2功能
1. **系统设置页面** - 配置管理
2. **用户管理页面** - 权限控制

通过这种方式，我们可以快速构建完整的页面，同时保持代码质量和一致性。