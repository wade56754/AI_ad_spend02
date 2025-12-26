# 前端组件注册表

> **版本**: v1.1
> **更新日期**: 2025-12-24
> **适用范围**: 前端代码工厂 (FE-Gen Skill)
> **组件总数**: 85 个

---

## 概述

本文档为前端代码工厂提供完整的组件注册表，确保 AI 生成代码时正确引用可用组件。

**目录结构**:
```
frontend/src/components/
├── ui/           → 58 个基础 UI 组件 (shadcn/ui)
├── dashboard/    → 16 个仪表盘组件
├── layout/       → 9 个布局组件
└── shared/       → 2 个共享组件
```

---

## 1. UI 基础组件 (44 个)

### 1.1 按钮类

#### Button
```typescript
import { Button } from "@/components/ui/button";

// Props
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  asChild?: boolean;
}

// 使用示例
<Button variant="primary" size="sm">提交</Button>
<Button variant="destructive">删除</Button>
<Button variant="outline" size="icon"><Icon /></Button>
```

### 1.2 表单组件

#### Input
```typescript
import { Input } from "@/components/ui/input";

// Props: 继承 React.InputHTMLAttributes<HTMLInputElement>

// 使用示例
<Input type="text" placeholder="请输入..." />
<Input type="number" min={0} max={100} />
```

#### Textarea
```typescript
import { Textarea } from "@/components/ui/textarea";

// Props: 继承 React.TextareaHTMLAttributes<HTMLTextAreaElement>

// 使用示例
<Textarea placeholder="请输入备注..." rows={4} />
```

#### Select
```typescript
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
  SelectGroup,
  SelectLabel,
  SelectSeparator,
} from "@/components/ui/select";

// 使用示例
<Select value={value} onValueChange={setValue}>
  <SelectTrigger>
    <SelectValue placeholder="请选择" />
  </SelectTrigger>
  <SelectContent>
    <SelectGroup>
      <SelectLabel>选项组</SelectLabel>
      <SelectItem value="option1">选项 1</SelectItem>
      <SelectItem value="option2">选项 2</SelectItem>
    </SelectGroup>
  </SelectContent>
</Select>
```

#### Checkbox
```typescript
import { Checkbox } from "@/components/ui/checkbox";

// 使用示例
<Checkbox checked={checked} onCheckedChange={setChecked} />
```

#### Switch
```typescript
import { Switch } from "@/components/ui/switch";

// 使用示例
<Switch checked={enabled} onCheckedChange={setEnabled} />
```

#### RadioGroup
```typescript
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

// 使用示例
<RadioGroup value={value} onValueChange={setValue}>
  <RadioGroupItem value="option1" id="r1" />
  <RadioGroupItem value="option2" id="r2" />
</RadioGroup>
```

#### Label
```typescript
import { Label } from "@/components/ui/label";

// 使用示例
<Label htmlFor="email">邮箱</Label>
```

#### Form (React Hook Form 集成)
```typescript
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
  useFormField,
} from "@/components/ui/form";

// 使用示例 (配合 react-hook-form + zod)
const form = useForm<FormValues>({
  resolver: zodResolver(formSchema),
});

<Form {...form}>
  <form onSubmit={form.handleSubmit(onSubmit)}>
    <FormField
      control={form.control}
      name="email"
      render={({ field }) => (
        <FormItem>
          <FormLabel>邮箱</FormLabel>
          <FormControl>
            <Input {...field} />
          </FormControl>
          <FormDescription>请输入您的邮箱地址</FormDescription>
          <FormMessage />
        </FormItem>
      )}
    />
  </form>
</Form>
```

### 1.3 展示组件

#### Card
```typescript
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";

// 使用示例
<Card>
  <CardHeader>
    <CardTitle>卡片标题</CardTitle>
    <CardDescription>卡片描述</CardDescription>
  </CardHeader>
  <CardContent>
    内容区域
  </CardContent>
  <CardFooter>
    <Button>操作</Button>
  </CardFooter>
</Card>
```

