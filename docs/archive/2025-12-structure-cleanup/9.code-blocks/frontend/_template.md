# [代码块名称] - [中文名]

> **复用级别**: :red_circle: 核心 / :yellow_circle: 模块 / :green_circle: 专用
> **源码位置**: `src/xxx/xxx.tsx`
> **最后更新**: YYYY-MM-DD

---

## 1. 概述

一句话描述这个代码块解决什么问题。

**使用场景**:
- 场景 1
- 场景 2

---

## 2. 接口契约

### 2.1 Props (输入)

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `prop1` | `string` | :white_check_mark: | - | 描述 |
| `prop2` | `number` | :x: | `0` | 描述 |
| `onAction` | `() => void` | :x: | - | 回调函数 |

### 2.2 Slots / Children

| 插槽 | 类型 | 说明 |
|------|------|------|
| `children` | `ReactNode` | 主内容 |
| `header` | `ReactNode` | 头部区域 |

### 2.3 暴露方法 (Ref)

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `reset()` | - | `void` | 重置状态 |

---

## 3. 依赖

### 3.1 Context 依赖

| Context | 用途 | 必须 |
|---------|------|------|
| `AuthContext` | 获取用户信息 | :white_check_mark: |
| `FilterContext` | 获取筛选条件 | :x: |

### 3.2 服务依赖

| 服务 | 用途 |
|------|------|
| `xxxApi` | 获取数据 |

### 3.3 代码块依赖

| 代码块 | 用途 |
|--------|------|
| `LoadingState` | 加载状态 |
| `ErrorState` | 错误状态 |

---

## 4. 使用示例

### 4.1 基础用法

```tsx
import { ComponentName } from '@/components/xxx'

export function MyPage() {
  return (
    <ComponentName
      prop1="value"
      prop2={100}
      onAction={() => console.log('clicked')}
    />
  )
}
```

### 4.2 高级用法

```tsx
import { ComponentName } from '@/components/xxx'

export function AdvancedExample() {
  const ref = useRef<ComponentNameRef>(null)

  return (
    <ComponentName
      ref={ref}
      prop1="value"
    >
      <CustomContent />
    </ComponentName>
  )
}
```

---

## 5. 组合规则

### 5.1 推荐组合

| 组合代码块 | 组合方式 | 效果 |
|-----------|---------|------|
| `PageHeader` | 容器包裹 | 提供页面标题 |
| `DataTable` | 并列使用 | 列表展示 |

### 5.2 互斥组合

| 互斥代码块 | 原因 |
|-----------|------|
| `SimpleTable` | 功能重复 |

---

## 6. 样式定制

### 6.1 CSS 变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `--card-padding` | `16px` | 内边距 |
| `--card-radius` | `8px` | 圆角 |

### 6.2 Tailwind 类覆盖

```tsx
<ComponentName className="custom-class" />
```

---

## 7. 测试

### 7.1 测试文件位置

```
src/components/xxx/__tests__/ComponentName.test.tsx
```

### 7.2 测试用例清单

- [ ] 基础渲染测试
- [ ] Props 变化测试
- [ ] 交互行为测试
- [ ] 边界条件测试

---

## 8. 源码位置

| 类型 | 路径 |
|------|------|
| 组件 | `src/components/xxx/ComponentName.tsx` |
| 类型 | `src/components/xxx/types.ts` |
| 测试 | `src/components/xxx/__tests__/` |
| 样式 | `src/components/xxx/styles.css` |

---

## 9. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | YYYY-MM-DD | 初始版本 |

---

## 10. 相关文档

- [模块规格书](../../10.module-specs/xxx.md)
- [设计稿](链接)
