# 广告账号管理 - 前端设计方案

> 作者：资深前端工程师 (10年经验)
> 版本：v2.0 | 日期：2025-12-22

---

## 设计哲学

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Information Density  ×  Operation Efficiency  ×  Insight │
│        信息密度              操作效率             数据洞察   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**核心目标**：让运营人员在 3 秒内找到目标账户，1 次点击完成常用操作。

---

## 1. 页面结构设计

```
┌─────────────────────────────────────────────────────────────────┐
│  Header: 页面标题 + 最后更新时间                                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │ 账户总数 │ │今日消耗  │ │本月消耗  │ │ 平均费率 │  ← Stats    │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │
├─────────────────────────────────────────────────────────────────┤
│  [🔍 搜索] [全部|投放中|测试中|暂停|死号] [投手▼] [代理商▼] [更多]│
│                                                    ← Filters   │
├─────────────────────────────────────────────────────────────────┤
│  已选择 3 个账户  [批量暂停] [批量分配]     [刷新] [导入] [导出] │
│                                                    ← Actions   │
├─────────────────────────────────────────────────────────────────┤
│  ☐ │ 账户信息              │投手│ 代理商   │今日消耗│本月消耗│状态│
│  ──┼───────────────────────┼────┼──────────┼────────┼────────┼────│
│  ☑ │ FB SONZDD-ADA+7-GX    │ YK │海总&志诚 │ $245.32│$4,521.8│投放│
│  ☐ │ FB Tencent IS Pte.Ltd │ LM │B哥-fb    │ $419.48│$3,009.5│投放│
│  ☐ │ TK TK-Global-HK-001   │ HY │官方授权户│  $89.50│$1,285.8│投放│
│                                                    ← Table     │
├─────────────────────────────────────────────────────────────────┤
│  共 156 个账户                        每页 [20▼] 条  ← Footer  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 关键设计决策

### 2.1 统计卡片 (Stats Cards)

**为什么放在顶部？**
- 运营人员打开页面第一眼需要知道"今天整体情况如何"
- 4 个关键指标：账户数、今日消耗、本月消耗、平均费率
- 使用渐变色区分不同指标，视觉层次清晰

**设计细节：**
```tsx
// 消耗趋势 - 一眼看出增长/下降
<span className={trend >= 0 ? 'text-green-600' : 'text-red-500'}>
  {trend >= 0 ? <TrendingUp /> : <TrendingDown />}
  {formatPercent(trend)} vs 昨日
</span>
```

### 2.2 智能筛选栏 (Filter Bar)

**Tab 式状态筛选 - 高频操作前置**
```
[全部] [投放中] [测试中] [暂停] [死号]
```
- 状态筛选是最常用的筛选条件
- Tab 式设计比下拉框快 1 次点击
- 选中状态视觉反馈明显

**渐进式筛选 - 按使用频率排列**
```
搜索框 → 状态 Tab → 投手 → 代理商 → 平台 → [更多]
```
- 80% 的筛选需求用前 4 个就够了
- "更多"里放低频筛选：账户类型、地区

### 2.3 表格设计 (Table Design)

**高信息密度但不拥挤**

```tsx
// 账户信息列 - 组合展示
<TableCell>
  <div className="flex items-start gap-3">
    {/* 平台标识 - 视觉锚点 */}
    <div className="w-8 h-8 rounded-lg bg-blue-600 text-white">FB</div>

    <div>
      {/* 主信息：账户名称 */}
      <span className="font-medium">SONZDD-ADA+7-GX-324</span>

      {/* 次信息：ID + 类型 + 地区 */}
      <div className="flex items-center gap-2 text-xs text-gray-400">
        <span className="font-mono">1138647123633445</span>
        <Badge>越南盾主题户</Badge>
        <span>印度</span>
      </div>
    </div>
  </div>
</TableCell>
```

**行为提示 - Hover 显示操作**
```tsx
// 操作按钮只在 hover 时显示
<Button className="opacity-0 group-hover:opacity-100">
  <MoreHorizontal />
</Button>
```

### 2.4 消耗数据展示

**带趋势的数字 - 不只是数字**
```tsx
<TableCell className="text-right">
  <div className="flex flex-col items-end">
    <span className="font-medium">$245.32</span>
    <span className="text-green-600 text-xs flex items-center">
      <TrendingUp className="w-3 h-3" />
      +23.6%
    </span>
  </div>
</TableCell>
```

**智能格式化 - 大数字易读**
```tsx
const formatCurrency = (value: number) => {
  if (value >= 10000) return `$${(value / 1000).toFixed(1)}k`;  // $12.5k
  return `$${value.toFixed(2)}`;                                // $245.32
};
```

### 2.5 批量操作设计

**选中后才显示操作按钮**
```tsx
{selectedCount > 0 ? (
  <>
    <span>已选择 <b>{selectedCount}</b> 个账户</span>
    <Button>批量暂停</Button>
    <Button>批量分配</Button>
    <Button className="text-red-600">批量归档</Button>
  </>
) : (
  <span className="text-gray-500">提示：勾选账户可进行批量操作</span>
)}
```

---

## 3. 交互细节

### 3.1 键盘快捷键 (建议实现)

| 快捷键 | 功能 |
|--------|------|
| `/` 或 `Ctrl+K` | 聚焦搜索框 |
| `Ctrl+A` | 全选当前页 |
| `Esc` | 清除选择/关闭弹窗 |
| `R` | 刷新数据 |
| `E` | 导出数据 |

### 3.2 搜索优化

**即时搜索 + 防抖**
```tsx
const [searchTerm, setSearchTerm] = useState('');
const debouncedSearch = useDebouncedValue(searchTerm, 300);