#### Badge
```typescript
import { Badge } from "@/components/ui/badge";

// Props
interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning';
}

// 使用示例
<Badge variant="success">已完成</Badge>
<Badge variant="warning">待处理</Badge>
<Badge variant="destructive">已拒绝</Badge>
```

#### StatusBadge (自定义)
```typescript
import { StatusBadge, StatusType } from "@/components/ui/StatusBadge";

// Props
interface StatusBadgeProps {
  status: 'success' | 'warning' | 'error' | 'info' | 'pending' | 'active' | 'inactive';
  children: React.ReactNode;
  dot?: boolean;           // 显示状态点
  size?: 'sm' | 'md' | 'lg';
  variant?: 'solid' | 'outline';
}

// 使用示例
<StatusBadge status="success" dot>已提交</StatusBadge>
<StatusBadge status="pending" size="sm">待审核</StatusBadge>
```

#### MetricCard (KPI 卡片)
```typescript
import { MetricCard } from "@/components/ui/MetricCard";

// Props
interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;           // 变化百分比
  changeType?: 'up' | 'down' | 'neutral';
  icon?: React.ComponentType<{ className?: string }>;
  description?: string;
  color?: 'primary' | 'success' | 'warning' | 'error' | 'info';
  loading?: boolean;
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
}

// 使用示例
<MetricCard
  title="总消耗"
  value="¥125,430"
  change={12.5}
  changeType="up"
  color="primary"
/>
```

#### Avatar
```typescript
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";

// 使用示例
<Avatar>
  <AvatarImage src="/avatar.png" />
  <AvatarFallback>CN</AvatarFallback>
</Avatar>
```

#### Progress
```typescript
import { Progress } from "@/components/ui/progress";

// 使用示例
<Progress value={66} />
```

#### Skeleton
```typescript
import { Skeleton } from "@/components/ui/skeleton";

// 使用示例
<Skeleton className="h-4 w-[250px]" />
<Skeleton className="h-12 w-12 rounded-full" />
```

#### Separator
```typescript
import { Separator } from "@/components/ui/separator";

// 使用示例
<Separator orientation="horizontal" />
<Separator orientation="vertical" />
```

### 1.4 导航组件

#### Tabs
```typescript
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

// 使用示例
<Tabs defaultValue="tab1">
  <TabsList>
    <TabsTrigger value="tab1">标签 1</TabsTrigger>
    <TabsTrigger value="tab2">标签 2</TabsTrigger>
  </TabsList>
  <TabsContent value="tab1">内容 1</TabsContent>
  <TabsContent value="tab2">内容 2</TabsContent>
</Tabs>
```

#### Breadcrumb
```typescript
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

// 使用示例
<Breadcrumb>
  <BreadcrumbList>
    <BreadcrumbItem>
      <BreadcrumbLink href="/">首页</BreadcrumbLink>
    </BreadcrumbItem>
    <BreadcrumbSeparator />
    <BreadcrumbItem>
      <BreadcrumbPage>当前页</BreadcrumbPage>
    </BreadcrumbItem>
  </BreadcrumbList>
</Breadcrumb>
```

#### DropdownMenu
```typescript
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";

// 使用示例
<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="outline">操作</Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent>
    <DropdownMenuLabel>操作菜单</DropdownMenuLabel>
    <DropdownMenuSeparator />
    <DropdownMenuItem>编辑</DropdownMenuItem>
    <DropdownMenuItem>删除</DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

### 1.5 反馈组件

#### Dialog (模态框)
```typescript
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
  DialogClose,
} from "@/components/ui/dialog";

// 使用示例
<Dialog open={open} onOpenChange={setOpen}>
  <DialogTrigger asChild>
    <Button>打开弹窗</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>确认操作</DialogTitle>
      <DialogDescription>此操作不可撤销</DialogDescription>
    </DialogHeader>
    <div>弹窗内容</div>
    <DialogFooter>
      <DialogClose asChild>
        <Button variant="outline">取消</Button>
      </DialogClose>
      <Button>确认</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

