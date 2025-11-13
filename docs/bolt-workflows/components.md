# Bolt.new 组件开发指南

## 🎯 组件开发策略

基于日报管理模块的成功经验，我们采用以下组件开发策略：

### 1. 可复用组件优先
### 2. 组件组合模式
### 3. 类型安全优先

## 🛠️ 在 Bolt.new 中开发组件

### 基础UI组件开发

#### 步骤1：使用模板创建组件
在 Bolt.new 中输入：

```
创建一个React组件，要求：
- 使用TypeScript
- 使用shadcn/ui组件库
- 名称为 DataTable
- 功能：支持分页、排序、筛选的数据表格
- 包含loading状态、空状态处理
- 响应式设计
```

#### 步骤2：生成可复用的DataTable组件
```typescript
// src/components/ui/DataTable.tsx
interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  loading?: boolean;
  pagination?: {
    page: number;
    pageSize: number;
    total: number;
    onPageChange: (page: number) => void;
  };
  onSort?: (column: string, direction: 'asc' | 'desc') => void;
  onFilter?: (filters: Record<string, any>) => void;
  actions?: React.ReactNode;
}

export function DataTable<T>({
  data,
  columns,
  loading = false,
  pagination,
  onSort,
  onFilter,
  actions,
}: DataTableProps<T>) {
  // Bolt.new 生成的实现
}
```

## 📦 业务组件开发

### 1. 广告账户管理组件

在 Bolt.new 中输入：

```
基于现有的日报管理组件，创建广告账户管理组件：

1. AdAccountList - 账户列表组件
   - 显示账户基本信息
   - 支持状态筛选
   - 支持项目筛选
   - 支持批量操作

2. AdAccountCard - 账户卡片组件
   - 显示账户状态
   - 显示关键指标
   - 快速操作按钮

3. AdAccountForm - 账户表单组件
   - 新建/编辑账户
   - 表单验证
   - 支持文件上传

4. AccountStatusBadge - 状态徽章
   - 颜色编码
   - 状态描述

保持与日报管理相同的设计风格和代码结构。
```

### 2. 使用相同的代码模式

```typescript
// 从日报组件中复用的模式
const AdAccountManagement = () => {
  // 1. 状态管理
  const [filters, setFilters] = useState<Filters>({});
  const [selectedItems, setSelectedItems] = useState<number[]>([]);

  // 2. 数据获取
  const { data, loading } = useQuery({
    queryKey: ['ad-accounts', filters],
    queryFn: () => fetchAdAccounts(filters),
  });

  // 3. 事件处理
  const handleBatchAction = useCallback(async (action: string) => {
    // 批量操作逻辑
  }, []);

  // 4. 渲染
  return (
    <Template title="广告账户管理">
      {/* 组件内容 */}
    </Template>
  );
};
```

## 🎨 设计系统组件

### 1. 在 Bolt.new 中创建设计系统

```
创建设计系统组件：

1. StatusBadge - 状态徽章组件
   - 支持多种状态类型
   - 自定义颜色
   - 图标支持

2. ActionButtons - 操作按钮组
   - 查看、编辑、删除
   - 权限控制
   - 批量操作

3. FilterBar - 筛选条件栏
   - 动态筛选条件
   - 重置功能
   - 搜索功能

4. LoadingStates - 加载状态
   - 表格加载
   - 表单提交
   - 页面切换
```

### 2. 保持一致性

```typescript
// src/components/ui/StatusBadge.tsx
interface StatusBadgeProps {
  status: 'active' | 'suspended' | 'pending' | 'archived';
  variant?: 'default' | 'outline';
  showText?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  variant = 'default',
  showText = true,
}) => {
  const statusConfig = {
    active: { color: 'bg-green-100 text-green-800', label: '活跃' },
    suspended: { color: 'bg-yellow-100 text-yellow-800', label: '暂停' },
    pending: { color: 'bg-blue-100 text-blue-800', label: '待处理' },
    archived: { color: 'bg-gray-100 text-gray-800', label: '已归档' },
  };

  const config = statusConfig[status];

  return (
    <Badge className={config.color} variant={variant}>
      {showText && config.label}
    </Badge>
  );
};
```

## 📊 数据可视化组件

### 1. 在 Bolt.new 中创建图表组件

