---
version: v2.1
status: ready_for_production
layer: dev-guide
owner: wade
last_reviewed: 2025-12-21
baseline: MASTER.md v4.4, SoT Freeze v2.6, FRONTEND_STYLE_GUIDE v2.1
---

# UI Design System - AI 广告代投系统

> **文档定位**: UI 设计系统规范，定义视觉设计标准、组件样式、主题系统
> **与 FRONTEND_STYLE_GUIDE 关系**: 本文档聚焦视觉设计，FRONTEND_STYLE_GUIDE 聚焦代码规范

---

## 1. 概述

### 1.1 文档目的

本文档定义 AI Ad Spend 系统的 UI 设计系统，作为视觉设计的唯一权威参考，覆盖：

- 颜色系统（品牌色、语义色、状态色）
- 排版系统（字体、字号、行高）
- 间距系统（基于 4px 网格）
- 组件库规范（shadcn/ui 定制）
- 图标系统（lucide-react）
- 响应式断点
- 主题系统（Light/Dark Mode）

### 1.2 设计原则

| 原则 | 说明 |
|------|------|
| **一致性** | 全系统统一视觉语言，减少用户认知负担 |
| **清晰性** | 信息层级清晰，重要操作突出显示 |
| **高效性** | 减少操作步骤，提供快捷路径 |
| **可访问性** | 符合 WCAG 2.1 AA 标准 |
| **SoT 对齐** | 状态颜色与 STATE_MACHINE.md 保持一致 |

---

## 2. 颜色系统

### 2.1 品牌色

> **规则**: 品牌色通过 CSS 变量定义，禁止硬编码十六进制值

| Token | CSS 变量 | Light Mode | Dark Mode | 用途 |
|-------|----------|------------|-----------|------|
| `primary` | `--primary` | `#2563EB` | `#3B82F6` | 主要操作、品牌标识 |
| `primary-foreground` | `--primary-foreground` | `#FFFFFF` | `#FFFFFF` | 主色上的文字 |

### 2.2 语义色（Semantic Colors）

| Token | CSS 变量 | 值 | 用途 |
|-------|----------|-----|------|
| `background` | `--background` | `#FFFFFF` / `#0A0A0B` | 页面背景 |
| `foreground` | `--foreground` | `#0A0A0B` / `#FAFAFA` | 主要文字 |
| `muted` | `--muted` | `#F4F4F5` / `#27272A` | 次要背景 |
| `muted-foreground` | `--muted-foreground` | `#71717A` / `#A1A1AA` | 辅助文字 |
| `accent` | `--accent` | `#F4F4F5` / `#27272A` | 强调背景 |
| `border` | `--border` | `#E4E4E7` / `#27272A` | 边框 |
| `destructive` | `--destructive` | `#EF4444` / `#DC2626` | 危险操作 |

### 2.3 状态颜色（Status Colors）

> **重要**: 状态颜色与 `STATE_MACHINE.md` v2.6 第 8 章对齐
>
> **规则**: 状态颜色必须通过 `STATUS_VARIANT_MAP` 集中管理（定义于 `@/features/shared/utils/statusColors.ts`）

#### 状态色板映射

| 语义 | Variant Key | 背景色 | 文字色 | 边框色 | 适用状态 |
|------|-------------|--------|--------|--------|----------|
| 成功 | `success` | `bg-green-100` | `text-green-800` | `border-green-200` | `trend_ok`, `final_confirmed`, `completed`, `approved` |
| 警告 | `warning` | `bg-yellow-100` | `text-yellow-800` | `border-yellow-200` | `trend_pending`, `final_pending`, `pending_review` |
| 错误 | `error` | `bg-red-100` | `text-red-800` | `border-red-200` | `rejected`, `cancelled`, `failed` |
| 信息 | `info` | `bg-blue-100` | `text-blue-800` | `border-blue-200` | `raw_submitted`, `draft` |
| 标记 | `flagged` | `bg-orange-100` | `text-orange-800` | `border-orange-200` | `trend_flagged` |
| 已解决 | `resolved` | `bg-teal-100` | `text-teal-800` | `border-teal-200` | `trend_resolved` |
| 锁定 | `locked` | `bg-gray-100` | `text-gray-800` | `border-gray-200` | `final_locked`, `archived` |

#### 8 状态机状态颜色映射（daily_reports.status）

