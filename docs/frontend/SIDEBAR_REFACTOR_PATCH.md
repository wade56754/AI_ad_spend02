# Sidebar 宽度和配色统一重构 Patch

> 目标：统一 Sidebar 宽度（展开 240px、折叠 72px），统一使用 sidebar 相关 CSS 变量。

---

## 📊 现状分析

### 当前宽度设置
- **展开态**: `16rem` (256px) - 在 `sidebar.tsx` 第 29 行
- **折叠态**: `3rem` (48px) - 在 `sidebar.tsx` 第 31 行
- **移动端**: `18rem` (288px) - 保持不变

### 当前颜色使用
- ✅ `globals.css` 已定义 sidebar CSS 变量（HSL 格式）
- ✅ `tailwind.config.ts` 已映射 sidebar 颜色到 Tailwind
- ✅ `sidebar.tsx` 已使用 `bg-sidebar`, `text-sidebar-foreground`, `border-sidebar-border` 等变量
- ⚠️ 宽度使用硬编码常量，需要改为统一标准

---

## 🎯 统一方案

### 宽度标准
- **展开态**: `240px` (`15rem`)
- **折叠态**: `72px` (`4.5rem`)
- **移动端**: `288px` (`18rem`) - 保持不变

### 颜色系统
所有颜色统一使用以下 Tailwind 变量：
- `bg-sidebar` - 背景色
- `text-sidebar-foreground` - 文字色
- `bg-sidebar-accent` - 激活/悬浮背景
- `text-sidebar-accent-foreground` - 激活/悬浮文字
- `border-sidebar-border` - 边框色
- `ring-sidebar-ring` - 焦点环

---

## 📝 修改前后对比

### 1. sidebar.tsx - 宽度常量

**修改前**:
```typescript
const SIDEBAR_WIDTH = '16rem';        // 256px
const SIDEBAR_WIDTH_ICON = '3rem';    // 48px
```

**修改后**:
```typescript
const SIDEBAR_WIDTH = '15rem';        // 240px
const SIDEBAR_WIDTH_ICON = '4.5rem';  // 72px
```

---

## 🔧 完整 Patch

```diff
--- a/frontend/components/ui/sidebar.tsx
+++ b/frontend/components/ui/sidebar.tsx
@@ -26,7 +26,7 @@
 const SIDEBAR_COOKIE_NAME = 'sidebar_state';
 const SIDEBAR_COOKIE_MAX_AGE = 60 * 60 * 24 * 7;
-const SIDEBAR_WIDTH = '16rem';
+const SIDEBAR_WIDTH = '15rem';
 const SIDEBAR_WIDTH_MOBILE = '18rem';
-const SIDEBAR_WIDTH_ICON = '3rem';
+const SIDEBAR_WIDTH_ICON = '4.5rem';
 const SIDEBAR_KEYBOARD_SHORTCUT = 'b';
```

---

## ✅ 验证清单

### 宽度验证
- [ ] 桌面端展开态宽度为 240px
- [ ] 桌面端折叠态宽度为 72px
- [ ] 移动端宽度为 288px（不变）
- [ ] 过渡动画流畅

### 颜色验证
- [ ] 所有背景色使用 `bg-sidebar`
- [ ] 所有文字色使用 `text-sidebar-foreground`
- [ ] 激活状态使用 `bg-sidebar-accent`
- [ ] 边框使用 `border-sidebar-border`
- [ ] 无硬编码 HEX 颜色

### 布局验证
- [ ] Dashboard 布局正确适配新宽度
- [ ] 主内容区不被 Sidebar 遮挡
- [ ] 响应式布局正常（移动端/桌面端）

---

## 📚 相关文件

- `frontend/components/ui/sidebar.tsx` - Sidebar 基础组件
- `frontend/components/layout/app-sidebar.tsx` - 应用侧边栏实现
- `frontend/app/dashboard/layout.tsx` - Dashboard 布局
- `frontend/app/globals.css` - CSS 变量定义
- `frontend/tailwind.config.ts` - Tailwind 配置

---

**版本**: v1.0  
**最后更新**: 2024-12-03

