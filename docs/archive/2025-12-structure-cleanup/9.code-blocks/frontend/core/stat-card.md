# StatCard - KPI 统计卡片

> **复用级别**: :red_circle: 核心
> **源码位置**: `frontend/src/features/dashboard/components/StatCard.tsx`
> **最后更新**: 2025-12-22

---

## 1. 概述

StatCard 是用于展示单个 KPI 指标的卡片组件，支持主数值、变化趋势、7日均值、目标说明等多层信息展示，并支持与趋势图联动。

**使用场景**:
- 驾驶舱页面的核心 KPI 展示
- 资金总览的汇总数据展示
- 项目盈亏看板的关键指标

---

## 2. 接口契约

### 2.1 Props (输入)

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `title` | `string` | :white_check_mark: | - | 指标标题，如"今日消耗" |
| `value` | `string \| number` | :white_check_mark: | - | 主数值，已格式化的显示值 |
| `change` | `number \| null` | :x: | - | 较昨日变化百分比 |
| `average7d` | `string \| number` | :x: | - | 7日均值 |
| `target` | `string` | :x: | - | 目标/预算说明 |
| `icon` | `ReactNode` | :white_check_mark: | - | 左上角图标 |
| `color` | `StatCardColor` | :white_check_mark: | - | 主题色 |
| `onClick` | `() => void` | :x: | - | 点击回调（联动趋势图） |
| `isActive` | `boolean` | :x: | `false` | 是否选中状态 |
| `testId` | `string` | :x: | - | 测试用 data-testid |

### 2.2 类型定义

```typescript
export type StatCardColor = 'blue' | 'green' | 'purple' | 'orange' | 'red';

export interface StatCardProps {
  title: string;
  value: string | number;
  change?: number | null;
  average7d?: string | number;
  target?: string;
  icon: React.ReactNode;
  color: StatCardColor;
  onClick?: () => void;
  isActive?: boolean;
  testId?: string;
}
```

### 2.3 颜色映射

| color 值 | 图标背景 | 激活边框 | 使用场景 |
|---------|---------|---------|---------|
| `blue` | blue-100 | blue-500 | 消耗类指标 |
| `green` | green-100 | green-500 | 收入类指标 |
| `purple` | violet-100 | violet-500 | 转化类指标 |
| `orange` | amber-100 | amber-500 | 利润类指标 |
| `red` | red-100 | red-500 | 警告类指标 |

---

## 3. 依赖

### 3.1 组件依赖

| 组件 | 来源 | 用途 |
|------|------|------|
| `Card`, `CardContent` | `@/components/ui/card` | 卡片容器 |
| `TrendingUp`, `TrendingDown` | `lucide-react` | 趋势箭头图标 |

### 3.2 工具依赖

| 工具 | 来源 | 用途 |
|------|------|------|
| `cn` | `@/lib/utils` | 类名合并 |

---

## 4. 使用示例

### 4.1 基础用法

```tsx
import { StatCard } from '@/features/dashboard/components/StatCard';
import { DollarSign } from 'lucide-react';

<StatCard
  title="今日消耗"
  value="¥125,680.50"
  icon={<DollarSign className="h-6 w-6" />}
  color="blue"
/>
```

### 4.2 完整用法（带变化、均值、目标）

```tsx
import { StatCard } from '@/features/dashboard/components/StatCard';
import { DollarSign } from 'lucide-react';

<StatCard
  title="今日消耗"
  value="¥125,680.50"
  change={12.5}
  average7d="¥118,000"
  target="预算 ¥100k-130k"
  icon={<DollarSign className="h-6 w-6" />}
  color="blue"
  testId="dashboard-stat-card-spend"
/>
```

### 4.3 联动趋势图（可点击）