| 状态 | Variant | 中文标签 | 图标 |
|------|---------|----------|------|
| `raw_submitted` | `info` | 已提交 | `FileCheck` |
| `trend_pending` | `warning` | 趋势检查中 | `Clock` |
| `trend_ok` | `success` | 趋势正常 | `CheckCircle` |
| `trend_flagged` | `flagged` | 趋势异常 | `AlertTriangle` |
| `trend_resolved` | `resolved` | 已解决 | `CheckCircle2` |
| `final_pending` | `warning` | 待确认 | `FileQuestion` |
| `final_confirmed` | `success` | 已确认 | `FileCheck2` |
| `final_locked` | `locked` | 已锁定 | `Lock` |

### 2.4 数据可视化系统 (Data Viz Colors)

> **原则**: 图表颜色必须通过 CSS 变量管理，确保在 Light/Dark 模式下均具有 WCAG AA 级对比度。

#### 语义化图表颜色 Token

| 语义 Token | CSS 变量 | Light Mode (参考) | Dark Mode (参考) | 用途说明 |
|------------|----------|-------------------|------------------|----------|
| `chart-primary` | `--chart-primary` | `#2563EB` (Blue-600) | `#60A5FA` (Blue-400) | 消耗/支出 (核心指标) |
| `chart-success` | `--chart-success` | `#16A34A` (Green-600) | `#4ADE80` (Green-400) | 收入/ROAS (正向指标) |
| `chart-warning` | `--chart-warning` | `#D97706` (Amber-600) | `#FBBF24` (Amber-400) | 利润 (关注指标) |
| `chart-info` | `--chart-info` | `#7C3AED` (Violet-600) | `#A78BFA` (Violet-400) | 粉丝数/点击 (辅助指标) |
| `chart-grid` | `--chart-grid` | `#E2E8F0` (Slate-200) | `#27272A` (Zinc-800) | 图表网格线/坐标轴 |
| `chart-tooltip` | `--chart-tooltip` | `#FFFFFF` | `#18181B` | 浮层背景色 |

#### Tailwind 配置

```typescript
// tailwind.config.ts
theme: {
  extend: {
    colors: {
      chart: {
        primary: "var(--chart-primary)",
        success: "var(--chart-success)",
        warning: "var(--chart-warning)",
        info:    "var(--chart-info)",
        grid:    "var(--chart-grid)",
        tooltip: "var(--chart-tooltip)",
      }
    }
  }
}
```

#### 使用示例

```tsx
// 图表组件中使用
<LineChart
  data={data}
  colors={{
    spend: 'var(--chart-primary)',    // 消耗
    revenue: 'var(--chart-success)',  // 收入
    profit: 'var(--chart-warning)',   // 利润
  }}
/>

// Tailwind 类使用
<div className="text-chart-primary">消耗: ¥12,345</div>
<div className="bg-chart-tooltip border border-chart-grid">...</div>
```

#### 旧版颜色映射 (向后兼容)

| 用途 | 新 Token | 旧写法 | 迁移说明 |
|------|----------|--------|----------|
| 消耗/支出 | `chart-primary` | `text-blue-500` | 使用 `text-chart-primary` |
| 收入 | `chart-success` | `text-green-500` | 使用 `text-chart-success` |
| 利润 | `chart-warning` | `text-amber-500` | 使用 `text-chart-warning` |
| 粉数 | `chart-info` | `text-violet-500` | 使用 `text-chart-info` |
| 辅助线 | `chart-grid` | `text-slate-400` | 使用 `text-chart-grid` |

---

## 3. 排版系统

### 3.1 字体栈

| 用途 | 字体 | Tailwind 类 | 备注 |
|------|------|-------------|------|
| 正文 | Inter, system-ui | `font-sans` | 默认字体 |
| 代码 | JetBrains Mono, monospace | `font-mono` | 代码块、数字 |

### 3.2 字号层级

| 语义 | 字号 | 行高 | 字重 | Tailwind 类 | 用途 |
|------|------|------|------|-------------|------|
| Display | 36px | 1.2 | Bold | `text-4xl font-bold` | 大标题 |
| H1 | 30px | 1.25 | Bold | `text-3xl font-bold` | 页面主标题 |
| H2 | 24px | 1.3 | Semibold | `text-2xl font-semibold` | 区块标题 |
| H3 | 20px | 1.4 | Semibold | `text-xl font-semibold` | 卡片标题 |
| H4 | 16px | 1.5 | Medium | `text-base font-medium` | 小标题 |
| Body | 14px | 1.5 | Normal | `text-sm` | 正文内容 |
| Small | 13px | 1.5 | Normal | `text-[13px]` | 次要文本 |
| Caption | 12px | 1.5 | Normal | `text-xs` | 辅助说明、时间戳 |

### 3.3 文字颜色

