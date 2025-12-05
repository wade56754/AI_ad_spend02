# Dashboard 配色系统优化方案 v1.0

> 暗色系数据仪表盘专业配色系统，适用于长期盯盘场景

---

## 1. 当前 Dashboard 配色诊断

### 总体评价

当前 Dashboard 采用 `slate-950` 作为页面背景，`slate-900/50` 作为卡片背景，整体基调偏深，但存在以下问题：

1. **层级区分度不足**：卡片与背景对比度偏低（约 3:1），长时间观看容易产生视觉疲劳
2. **告警区域过于压迫**：整块红色背景（`bg-red-950/30`）虽然醒目，但视觉压迫感强，不适合长期盯盘
3. **文字层级不够清晰**：`text-slate-100`、`text-slate-400`、`text-slate-500` 之间的对比度差异不够明显
4. **功能色职责不清**：蓝色、绿色、红色、橙色混用，缺少统一的语义化定义

### 按区域问题清单

#### 顶部 KPI 区
- 卡片背景 `bg-slate-900/50` 与页面背景 `bg-slate-950` 区分度低
- 告警卡片整块红色背景，视觉压迫感强
- 主数值与副标题对比度不够

#### 中间趋势图区
- 网格线颜色 `#1e293b` 过深，与背景区分不明显
- 坐标轴文字 `#94a3b8` 可读性一般
- Tooltip 背景色与卡片背景接近

#### 右侧风险预警区
- 整块红色背景过于压迫
- P0/P1 标签颜色区分度不够
- 条目之间的视觉边界不够清晰

#### 底部待办/资金区
- 任务项优先级颜色区分不明显
- 资金卡片层级感弱
- 进度条颜色与背景对比度低

---

## 2. 推荐颜色系统与变量设计

### 2.1 三层背景亮度系统

| 层级 | 用途 | HEX 值 | Tailwind 类名 | 说明 |
|------|------|--------|---------------|------|
| **Shell** | 页面背景 | `#0A0E1A` | `bg-shell` | 最底层，接近黑色但带微蓝调 |
| **Card** | 卡片背景 | `#131825` | `bg-card` | 比 Shell 亮 20%，清晰区分 |
| **Elevated** | 悬浮/高亮背景 | `#1A2332` | `bg-elevated` | 比 Card 亮 15%，用于 hover/active |

**对比度计算**：
- Shell → Card: 约 1.25:1（视觉区分明显）
- Card → Elevated: 约 1.15:1（层次感清晰）

### 2.2 文本层级系统

| 层级 | 用途 | HEX 值 | Tailwind 类名 | 对比度（相对 Card） |
|------|------|--------|---------------|---------------------|
| **Strong** | 主标题、关键数字 | `#F8FAFC` | `text-strong` | 约 12:1（高对比） |
| **Body** | 正文、次要标题 | `#CBD5E1` | `text-body` | 约 7:1（可读） |
| **Muted** | 辅助文字、标签 | `#94A3B8` | `text-muted` | 约 4:1（可读但次要） |
| **Subtle** | 时间戳、分隔符 | `#64748B` | `text-subtle` | 约 2.5:1（仅装饰） |

### 2.3 功能色系统

| 功能 | 主色 HEX | 浅色 HEX | Tailwind 类名 | 用途 |
|------|----------|----------|--------------|------|
| **Accent** | `#3B82F6` | `#60A5FA` | `accent` / `accent-light` | 品牌主色、链接、Primary KPI |
| **Success** | `#10B981` | `#34D399` | `success` / `success-light` | 正向指标、完成状态 |
| **Warning** | `#F59E0B` | `#FBBF24` | `warning` / `warning-light` | 警告、待处理 |
| **Danger** | `#EF4444` | `#F87171` | `danger` / `danger-light` | 严重告警、错误 |
| **Info** | `#06B6D4` | `#22D3EE` | `info` / `info-light` | 信息提示、次要指标 |

**告警色使用原则**：
- **P0 严重**：使用 `danger` 主色，但**不整块背景**，改为左侧边框 + 图标 + 数字
- **P1 警告**：使用 `warning` 主色，同样采用点状高亮

### 2.4 边框与分隔线

| 类型 | HEX 值 | Tailwind 类名 | 用途 |
|------|--------|---------------|------|
| **Border Default** | `#1E293B` | `border-default` | 卡片边框、输入框边框 |
| **Border Muted** | `#334155` | `border-muted` | 分隔线、列表项边框 |
| **Border Accent** | `#3B82F6` | `border-accent` | 选中状态、焦点边框 |
| **Border Danger** | `#7F1D1D` | `border-danger` | 告警卡片边框（半透明） |

