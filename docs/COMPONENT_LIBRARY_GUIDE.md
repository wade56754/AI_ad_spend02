# AI广告代投系统 - 组件库开发指南

> **版本**: v1.0
> **更新日期**: 2024-11-13
> **开发团队**: Claude Frontend Team

---

## 📋 目录
1. [组件库架构](#组件库架构)
2. [开发规范](#开发规范)
3. [组件分类](#组件分类)
4. [命名规范](#命名规范)
5. [组件结构](#组件结构)
6. [状态管理](#状态管理)
7. [测试规范](#测试规范)
8. [文档规范](#文档规范)
9. [发布流程](#发布流程)

---

## 🏗️ 组件库架构

### 目录结构
```
frontend/
├── components/
│   ├── ui/                    # 基础UI组件
│   │   ├── Button/
│   │   │   ├── index.tsx      # 组件入口
│   │   │   ├── Button.tsx     # 主组件
│   │   │   ├── Button.stories.tsx # Storybook故事
│   │   │   ├── Button.test.tsx    # 单元测试
│   │   │   └── types.ts       # 类型定义
│   │   ├── Card/
│   │   ├── Input/
│   │   ├── Modal/
│   │   ├── Badge/
│   │   ├── Tooltip/
│   │   ├── Dropdown/
│   │   └── index.ts           # 统一导出
│   ├── layout/                # 布局组件
│   │   ├── Header/
│   │   ├── Sidebar/
│   │   ├── Footer/
│   │   ├── Container/
│   │   └── index.ts
│   ├── charts/                # 图表组件
│   │   ├── LineChart/
│   │   ├── BarChart/
│   │   ├── PieChart/
│   │   └── index.ts
│   ├── forms/                 # 表单组件
│   │   ├── FormField/
│   │   ├── FormInput/
│   │   ├── FormSelect/
│   │   ├── FormCheckbox/
│   │   └── index.ts
│   └── features/              # 功能组件
│       ├── ProjectCard/
│       ├── MetricCard/
│       ├── StatusBadge/
│       ├── DataTable/
│       └── index.ts
├── hooks/                      # 自定义Hook
│   ├── useAnimation.ts
│   ├── useLocalStorage.ts
│   ├── useDebounce.ts
│   └── index.ts
├── utils/                      # 工具函数
│   ├── formatters.ts
│   ├── validators.ts
│   ├── constants.ts
│   └── index.ts
├── types/                      # 类型定义
│   ├── ui.ts
│   ├── api.ts
│   ├── common.ts
│   └── index.ts
└── styles/
    ├── design-system.css       # 设计系统
    ├── components.css          # 组件样式
    └── utilities.css           # 工具类样式
```

---

## 📝 开发规范

### 1. TypeScript 规范
```typescript
// 严格的类型定义
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  children: React.ReactNode;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
}

// 使用泛型
interface DataTableProps<T> {
  data: T[];
  columns: ColumnConfig<T>[];
  onRowClick?: (row: T) => void;
  loading?: boolean;
}
```

### 2. 组件编写规范
```tsx
// 使用 forwardRef 支持ref传递
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({
    variant = 'primary',
    size = 'md',
    disabled = false,
    loading = false,
    icon,
    children,
    className,
    onClick,
    ...props
  }, ref) => {

    // 处理按钮点击
    const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
      if (disabled || loading) return;
      onClick?.(event);
    };

    // 构建CSS类名
    const buttonClasses = cn(
      'btn',
      `btn-${variant}`,
      `btn-${size}`,
      {
        'btn-loading': loading,
        'btn-disabled': disabled,
      },
      className
    );

    return (
      <button
        ref={ref}
        className={buttonClasses}
        disabled={disabled}
        onClick={handleClick}
        {...props}
      >
        {loading && <LoadingSpinner className="btn-loading-spinner" />}
        {icon && <span className="btn-icon">{icon}</span>}
        <span className="btn-text">{children}</span>
      </button>
    );
  }
);

Button.displayName = 'Button';
```

### 3. 样式规范
```css
/* 使用CSS变量 */
.btn {
  padding: var(--btn-padding-y) var(--btn-padding-x);
  border-radius: var(--btn-border-radius);
  font-weight: var(--btn-font-weight);
  transition: all var(--btn-transition);
}

/* 变体样式 */
.btn-primary {
  background: var(--gradient-primary);
  color: white;
}

.btn-secondary {
  background: transparent;
  color: var(--primary-500);
  border: 2px solid var(--primary-500);
}

/* 尺寸变体 */
.btn-sm {
  padding: var(--btn-padding-sm-y) var(--btn-padding-sm-x);
  font-size: var(--btn-font-size-sm);
}

.btn-lg {
  padding: var(--btn-padding-lg-y) var(--btn-padding-lg-x);
  font-size: var(--btn-font-size-lg);
}
```

---

## 🧩 组件分类

### 1. 基础UI组件 (ui/)
**用途**: 构成界面的基础元素，不包含业务逻辑

#### Button - 按钮
```typescript
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}
```

#### Card - 卡片
```typescript
interface CardProps {
  hoverable?: boolean;
  loading?: boolean;
  bordered?: boolean;
  className?: string;
  children: React.ReactNode;
}

interface CardHeaderProps {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  extra?: React.ReactNode;
}

interface CardContentProps {
  children: React.ReactNode;
}
```

#### Modal - 模态框
```typescript
interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: React.ReactNode;
  footer?: React.ReactNode;
  width?: number;
  closable?: boolean;
  maskClosable?: boolean;
  centered?: boolean;
  children: React.ReactNode;
}
```

### 2. 布局组件 (layout/)
**用途**: 页面结构和布局相关组件

#### Header - 顶部导航
```typescript
interface HeaderProps {
  title?: string;
  subtitle?: string;
  extra?: React.ReactNode;
  breadcrumbs?: BreadcrumbItem[];
  user?: User;
  onMenuToggle?: () => void;
}
```

#### Sidebar - 侧边栏
```typescript
interface SidebarProps {
  collapsed?: boolean;
  onCollapse?: (collapsed: boolean) => void;
  selectedKeys?: string[];
  menuItems: MenuItem[];
  logo?: React.ReactNode;
  footer?: React.ReactNode;
}
```

### 3. 表单组件 (forms/)
**用途**: 表单输入和数据收集组件

#### FormField - 表单字段
```typescript
interface FormFieldProps {
  label?: string;
  required?: boolean;
  error?: string;
  hint?: string;
  children: React.ReactNode;
}
```

#### FormInput - 输入框
```typescript
interface FormInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string;
  error?: string;
  hint?: string;
  size?: 'sm' | 'md' | 'lg';
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
}
```

### 4. 功能组件 (features/)
**用途**: 包含业务逻辑的复合组件

#### MetricCard - 指标卡片
```typescript
interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  loading?: boolean;
  color?: 'primary' | 'success' | 'warning' | 'error';
}
```

#### DataTable - 数据表格
```typescript
interface DataTableProps<T> {
  data: T[];
  columns: ColumnConfig<T>[];
  loading?: boolean;
  pagination?: PaginationConfig;
  selection?: SelectionConfig<T>;
  sorting?: SortingConfig;
  filtering?: FilteringConfig;
  onRowClick?: (row: T) => void;
  onSelectionChange?: (selectedRows: T[]) => void;
}
```

---

## 🏷️ 命名规范

### 1. 文件命名
```
组件文件:          PascalCase
  - Button.tsx
  - DataTable.tsx

Hook文件:           camelCase + use前缀
  - useAnimation.ts
  - useLocalStorage.ts

工具文件:           camelCase
  - formatters.ts
  - validators.ts

类型文件:           camelCase
  - ui.ts
  - api.ts

样式文件:           kebab-case
  - button.module.css
  - design-system.css
```

### 2. 组件命名
```typescript
// 组件名称使用 PascalCase
const Button = () => {};
const DataTable = () => {};

// Props 接口命名
interface ButtonProps {}
interface DataTableProps<T> {}

// 子组件命名
const Card = () => {};
const CardHeader = () => {};
const CardContent = () => {};
```

### 3. CSS 类名命名
```css
/* 使用 BEM 命名规范 */
.button { }                    /* Block */
.button--primary { }           /* Modifier */
.button--large { }             /* Modifier */
.button__icon { }              /* Element */
.button__text { }              /* Element */

/* 或者使用 kebab-case */
.metric-card { }
.metric-card--success { }
.metric-card__title { }
.metric-card__value { }
```

---

## 📦 组件结构

### 1. 标准组件结构
```tsx
// Button/index.tsx
export { Button } from './Button';
export type { ButtonProps } from './types';

// Button/Button.tsx
import React from 'react';
import { ButtonProps } from './types';
import { cn } from '@/utils/cn';

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ children, className, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn('btn', className)}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';

// Button/types.ts
export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

// Button/Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './index';

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
};

export default meta;

type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Primary Button',
  },
};
```

### 2. 复合组件结构
```tsx
// DataTable/index.tsx
export { DataTable } from './DataTable';
export { useDataTable } from './useDataTable';
export type { DataTableProps, ColumnConfig } from './types';

// DataTable/DataTable.tsx
import React from 'react';
import { DataTableProps } from './types';
import { useDataTable } from './useDataTable';
import { TableHeader } from './TableHeader';
import { TableBody } from './TableBody';
import { TableFooter } from './TableFooter';

export const DataTable = <T,>({
  data,
  columns,
  pagination,
  selection,
  ...props
}: DataTableProps<T>) => {
  const {
    sortedData,
    sortConfig,
    handleSort,
    selectedRows,
    handleSelection,
    paginatedData,
  } = useDataTable({ data, pagination, selection });

  return (
    <div className="data-table">
      <TableHeader
        columns={columns}
        sortConfig={sortConfig}
        onSort={handleSort}
      />
      <TableBody
        data={paginatedData}
        columns={columns}
        selectedRows={selectedRows}
        onSelectionChange={handleSelection}
      />
      {pagination && (
        <TableFooter
          pagination={pagination}
          total={data.length}
        />
      )}
    </div>
  );
};
```

---

## 🔄 状态管理

### 1. 组件内部状态
```tsx
const [isOpen, setIsOpen] = useState(false);
const [selectedItem, setSelectedItem] = useState<T | null>(null);
```

### 2. 自定义Hook
```tsx
// hooks/useModal.ts
export const useModal = (initialOpen = false) => {
  const [isOpen, setIsOpen] = useState(initialOpen);
  const [data, setData] = useState<any>(null);

  const open = (modalData?: any) => {
    setData(modalData);
    setIsOpen(true);
  };

  const close = () => {
    setIsOpen(false);
    setData(null);
  };

  const toggle = () => {
    setIsOpen(!isOpen);
  };

  return {
    isOpen,
    data,
    open,
    close,
    toggle,
  };
};
```

### 3. Context使用
```tsx
// contexts/ThemeContext.tsx
interface ThemeContextType {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};
```

---

## 🧪 测试规范

### 1. 单元测试
```tsx
// Button/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './index';

describe('Button', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button')).toBeInTheDocument();
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('shows loading state', () => {
    render(<Button loading>Click me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('applies variant classes correctly', () => {
    render(<Button variant="secondary">Click me</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-secondary');
  });
});
```

### 2. 集成测试
```tsx
// FormField/FormField.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FormField } from './index';

describe('FormField', () => {
  it('validates required field', async () => {
    const onSubmit = vi.fn();

    render(
      <form onSubmit={onSubmit}>
        <FormField label="Name" required>
          <input data-testid="name-input" />
        </FormField>
        <button type="submit">Submit</button>
      </form>
    );

    await userEvent.click(screen.getByRole('button', { name: 'Submit' }));

    expect(screen.getByText('Name is required')).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
```

### 3. 可访问性测试
```tsx
// Button/Button.a11y.test.tsx
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { Button } from './index';

describe('Button Accessibility', () => {
  it('should not have accessibility violations', async () => {
    const { container } = render(<Button>Click me</Button>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('supports keyboard navigation', () => {
    render(<Button>Click me</Button>);
    const button = screen.getByRole('button');

    expect(button).toHaveAttribute('tabIndex', '0');
  });

  it('provides aria-label when icon only', () => {
    render(<Button aria-label="Close">✕</Button>);
    expect(screen.getByRole('button')).toHaveAccessibleName('Close');
  });
});
```

---

## 📚 文档规范

### 1. JSDoc注释
```typescript
/**
 * Button组件
 *
 * @example
 * ```tsx
 * <Button variant="primary" onClick={() => console.log('clicked')}>
 *   Click me
 * </Button>
 * ```
 */
export interface ButtonProps {
  /**
   * 按钮变体
   * @default 'primary'
   */
  variant?: 'primary' | 'secondary' | 'ghost';

  /**
   * 按钮大小
   * @default 'md'
   */
  size?: 'sm' | 'md' | 'lg';

  /**
   * 是否禁用
   * @default false
   */
  disabled?: boolean;

  /**
   * 是否显示加载状态
   * @default false
   */
  loading?: boolean;

  /**
   * 按钮内容
   */
  children: React.ReactNode;

  /**
   * 点击回调函数
   */
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
}
```

### 2. Storybook文档
```tsx
// Button/Button.stories.tsx
const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: '基础按钮组件，支持多种变体和尺寸。',
      },
    },
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'ghost'],
      description: '按钮的视觉风格',
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: '按钮的尺寸',
    },
    disabled: {
      control: 'boolean',
      description: '是否禁用按钮',
    },
    loading: {
      control: 'boolean',
      description: '是否显示加载状态',
    },
  },
};

export default meta;
```

### 3. README文档
```markdown
# Button 组件

## 使用方法

```tsx
import { Button } from '@/components/ui';

export default function Example() {
  return (
    <Button variant="primary" onClick={() => console.log('clicked')}>
      Click me
    </Button>
  );
}
```

## API

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| variant | 'primary' \| 'secondary' \| 'ghost' | 'primary' | 按钮变体 |
| size | 'sm' \| 'md' \| 'lg' | 'md' | 按钮尺寸 |
| disabled | boolean | false | 是否禁用 |
| loading | boolean | false | 是否加载中 |
| onClick | function | - | 点击回调 |

## 示例

### 基础用法
```tsx
<Button>Default Button</Button>
<Button variant="primary">Primary Button</Button>
<Button variant="secondary">Secondary Button</Button>
```

### 不同尺寸
```tsx
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>
```

### 状态
```tsx
<Button disabled>Disabled</Button>
<Button loading>Loading</Button>
```

### 带图标
```tsx
<Button icon={<PlusIcon />}>Add Item</Button>
```
```

---

## 🚀 发布流程

### 1. 开发流程
```bash
# 1. 创建功能分支
git checkout -b feature/button-component

# 2. 开发组件
# 编写组件代码、测试、文档

# 3. 本地测试
npm run test
npm run lint
npm run storybook

# 4. 提交代码
git add .
git commit -m "feat: add Button component"

# 5. 推送分支
git push origin feature/button-component

# 6. 创建 Pull Request
# 代码审查、测试通过后合并
```

### 2. 版本管理
```json
// package.json
{
  "name": "@your-org/ui-components",
  "version": "1.0.0",
  "main": "dist/index.js",
  "module": "dist/index.esm.js",
  "types": "dist/index.d.ts",
  "files": [
    "dist",
    "README.md"
  ]
}
```

### 3. 构建发布
```bash
# 1. 构建组件库
npm run build

# 2. 发布到npm
npm publish

# 3. 更新版本号
npm version patch  # 1.0.1
npm version minor  # 1.1.0
npm version major  # 2.0.0
```

### 4. 使用组件库
```bash
# 安装组件库
npm install @your-org/ui-components

# 在项目中使用
import { Button, Card, Modal } from '@your-org/ui-components';
import '@your-org/ui-components/styles';
```

---

## 📋 检查清单

### 开发阶段
- [ ] 组件符合设计系统规范
- [ ] TypeScript类型定义完整
- [ ] 支持ref传递
- [ ] 实现所有必需的props
- [ ] 处理边界情况
- [ ] 添加键盘导航支持
- [ ] 添加ARIA属性
- [ ] 响应式设计

### 测试阶段
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过
- [ ] 可访问性测试通过
- [ ] 跨浏览器兼容性测试
- [ ] Storybook故事完整

### 文档阶段
- [ ] JSDoc注释完整
- [ ] Storybook文档齐全
- [ ] README使用说明
- [ ] API文档准确
- [ ] 示例代码可运行

### 发布阶段
- [ ] 构建成功无错误
- [ ] 版本号正确更新
- [ ] CHANGELOG更新
- [ ] npm发布成功
- [ ] 文档网站更新

---

*本指南将根据组件库的发展和团队反馈持续更新，确保组件库的质量和可维护性。*