| 语义 | Tailwind 类 | 用途 |
|------|-------------|------|
| 主要文字 | `text-foreground` | 标题、正文 |
| 次要文字 | `text-muted-foreground` | 辅助说明、placeholder |
| 禁用文字 | `text-muted-foreground/50` | 禁用状态 |
| 链接文字 | `text-primary` | 可点击链接 |
| 错误文字 | `text-destructive` | 错误信息 |

---

## 4. 间距系统

### 4.1 基础间距（4px 网格）

| Token | 值 | Tailwind | 用途 |
|-------|-----|----------|------|
| `spacing-1` | 4px | `p-1` / `m-1` | 紧凑内边距 |
| `spacing-2` | 8px | `p-2` / `m-2` | 按钮内边距、图标间距 |
| `spacing-3` | 12px | `p-3` / `m-3` | 小卡片内边距 |
| `spacing-4` | 16px | `p-4` / `m-4` | 标准内边距 |
| `spacing-5` | 20px | `p-5` / `m-5` | 中等间距 |
| `spacing-6` | 24px | `p-6` / `m-6` | 大卡片内边距 |
| `spacing-8` | 32px | `p-8` / `m-8` | 区块间距 |

### 4.2 组件间距规范

| 场景 | 间距 | Tailwind 类 |
|------|------|-------------|
| 同组元素（如按钮组） | 8px | `gap-2` / `space-x-2` |
| 表单字段间距 | 16px | `gap-4` / `space-y-4` |
| 卡片内元素间距 | 16px | `gap-4` |
| 区块分隔 | 24px | `gap-6` / `mb-6` |
| 页面区块间距 | 32px | `gap-8` / `py-8` |

### 4.3 布局间距

| 元素 | 尺寸 | Tailwind 类 |
|------|------|-------------|
| 页面内边距 | 24px | `p-6` |
| 卡片内边距 | 16px-24px | `p-4` / `p-6` |
| 表格单元格 | 12px 16px | `px-4 py-3` |
| 模态框内边距 | 24px | `p-6` |

---

## 5. 组件库规范

### 5.1 基础组件（shadcn/ui）

> **规则**: 使用 shadcn/ui 作为基础组件库，按需引入并可定制

| 组件 | 来源 | 定制说明 |
|------|------|----------|
| Button | shadcn/ui | 支持 variant: default, secondary, outline, ghost, destructive |
| Card | shadcn/ui | 统一圆角 `rounded-xl`，阴影 `shadow-sm` |
| Input | shadcn/ui | 统一高度 40px |
| Select | shadcn/ui | 下拉菜单 |
| Dialog | shadcn/ui | 模态框 |
| Table | shadcn/ui | 数据表格 |
| Badge | shadcn/ui | 标签（状态显示） |
| Tabs | shadcn/ui | 标签页切换 |
| DropdownMenu | shadcn/ui | 下拉菜单 |
| Tooltip | shadcn/ui | 悬浮提示 |

### 5.2 按钮规范

| Variant | 用途 | 样式 |
|---------|------|------|
| `default` | 主要操作 | 品牌蓝背景，白色文字 |
| `secondary` | 次要操作 | 灰色背景 |
| `outline` | 边框按钮 | 透明背景，边框 |
| `ghost` | 幽灵按钮 | 无背景，hover 显示 |
| `destructive` | 危险操作 | 红色背景 |

| Size | 高度 | 内边距 | Tailwind 类 |
|------|------|--------|-------------|
| `sm` | 32px | 8px 12px | `h-8 px-3 text-xs` |
| `default` | 40px | 10px 16px | `h-10 px-4 text-sm` |
| `lg` | 48px | 12px 20px | `h-12 px-5 text-base` |
| `icon` | 40px | - | `h-10 w-10` |

### 5.3 卡片规范

```css
/* 标准卡片样式 */
.card-base {
  @apply bg-white rounded-xl border border-gray-200 shadow-sm;
}

/* 卡片内边距 */
.card-padding {
  @apply p-4 md:p-6;
}

/* 卡片标题 */
.card-header {
  @apply pb-4 border-b border-gray-100;
}
```

### 5.4 表格规范

| 元素 | 样式 |
|------|------|
| 表头 | `bg-gray-50 text-xs font-medium text-gray-500 uppercase` |
| 表格行 | `border-b border-gray-100 hover:bg-gray-50` |
| 单元格内边距 | `px-4 py-3` |
| 对齐 | 文本左对齐，数字右对齐 |

### 5.5 表单规范