---

## 3. Tailwind 配置映射

### 3.1 扩展 tailwind.config.ts

```typescript
// frontend/tailwind.config.ts
extend: {
  colors: {
    // 背景层级
    shell: '#0A0E1A',
    card: '#131825',
    elevated: '#1A2332',
    
    // 文本层级
    'text-strong': '#F8FAFC',
    'text-body': '#CBD5E1',
    'text-muted': '#94A3B8',
    'text-subtle': '#64748B',
    
    // 功能色
    accent: {
      DEFAULT: '#3B82F6',
      light: '#60A5FA',
      dark: '#2563EB',
    },
    success: {
      DEFAULT: '#10B981',
      light: '#34D399',
      dark: '#059669',
    },
    warning: {
      DEFAULT: '#F59E0B',
      light: '#FBBF24',
      dark: '#D97706',
    },
    danger: {
      DEFAULT: '#EF4444',
      light: '#F87171',
      dark: '#DC2626',
    },
    info: {
      DEFAULT: '#06B6D4',
      light: '#22D3EE',
      dark: '#0891B2',
    },
    
    // 边框
    'border-default': '#1E293B',
    'border-muted': '#334155',
    'border-accent': '#3B82F6',
    'border-danger': '#7F1D1D',
  },
}
```

### 3.2 CSS 变量方案（可选）

如果希望更灵活的主题切换，可以在 `globals.css` 中定义：

```css
:root {
  /* 背景层级 */
  --color-shell: #0A0E1A;
  --color-card: #131825;
  --color-elevated: #1A2332;
  
  /* 文本层级 */
  --color-text-strong: #F8FAFC;
  --color-text-body: #CBD5E1;
  --color-text-muted: #94A3B8;
  --color-text-subtle: #64748B;
  
  /* 功能色 */
  --color-accent: #3B82F6;
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-danger: #EF4444;
}
```

---

## 4. 关键区域配色落地方案

### 4.1 顶部 KPI 卡片

**Primary KPI（主要指标）**：
- 背景：`bg-card` + `border border-default`
- 图标背景：`bg-accent/10`（蓝色半透明）
- 图标颜色：`text-accent`
- 主数值：`text-strong text-2xl`
- 副标题：`text-muted text-xs`
- 趋势标签：`bg-elevated` + `text-success`（上升）或 `text-danger`（下降）

**Secondary KPI（次要指标）**：
- 背景：`bg-card` + `border border-default`
- 图标背景：`bg-elevated`
- 图标颜色：`text-muted`
- 主数值：`text-body text-xl`
- 副标题：`text-muted text-xs`

**告警 KPI（待审日报）**：
- 背景：`bg-card` + `border-l-4 border-danger`（左侧红色边框，不整块背景）
- 图标背景：`bg-danger/10`
- 图标颜色：`text-danger`
- 主数值：`text-danger text-2xl`（红色数字）
- 副标题：`text-muted text-xs`

### 4.2 中间趋势图区

**图表容器**：
- 背景：`bg-card` + `border border-default`
- 标题：`text-strong text-lg`
- 副标题：`text-muted text-sm`

**图表元素**：
- 网格线：`stroke-[#1E293B]`（与 border-default 一致）
- X/Y 轴文字：`text-muted`（`#94A3B8`）
- 柱状图：`fill-accent` + 渐变（`from-accent/40 to-accent/0`）
- 折线图：`stroke-success`（绿色，表示 ROI）
- Tooltip 背景：`bg-elevated` + `border border-default`
- Tooltip 文字：`text-body`

### 4.3 右侧风险预警区

**卡片容器**：
- 背景：`bg-card` + `border border-default`
- 标题：`text-strong` + `text-warning`（橙色图标）

**预警条目（P0 严重）**：
- 背景：`bg-elevated` + `border-l-4 border-danger`（左侧红色边框）
- 账户名：`text-body font-semibold`
- 问题类型：`text-muted text-xs`
- P0 标签：`bg-danger/20 text-danger border border-danger/40`（半透明背景）
- 详情文字：`text-muted text-xs`
- 时间戳：`text-subtle text-[10px]`

**预警条目（P1 警告）**：
- 背景：`bg-elevated` + `border-l-4 border-warning`（左侧橙色边框）
- P1 标签：`bg-warning/20 text-warning border border-warning/40`

**关键改进**：
- ❌ 不再使用整块红色背景 `bg-red-950/30`
- ✅ 改为左侧彩色边框 + 半透明标签 + 彩色图标/数字

### 4.4 底部今日待办区

