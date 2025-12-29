/**
 * 前端组件库索引
 *
 * 统一导出所有 UI 组件，便于使用
 *
 * 使用方式:
 * ```tsx
 * import { Button, Card, DataTable, MetricCard } from '@/components'
 * ```
 *
 * Version: 1.0
 * Last Updated: 2025-12-28
 */

// ============================================
// 基础 UI 组件 (shadcn/ui)
// ============================================

// 按钮
export { Button, buttonVariants } from './ui/button'

// 输入控件
export { Input } from './ui/input'
export { Textarea } from './ui/textarea'
export { Checkbox } from './ui/checkbox'
export { RadioGroup, RadioGroupItem } from './ui/radio-group'
export { Switch } from './ui/switch'
export { Slider } from './ui/slider'
export {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from './ui/select'

// 表单
export {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  useFormField,
} from './ui/form'
export { Label } from './ui/label'
export { Calendar } from './ui/calendar'

// ============================================
// 数据展示
// ============================================

// 表格
export {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from './ui/table'

// 卡片
export {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from './ui/card'

// 标签/徽章
export { Badge, badgeVariants } from './ui/badge'
export { Avatar, AvatarFallback, AvatarImage } from './ui/avatar'

// 进度/骨架屏
export { Progress } from './ui/progress'
export { Skeleton } from './ui/skeleton'

// ============================================
// 反馈组件
// ============================================

// 警告/提示
export { Alert, AlertDescription, AlertTitle } from './ui/alert'

// 对话框
export {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from './ui/alert-dialog'

export {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog'

// 抽屉
export {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from './ui/sheet'

// Toast (sonner)
export { Toaster } from './ui/sonner'

// ============================================
// 导航组件
// ============================================

// 标签页
export { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'

// 面包屑
export {
  Breadcrumb,
  BreadcrumbEllipsis,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from './ui/breadcrumb'

// 导航菜单
export {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuIndicator,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
  NavigationMenuViewport,
  navigationMenuTriggerStyle,
} from './ui/navigation-menu'

// 菜单栏
export {
  Menubar,
  MenubarCheckboxItem,
  MenubarContent,
  MenubarGroup,
  MenubarItem,
  MenubarLabel,
  MenubarMenu,
  MenubarPortal,
  MenubarRadioGroup,
  MenubarRadioItem,
  MenubarSeparator,
  MenubarShortcut,
  MenubarSub,
  MenubarSubContent,
  MenubarSubTrigger,
  MenubarTrigger,
} from './ui/menubar'

// 下拉菜单
export {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuPortal,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from './ui/dropdown-menu'

// 右键菜单
export {
  ContextMenu,
  ContextMenuCheckboxItem,
  ContextMenuContent,
  ContextMenuGroup,
  ContextMenuItem,
  ContextMenuLabel,
  ContextMenuPortal,
  ContextMenuRadioGroup,
  ContextMenuRadioItem,
  ContextMenuSeparator,
  ContextMenuShortcut,
  ContextMenuSub,
  ContextMenuSubContent,
  ContextMenuSubTrigger,
  ContextMenuTrigger,
} from './ui/context-menu'

// ============================================
// 布局组件
// ============================================

export { Separator } from './ui/separator'
export { ScrollArea, ScrollBar } from './ui/scroll-area'
export { AspectRatio } from './ui/aspect-ratio'

// 折叠
export { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible'

// 手风琴
export {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from './ui/accordion'

// ============================================
// 覆盖层组件
// ============================================

// 弹出框
export { Popover, PopoverContent, PopoverTrigger } from './ui/popover'

// 提示
export {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from './ui/tooltip'

// 悬浮卡片
export { HoverCard, HoverCardContent, HoverCardTrigger } from './ui/hover-card'

// 命令面板
export {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from './ui/command'

// ============================================
// 切换组件
// ============================================

export { Toggle, toggleVariants } from './ui/toggle'
export { ToggleGroup, ToggleGroupItem } from './ui/toggle-group'

// ============================================
// 业务组件
// ============================================

// 指标卡片
export { MetricCard } from './ui/MetricCard'

// 状态标签
export { StatusBadge } from './ui/StatusBadge'

// SSR 安全包装器
export { SSRSafeWrapper } from './ui/SSRSafeWrapper'

// 主题切换
export { ThemeToggle } from './ui/theme-toggle'

// 用户下拉菜单
export { UserProfileDropdown } from './ui/user-profile-dropdown'

// ============================================
// 数据表格组件
// ============================================

export { DataTable } from './ui/data-table/DataTable'
export type { DataTableProps, Column } from './ui/data-table/DataTable'
export { DataTablePagination } from './ui/data-table/DataTablePagination'
export { DataTableToolbar } from './ui/data-table/DataTableToolbar'

// ============================================
// 数据状态组件
// ============================================

export { DataStateProvider } from './ui/data-state/DataStateProvider'
export { DataStateManager } from './ui/data-state/DataStateManager'
export {
  LoadingState,
  Skeleton as DataSkeleton,
  CardSkeleton,
  MetricCardSkeleton,
  TableSkeleton,
} from './ui/data-state/LoadingState'
export { EmptyState } from './ui/data-state/EmptyState'
export { ErrorState } from './ui/data-state/ErrorState'

// ============================================
// 布局组件
// ============================================

export { default as AppLayout } from './layout/AppLayout'
export { default as AppShell } from './layout/AppShell'
export { default as DashboardLayout } from './layout/DashboardLayout'
export { default as Header } from './layout/Header'
export { default as Sidebar } from './layout/Sidebar'

// ============================================
// 错误边界
// ============================================

export { GlobalErrorBoundary } from './shared/GlobalErrorBoundary'
export { ErrorBoundary, withErrorBoundary } from './shared/error-boundary'

// ============================================
// 优化版组件 (Phase 3)
// ============================================

export { OptimizedButton } from './ui/optimized-button'
export type { OptimizedButtonProps, ButtonVariant, ButtonSize } from './ui/optimized-button'
export { OptimizedMetricCard } from './ui/optimized-metric-card'
export type { OptimizedMetricCardProps, TrendType, MetricColor } from './ui/optimized-metric-card'