| 元素 | 规范 |
|------|------|
| Label | `text-sm font-medium text-foreground mb-2` |
| Input | 高度 40px，圆角 6px，聚焦时蓝色边框 |
| Error Message | `text-xs text-destructive mt-1` |
| Helper Text | `text-xs text-muted-foreground mt-1` |
| 字段间距 | 16px (`space-y-4`) |

---

## 6. 图标系统

### 6.1 图标库

> **规则**: 统一使用 lucide-react 图标库

```tsx
import { Home, Settings, User, ChevronRight } from 'lucide-react'
```

### 6.2 图标尺寸

| Size | 尺寸 | 用途 | Tailwind 类 |
|------|------|------|-------------|
| `xs` | 14px | 行内图标 | `w-3.5 h-3.5` |
| `sm` | 16px | 按钮图标、标签 | `w-4 h-4` |
| `md` | 20px | 导航图标 | `w-5 h-5` |
| `lg` | 24px | 卡片图标 | `w-6 h-6` |
| `xl` | 32px | 空状态图标 | `w-8 h-8` |

### 6.3 常用图标映射

| 场景 | 图标 | 组件 |
|------|------|------|
| 首页/仪表盘 | `Home` | `<Home />` |
| 设置 | `Settings` | `<Settings />` |
| 用户 | `User` | `<User />` |
| 搜索 | `Search` | `<Search />` |
| 通知 | `Bell` | `<Bell />` |
| 添加 | `Plus` | `<Plus />` |
| 编辑 | `Pencil` | `<Pencil />` |
| 删除 | `Trash2` | `<Trash2 />` |
| 成功 | `CheckCircle` | `<CheckCircle />` |
| 警告 | `AlertTriangle` | `<AlertTriangle />` |
| 错误 | `XCircle` | `<XCircle />` |
| 信息 | `Info` | `<Info />` |
| 锁定 | `Lock` | `<Lock />` |
| 刷新 | `RefreshCw` | `<RefreshCw />` |
| 导出 | `Download` | `<Download />` |
| 导入 | `Upload` | `<Upload />` |

---

## 7. 响应式断点

### 7.1 断点定义

| 断点 | 宽度 | Tailwind 前缀 | 设备类型 |
|------|------|---------------|----------|
| Mobile | < 640px | 默认 | 手机 |
| `sm` | ≥ 640px | `sm:` | 大屏手机 |
| `md` | ≥ 768px | `md:` | 平板 |
| `lg` | ≥ 1024px | `lg:` | 小型桌面 |
| `xl` | ≥ 1280px | `xl:` | 桌面 |
| `2xl` | ≥ 1400px | `2xl:` | 大屏桌面 |

### 7.2 布局响应式行为

| 元素 | Mobile | Tablet (md) | Desktop (lg+) |
|------|--------|-------------|---------------|
| Sidebar | 隐藏（汉堡菜单） | 可折叠 | 固定展开 |
| 统计卡片 | 1列 | 2列 | 4列 |
| 数据表格 | 横向滚动 | 响应式列 | 完整显示 |
| 表单 | 单列 | 双列可选 | 双列 |

### 7.3 内容容器

```tsx
// 最大宽度约束
<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  {/* 页面内容 */}
</div>
```

---

## 8. 主题系统

### 8.1 Light/Dark Mode

> **规则**: 使用 CSS 变量支持主题切换，通过 `class` 策略控制

```css
/* Light Mode (默认) */
:root {
  --background: 0 0% 100%;
  --foreground: 240 10% 3.9%;
  --primary: 221.2 83.2% 53.3%;
  /* ... */
}

/* Dark Mode */
.dark {
  --background: 240 10% 3.9%;
  --foreground: 0 0% 98%;
  --primary: 217.2 91.2% 59.8%;
  /* ... */
}
```

### 8.2 主题切换

```tsx
// 使用 next-themes
import { useTheme } from 'next-themes'

function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  return (
    <Button
      variant="ghost"
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
    >
      {theme === 'dark' ? <Sun /> : <Moon />}
    </Button>
  )
}
```

---

## 9. 交互模式

### 9.1 加载状态

| 场景 | 展示方式 |
|------|----------|
| 页面加载 | Skeleton 骨架屏 |
| 按钮提交 | Button 禁用 + Spinner |
| 列表加载 | 表格行 Skeleton |
| 无限滚动 | 底部 Spinner |

### 9.2 空状态

```tsx
<div className="flex flex-col items-center justify-center py-12">
  <Inbox className="w-12 h-12 text-muted-foreground mb-4" />
  <h3 className="text-lg font-medium text-foreground mb-2">暂无数据</h3>
  <p className="text-sm text-muted-foreground mb-4">
    还没有任何记录
  </p>
  <Button>创建记录</Button>
</div>
```

