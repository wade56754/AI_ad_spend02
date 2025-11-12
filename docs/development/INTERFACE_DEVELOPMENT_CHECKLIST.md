# 接口开发检查清单

## 📋 开发前检查

### 需求确认
- [ ] 业务需求明确，理解核心功能
- [ ] 权限要求清楚，角色权限矩阵确认
- [ ] 数据模型定义完成，数据库表结构确认
- [ ] 接口设计文档完成，通过团队评审

### 技术准备
- [ ] 确认遵循项目开发规范 (.project-rules.md)
- [ ] 了解相关业务模块和数据表关系
- [ ] 确认使用正确的响应格式和错误码
- [ ] 准备相关测试数据

## 🏗️ 代码实现检查

### 文件结构
- [ ] 在正确的router目录下创建路由文件
- [ ] 遵循目录命名规范：`backend/routers/{module}.py`
- [ ] schemas文件位置：`backend/schemas/{module}.py`
- [ ] 模型文件位置：`backend/models/{module}.py`

### 导入规范
- [ ] 标准库导入在最前
- [ ] 第三方库导入在中间
- [ ] 本地模块导入在最后
- [ ] 使用正确的类型注解

```python
# 正确导入示例
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.response import success_response, paginated_response
from backend.core.security import AuthenticatedUser, get_current_user
```

### 路由定义
- [ ] 使用正确的HTTP方法 (GET/POST/PUT/DELETE)
- [ ] 路由路径遵循RESTful规范
- [ ] 添加清晰的API标签和描述
- [ ] 定义正确的响应模型类型

```python
@router.get("/", response_model=StandardResponse[ProjectListResponse])
async def list_projects(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
```

### 权限控制
- [ ] 添加角色权限检查装饰器
- [ ] 实现业务逻辑权限验证
- [ ] 权限矩阵正确配置
- [ ] 敏感操作添加审计日志

```python
@router.post("/")
@require_role(["admin", "manager"])
@require_permission("project:create")
async def create_project(
    project_data: ProjectCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
```

### 参数验证
- [ ] 使用Pydantic模型进行请求体验证
- [ ] 添加字段验证规则 (长度、格式等)
- [ ] 实现自定义验证器
- [ ] 错误信息用户友好

```python
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="项目名称")
    code: str = Field(..., min_length=1, max_length=50, regex=r"^[A-Z0-9_]+$")
    description: Optional[str] = Field(None, max_length=1000)

    @validator('code')
    def validate_code(cls, v):
        if Project.code_exists(v):
            raise ValueError('项目代码已存在')
        return v
```

### 业务逻辑
- [ ] 数据库查询使用正确的ORM方式
- [ ] 实现事务处理 (需要时)
- [ ] 添加异常处理和错误恢复
- [ ] 考虑并发场景和数据一致性
- [ ] 实现适当的缓存策略

### 响应格式
- [ ] 使用StandardResponse统一响应格式
- [ ] 成功响应包含正确的数据结构
- [ ] 错误响应包含详细错误信息
- [ ] 分页响应包含完整的分页信息

```python
return paginated_response(
    data=data,
    page=page,
    page_size=page_size,
    total=total,
    message="获取项目列表成功"
)
```

## 🧪 测试检查

### 单元测试
- [ ] 为每个接口编写单元测试
- [ ] 测试正常场景和异常场景
- [ ] 测试参数验证和边界条件
- [ ] 测试权限控制和业务规则

### 集成测试
- [ ] 测试完整的工作流程
- [ ] 测试数据库交互
- [ ] 测试认证和授权流程
- [ ] 测试并发场景

### 测试覆盖率
- [ ] 代码覆盖率 > 80%
- [ ] 关键业务逻辑100%覆盖
- [ ] 异常处理场景充分测试

```python
def test_create_project_success(client, auth_headers):
    """测试成功创建项目"""
    project_data = {
        "name": "测试项目",
        "code": "TEST001",
        "description": "测试描述"
    }

    response = client.post(
        "/api/v1/projects",
        json=project_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "测试项目"
```

## 📖 文档检查

### API文档
- [ ] 添加接口描述和业务说明
- [ ] 完善参数说明和示例
- [ ] 添加错误码说明
- [ ] 提供请求/响应示例

### 代码注释
- [ ] 复杂业务逻辑添加注释
- [ ] 重要算法和公式添加说明
- [ ] 临时代码添加TODO注释
- [ ] 遵循Python docstring规范

## 🔒 安全检查

### 输入验证
- [ ] 所有输入参数进行验证
- [ ] 防止SQL注入攻击
- [ ] 防止XSS攻击
- [ ] 文件上传安全检查

### 权限控制
- [ ] 实现基于角色的权限控制
- [ ] 敏感操作需要额外验证
- [ ] 实现数据访问隔离 (RLS)
- [ ] 添加操作审计日志

### 数据保护
- [ ] 敏感数据加密存储
- [ ] 不在日志中记录敏感信息
- [ ] 实现适当的数据脱敏
- [ ] 遵循数据隐私法规

## ⚡ 性能检查

### 响应时间
- [ ] 接口响应时间 < 200ms (P95)
- [ ] 大数据量查询实现分页
- [ ] 使用数据库索引优化查询
- [ ] 实现适当的缓存策略

### 资源使用
- [ ] 数据库连接池合理配置
- [ ] 避免N+1查询问题
- [ ] 内存使用优化
- [ ] 实现异步处理 (需要时)

## 🚀 部署检查

### 环境配置
- [ ] 环境变量配置正确
- [ ] 数据库连接正常
- [ ] 第三方服务配置验证
- [ ] 监控和日志配置完成

### 健康检查
- [ ] 实现健康检查接口
- [ ] 准备就绪检查接口
- [ ] 监控关键业务指标
- [ ] 配置告警规则

## 📝 代码质量检查

### 代码规范
- [ ] 通过Black格式化检查
- [ ] 通过isort导入排序检查
- [ ] 通过flake8代码质量检查
- [ ] 通过mypy类型检查

### 代码审查
- [ ] 代码逻辑清晰易懂
- [ ] 变量和函数命名规范
- [ ] 没有硬编码的敏感信息
- [ ] 遵循项目开发规范

## ✅ 交付前最终检查

- [ ] 所有测试通过
- [ ] 代码审查完成
- [ ] API文档更新
- [ ] 部署配置就绪
- [ ] 监控指标配置完成
- [ ] 回滚方案准备就绪

---

## 📊 质量评估

每个接口开发完成后，进行质量评估：

- **功能完整性**: 90/100
- **代码质量**: 95/100
- **测试覆盖率**: 85/100
- **文档完整性**: 90/100
- **安全性**: 95/100
- **性能**: 90/100

**总分**: ≥ 90分方可交付