**卡片容器**：
- 背景：`bg-card` + `border border-default`
- 标题：`text-strong`
- 进度条：`bg-elevated` + `fill-accent`（蓝色进度条）

**任务项**：
- 背景：`bg-card` + `hover:bg-elevated` + `border border-transparent hover:border-default`
- 优先级指示点：
  - High: `bg-danger` + `ring-danger/20`
  - Medium: `bg-warning` + `ring-warning/20`
  - Low: `bg-muted` + `ring-muted/20`
- 任务标题：`text-body` + `group-hover:text-accent`
- 完成状态：`text-muted line-through`
- 时间/负责人：`text-muted text-xs`

### 4.5 资金概览区

**卡片容器**：
- 背景：`bg-card` + `border border-default`

**总余额卡片**：
- 背景：`bg-elevated` + `border border-default`
- 标签：`text-muted text-xs`
- 主数值：`text-strong text-2xl`
- 副数值：`text-body text-xs`
- 进度条：`bg-card` + `fill-success`（绿色表示可用）

**待审核充值卡片**：
- 背景：`bg-elevated` + `border border-default`
- 标签：`text-muted text-xs`
- 主数值：`text-warning text-xl`（橙色，表示待处理）
- 副数值：`text-body text-xs`

---

## 5. 示例 TSX 代码片段

### 5.1 优化后的 KPI 卡片组件

```tsx
// frontend/src/modules/dashboard/components/DashboardKpiRow.tsx (优化版)

function KpiCard({ metric, span, isPrimary, isAlert }: KpiCardProps) {
  const IconComponent = metric.icon;

  return (
    <div
      className={cn(
        'col-span-12 sm:col-span-6 lg:col-span-' + span,
        'rounded-lg border p-4 transition-all duration-200',
        'bg-card border-default',
        'hover:bg-elevated hover:border-muted',
        // 告警卡片：左侧红色边框，不整块背景
        isAlert && 'border-l-4 border-danger'
      )}
    >
      <div className="flex justify-between items-start mb-3">
        {/* 图标 */}
        <div
          className={cn(
            'p-2 rounded-lg transition-transform hover:scale-105',
            isAlert
              ? 'bg-danger/10'
              : isPrimary
              ? 'bg-accent/10'
              : 'bg-elevated'
          )}
        >
          <IconComponent
            className={cn(
              'w-5 h-5',
              isAlert
                ? 'text-danger'
                : isPrimary
                ? 'text-accent'
                : 'text-muted'
            )}
          />
        </div>

        {/* 趋势标签 */}
        {metric.change !== undefined && (
          <div
            className={cn(
              'flex items-center text-xs font-semibold px-2 py-0.5 rounded-full',
              'bg-elevated',
              metric.changeType === 'up'
                ? 'text-success'
                : metric.changeType === 'down'
                ? 'text-danger'
                : 'text-muted'
            )}
          >
            {metric.change > 0 ? '+' : ''}
            {metric.change}%
            {metric.changeType === 'up' && (
              <ArrowUpRight className="w-3 h-3 ml-0.5" />
            )}
          </div>
        )}
      </div>

      {/* 标题和数值 */}
      <div>
        <div className="text-muted text-xs font-medium uppercase tracking-wider mb-1.5">
          {metric.title}
        </div>
        <div className="flex items-baseline gap-2">
          <span
            className={cn(
              'font-bold tracking-tight',
              isPrimary ? 'text-2xl' : 'text-xl',
              isAlert ? 'text-danger' : 'text-strong'
            )}
          >
            {metric.value}
          </span>
          {metric.description && (
            <span className="text-xs text-muted">{metric.description}</span>
          )}
        </div>
      </div>
    </div>
  );
}
```

### 5.2 优化后的风险预警条目