### 9.3 错误状态

| 类型 | 展示方式 | 位置 |
|------|----------|------|
| 字段错误 | 红色文字 | 输入框下方 |
| 表单错误 | Alert 横幅 | 表单顶部 |
| 页面错误 | 错误页面 | 全屏 |
| 系统错误 | Toast 通知 | 右上角 |

### 9.4 反馈 Toast

| 类型 | 颜色 | 图标 | 持续时间 |
|------|------|------|----------|
| Success | 绿色 | `CheckCircle` | 3s |
| Error | 红色 | `XCircle` | 5s |
| Warning | 黄色 | `AlertTriangle` | 4s |
| Info | 蓝色 | `Info` | 3s |

---

## 10. SoT 对齐规则

### 10.1 状态显示对齐

- **日报状态**: 必须使用 `STATE_MACHINE.md` v2.6 第 8 章定义的 8 个状态
- **颜色映射**: 必须通过 `STATUS_VARIANT_MAP` 统一管理
- **图标使用**: 参照本文档第 6.3 节图标映射

### 10.2 错误提示对齐

- **错误码**: 必须引用 `ERROR_CODES_SOT.md` v2.1 定义的错误码
- **错误消息**: 使用 `ERROR_MESSAGES` 映射表（`@/lib/api/apiErrors.ts`）

### 10.3 权限控制

- **按钮禁用**: 无权限时禁用并显示 Tooltip
- **菜单隐藏**: 无模块权限时隐藏菜单项
- **终态保护**: `final_locked` 状态禁用所有编辑操作（INV-002）

---

## 11. 实现参考

### 11.1 相关代码位置

| 内容 | 路径 |
|------|------|
| 状态颜色常量 | `@/features/shared/utils/statusColors.ts` |
| 状态配置 | `@/features/{domain}/utils/statusConfig.ts` |
| API 错误映射 | `@/lib/api/apiErrors.ts` |
| shadcn 组件 | `@/components/ui/` |
| 共享组件 | `@/features/shared/components/` |

### 11.2 关联文档

| 文档 | 版本 | 关系 |
|------|------|------|
| `FRONTEND_STYLE_GUIDE.md` | v2.1 | 代码规范（本文档聚焦视觉设计） |
| `STATE_MACHINE.md` | v2.6 | 状态枚举定义 |
| `ERROR_CODES_SOT.md` | v2.1 | 错误码定义 |
| `UI_FLOW_SPEC.md` | v1.0 | 交互流程定义 |

---

## 附录 A: 快速参考

### A.1 颜色速查

```
品牌蓝: #2563EB (primary)
成功绿: #22C55E (success)
警告黄: #EAB308 (warning)
错误红: #EF4444 (error)
信息蓝: #3B82F6 (info)
标记橙: #F97316 (flagged)
灰色: #6B7280 (muted)
```

### A.2 间距速查

```
4px  = p-1 / m-1
8px  = p-2 / m-2
12px = p-3 / m-3
16px = p-4 / m-4
24px = p-6 / m-6
32px = p-8 / m-8
```

### A.3 字号速查

```
H1: text-3xl (30px)
H2: text-2xl (24px)
H3: text-xl (20px)
Body: text-sm (14px)
Caption: text-xs (12px)
```

---

## 变更日志

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v0.1 | 2025-11-27 | 初始框架（TODO 占位） | wade |
| v2.0 | 2025-12-09 | **全面重写**：<br>- 完善颜色系统（品牌色、语义色、状态色）<br>- 对齐 STATE_MACHINE.md v2.6 状态颜色<br>- 添加排版系统详细规范<br>- 添加间距系统（4px 网格）<br>- 添加组件库规范（shadcn/ui）<br>- 添加图标系统（lucide-react）<br>- 添加响应式断点<br>- 添加主题系统<br>- 添加交互模式规范<br>- 添加 SoT 对齐规则 | Claude |
| v2.1 | 2025-12-21 | **增强数据可视化系统**：<br>- Section 2.4 重写为语义化图表颜色 Token<br>- 添加 CSS 变量支持 Light/Dark 模式<br>- 添加 Tailwind chart 颜色配置<br>- 添加扩展色板（secondary/tertiary/quaternary）<br>- 添加向后兼容迁移指南 | Claude |

---

**文档版本**: v2.1
**状态**: ready_for_production
**最后更新**: 2025-12-21
**维护者**: wade
**基准**: MASTER.md v4.4, SoT Freeze v2.6, FRONTEND_STYLE_GUIDE v2.1