```tsx
import { StatCard } from '@/features/dashboard/components/StatCard';
import { DollarSign, Users, BarChart3, Target } from 'lucide-react';

function Dashboard() {
  const [activeMetric, setActiveMetric] = useState<'spend' | 'conversions' | 'revenue' | 'profit'>('spend');

  return (
    <div className="grid grid-cols-4 gap-6">
      <StatCard
        title="今日消耗"
        value="¥125,680.50"
        change={12.5}
        icon={<DollarSign className="h-6 w-6" />}
        color="blue"
        onClick={() => setActiveMetric('spend')}
        isActive={activeMetric === 'spend'}
      />
      <StatCard
        title="今日粉数"
        value="3,256"
        change={8.3}
        icon={<Users className="h-6 w-6" />}
        color="purple"
        onClick={() => setActiveMetric('conversions')}
        isActive={activeMetric === 'conversions'}
      />
      {/* ... 更多卡片 */}
    </div>
  );
}
```

### 4.4 负变化展示

```tsx
<StatCard
  title="今日利润"
  value="¥-5,680.50"
  change={-15.2}  // 负数会显示红色下降箭头
  icon={<Target className="h-6 w-6" />}
  color="red"
/>
```

---

## 5. 组合规则

### 5.1 推荐组合

| 组合代码块 | 组合方式 | 效果 |
|-----------|---------|------|
| `MainTrendChart` | 并列 + 联动 | 点击卡片切换趋势图指标 |
| `PageHeader` | 容器包裹 | 提供标题区域 |
| `GlobalDateFilter` | 并列 | 时间范围影响卡片数据 |

### 5.2 网格布局建议

```tsx
// 4 列布局（Desktop）
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
  <StatCard ... />
  <StatCard ... />
  <StatCard ... />
  <StatCard ... />
</div>
```

---

## 6. 样式定制

### 6.1 尺寸变体

当前组件内边距固定为 `p-6`，如需调整可通过外层容器控制。

### 6.2 深色模式

组件已内置深色模式支持：
- 图标背景: `dark:bg-{color}-950/30`
- 文字颜色: `dark:text-{color}-400`
- 边框: 自动适配

---

## 7. 测试

### 7.1 测试文件位置

```
frontend/src/features/dashboard/components/__tests__/StatCard.test.tsx
```

### 7.2 测试用例清单

- [x] 基础渲染：显示标题和数值
- [x] 正变化：显示绿色上升箭头
- [x] 负变化：显示红色下降箭头
- [x] 无变化：不显示趋势指示器
- [x] 点击事件：触发 onClick
- [x] 激活状态：显示边框高亮
- [x] 7日均值：正确显示
- [x] 目标说明：正确显示

### 7.3 测试示例

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { StatCard } from './StatCard';
import { DollarSign } from 'lucide-react';

describe('StatCard', () => {
  it('renders title and value', () => {
    render(
      <StatCard
        title="今日消耗"
        value="¥100"
        icon={<DollarSign />}
        color="blue"
      />
    );
    expect(screen.getByText('今日消耗')).toBeInTheDocument();
    expect(screen.getByText('¥100')).toBeInTheDocument();
  });

  it('shows positive change with green indicator', () => {
    render(
      <StatCard
        title="消耗"
        value="¥100"
        change={10.5}
        icon={<DollarSign />}
        color="blue"
      />
    );
    expect(screen.getByText('10.5%')).toHaveClass('text-green-700');
  });

  it('triggers onClick when clicked', () => {
    const handleClick = jest.fn();
    render(
      <StatCard
        title="消耗"
        value="¥100"
        icon={<DollarSign />}
        color="blue"
        onClick={handleClick}
      />
    );
    fireEvent.click(screen.getByText('消耗').closest('div')!);
    expect(handleClick).toHaveBeenCalled();
  });
});
```

---

## 8. 源码位置

| 类型 | 路径 |
|------|------|
| 组件 | `frontend/src/features/dashboard/components/StatCard.tsx` |
| Skeleton | `frontend/src/features/dashboard/components/StatCardSkeleton.tsx` |
| 类型 | (内联在组件文件中) |
| 测试 | `frontend/src/features/dashboard/components/__tests__/StatCard.test.tsx` |

---

## 9. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-22 | 初始版本，包含完整功能 |

---

## 10. 相关文档

- [A1-dashboard 模块规格书](../../10.module-specs/A1-dashboard.md)
- [UI 设计规范](../../3.dev-guides/FRONTEND_STYLE_GUIDE_v2.0.md)