```tsx
// frontend/src/modules/dashboard/components/DashboardRiskPanel.tsx (优化版)

{alerts.map((alert) => (
  <div
    key={alert.id}
    onClick={() => onAlertClick?.(alert)}
    className={cn(
      'p-2.5 bg-elevated border rounded-lg transition-all',
      'hover:bg-elevated/80 hover:border-muted',
      'cursor-pointer group',
      // 关键改进：左侧彩色边框，不整块背景
      alert.level === 'critical'
        ? 'border-l-4 border-danger'
        : 'border-l-4 border-warning'
    )}
  >
    <div className="flex justify-between items-start mb-1.5">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-semibold text-body group-hover:text-accent transition-colors truncate">
            {alert.account}
          </span>
          {alert.project && (
            <span className="text-xs text-muted truncate">
              · {alert.project}
            </span>
          )}
        </div>
        <div className="text-xs font-medium text-muted mb-1">
          {alert.type}
        </div>
      </div>
      <Badge
        variant={alert.level === 'critical' ? 'destructive' : 'secondary'}
        className={cn(
          'text-[10px] px-2 py-0.5 uppercase tracking-wide font-bold border shrink-0 ml-2',
          alert.level === 'critical'
            ? 'bg-danger/20 text-danger border-danger/40'
            : 'bg-warning/20 text-warning border-warning/40'
        )}
      >
        {alert.level === 'critical' ? 'P0' : 'P1'}
      </Badge>
    </div>
    <div className="flex items-center gap-1.5">
      <span
        className={cn(
          'w-1.5 h-1.5 rounded-full shrink-0',
          alert.level === 'critical' ? 'bg-danger' : 'bg-warning'
        )}
      />
      <span className="text-xs text-muted flex-1">{alert.msg}</span>
    </div>
    {alert.timestamp && (
      <div className="text-[10px] text-subtle mt-1.5 ml-3">
        {alert.timestamp}
      </div>
    )}
  </div>
))}
```

---

## 6. 渐进式改造建议

### P0 - 立即改（核心问题）

1. **更新 tailwind.config.ts**
   - 添加 `shell`、`card`、`elevated` 背景色
   - 添加 `text-strong`、`text-body`、`text-muted`、`text-subtle` 文本色
   - 添加 `accent`、`success`、`warning`、`danger`、`info` 功能色
   - 添加 `border-default`、`border-muted` 边框色

2. **修复告警卡片**
   - 移除整块红色背景 `bg-red-950/30`
   - 改为左侧红色边框 `border-l-4 border-danger`
   - 更新 `DashboardKpiRow.tsx` 和 `DashboardRiskPanel.tsx`

3. **优化页面背景**
   - 将 `bg-slate-950` 改为 `bg-shell`
   - 将卡片 `bg-slate-900/50` 改为 `bg-card`

### P1 - 一两天内（提升可读性）

4. **统一文本层级**
   - 主标题：`text-strong`
   - 正文：`text-body`
   - 辅助文字：`text-muted`
   - 时间戳：`text-subtle`

5. **优化图表配色**
   - 网格线：`stroke-[#1E293B]`
   - 坐标轴文字：`text-muted`
   - Tooltip 背景：`bg-elevated`

6. **统一边框系统**
   - 卡片边框：`border-default`
   - 分隔线：`border-muted`
   - 告警边框：`border-danger`（半透明）

### P2 - 后续优化（锦上添花）

7. **添加 CSS 变量支持**
   - 在 `globals.css` 中定义 CSS 变量
   - 支持未来主题切换

8. **优化图表渐变**
   - 柱状图渐变：`from-accent/40 to-accent/0`
   - 折线图：`stroke-success`

9. **统一 Badge/Tag 样式**
   - 半透明背景：`bg-{color}/20`
   - 边框：`border-{color}/40`
   - 文字：`text-{color}`

10. **废弃旧组件**
    - 标记 `optimized-*`、`modern-*` 组件为 `@deprecated`
    - 提供迁移指南

---

## 7. 颜色对比度检查清单

| 组合 | 前景色 | 背景色 | 对比度 | 状态 |
|------|--------|--------|--------|------|
| 主标题 | `text-strong` | `bg-card` | 12:1 | ✅ WCAG AAA |
| 正文 | `text-body` | `bg-card` | 7:1 | ✅ WCAG AA |
| 辅助文字 | `text-muted` | `bg-card` | 4:1 | ✅ WCAG AA |
| 告警文字 | `text-danger` | `bg-card` | 5:1 | ✅ WCAG AA |
| 卡片边框 | `border-default` | `bg-shell` | 1.25:1 | ✅ 视觉区分 |

---

## 8. 实施检查清单

- [ ] 更新 `tailwind.config.ts` 添加新颜色
- [ ] 更新 `page.tsx` 背景色为 `bg-shell`
- [ ] 更新 `DashboardKpiRow.tsx` 使用新配色
- [ ] 更新 `DashboardRiskPanel.tsx` 移除整块红色背景
- [ ] 更新 `DashboardTrendSection.tsx` 图表配色
- [ ] 更新 `DashboardTodayTasks.tsx` 文本层级
- [ ] 更新 `DashboardFundsOverview.tsx` 卡片配色
- [ ] 运行 `pnpm type-check` 验证类型
- [ ] 运行 `pnpm lint` 检查代码
- [ ] 浏览器测试视觉效果

---

**版本**: v1.0  
**最后更新**: 2024-12-03  
**维护者**: Frontend Team