#### AlertDialog (确认对话框)
```typescript
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel,
} from "@/components/ui/alert-dialog";

// 使用示例
<AlertDialog>
  <AlertDialogTrigger asChild>
    <Button variant="destructive">删除</Button>
  </AlertDialogTrigger>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>确定删除?</AlertDialogTitle>
      <AlertDialogDescription>此操作无法撤销</AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>取消</AlertDialogCancel>
      <AlertDialogAction onClick={onDelete}>删除</AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

#### Alert
```typescript
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";

// 使用示例
<Alert variant="destructive">
  <AlertTitle>错误</AlertTitle>
  <AlertDescription>操作失败，请重试</AlertDescription>
</Alert>
```

#### Tooltip
```typescript
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from "@/components/ui/tooltip";

// 使用示例 (需要 TooltipProvider 包裹)
<TooltipProvider>
  <Tooltip>
    <TooltipTrigger asChild>
      <Button variant="ghost">?</Button>
    </TooltipTrigger>
    <TooltipContent>
      <p>提示信息</p>
    </TooltipContent>
  </Tooltip>
</TooltipProvider>
```

#### Popover
```typescript
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from "@/components/ui/popover";

// 使用示例
<Popover>
  <PopoverTrigger asChild>
    <Button>打开</Button>
  </PopoverTrigger>
  <PopoverContent>
    浮层内容
  </PopoverContent>
</Popover>
```

### 1.6 表格组件

#### Table (基础表格)
```typescript
import {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
} from "@/components/ui/table";

// 使用示例
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>名称</TableHead>
      <TableHead>金额</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell>项目A</TableCell>
      <TableCell>¥1,000</TableCell>
    </TableRow>
  </TableBody>
</Table>
```

#### DataTable (增强表格) ⭐ 推荐使用
```typescript
import { DataTable, Column, DataTableProps } from "@/components/ui/data-table/DataTable";

// Props
interface Column<T> {
  key: string;
  header: string;
  sortable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
  render?: (value: unknown, row: T, index: number) => React.ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  page?: number;
  pageSize?: number;
  total?: number;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  sortBy?: string | null;
  sortOrder?: 'asc' | 'desc';
  onSort?: (column: string) => void;
  emptyMessage?: string;
  striped?: boolean;
  hoverable?: boolean;
}

// 使用示例
const columns: Column<DailyReport>[] = [
  { key: 'date', header: '日期', sortable: true },
  { key: 'spend', header: '消耗', align: 'right',
    render: (value) => `¥${value.toFixed(2)}` },
  { key: 'status', header: '状态',
    render: (_, row) => <StatusBadge status={row.status}>{row.statusLabel}</StatusBadge> },
];

<DataTable
  columns={columns}
  data={reports}
  loading={isLoading}
  page={page}
  pageSize={20}
  total={total}
  onPageChange={setPage}
  sortBy={sortBy}
  sortOrder={sortOrder}
  onSort={handleSort}
/>
```

### 1.7 状态管理组件

#### DataStateManager (数据状态管理)
```typescript
import { DataStateManager, SkeletonCard, DashboardSkeleton } from "@/components/ui/data-state-manager";

// Props
interface DataStateManagerProps {
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  onRetry?: () => void;
  children: React.ReactNode;
  loadingComponent?: React.ReactNode;
  errorComponent?: React.ReactNode;
  emptyComponent?: React.ReactNode;
}

// 使用示例
<DataStateManager
  loading={isLoading}
  error={error?.message}
  empty={data.length === 0}
  onRetry={refetch}
>
  <DataTable columns={columns} data={data} />
</DataStateManager>
```

#### LoadingState / ErrorState / EmptyState
```typescript
import { LoadingState } from "@/components/ui/data-state/LoadingState";
import { ErrorState } from "@/components/ui/data-state/ErrorState";
import { EmptyState } from "@/components/ui/data-state/EmptyState";

// 独立使用
<LoadingState message="加载中..." />
<ErrorState message="加载失败" onRetry={refetch} />
<EmptyState message="暂无数据" />
```

### 1.8 日期选择

#### Calendar
```typescript
import { Calendar } from "@/components/ui/calendar";