```
创建数据可视化组件：

1. MetricCard - 指标卡片
   - 数值展示
   - 趋势指示器
   - 对比数据

2. SparklineChart - 迷你图
   - 简单的趋势展示
   - 在表格中使用

3. ProgressRing - 进度环
   - 项目进度
   - 完成度
   - 性能指标

4. HeatMap - 热力图
   - 数据密集展示
   - 相关性分析
```

### 2. 使用Recharts模板

```typescript
// src/components/charts/MetricCard.tsx
interface MetricCardProps {
  title: string;
  value: number | string;
  previous?: number;
  trend?: 'up' | 'down' | 'neutral';
  icon?: React.ReactNode;
  format?: (value: number) => string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  previous,
  trend,
  icon,
  format = (v) => v.toString(),
}) => {
  const trendColor = trend === 'up' ? 'text-green-600' :
                   trend === 'down' ? 'text-red-600' :
                   'text-gray-600';

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold">{format(value as number)}</p>
            {previous && (
              <div className={`flex items-center text-sm ${trendColor}`}>
                <TrendingUp className={`w-4 h-4 mr-1 ${
                  trend === 'down' ? 'rotate-180' : ''
                }`} />
                {((value as number - previous) / previous * 100).toFixed(1)}%
              </div>
            )}
          </div>
          {icon && <div className="text-gray-400">{icon}</div>}
        </div>
      </CardContent>
    </Card>
  );
};
```

## 🔄 组件更新和优化

### 1. 使用 Bolt.new 优化现有组件

```
帮我优化现有的 DataTable 组件：

1. 添加虚拟滚动支持（大数据量）
2. 改进筛选功能（多条件组合）
3. 添加导出功能（CSV/Excel）
4. 优化性能（React.memo）
5. 添加更好的空状态设计
6. 增强键盘导航支持
7. 添加列宽调整功能
```

### 2. 组件版本管理

```typescript
// src/components/ui/DataTable/index.ts
export { DataTableV1 } from './DataTable';
export { DataTableV2 } from './DataTableV2';

// 根据配置选择版本
export const DataTable = process.env.USE_ADVANCED_TABLE
  ? DataTableV2
  : DataTableV1;
```

## 🧪 组件测试

### 1. 在 Bolt.new 中生成测试

```
为 StatusBadge 组件编写单元测试：

要求：
- 使用 Jest + React Testing Library
- 测试所有状态类型
- 测试不同变体
- 测试快照
- 测试可访问性
- 覆盖率要求 > 90%
```

### 2. 组件文档

```
为 AdAccountList 组件创建文档：

1. 组件描述
2. Props 接口文档
3. 使用示例
4. 最佳实践
5. 常见问题
6. 故障排除
```

## 📚 组件库使用

### 1. 在 Bolt.new 中使用组件

```
如何使用我们创建的组件：

1. 导入DataTable组件创建用户列表页面：
   - 显示用户数据
   - 支持搜索和筛选
   - 支持批量操作

2. 结合StatusBadge和ActionButtons：
   - 在表格中显示用户状态
   - 提供编辑和删除操作

3. 使用MetricCard创建仪表板：
   - 显示关键指标
   - 展示趋势变化
   - 实时数据更新
```

### 2. 组件组合示例

```typescript
// 使用示例
const UserManagement = () => {
  return (
    <div className="space-y-4">
      <div className="flex justify-between">
        <h1>用户管理</h1>
        <Button>新建用户</Button>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-4">
        <MetricCard title="总用户数" value={1234} trend="up" icon={<Users />} />
        <MetricCard title="活跃用户" value={987} trend="up" icon={<UserCheck />} />
      </div>

      <DataTable
        columns={userColumns}
        data={users}
        loading={loading}
        onRowClick={handleRowClick}
        actions={
          <Button onClick={handleBatchDelete} disabled={!selectedItems.length}>
            批量删除
          </Button>
        }
      />
    </div>
  );
};
```

## 🎯 下一步计划

1. **完成基础组件库**（1-2天）
2. **开发广告账户组件**（2-3天）
3. **开发对账系统组件**（2-3天）
4. **优化和测试**（1天）

通过这种方式，我们可以快速构建一个高质量、可复用的组件库，大大提高开发效率。