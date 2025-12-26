# MainTrendChart - 主趋势图

> **复用级别**: :yellow_circle: 模块
> **源码位置**: `frontend/src/features/dashboard/components/MainTrendChart.tsx`
> **最后更新**: 2025-12-22

---

## 1. 概述

MainTrendChart 是一个多指标趋势图组件，支持在消耗/收入/利润/转化之间切换，包含自动生成的数据洞察总结。

**使用场景**:
- 驾驶舱页面的核心趋势展示
- 报表页面的数据可视化
- 与 KPI 卡片联动展示

---

## 2. 接口契约

### 2.1 Props (输入)

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `data` | `TrendDataPoint[]` | :white_check_mark: | - | 趋势数据点数组 |
| `activeMetric` | `MetricType` | :white_check_mark: | - | 当前选中的指标 |
| `onMetricChange` | `(metric: MetricType) => void` | :x: | - | 指标切换回调 |
| `summary` | `string` | :x: | - | AI 生成的数据洞察 |
| `className` | `string` | :x: | - | 额外样式类 |

### 2.2 类型定义

```typescript
export type MetricType = 'spend' | 'revenue' | 'profit' | 'conversions';

export interface TrendDataPoint {
  date: string;       // YYYY-MM-DD 格式
  spend?: number;     // 消耗金额
  revenue?: number;   // 收入金额
  profit?: number;    // 利润金额
  conversions?: number; // 转化数量
}

interface MainTrendChartProps {
  data: TrendDataPoint[];
  activeMetric: MetricType;
  onMetricChange?: (metric: MetricType) => void;
  summary?: string;
  className?: string;
}
```

### 2.3 指标配置

| MetricType | 中文名 | 线条颜色 | 数据单位 |
|------------|--------|---------|---------|
| `spend` | 消耗 | #2563EB (蓝) | 元 (¥) |
| `revenue` | 收入 | #16A34A (绿) | 元 (¥) |
| `profit` | 利润 | #D97706 (橙) | 元 (¥) |
| `conversions` | 粉数 | #7C3AED (紫) | 个 |

---

## 3. 依赖

### 3.1 组件依赖

| 组件 | 来源 | 用途 |
|------|------|------|
| `Card`, `CardHeader`, `CardContent`, `CardTitle` | `@/components/ui/card` | 卡片容器 |
| `Button` | `@/components/ui/button` | 查看明细按钮 |
| `LineChart`, `Line`, `XAxis`, `YAxis`, ... | `recharts` | 图表绑定 |
| `TrendingUp`, `ExternalLink` | `lucide-react` | 图标 |

### 3.2 工具依赖

| 工具 | 来源 | 用途 |
|------|------|------|
| `cn` | `@/lib/utils` | 类名合并 |

---

## 4. 使用示例

### 4.1 基础用法

```tsx
import { MainTrendChart, type TrendDataPoint } from '@/features/dashboard/components/MainTrendChart';

const data: TrendDataPoint[] = [
  { date: '2025-12-15', spend: 100000, revenue: 130000, profit: 30000, conversions: 2500 },
  { date: '2025-12-16', spend: 110000, revenue: 145000, profit: 35000, conversions: 2800 },
  { date: '2025-12-17', spend: 105000, revenue: 140000, profit: 35000, conversions: 2700 },
];

<MainTrendChart
  data={data}
  activeMetric="spend"
/>
```

### 4.2 与 KPI 卡片联动

```tsx
import { useState } from 'react';
import { MainTrendChart, type MetricType } from '@/features/dashboard/components/MainTrendChart';
import { StatCard } from '@/features/dashboard/components/StatCard';

function Dashboard() {
  const [activeMetric, setActiveMetric] = useState<MetricType>('spend');

  return (
    <div className="space-y-6">
      {/* KPI 卡片区 */}
      <div className="grid grid-cols-4 gap-6">
        <StatCard
          title="今日消耗"
          value="¥125,680"
          onClick={() => setActiveMetric('spend')}
          isActive={activeMetric === 'spend'}
          {...otherProps}
        />
        {/* 更多卡片... */}
      </div>

      {/* 趋势图 */}
      <MainTrendChart
        data={trendData}
        activeMetric={activeMetric}
        onMetricChange={setActiveMetric}
        summary="近7日消耗稳定上升，日均增长2.3%"
      />
    </div>
  );
}
```

### 4.3 使用自动总结生成

```tsx
import { MainTrendChart, generateSummary } from '@/features/dashboard/components/MainTrendChart';

const data = [...]; // 趋势数据
const activeMetric = 'spend';

// 自动生成总结文案
const summary = generateSummary(data, activeMetric);

<MainTrendChart
  data={data}
  activeMetric={activeMetric}
  summary={summary}
/>
```