// 使用示例 (基于 react-day-picker)
<Calendar
  mode="single"
  selected={date}
  onSelect={setDate}
  disabled={(date) => date > new Date()}
/>
```

### 1.9 主题切换

#### ThemeToggle
```typescript
import { ThemeToggle } from "@/components/ui/theme-toggle";

// 使用示例
<ThemeToggle />
```

### 1.10 SSR 安全

#### SSRSafeWrapper
```typescript
import { SSRSafeWrapper } from "@/components/ui/SSRSafeWrapper";

// 使用示例 (避免 hydration 错误)
<SSRSafeWrapper>
  <ClientOnlyComponent />
</SSRSafeWrapper>
```

### 1.11 侧边抽屉 (Sheet)

#### Sheet
```typescript
import {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetHeader,
  SheetFooter,
  SheetTitle,
  SheetDescription,
  SheetClose,
} from "@/components/ui/sheet";

// Props
interface SheetContentProps {
  side?: 'top' | 'bottom' | 'left' | 'right';  // 默认 right
}

// 使用示例
<Sheet>
  <SheetTrigger asChild>
    <Button>打开抽屉</Button>
  </SheetTrigger>
  <SheetContent side="right">
    <SheetHeader>
      <SheetTitle>抽屉标题</SheetTitle>
      <SheetDescription>抽屉描述</SheetDescription>
    </SheetHeader>
    <div>抽屉内容</div>
    <SheetFooter>
      <SheetClose asChild>
        <Button>关闭</Button>
      </SheetClose>
    </SheetFooter>
  </SheetContent>
</Sheet>
```

### 1.12 手风琴 (Accordion)

#### Accordion
```typescript
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";

// 使用示例
<Accordion type="single" collapsible>
  <AccordionItem value="item-1">
    <AccordionTrigger>标题 1</AccordionTrigger>
    <AccordionContent>内容 1</AccordionContent>
  </AccordionItem>
  <AccordionItem value="item-2">
    <AccordionTrigger>标题 2</AccordionTrigger>
    <AccordionContent>内容 2</AccordionContent>
  </AccordionItem>
</Accordion>
```

### 1.13 命令面板 (Command)

#### Command
```typescript
import {
  Command,
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandShortcut,
  CommandSeparator,
} from "@/components/ui/command";

// 使用示例 (Ctrl+K 搜索面板)
<CommandDialog open={open} onOpenChange={setOpen}>
  <CommandInput placeholder="搜索..." />
  <CommandList>
    <CommandEmpty>未找到结果</CommandEmpty>
    <CommandGroup heading="建议">
      <CommandItem>
        <span>日历</span>
        <CommandShortcut>⌘C</CommandShortcut>
      </CommandItem>
    </CommandGroup>
  </CommandList>
</CommandDialog>
```

### 1.14 滑块 (Slider)

#### Slider
```typescript
import { Slider } from "@/components/ui/slider";

// Props: 继承 @radix-ui/react-slider
// 使用示例
<Slider
  defaultValue={[50]}
  max={100}
  step={1}
  onValueChange={(value) => console.log(value)}
/>
```

### 1.15 切换按钮 (Toggle)

#### Toggle
```typescript
import { Toggle } from "@/components/ui/toggle";

// Props
interface ToggleProps {
  variant?: 'default' | 'outline';
  size?: 'default' | 'sm' | 'lg';
  pressed?: boolean;
  onPressedChange?: (pressed: boolean) => void;
}

// 使用示例
<Toggle aria-label="切换粗体" pressed={bold} onPressedChange={setBold}>
  <Bold className="h-4 w-4" />
</Toggle>
```

#### ToggleGroup
```typescript
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

// 使用示例
<ToggleGroup type="single" value={alignment} onValueChange={setAlignment}>
  <ToggleGroupItem value="left">左对齐</ToggleGroupItem>
  <ToggleGroupItem value="center">居中</ToggleGroupItem>
  <ToggleGroupItem value="right">右对齐</ToggleGroupItem>
