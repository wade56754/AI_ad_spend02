# AI广告代投系统 - 开发规范

> **版本**: v1.0
> **创建日期**: 2025-11-11
> **适用范围**: 所有开发人员
> **更新频率**: 随时更新

---

## 📋 目录

1. [编码规范](#-编码规范)
2. [Context7 MCP使用规范](#-context7-mcp使用规范)
3. [Git工作流规范](#-git工作流规范)
4. [API开发规范](#-api开发规范)
5. [数据库规范](#-数据库规范)
6. [前端开发规范](#-前端开发规范)
7. [测试规范](#-测试规范)
8. [安全规范](#-安全规范)

---

## 📝 编码规范

### Python (后端)

#### 1. 基础规范
- 使用 **Black** 进行代码格式化
- 使用 **isort** 进行导入排序
- 使用 **flake8** 进行代码检查
- 最大行长度：88字符
- 使用 **Type Hints**（Python 3.11+）

```python
# 导入顺序示例
import os
import sys
from datetime import datetime
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.project_service import ProjectService
```

#### 2. 命名规范
- **类名**: PascalCase (`ProjectService`)
- **函数/变量名**: snake_case (`get_project_by_id`)
- **常量**: UPPER_SNAKE_CASE (`MAX_RETRY_COUNT`)
- **私有成员**: 前缀下划线 (`_internal_method`)

#### 3. 文档字符串
使用Google风格的docstring：

```python
def create_project(
    project_data: ProjectCreate,
    db: Session,
    current_user: User = Depends(get_current_user)
) -> Project:
    """创建新项目.

    Args:
        project_data: 项目创建数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        创建的项目对象

    Raises:
        HTTPException: 当项目代码已存在时
    """
    pass
```

### TypeScript (前端)

#### 1. 基础规范
- 使用 **Prettier** 进行格式化
- 使用 **ESLint** 进行代码检查
- 使用 **TypeScript strict mode**
- 最大行长度：100字符

#### 2. 命名规范
- **组件名**: PascalCase (`ProjectCard`)
- **接口/类型**: PascalCase (`ProjectData`)
- **变量/函数**: camelCase (`getProjectList`)
- **常量**: UPPER_SNAKE_CASE (`API_BASE_URL`)
- **文件名**: kebab-case (`project-card.tsx`)

#### 3. 类型定义
```typescript
// 接口定义
interface Project {
  id: string;
  name: string;
  status: ProjectStatus;
  createdAt: Date;
}

// 联合类型
type ProjectStatus = 'planning' | 'active' | 'paused' | 'completed';

// 泛型使用
interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
}
```

---

## 🔍 Context7 MCP使用规范

### 1. 何时使用Context7

**✅ 推荐使用场景**：
- 学习新的技术栈或框架
- 获取最新的API文档和代码示例
- 解决具体的技术问题
- 查找最佳实践和模式
- 验证自己的实现方案

**❌ 不推荐使用场景**：
- 基础的语法查询（应使用IDE插件）
- 简单的代码片段生成（应使用本地工具）
- 敏感信息的处理（应查看官方文档）

### 2. 使用流程

#### 2.1 查询库信息
```bash
# 第一步：解析库名
resolve-library-id next.js

# 第二步：获取文档
get-library-docs /vercel/next.js topic="routing" tokens=5000
```

#### 2.2 查询最佳实践
```python
# 示例：查询Next.js App Router最佳实践
{
  "tool": "resolve-library-id",
  "arguments": {
    "libraryName": "next.js"
  }
}

# 然后使用获取的ID查询特定主题
{
  "tool": "get-library-docs",
  "arguments": {
    "context7CompatibleLibraryID": "/vercel/next.js",
    "topic": "app router best practices",
    "tokens": 3000
  }
}
```

### 3. 记录规范

当使用Context7获取信息后，必须在项目中记录：

#### 3.1 技术决策记录
在相关模块的README中记录：

```markdown
## 技术选型说明

### 使用React Hook Form的原因
- 通过Context7查询发现，React Hook Form性能优于Formik
- 参考文档：/radix-ui/react-hook-form (2025-11-11查询)
- 决策日期：2025-11-11
```

#### 3.2 代码注释
```typescript
/**
 * 使用Zod进行表单验证
 * 参考：https://zod.dev/ (通过Context7获取)
 * 原因：TypeScript-first，性能优秀，与React Hook Form集成良好
 */
const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});
```

### 4. Context7查询日志

在`docs/context7-queries.md`中记录查询历史：

```markdown
# Context7查询日志

## 2025-11-11

### Query 1
- **目的**: 了解Next.js 15的新特性
- **查询**: resolve-library-id "next.js"
- **结果**: /vercel/next.js
- **后续**: 获取了App Router详细文档

### Query 2
- **目的**: 查询Supabase RLS最佳实践
- **查询**: get-library-docs /supabase/supabase topic="row level security"
- **收获**: RLS策略优化方案
```

### 5. 注意事项

1. **不要完全依赖**：Context7提供的信息需要验证
2. **版本确认**：确保查询的文档版本与项目使用的版本一致
3. **安全考虑**：不要在查询中包含敏感信息
4. **性能考虑**：避免频繁查询相同内容，应做好本地记录

---

## 🌿 Git工作流规范

### 1. 分支策略

```bash
main          # 主分支，生产环境代码
├── develop   # 开发分支，集成测试
├── feature/* # 功能分支
├── hotfix/*  # 热修复分支
└── release/* # 发布分支
```

### 2. 提交规范

使用[Conventional Commits](https://www.conventionalcommits.org/)规范：

```bash
# 格式
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]

# 示例
feat(auth): add JWT token refresh mechanism

- Implement automatic token refresh
- Add refresh token storage
- Handle token expiration gracefully

Closes #123
```

**提交类型**：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

### 3. Pull Request规范

#### 3.1 PR标题
```bash
<type>(<scope>): <description>

# 示例
feat(api): implement project CRUD operations
```

#### 3.2 PR描述模板
```markdown
## 变更类型
- [ ] Bug修复
- [ ] 新功能
- [ ] 破坏性变更
- [ ] 文档更新

## 变更描述
简要描述本次变更的内容

## 相关Issue
Closes #(issue number)

## 测试
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试完成

## 截图（如适用）
添加相关截图

## Checklist
- [ ] 代码遵循项目规范
- [ ] 自查代码格式
- [ ] 添加必要的测试
- [ ] 更新相关文档
```

---

## 🔌 API开发规范

### 1. RESTful API设计

#### 1.1 URL设计
```bash
# 资源命名使用复数
GET    /api/v1/projects           # 获取项目列表
POST   /api/v1/projects           # 创建项目
GET    /api/v1/projects/{id}      # 获取特定项目
PUT    /api/v1/projects/{id}      # 更新项目
DELETE /api/v1/projects/{id}      # 删除项目

# 嵌套资源
GET    /api/v1/projects/{id}/accounts  # 获取项目的账户列表
```

#### 1.2 HTTP状态码
```python
# 成功响应
200 OK          # 请求成功
201 Created     # 资源创建成功
204 No Content  # 删除成功

# 客户端错误
400 Bad Request      # 请求参数错误
401 Unauthorized     # 未认证
403 Forbidden        # 无权限
404 Not Found        # 资源不存在
409 Conflict         # 资源冲突
422 Unprocessable Entity  # 验证失败

# 服务端错误
500 Internal Server Error  # 服务器错误
```

#### 1.3 统一响应格式
```python
# 成功响应
{
  "success": true,
  "data": {...},
  "message": "操作成功",
  "code": "SUCCESS",
  "request_id": "uuid",
  "timestamp": "2025-11-11T10:30:00Z"
}

# 错误响应
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数验证失败",
    "details": {...}  # 可选
  },
  "request_id": "uuid",
  "timestamp": "2025-11-11T10:30:00Z"
}
```

### 2. FastAPI特定规范

#### 2.1 路由定义
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[ProjectResponse]:
    """获取项目列表"""
    pass
```

#### 2.2 依赖注入
```python
# 单例依赖
@lru_cache()
def get_settings() -> Settings:
    return Settings()

# 请求级别依赖
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 🗄️ 数据库规范

### 1. 命名规范

#### 1.1 表名
- 使用复数形式
- 小写字母+下划线
- 见名知意

```sql
-- 好的命名
projects
user_roles
project_account_assignments

-- 不好的命名
proj
user
assign
```

#### 1.2 字段名
```sql
-- 主键
id UUID PRIMARY KEY DEFAULT gen_random_uuid()

-- 外键（表名_主键名）
project_id UUID NOT NULL
user_id UUID NOT NULL

-- 时间戳
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()

-- 布尔值
is_active BOOLEAN DEFAULT true
has_access BOOLEAN DEFAULT false
```

### 2. 索引规范

#### 2.1 索引命名
```sql
-- 普通索引：idx_表名_字段名
idx_projects_status
idx_users_email

-- 复合索引：idx_表名_字段1_字段2
idx_ad_accounts_project_status
idx_topups_created_status

-- 唯一索引：uk_表名_字段名
uk_projects_code
uk_users_email
```

#### 2.2 索引创建原则
```sql
-- 外键必须建索引
CREATE INDEX idx_projects_manager_id ON projects(manager_id);

-- 经常查询的字段
CREATE INDEX idx_ad_accounts_status ON ad_accounts(status);

-- 复合查询
CREATE INDEX idx_ad_spend_daily_account_date
ON ad_spend_daily(ad_account_id, date);

-- 部分索引（提高性能）
CREATE INDEX idx_active_projects
ON projects(status) WHERE status = 'active';
```

### 3. 迁移规范

```bash
# 迁移文件命名
YYYYMMDD_HHMMSS_description.py

# 示例
20251111_143000_create_projects_table.py
20251111_150000_add_user_roles.py
```

---

## 🎨 前端开发规范

### 1. 组件规范

#### 1.1 函数组件
```typescript
// 使用React.FC或显式返回类型
interface ProjectCardProps {
  project: Project;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
}

const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onEdit,
  onDelete
}) => {
  // 组件逻辑
  return <div>{/* JSX */}</div>;
};

export default ProjectCard;
```

#### 1.2 自定义Hook
```typescript
// use前缀命名
// 返回值使用数组格式 [value, actions]

const useProject = (id: string) => {
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 逻辑实现

  return [project, { loading, error, refresh }];
};

export default useProject;
```

### 2. 状态管理

#### 2.1 本地状态
```typescript
// 简单状态：useState
const [count, setCount] = useState(0);

// 复杂状态：useReducer
const [state, dispatch] = useReducer(projectReducer, initialState);
```

#### 2.2 服务端状态
```typescript
// 使用SWR或React Query
const { data, error, mutate } = useSWR(
  '/api/projects',
  fetcher
);

// 自定义fetcher
const fetcher = async (url: string) => {
  const response = await apiClient.get(url);
  return response.data;
};
```

### 3. 样式规范

#### 3.1 Tailwind CSS
```typescript
// 使用clsx合并类名
import clsx from 'clsx';

const buttonClasses = clsx(
  'px-4 py-2 rounded-md font-medium transition-colors',
  {
    'bg-blue-600 text-white': variant === 'primary',
    'bg-gray-200 text-gray-900': variant === 'secondary',
    'opacity-50 cursor-not-allowed': disabled,
  }
);
```

#### 3.2 shadcn/ui组件
```typescript
// 遵循shadcn/ui的设计系统
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

// 扩展组件
const ExtendedButton = React.forwardRef<
  HTMLButtonElement,
  ButtonProps & { loading?: boolean }
>(({ children, loading, ...props }, ref) => {
  return (
    <Button ref={ref} disabled={loading || props.disabled} {...props}>
      {loading ? <Spinner /> : children}
    </Button>
  );
});
```

---

## 🧪 测试规范

### 1. 测试金字塔

```
E2E Tests (10%)
├── 用户流程测试
└── 关键业务路径

Integration Tests (20%)
├── API测试
├── 组件集成测试
└── 数据库测试

Unit Tests (70%)
├── 函数测试
├── 组件单元测试
└── 工具函数测试
```

### 2. 测试文件命名

```
__tests__/
├── unit/
│   ├── services/
│   │   └── project_service.test.py
│   └── utils/
│       └── date_utils.test.py
├── integration/
│   ├── api/
│   │   └── test_projects.py
│   └── database/
│       └── test_project_crud.py
└── e2e/
    ├── user-journey.spec.ts
    └── critical-path.spec.ts
```

### 3. 测试示例

#### 3.1 Python单元测试
```python
import pytest
from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate

class TestProjectService:
    def test_create_project_success(self, db_session, sample_user):
        """测试成功创建项目"""
        service = ProjectService(db_session)
        project_data = ProjectCreate(
            name="Test Project",
            code="TEST001",
            client_name="Test Client"
        )

        project = service.create(project_data, sample_user.id)

        assert project.id is not None
        assert project.name == "Test Project"
        assert project.created_by == sample_user.id
```

#### 3.2 TypeScript单元测试
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { ProjectCard } from './ProjectCard';

describe('ProjectCard', () => {
  const mockProject = {
    id: '1',
    name: 'Test Project',
    status: 'active' as const,
  };

  it('renders project information correctly', () => {
    render(<ProjectCard project={mockProject} />);

    expect(screen.getByText('Test Project')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', () => {
    const onEdit = jest.fn();
    render(<ProjectCard project={mockProject} onEdit={onEdit} />);

    fireEvent.click(screen.getByRole('button', { name: /edit/i }));

    expect(onEdit).toHaveBeenCalledWith('1');
  });
});
```

---

## 🔒 安全规范

### 1. 认证与授权

#### 1.1 JWT Token
```typescript
// Token存储：httpOnly Cookie（推荐）或安全存储
// 不要在localStorage存储敏感信息

// API请求自动添加Token
apiClient.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

#### 1.2 权限检查
```python
# 后端权限装饰器
def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user.has_permission(permission):
                raise HTTPException(403, "Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@router.post("/projects")
@require_permission("project:create")
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user)
):
    pass
```

### 2. 数据验证

#### 2.1 输入验证
```python
from pydantic import BaseModel, validator
import re

class UserCreate(BaseModel):
    email: str
    password: str

    @validator('email')
    def validate_email(cls, v):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        return v
```

#### 2.2 SQL注入防护
```python
# 使用ORM参数化查询
query = select(Project).where(
    Project.status == status,
    Project.created_at >= start_date
)

# 不要使用字符串拼接
# 错误示例
# query = f"SELECT * FROM projects WHERE status = '{status}'"
```

### 3. 敏感数据处理

#### 3.1 环境变量
```bash
# .env.example（可提交）
DATABASE_URL=postgresql://user:password@localhost/db
JWT_SECRET=your-secret-key
SUPABASE_URL=your-supabase-url

# .env（不提交）
DATABASE_URL=postgresql://real_user:real_password@localhost/real_db
JWT_SECRET=super-secret-key-12345
SUPABASE_URL=https://your-project.supabase.co
```

#### 3.2 日志安全
```python
import logging

# 不要记录敏感信息
logger.info(f"User {user_id} logged in")  # ✅ 正确
logger.info(f"User {email} logged in with {password}")  # ❌ 错误

# 使用结构化日志
logger.info("User login", extra={
    "user_id": user.id,
    "ip_address": request.client.host,
    "user_agent": request.headers.get("user-agent")
})
```

---

## 📚 相关文档

- [API文档](./BACKEND_API_GUIDE.md)
- [数据库设计](./DATA_SCHEMA.md)
- [部署指南](./DEPLOYMENT_GUIDE.md)
- [Context7查询日志](./docs/context7-queries.md)

---

## 📝 更新记录

### 2025-11-11
- 初始版本创建
- 添加Context7 MCP使用规范
- 整合所有开发规范

---

**文档版本**: v1.0
**创建日期**: 2025-11-11
**维护人**: 开发团队
**审核人**: 技术负责人