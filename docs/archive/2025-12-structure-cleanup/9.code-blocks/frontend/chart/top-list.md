# TopLists - Top N 归因列表

> **复用级别**: :yellow_circle: 模块
> **源码位置**: `frontend/src/features/dashboard/components/TopLists.tsx`
> **最后更新**: 2025-12-22

---

## 1. 概述

TopLists 是一个展示 Top N 计划/项目列表的组件，用于打通"数据 → 归因对象 → 行动"闭环。支持消耗 Top 和 ROAS 最差两种排行。

**使用场景**:
- 驾驶舱页面：快速定位高消耗/低效项目
- 项目盈亏看板：识别需要关注的项目
- 报表页面：详细分析

---

## 2. 接口契约

### 2.1 Props (输入)

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `topSpendCampaigns` | `CampaignData[]` | :white_check_mark: | - | 消耗 Top N 数据 |
| `worstROASCampaigns` | `CampaignData[]` | :white_check_mark: | - | ROAS 最差 Top N 数据 |
| `className` | `string` | :x: | - | 额外样式类 |

### 2.2 类型定义

```typescript
export interface CampaignData {
  id: string;
  name: string;
  accountName: string;
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  roas: number;
  status: 'active' | 'paused' | 'pending';
}

interface TopListsProps {
  topSpendCampaigns: CampaignData[];
  worstROASCampaigns: CampaignData[];
  className?: string;
}
```

### 2.3 状态配置

| status 值 | 中文名 | 徽章样式 | 颜色点 |
|----------|--------|---------|--------|
| `active` | 投放中 | default | 绿色 |
| `paused` | 已暂停 | secondary | 灰色 |
| `pending` | 待审核 | outline | 黄色 |

---

## 3. 依赖

### 3.1 组件依赖

| 组件 | 来源 | 用途 |
|------|------|------|
| `Card`, `CardHeader`, `CardContent`, `CardTitle` | `@/components/ui/card` | 卡片容器 |
| `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell` | `@/components/ui/table` | 表格 |
| `Badge` | `@/components/ui/badge` | 状态徽章 |
| `Button` | `@/components/ui/button` | 查看全部按钮 |
| `ExternalLink`, `TrendingUp`, `TrendingDown` | `lucide-react` | 图标 |

### 3.2 工具依赖

| 工具 | 来源 | 用途 |
|------|------|------|
| `formatCurrency`, `formatNumber` | `../utils/formatters` | 数值格式化 |

---

## 4. 使用示例

### 4.1 基础用法

```tsx
import { TopLists, type CampaignData } from '@/features/dashboard/components/TopLists';

const topSpend: CampaignData[] = [
  {
    id: 'camp001',
    name: '618大促-爆款商品A',
    accountName: 'FB-品牌主账户',
    spend: 45680,
    impressions: 2350000,
    clicks: 12500,
    conversions: 856,
    roas: 2.35,
    status: 'active',
  },
  // ... 更多数据
];

const worstROAS: CampaignData[] = [
  // ... ROAS 最差的项目
];

<TopLists
  topSpendCampaigns={topSpend}
  worstROASCampaigns={worstROAS}
/>
```

### 4.2 使用 Mock 数据生成器

```tsx
import { TopLists, generateMockTopLists } from '@/features/dashboard/components/TopLists';

function Dashboard() {
  const topListsData = useMemo(() => generateMockTopLists(), []);

  return (
    <TopLists
      topSpendCampaigns={topListsData.topSpend}
      worstROASCampaigns={topListsData.worstROAS}
    />
  );
}
```

### 4.3 结合时间筛选

```tsx
import { TopLists } from '@/features/dashboard/components/TopLists';
import { useTopProjects } from '@/features/dashboard/hooks/useTopProjects';

function Dashboard() {
  const { dateRange } = useGlobalFilters();
  const { data: topLists, isLoading } = useTopProjects(dateRange);

  if (isLoading) return <Skeleton />;

  return (
    <TopLists
      topSpendCampaigns={topLists?.topSpend || []}
      worstROASCampaigns={topLists?.worstROAS || []}
    />
  );
}
```

---

## 5. 表格列定义

### 5.1 消耗 Top 列表

| # | 列名 | 字段 | 对齐 | 格式化 |
|---|------|------|------|--------|
| 1 | # | index + 1 | 左 | - |
| 2 | 计划名称 | name | 左 | 截断 200px |
| 3 | 所属账户 | accountName | 左 | - |
| 4 | 消耗 | spend | 右 | formatCurrency |
| 5 | 展现 | impressions | 右 | formatNumber |
| 6 | 点击 | clicks | 右 | formatNumber |
| 7 | 转化 | conversions | 右 | formatNumber |
| 8 | ROAS | roas | 右 | 2位小数 + 颜色 |
| 9 | 状态 | status | 中 | Badge |
| 10 | 操作 | - | 右 | 跳转按钮 |