</ToggleGroup>
```

### 1.16 滚动区域 (ScrollArea)

#### ScrollArea
```typescript
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";

// 使用示例
<ScrollArea className="h-[200px] w-[350px] rounded-md border p-4">
  长内容...
  <ScrollBar orientation="vertical" />
</ScrollArea>
```

### 1.17 Toast 通知 (Sonner)

#### Toaster
```typescript
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";

// 在 layout.tsx 中添加
<Toaster />

// 使用示例
toast.success("操作成功");
toast.error("操作失败");
toast.info("提示信息");
toast.warning("警告信息");
toast.loading("加载中...");
```

### 1.18 其他新增组件

#### Collapsible (折叠)
```typescript
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from "@/components/ui/collapsible";

<Collapsible open={isOpen} onOpenChange={setIsOpen}>
  <CollapsibleTrigger>展开/收起</CollapsibleTrigger>
  <CollapsibleContent>可折叠内容</CollapsibleContent>
</Collapsible>
```

#### NavigationMenu (导航菜单)
```typescript
import {
  NavigationMenu,
  NavigationMenuList,
  NavigationMenuItem,
  NavigationMenuTrigger,
  NavigationMenuContent,
  NavigationMenuLink,
} from "@/components/ui/navigation-menu";
```

#### HoverCard (悬浮卡片)
```typescript
import { HoverCard, HoverCardTrigger, HoverCardContent } from "@/components/ui/hover-card";

<HoverCard>
  <HoverCardTrigger>悬浮触发</HoverCardTrigger>
  <HoverCardContent>悬浮内容</HoverCardContent>
</HoverCard>
```

#### ContextMenu (右键菜单)
```typescript
import {
  ContextMenu,
  ContextMenuTrigger,
  ContextMenuContent,
  ContextMenuItem,
} from "@/components/ui/context-menu";
```

#### Menubar (菜单栏)
```typescript
import {
  Menubar,
  MenubarMenu,
  MenubarTrigger,
  MenubarContent,
  MenubarItem,
} from "@/components/ui/menubar";
```

#### AspectRatio (宽高比)
```typescript
import { AspectRatio } from "@/components/ui/aspect-ratio";

<AspectRatio ratio={16 / 9}>
  <img src="..." alt="..." className="object-cover" />
</AspectRatio>
```

---

## 2. Dashboard 组件 (16 个)

### 2.1 图表组件

#### TrendChart (趋势图)
```typescript
import { TrendChart, TrendDataPoint } from "@/components/dashboard/TrendChart";

// Props
interface TrendDataPoint {
  date: string;
  value: number;
  label?: string;
}

interface TrendChartProps {
  title: string;
  description?: string;
  data: TrendDataPoint[];
  height?: number;
  showTrend?: boolean;
}

// 使用示例
<TrendChart
  title="消耗趋势"
  data={[
    { date: '2024-01-01', value: 1000 },
    { date: '2024-01-02', value: 1200 },
  ]}
  height={300}
  showTrend
/>
```

#### DonutChart (环形图)
```typescript
import { DonutChart } from "@/components/dashboard/DonutChart";

// 使用示例
<DonutChart data={channelData} />
```

#### ChartCard (图表容器)
```typescript
import { ChartCard } from "@/components/dashboard/ChartCard";

// 使用示例
<ChartCard title="消耗分布">
  <DonutChart data={data} />
</ChartCard>
```

### 2.2 统计组件

#### DashboardStats (统计卡片组)
```typescript
import { DashboardStats } from "@/components/dashboard/DashboardStats";

// 使用示例
<DashboardStats />
```

#### ProjectTopList (Top 5 列表)
```typescript
import { ProjectTopList } from "@/components/dashboard/ProjectTopList";

// Props
interface ProjectItem {
  id: string;
  name: string;
  roi: number;
  spend: string;
  status: 'active' | 'paused';
  trend: 'up' | 'down' | 'neutral';
}

interface ProjectTopListProps {
  title?: string;
  projects?: ProjectItem[];
  className?: string;
}