---

## 5. 组合规则

### 5.1 推荐组合

| 组合代码块 | 组合方式 | 效果 |
|-----------|---------|------|
| `StatCard` | 联动 | 点击卡片切换图表指标 |
| `GlobalDateFilter` | 并列 | 时间范围影响图表数据 |
| `TopLists` | 并列 | 从趋势发现 → 归因到项目 |

### 5.2 数据流

```
┌─────────────────┐     点击      ┌─────────────────┐
│   StatCard      │ ─────────────►│ onMetricChange  │
│ (isActive=true) │               │ (setActiveMetric)│
└─────────────────┘               └────────┬────────┘
                                           │
                                           ▼
┌─────────────────┐     activeMetric  ┌─────────────────┐
│   趋势图更新     │◄─────────────────│ MainTrendChart  │
│   (重新渲染)     │                  │                 │
└─────────────────┘                  └─────────────────┘
```

---

## 6. 样式定制

### 6.1 图表配置

| 配置项 | 当前值 | 说明 |
|--------|--------|------|
| 高度 | 320px | ResponsiveContainer height |
| 网格线 | 虚线 3 3 | CartesianGrid strokeDasharray |
| 线条粗细 | 2.5px | Line strokeWidth |
| 数据点 | r=4, 悬浮 r=6 | dot / activeDot |

### 6.2 Y 轴格式化

```typescript
// 金额指标：超过 1 万显示为 "¥Xw"
// 转化指标：超过 1000 显示为 "Xk"
const formatYAxis = (value: number, metric: MetricType) => {
  if (metric === 'conversions') {
    return value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value.toString();
  }
  return value >= 10000
    ? `¥${(value / 10000).toFixed(1)}w`
    : `¥${(value / 1000).toFixed(1)}k`;
};
```

---

## 7. 辅助函数

### 7.1 generateSummary

自动生成数据洞察文案：

```typescript
import { generateSummary } from '@/features/dashboard/components/MainTrendChart';

const summary = generateSummary(data, 'spend');
// 输出: "近 7 天日均消耗 ¥120,000，较首日+15.2%，整体趋势上升。"
```

**生成逻辑**:
1. 计算期间平均值
2. 计算首日到末日的变化率
3. 判断上升/下降趋势
4. 组合成自然语言描述

---

## 8. 测试

### 8.1 测试用例清单

- [ ] 基础渲染：显示图表和标题
- [ ] 指标切换：点击标签切换数据线
- [ ] 空数据：优雅处理空数组
- [ ] 数据更新：数据变化后重新渲染
- [ ] Tooltip：悬浮显示正确数值
- [ ] 总结文案：正确显示 summary
- [ ] 响应式：不同屏幕宽度正常显示

### 8.2 测试示例

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { MainTrendChart } from './MainTrendChart';

const mockData = [
  { date: '2025-12-15', spend: 100000, conversions: 2500 },
  { date: '2025-12-16', spend: 110000, conversions: 2800 },
];

describe('MainTrendChart', () => {
  it('renders chart title', () => {
    render(<MainTrendChart data={mockData} activeMetric="spend" />);
    expect(screen.getByText('核心指标趋势')).toBeInTheDocument();
  });

  it('switches metric on tab click', () => {
    const onMetricChange = jest.fn();
    render(
      <MainTrendChart
        data={mockData}
        activeMetric="spend"
        onMetricChange={onMetricChange}
      />
    );
    fireEvent.click(screen.getByText('收入'));
    expect(onMetricChange).toHaveBeenCalledWith('revenue');
  });

  it('displays summary when provided', () => {
    render(
      <MainTrendChart
        data={mockData}
        activeMetric="spend"
        summary="消耗稳定上升"
      />
    );
    expect(screen.getByText(/消耗稳定上升/)).toBeInTheDocument();
  });
});
```

---

## 9. 源码位置

| 类型 | 路径 |
|------|------|
| 组件 | `frontend/src/features/dashboard/components/MainTrendChart.tsx` |
| 类型 | (内联在组件文件中) |
| 测试 | `frontend/src/features/dashboard/components/__tests__/MainTrendChart.test.tsx` |

---

## 10. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-22 | 初始版本 |

---

## 11. 相关文档

- [A1-dashboard 模块规格书](../../10.module-specs/A1-dashboard.md)
- [StatCard 代码块](../core/stat-card.md)
- [recharts 文档](https://recharts.org/)
