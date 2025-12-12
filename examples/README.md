# Examples - AI 代码模式库

> **版本**: v1.0
> **用途**: 为 AI 代码生成提供标准模式参考

本目录包含项目的代码模式示例，供 AI 助手（Claude Code）在生成代码时参考，确保生成的代码符合项目规范。

## 目录结构

```
examples/
├── backend/
│   ├── router_pattern.py          # Router 层标准模式
│   ├── service_pattern.py         # Service 层标准模式
│   ├── schema_pattern.py          # Pydantic Schema 标准模式
│   └── state_machine_test_pattern.py  # 状态机测试标准模式
├── frontend/
│   ├── page_pattern.tsx           # 页面组件标准模式
│   ├── api_client_pattern.ts      # API Client 标准模式
│   └── form_pattern.tsx           # 表单组件标准模式
└── README.md                      # 本文件
```

## 后端模式

### Router 模式 (`router_pattern.py`)

展示 FastAPI Router 的标准写法：

- 依赖注入获取 Service 实例
- 统一响应格式 (`success_response`, `error_response`)
- 错误码遵循 `ERROR_CODES_SOT.md v2.1`
- 权限控制通过 `require_role` 装饰器

```python
# 依赖注入模式
def get_example_service(db: Session = Depends(get_db)) -> ExampleService:
    return ExampleService(db)

# 端点定义模式
@router.get("/{item_id}", response_model=StandardResponse)
async def get_example(
    item_id: int,
    service: ExampleService = Depends(get_example_service),
    current_user: User = Depends(get_current_user),
):
    ...
```

### Service 模式 (`service_pattern.py`)

展示业务逻辑层的标准写法：

- 注入 Session，使用事务上下文管理器
- 业务规则校验引用 `BUSINESS_RULES.md`
- 状态转换遵循 `STATE_MACHINE.md`
- 日志记录关键操作
- 禁止绕过账本系统 (`LEDGER_SOT.md v1.1`)

```python
# 事务管理模式
@contextmanager
def transaction(self):
    try:
        yield
        self.db.commit()
    except Exception as e:
        self.db.rollback()
        raise

# 状态转换模式
def approve(self, item_id: int, current_user: User):
    # 校验当前状态
    # 执行转换
    # 创建审计日志
    ...
```

### Schema 模式 (`schema_pattern.py`)

展示 Pydantic v2 Schema 的标准写法：

- 字段命名对齐 SoT 数据流规范 (raw/real/final)
- 验证器使用 `@field_validator` 装饰器
- 响应模型使用 `computed_field` 计算字段

```python
class ExampleCreateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    amount: Decimal = Field(..., ge=0, description="金额")

    @field_validator('amount')
    @classmethod
    def validate_amount_precision(cls, v):
        return Decimal(str(v)).quantize(Decimal('0.01'))
```

### 状态机测试模式 (`state_machine_test_pattern.py`)

展示状态机测试的标准写法：

- 测试所有合法状态转换
- 测试所有非法状态转换（应该失败）
- 测试边界条件和权限约束
- 参数化测试覆盖所有路径

```python
@pytest.mark.parametrize("from_status,to_status,should_succeed", [
    ("raw_submitted", "trend_pending", True),
    ("raw_submitted", "trend_ok", False),  # 非法跳转
])
def test_state_transitions(from_status, to_status, should_succeed):
    ...
```

## 前端模式

### 页面组件模式 (`page_pattern.tsx`)

展示 Next.js 页面组件的标准写法：

- `'use client'` 指令
- 状态管理 (useState, useMemo, useCallback)
- 数据获取 (React Query hooks)
- 组件拆分（提取子组件）

```tsx
export function ExamplePage() {
  // State 管理
  const [activeTab, setActiveTab] = useState('all');
  const [filters, setFilters] = useState(initialFilterState);

  // 查询参数构建
  const queryParams = useMemo(() => {...}, [activeTab, filters]);

  // 数据获取
  const { data, refetch } = useExamples(queryParams);

  // 事件处理器
  const handleViewDetail = useCallback((item) => {...}, []);

  return (...);
}
```

### API Client 模式 (`api_client_pattern.ts`)

展示 API 调用的标准写法：

- 统一的 `apiRequest` 基础函数
- 类型安全的响应处理
- 错误码对齐 `ERROR_CODES_SOT.md`
- Token 自动刷新
- React Query hooks 封装

```typescript
// API 函数
export const exampleApi = {
  list: async (params) => apiRequest('/api/v1/examples', ...),
  create: async (data) => apiRequest('/api/v1/examples', { method: 'POST', ... }),
};

// React Query Hook
export function useExamples(params) {
  return useQuery({
    queryKey: ['examples', params],
    queryFn: () => exampleApi.list(params),
  });
}
```

### 表单组件模式 (`form_pattern.tsx`)

展示表单组件的标准写法：

- React Hook Form + Zod 验证
- shadcn/ui 表单组件
- 受控组件与 Dialog 结合
- 错误处理与提示
- 加载状态管理

```tsx
const formSchema = z.object({
  name: z.string().min(1, '名称不能为空'),
  amount: z.number().min(0, '金额不能为负数'),
});

export function ExampleForm({ open, onClose, onSuccess }) {
  const form = useForm({
    resolver: zodResolver(formSchema),
  });

  const onSubmit = async (values) => {...};

  return (
    <Dialog open={open}>
      <Form {...form}>
        <FormField name="name" render={...} />
      </Form>
    </Dialog>
  );
}
```

## SoT 参考

所有示例代码都引用以下 SoT 文档：

| 文档 | 版本 | 用途 |
|------|------|------|
| STATE_MACHINE.md | v2.6 | 状态机定义 |
| DATA_SCHEMA.md | v5.2 | 数据结构 |
| BUSINESS_RULES.md | v3.2 | 业务规则 |
| API_SOT.md | v9.0 | API 规范 |
| ERROR_CODES_SOT.md | v2.1 | 错误码 |
| LEDGER_SOT.md | v1.1 | 账本系统 |

## 使用方式

### 对于 AI 助手

在生成代码时，请参考本目录下的示例文件：

1. **后端开发**: 参考 `backend/` 目录下的模式
2. **前端开发**: 参考 `frontend/` 目录下的模式
3. **测试编写**: 参考 `state_machine_test_pattern.py`

### 对于开发者

1. 新增功能时，复制相应模式文件作为起点
2. 修改时保持模式一致性
3. 发现更好的模式时，更新示例文件

## 维护

- **更新时机**: 当项目模式发生变化时
- **审核要求**: 模式变更需要团队 review
- **版本管理**: 随项目版本迭代

---

**创建日期**: 2025-12-11
**基于**: Context Engineering 最佳实践