// 使用示例
<ProjectTopList
  title="消耗 Top 5"
  projects={topProjects}
/>
```

### 2.3 表格组件

#### ProjectTable (项目表格)
```typescript
import { ProjectTable } from "@/components/dashboard/ProjectTable";
```

#### AbnormalAccountsTable (异常账户表格)
```typescript
import { AbnormalAccountsTable } from "@/components/dashboard/AbnormalAccountsTable";
```

### 2.4 卡片组件

#### ModuleCard / ModuleGrid
```typescript
import { ModuleCard } from "@/components/dashboard/ModuleCard";
import { ModuleGrid } from "@/components/dashboard/ModuleGrid";
```

#### TodayTasksCard (今日待办)
```typescript
import { TodayTasksCard } from "@/components/dashboard/TodayTasksCard";
```

### 2.5 布局组件

#### AppLayout (仪表盘布局)
```typescript
import { AppLayout } from "@/components/dashboard/AppLayout";

// 包含 Sidebar + Header + 主内容区
<AppLayout>
  <DashboardContent />
</AppLayout>
```

#### Sidebar (侧边栏)
```typescript
import { Sidebar } from "@/components/dashboard/sidebar";
```

#### Header (头部)
```typescript
import { Header } from "@/components/dashboard/header";
```

---

## 3. Layout 组件 (9 个)

### 3.1 应用布局

#### AppLayout ⭐ 推荐使用
```typescript
import { AppLayout } from "@/components/layout/AppLayout";

// 主应用布局，包含侧边栏和头部
<AppLayout>
  <PageContent />
</AppLayout>
```

#### DashboardLayout
```typescript
import { DashboardLayout } from "@/components/layout/DashboardLayout";
```

### 3.2 页面模板

#### PageHeader
```typescript
import { PageHeader } from "@/components/layout/page-header";

// 使用示例
<PageHeader
  title="日报管理"
  description="管理每日投放数据"
  action={<Button>新建日报</Button>}
/>
```

#### PageTemplate
```typescript
import { PageTemplate } from "@/components/layout/page-template";
```

### 3.3 导航组件

#### Header
```typescript
import { Header } from "@/components/layout/Header";
```

#### Sidebar
```typescript
import { Sidebar } from "@/components/layout/Sidebar";
```

#### ModernNavigation / OptimizedNavigation
```typescript
import { ModernNavigation } from "@/components/layout/modern-navigation";
import { OptimizedNavigation } from "@/components/layout/optimized-navigation";
```

### 3.4 已弃用

#### AppShell ⚠️ DEPRECATED
```typescript
// ❌ 请勿使用
import { AppShell } from "@/components/layout/AppShell";

// ✅ 改用 AppLayout
import { AppLayout } from "@/components/layout/AppLayout";
```

---

## 4. Shared 组件 (2 个)

### 4.1 错误边界

#### GlobalErrorBoundary
```typescript
import { GlobalErrorBoundary } from "@/components/shared/GlobalErrorBoundary";

// 全局错误边界
<GlobalErrorBoundary>
  <App />
</GlobalErrorBoundary>
```

#### ErrorBoundary
```typescript
import { ErrorBoundary } from "@/components/shared/error-boundary";

// 局部错误边界
<ErrorBoundary fallback={<ErrorState />}>
  <ComponentThatMightError />
</ErrorBoundary>
```

---

## 5. 组件使用规范

### 5.1 导入约定
```typescript
// UI 组件从 @/components/ui 导入
import { Button, Input, Card } from "@/components/ui";

// 或按需导入单个文件
import { Button } from "@/components/ui/button";
import { DataTable } from "@/components/ui/data-table/DataTable";
```

### 5.2 表单最佳实践
```typescript
// 推荐: React Hook Form + Zod
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";

const schema = z.object({
  amount: z.number().min(0, "金额不能为负"),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "日期格式错误"),
});