### 5.2 ROAS 颜色规则

```typescript
const roasColor =
  roas >= 1.8 ? 'text-green-600' :  // 良好
  roas >= 1.2 ? 'text-yellow-600' : // 一般
  'text-red-600';                    // 差
```

---

## 6. 组合规则

### 6.1 推荐组合

| 组合代码块 | 组合方式 | 效果 |
|-----------|---------|------|
| `MainTrendChart` | 并列 | 趋势 → 归因 → 详情 |
| `StatCard` | 上下 | KPI 概览 → Top 列表 |
| `GlobalDateFilter` | 联动 | 时间范围影响列表数据 |

### 6.2 布局建议

```tsx
// 驾驶舱布局：两个 Top 列表垂直排列
<div className="space-y-6">
  <TopLists
    topSpendCampaigns={...}
    worstROASCampaigns={...}
  />
</div>

// 也可以自定义布局
<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
  {/* 单独使用消耗 Top */}
  <TopSpendCard campaigns={topSpend} />
  {/* 单独使用 ROAS 最差 */}
  <WorstROASCard campaigns={worstROAS} />
</div>
```

---

## 7. 跳转链接

| 位置 | 链接 | 说明 |
|------|------|------|
| 消耗 Top "查看全部" | `/projects?sort=spend&order=desc` | 按消耗降序 |
| ROAS 最差 "查看全部" | `/projects?sort=roas&order=asc` | 按 ROAS 升序 |
| 单行"操作"按钮 | `/projects/{id}` | 项目详情 |

---

## 8. 辅助函数

### 8.1 generateMockTopLists

生成测试用的 Mock 数据：

```typescript
import { generateMockTopLists } from '@/features/dashboard/components/TopLists';

const { topSpend, worstROAS } = generateMockTopLists();
// topSpend: 按消耗降序排列的前 5 条
// worstROAS: 按 ROAS 升序排列的前 5 条
```

---

## 9. 测试

### 9.1 测试用例清单

- [ ] 基础渲染：显示两个卡片标题
- [ ] 数据展示：正确显示表格数据
- [ ] 空数据：显示"暂无数据"提示
- [ ] ROAS 颜色：根据值显示正确颜色
- [ ] 状态徽章：正确显示不同状态
- [ ] 跳转链接：点击操作按钮跳转正确

### 9.2 测试示例

```tsx
import { render, screen } from '@testing-library/react';
import { TopLists } from './TopLists';

const mockData = [
  {
    id: '1',
    name: '测试计划',
    accountName: '测试账户',
    spend: 10000,
    impressions: 100000,
    clicks: 5000,
    conversions: 100,
    roas: 1.5,
    status: 'active' as const,
  },
];

describe('TopLists', () => {
  it('renders both top lists', () => {
    render(
      <TopLists
        topSpendCampaigns={mockData}
        worstROASCampaigns={mockData}
      />
    );
    expect(screen.getByText('今日消耗 Top 5 计划')).toBeInTheDocument();
    expect(screen.getByText('ROAS 最差 Top 5 计划')).toBeInTheDocument();
  });

  it('displays campaign data correctly', () => {
    render(
      <TopLists
        topSpendCampaigns={mockData}
        worstROASCampaigns={[]}
      />
    );
    expect(screen.getByText('测试计划')).toBeInTheDocument();
    expect(screen.getByText('测试账户')).toBeInTheDocument();
  });

  it('shows empty state when no data', () => {
    render(
      <TopLists
        topSpendCampaigns={[]}
        worstROASCampaigns={[]}
      />
    );
    expect(screen.getAllByText('当前筛选条件下暂无数据')).toHaveLength(2);
  });
});
```

---

## 10. 源码位置

| 类型 | 路径 |
|------|------|
| 组件 | `frontend/src/features/dashboard/components/TopLists.tsx` |
| 格式化工具 | `frontend/src/features/dashboard/utils/formatters.ts` |
| 类型 | (内联在组件文件中) |
| 测试 | `frontend/src/features/dashboard/components/__tests__/TopLists.test.tsx` |

---

## 11. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-22 | 初始版本 |

---

## 12. 相关文档

- [A1-dashboard 模块规格书](../../10.module-specs/A1-dashboard.md)
- [DataTable 代码块](../core/data-table.md)
- [StatusBadge 代码块](../core/status-badge.md)