// 搜索时高亮匹配文本
<HighlightText text={account.name} highlight={searchTerm} />
```

**搜索范围**
- 账户名称
- 平台账户ID
- 投手名
- 代理商名

### 3.3 状态切换动画

```tsx
// 状态变化时的微动画
<Badge className="transition-all duration-200">
  <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
  投放中
</Badge>
```

---

## 4. 响应式设计

### 4.1 断点策略

| 断点 | 布局调整 |
|------|----------|
| `≥1280px` | 完整展示所有列 |
| `1024-1279px` | 隐藏"费率"列 |
| `768-1023px` | 隐藏"地区"列，统计卡片 2x2 |
| `<768px` | 表格改为卡片列表 |

### 4.2 移动端适配 (如需要)

```tsx
// 移动端改为卡片列表
<div className="md:hidden">
  {accounts.map(account => (
    <AccountCard key={account.id} account={account} />
  ))}
</div>

// 桌面端显示表格
<div className="hidden md:block">
  <AccountTable accounts={accounts} />
</div>
```

---

## 5. 性能优化

### 5.1 虚拟滚动 (大数据量)

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

// 1000+ 条数据时使用虚拟滚动
const virtualizer = useVirtualizer({
  count: accounts.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 64, // 行高
  overscan: 5,
});
```

### 5.2 数据缓存

```tsx
// TanStack Query 配置
const { data } = useQuery({
  queryKey: ['adAccounts', filters],
  queryFn: () => fetchAdAccounts(filters),
  staleTime: 30 * 1000,      // 30秒内不重新请求
  refetchInterval: 60 * 1000, // 每分钟自动刷新
});
```

### 5.3 筛选条件记忆

```tsx
// 使用 URL 参数保存筛选状态
const [searchParams, setSearchParams] = useSearchParams();

// 刷新页面后筛选条件保留
const filters = {
  status: searchParams.get('status') || '',
  buyer: searchParams.get('buyer') || '',
};
```

---

## 6. 组件拆分

```
AdAccountsPageV2/
├── index.tsx              # 主页面组件
├── StatsCards.tsx         # 统计卡片
├── FilterBar.tsx          # 筛选栏
├── ActionBar.tsx          # 操作工具栏
├── AccountTable.tsx       # 账户表格
├── AccountRow.tsx         # 表格行（可选拆分）
├── AccountCard.tsx        # 移动端卡片
├── hooks/
│   ├── useAccountFilters.ts   # 筛选逻辑
│   ├── useAccountSelection.ts # 选择逻辑
│   └── useAccountStats.ts     # 统计计算
└── utils/
    ├── formatters.ts      # 格式化函数
    └── constants.ts       # 状态配置等
```

---

## 7. 与后端对接

### 7.1 API 设计建议

```typescript
// GET /api/v1/ad-accounts
interface AdAccountListParams {
  page: number;
  page_size: number;
  status?: string;
  buyer_id?: string;
  supplier_id?: string;
  platform?: 'FB' | 'TK';
  search?: string;
  sort_by?: 'today_spend' | 'month_spend' | 'created_at';
  sort_order?: 'asc' | 'desc';
}

// Response
interface AdAccountListResponse {
  items: AdAccount[];
  meta: {
    pagination: { page, page_size, total, total_pages };
    stats: {
      total_accounts: number;
      active_accounts: number;
      today_spend: number;
      month_spend: number;
      avg_fee_rate: number;
    };
  };
}
```

### 7.2 实时更新

```tsx
// WebSocket 订阅消耗更新
useEffect(() => {
  const ws = new WebSocket('ws://api/spend-updates');

  ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    // 更新对应账户的今日消耗
    queryClient.setQueryData(['adAccounts'], (old) => ({
      ...old,
      items: old.items.map(acc =>
        acc.id === update.account_id
          ? { ...acc, todaySpend: update.new_spend }
          : acc
      ),
    }));
  };

  return () => ws.close();
}, []);
```

---

## 8. 待优化项

| 优先级 | 功能 | 说明 |
|--------|------|------|
| P0 | 对接真实 API | 替换 mock 数据 |
| P0 | 批量操作功能 | 实现批量暂停/分配/归档 |
| P1 | 导入导出 | Excel 导入/导出功能 |
| P1 | 账户详情页 | 点击账户查看详细消耗历史 |
| P2 | 虚拟滚动 | 大数据量性能优化 |
| P2 | 键盘快捷键 | 提升操作效率 |
| P3 | 移动端适配 | 响应式布局 |

---

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v2.0 | 2025-12-22 | 基于业务需求重新设计 |