const form = useForm({
  resolver: zodResolver(schema),
  defaultValues: { amount: 0, date: '' },
});
```

### 5.3 数据表格最佳实践
```typescript
// 推荐: 使用 DataTable + DataStateManager
import { DataTable, Column } from "@/components/ui/data-table/DataTable";
import { DataStateManager } from "@/components/ui/data-state-manager";
import { StatusBadge } from "@/components/ui/StatusBadge";

const columns: Column<Report>[] = [
  { key: 'date', header: '日期', sortable: true },
  { key: 'amount', header: '金额', align: 'right',
    render: (v) => `¥${(v as number).toFixed(2)}` },
  { key: 'status', header: '状态',
    render: (_, row) => <StatusBadge status={row.status}>{row.statusLabel}</StatusBadge> },
];

<DataStateManager loading={isLoading} error={error} empty={data.length === 0}>
  <DataTable columns={columns} data={data} />
</DataStateManager>
```

### 5.4 弹窗最佳实践
```typescript
// 推荐: 受控模式
const [open, setOpen] = useState(false);

<Dialog open={open} onOpenChange={setOpen}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>标题</DialogTitle>
    </DialogHeader>
    {/* 内容 */}
    <DialogFooter>
      <Button variant="outline" onClick={() => setOpen(false)}>取消</Button>
      <Button onClick={handleSubmit}>确认</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

---

## 6. 组件完整清单

### UI 组件 (58 个)
| 组件 | 路径 | 状态 |
|------|------|------|
| accordion | ui/accordion.tsx | ✅ Active |
| alert-dialog | ui/alert-dialog.tsx | ✅ Active |
| alert | ui/alert.tsx | ✅ Active |
| aspect-ratio | ui/aspect-ratio.tsx | ✅ Active |
| avatar | ui/avatar.tsx | ✅ Active |
| badge | ui/badge.tsx | ✅ Active |
| breadcrumb | ui/breadcrumb.tsx | ✅ Active |
| button | ui/button.tsx | ✅ Active |
| calendar | ui/calendar.tsx | ✅ Active |
| card | ui/card.tsx | ✅ Active |
| checkbox | ui/checkbox.tsx | ✅ Active |
| collapsible | ui/collapsible.tsx | ✅ Active |
| command | ui/command.tsx | ✅ Active |
| context-menu | ui/context-menu.tsx | ✅ Active |
| data-state-manager | ui/data-state-manager.tsx | ✅ Active |
| data-table | ui/data-table.tsx | ✅ Active |
| DataTable | ui/data-table/DataTable.tsx | ✅ Active |
| DataTablePagination | ui/data-table/DataTablePagination.tsx | ✅ Active |
| DataTableToolbar | ui/data-table/DataTableToolbar.tsx | ✅ Active |
| DataStateManager | ui/data-state/DataStateManager.tsx | ✅ Active |
| DataStateProvider | ui/data-state/DataStateProvider.tsx | ✅ Active |
| EmptyState | ui/data-state/EmptyState.tsx | ✅ Active |
| ErrorState | ui/data-state/ErrorState.tsx | ✅ Active |
| LoadingState | ui/data-state/LoadingState.tsx | ✅ Active |
| dialog | ui/dialog.tsx | ✅ Active |
| dropdown-menu | ui/dropdown-menu.tsx | ✅ Active |
| form | ui/form.tsx | ✅ Active |
| hover-card | ui/hover-card.tsx | ✅ Active |
| input | ui/input.tsx | ✅ Active |
| label | ui/label.tsx | ✅ Active |
| menubar | ui/menubar.tsx | ✅ Active |
| MetricCard | ui/MetricCard.tsx | ✅ Active |
| modern-dashboard | ui/modern-dashboard.tsx | ✅ Active |
| navigation-menu | ui/navigation-menu.tsx | ✅ Active |
| optimized-button | ui/optimized-button.tsx | ✅ Active |
| optimized-dashboard | ui/optimized-dashboard.tsx | ✅ Active |
| optimized-metric-card | ui/optimized-metric-card.tsx | ✅ Active |
| popover | ui/popover.tsx | ✅ Active |
| progress | ui/progress.tsx | ✅ Active |
| radio-group | ui/radio-group.tsx | ✅ Active |
| scroll-area | ui/scroll-area.tsx | ✅ Active |
| select | ui/select.tsx | ✅ Active |
| separator | ui/separator.tsx | ✅ Active |
| sheet | ui/sheet.tsx | ✅ Active |
| skeleton | ui/skeleton.tsx | ✅ Active |
| slider | ui/slider.tsx | ✅ Active |
| sonner | ui/sonner.tsx | ✅ Active |
| SSRSafeWrapper | ui/SSRSafeWrapper.tsx | ✅ Active |
| StatusBadge | ui/StatusBadge.tsx | ✅ Active |
| switch | ui/switch.tsx | ✅ Active |
| table | ui/table.tsx | ✅ Active |
| tabs | ui/tabs.tsx | ✅ Active |
| textarea | ui/textarea.tsx | ✅ Active |
| theme-toggle | ui/theme-toggle.tsx | ✅ Active |
| toggle | ui/toggle.tsx | ✅ Active |
| toggle-group | ui/toggle-group.tsx | ✅ Active |
| tooltip | ui/tooltip.tsx | ✅ Active |
| user-profile-dropdown | ui/user-profile-dropdown.tsx | ✅ Active |

### Dashboard 组件 (16 个)
| 组件 | 路径 | 状态 |
|------|------|------|
| AbnormalAccountsTable | dashboard/AbnormalAccountsTable.tsx | ✅ Active |
| AppLayout | dashboard/AppLayout.tsx | ✅ Active |
| ChartCard | dashboard/ChartCard.tsx | ✅ Active |
| ChartLegend | dashboard/ChartLegend.tsx | ✅ Active |
| DashboardStats | dashboard/DashboardStats.tsx | ✅ Active |
| DonutChart | dashboard/DonutChart.tsx | ✅ Active |
| header | dashboard/header.tsx | ✅ Active |
| ModuleCard | dashboard/ModuleCard.tsx | ✅ Active |
| ModuleGrid | dashboard/ModuleGrid.tsx | ✅ Active |
| ProjectTable | dashboard/ProjectTable.tsx | ✅ Active |
| ProjectTopList | dashboard/ProjectTopList.tsx | ✅ Active |
| RightColumn | dashboard/RightColumn.tsx | ✅ Active |
| sidebar | dashboard/sidebar.tsx | ✅ Active |
| TodayTasksCard | dashboard/TodayTasksCard.tsx | ✅ Active |
| TrendChart | dashboard/TrendChart.tsx | ✅ Active |
| TrendChartCard | dashboard/TrendChartCard.tsx | ✅ Active |

### Layout 组件 (9 个)
| 组件 | 路径 | 状态 |
|------|------|------|
| AppLayout | layout/AppLayout.tsx | ✅ Active |
| AppShell | layout/AppShell.tsx | ⚠️ Deprecated |
| DashboardLayout | layout/DashboardLayout.tsx | ✅ Active |
| Header | layout/Header.tsx | ✅ Active |
| modern-navigation | layout/modern-navigation.tsx | ✅ Active |
| optimized-navigation | layout/optimized-navigation.tsx | ✅ Active |
| page-header | layout/page-header.tsx | ✅ Active |
| page-template | layout/page-template.tsx | ✅ Active |
| Sidebar | layout/Sidebar.tsx | ✅ Active |

### Shared 组件 (2 个)
| 组件 | 路径 | 状态 |
|------|------|------|
| error-boundary | shared/error-boundary.tsx | ✅ Active |
| GlobalErrorBoundary | shared/GlobalErrorBoundary.tsx | ✅ Active |

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.1 | 2025-12-24 | 新增 14 个 shadcn/ui 组件：accordion, command, sheet, slider, toggle, toggle-group, scroll-area, sonner, collapsible, navigation-menu, hover-card, context-menu, menubar, aspect-ratio |
| v1.0 | 2025-12-24 | 初始版本，收录 71 个组件 |

---

**维护者**: AI 广告代投系统开发团队
**引用文档**:
- shadcn/ui 官方文档
- `frontend/src/components/` 源代码
