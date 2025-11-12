# 接口开发任务流程总览 (基于优化文档v2.1)

> **适用场景**: 使用Claude助手进行四阶段接口开发
> **开发模式**: 设计→实现→测试→交付的完整工作流
> **质量保证**: 每个阶段都有明确的交付标准和检查点

---

## 🎯 开发阶段概览

### 阶段一：需求与设计 (2-3天)
**目标**: 完成接口设计和业务流程定义
**核心交付**:
- [ ] 业务需求分析与边界定义
- [ ] API端点清单（方法/路径/描述/权限/状态码）
- [ ] 请求/响应Schema设计（Pydantic v2）
- [ ] 错误码映射和权限矩阵
- [ ] 数据模型设计和索引建议

### 阶段二：代码实现 (3-5天)
**目标**: 完成接口编码和业务逻辑实现
**核心交付**:
- [ ] FastAPI路由骨架（依赖注入、认证、事务）
- [ ] Pydantic模型实现（ConfigDict配置）
- [ ] 业务逻辑层实现（Service层）
- [ ] 统一响应格式（success_response/error_response）
- [ ] 异常处理和审计日志

### 阶段三：测试验证 (2-3天)
**目标**: 完成测试覆盖和质量验证
**核心交付**:
- [ ] 单元测试（Service层逻辑）
- [ ] 集成测试（API契约测试）
- [ ] 分页和错误场景测试
- [ ] 权限控制测试矩阵
- [ ] 覆盖率报告（≥70%）

### 阶段四：文档与交付 (1-2天)
**目标**: 完成文档和部署准备
**核心交付**:
- [ ] API文档更新（OpenAPI规范）
- [ ] 接口使用示例（README片段）
- [ ] 部署检查清单
- [ ] 性能基线验证
- [ ] 发布前最终审查

---

## 📋 详细任务清单

### 🔍 阶段一：需求与设计任务

#### 1.1 需求分析 (0.5天)
- [ ] **业务需求梳理**
  - [ ] 明确核心业务场景（如：项目管理、账户分配、日报提交）
  - [ ] 识别参与角色及其权限边界（admin/finance/data_operator/account_manager/media_buyer）
  - [ ] 定义数据流向和关键业务规则
  - [ ] 输出：业务流程图（Mermaid格式）

- [ ] **技术边界定义**
  - [ ] 确定API版本策略（默认v1）
  - [ ] 定义资源命名规范（复数形式）
  - [ ] 确定认证方式（JWT Bearer）
  - [ ] 定义分页和过滤参数标准

#### 1.2 接口设计 (1天)
- [ ] **端点清单设计**
  ```markdown
  ## 端点设计示例
  | 方法 | 路径 | 描述 | 权限要求 | 幂等性 | 状态码 |
  |------|------|------|----------|--------|--------|
  | GET | /api/v1/projects | 获取项目列表 | admin,manager | 是 | 200 |
  | POST | /api/v1/projects | 创建新项目 | admin | 否 | 201 |
  | GET | /api/v1/projects/{id} | 获取项目详情 | admin,manager,client | 是 | 200 |
  ```

- [ ] **请求/响应Schema设计**
  - [ ] 使用Pydantic v2语法设计所有模型
  - [ ] 定义请求验证规则（字段约束、自定义验证）
  - [ ] 设计响应结构（成功/错误/分页）
  - [ ] 确保ConfigDict(from_attributes=True)

- [ ] **错误码设计**
  - [ ] 系统级错误码（SYS_xxx格式）
  - [ ] 业务级错误码（BIZ_xxx格式）
  - [ ] 安全级错误码（SEC_xxx格式）
  - [ ] HTTP状态码映射关系

#### 1.3 数据模型设计 (0.5天)
- [ ] **数据库表设计**
  - [ ] 表结构定义（字段类型、约束、索引）
  - [ ] RLS策略设计（行级安全策略）
  - [ ] 外键关系和级联规则
  - [ ] 审计字段设计（created_at/updated_at）

- [ ] **性能优化考虑**
  - [ ] 索引策略（查询优化）
  - [ ] 分页策略（cursor-based vs offset）
  - [ ] 缓存策略（Redis集成点）

#### 1.4 权限设计 (0.5天)
- [ ] **权限矩阵设计**
  ```markdown
  ## 权限矩阵示例
  资源/操作 | admin | finance | data_op | acct_mgr | media_buyer
  -----------|-------|---------|---------|----------|------------
  项目列表   | ✓     | ✓       | ✓       | ✓        | ✓
  项目创建   | ✓     | ✗       | ✗       | ✗        | ✗
  财务审批   | ✓     | ✓       | ✗       | ✗        | ✗
  ```

- [ ] **数据隔离策略**
  - [ ] 基于角色的数据可见性
  - [ ] RLS策略实现方案
  - [ ] 租户隔离机制

#### 阶段一交付检查
- [ ] 接口设计文档（含端点清单）
- [ ] Pydantic Schema定义草案
- [ ] 数据库ER图和DDL脚本
- [ ] 权限矩阵和RLS策略
- [ ] 业务流程图（Mermaid）

---

### 💻 阶段二：代码实现任务

#### 2.1 环境准备 (0.5天)
- [ ] **开发环境配置**
  - [ ] Python 3.11+虚拟环境
  - [ ] 依赖安装：`pip install -r requirements.txt`
  - [ ] 环境变量配置：`.env`文件
  - [ ] 数据库连接测试

- [ ] **代码结构初始化**
  - [ ] 创建模块目录结构
  - [ ] 初始化路由文件
  - [ ] 创建Schema、Service、测试文件模板

#### 2.2 Pydantic模型实现 (1天)
- [ ] **请求模型实现**
  ```python
  # 项目创建请求模型示例
  class ProjectCreateRequest(BaseModel):
      model_config = ConfigDict(from_attributes=True)

      name: str = Field(..., min_length=1, max_length=100)
      description: Optional[str] = Field(None, max_length=500)
      client_id: int = Field(..., gt=0)
      budget: Decimal = Field(..., gt=0, decimal_places=2)

      @field_validator('name')
      def validate_name(cls, v):
          if not v.strip():
              raise ValueError('项目名称不能为空')
          return v.strip()
  ```

- [ ] **响应模型实现**
  ```python
  # 项目响应模型示例
  class ProjectResponse(BaseModel):
      model_config = ConfigDict(from_attributes=True)

      id: int
      name: str
      description: Optional[str]
      client_id: int
      client_name: str
      budget: Decimal
      spent: Decimal
      status: str
      created_at: datetime
      updated_at: datetime
  ```

- [ ] **分页模型实现**
  ```python
  class PaginationMeta(BaseModel):
      page: int = Field(ge=1)
      page_size: int = Field(ge=1, le=100)
      total: int = Field(ge=0)
      total_pages: int = Field(ge=0)

  class ProjectListResponse(BaseModel):
      items: List[ProjectResponse]
      meta: PaginationMeta
  ```

#### 2.3 Service层实现 (1.5天)
- [ ] **基础CRUD操作**
  - [ ] 数据访问层封装
  - [ ] 事务边界管理
  - [ ] 数据验证和业务规则检查
  - [ ] 异常处理和错误码映射

- [ ] **业务逻辑实现**
  ```python
  @transaction
  async def create_project(
      self,
      request: ProjectCreateRequest,
      current_user: User
  ) -> Project:
      # 业务规则检查
      if not await self._can_user_create_project(current_user):
          raise PermissionError("用户无权限创建项目")

      # 数据创建
      project = Project(
          name=request.name,
          description=request.description,
          client_id=request.client_id,
          budget=request.budget,
          created_by=current_user.id
      )

      self.db.add(project)
      self.db.flush()

      # 审计日志
      await audit_log(
          action="project.created",
          resource_id=project.id,
          user_id=current_user.id
      )

      return project
  ```

#### 2.4 路由层实现 (1天)
- [ ] **路由定义和依赖注入**
  ```python
  from fastapi import APIRouter, Depends, HTTPException, Query
  from backend.core.dependencies import get_db, require_role
  from backend.core.response import success_response, error_response, paginated_response

  router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

  @router.get(
      "",
      response_model=StandardResponse[ProjectListResponse],
      dependencies=[Depends(require_role(["admin", "manager", "client"]))]
  )
  async def list_projects(
      page: int = Query(1, ge=1),
      page_size: int = Query(20, ge=1, le=100),
      search: Optional[str] = Query(None),
      status: Optional[str] = Query(None),
      db: Session = Depends(get_db),
      current_user: User = Depends(get_current_user)
  ):
  ```

- [ ] **统一响应格式**
  ```python
  @router.post(
      "",
      response_model=StandardResponse[ProjectResponse],
      status_code=201,
      dependencies=[Depends(require_role(["admin"]))]
  )
  async def create_project(
      request: ProjectCreateRequest,
      db: Session = Depends(get_db),
      current_user: User = Depends(get_current_user)
  ):
      try:
          project_service = ProjectService(db)
          project = await project_service.create_project(request, current_user)
          return success_response(
              data=ProjectResponse.model_validate(project),
              message="项目创建成功"
          )
      except PermissionError as e:
          return error_response(
              code="PERMISSION_DENIED",
              message=str(e),
              status_code=403
          )
  ```

#### 2.5 异常处理和日志 (0.5天)
- [ ] **全局异常处理器**
  ```python
  @app.exception_handler(PermissionError)
  async def permission_exception_handler(request, exc):
      return error_response(
          code="PERMISSION_DENIED",
          message=str(exc),
          status_code=403
      )
  ```

- [ ] **审计日志实现**
  ```python
  async def audit_log(
      action: str,
      resource_id: int,
      user_id: int,
      details: Optional[Dict] = None
  ):
      audit = AuditLog(
          action=action,
          resource_id=resource_id,
          user_id=user_id,
          details=details or {},
          ip_address=request.client.host
      )
      db.add(audit)
      await db.commit()
  ```

#### 阶段二交付检查
- [ ] 完整的路由实现（含认证和权限）
- [ ] Pydantic模型（请求/响应/分页）
- [ ] Service层业务逻辑
- [ ] 统一响应格式应用
- [ ] 异常处理和审计日志
- [ ] 代码格式化和静态检查通过

---

### 🧪 阶段三：测试验证任务

#### 3.1 单元测试 (1天)
- [ ] **Service层测试**
  ```python
  class TestProjectService:
      async def test_create_project_success(self, db_session):
          service = ProjectService(db_session)
          request = ProjectCreateRequest(
              name="测试项目",
              description="测试描述",
              client_id=1,
              budget=10000.00
          )
          user = User(id=1, role="admin")

          project = await service.create_project(request, user)

          assert project.name == "测试项目"
          assert project.created_by == 1
  ```

- [ ] **业务规则测试**
  - [ ] 权限验证测试
  - [ ] 数据验证测试
  - [ ] 边界条件测试
  - [ ] 异常场景测试

#### 3.2 API集成测试 (1天)
- [ ] **契约测试**
  ```python
  class TestProjectAPI:
      async def test_create_project_api(self, client, auth_headers):
          request_data = {
              "name": "API测试项目",
              "description": "API测试描述",
              "client_id": 1,
              "budget": "10000.00"
          }

          response = await client.post(
              "/api/v1/projects",
              json=request_data,
              headers=auth_headers
          )

          assert response.status_code == 201
          data = response.json()
          assert data["success"] is True
          assert data["data"]["name"] == "API测试项目"
  ```

- [ ] **分页测试**
  ```python
  async def test_list_projects_pagination(self, client, auth_headers):
      # 测试第一页
      response = await client.get(
          "/api/v1/projects?page=1&page_size=5",
          headers=auth_headers
      )
      data = response.json()
      assert data["meta"]["pagination"]["page"] == 1
      assert data["meta"]["pagination"]["page_size"] == 5

      # 测试超出范围
      response = await client.get(
          "/api/v1/projects?page=999&page_size=5",
          headers=auth_headers
      )
      data = response.json()
      assert len(data["data"]["items"]) == 0
  ```

#### 3.3 权限测试 (0.5天)
- [ ] **角色权限矩阵测试**
  ```python
  @pytest.mark.parametrize("role,expected_status", [
      ("admin", 201),
      ("finance", 403),
      ("data_operator", 403),
      ("account_manager", 403),
      ("media_buyer", 403)
  ])
  async def test_create_project_permissions(self, client, role, expected_status):
      auth_headers = await get_auth_headers_for_role(role)

      response = await client.post(
          "/api/v1/projects",
          json={...},
          headers=auth_headers
      )

      assert response.status_code == expected_status
  ```

- [ ] **数据隔离测试**
  - [ ] 不同角色数据可见性测试
  - [ ] RLS策略有效性测试
  - [ ] 跨租户访问阻止测试

#### 3.4 性能和安全测试 (0.5天)
- [ ] **性能基线测试**
  ```python
  async def test_list_projects_performance(self, client, auth_headers):
      import time

      start_time = time.time()
      response = await client.get(
          "/api/v1/projects?page=1&page_size=20",
          headers=auth_headers
      )
      end_time = time.time()

      assert response.status_code == 200
      assert end_time - start_time < 0.3  # 300ms内响应
  ```

- [ ] **安全测试**
  - [ ] SQL注入防护测试
  - [ ] XSS防护测试
  - [ ] 认证绕过测试
  - [ ] 敏感数据泄露检查

#### 3.5 覆盖率报告 (0.5天)
- [ ] **代码覆盖率收集**
  ```bash
  pytest --cov=backend.routers.projects \
          --cov=backend.services.project_service \
          --cov-report=term-missing \
          --cov-report=html
  ```

- [ ] **覆盖率质量门禁**
  - [ ] 总覆盖率 ≥ 70%
  - [ ] 核心业务逻辑覆盖率 = 100%
  - [ ] 分支覆盖率 ≥ 80%

#### 阶段三交付检查
- [ ] 单元测试套件（≥70%覆盖率）
- [ ] API集成测试（含分页和错误）
- [ ] 权限测试矩阵
- [ ] 性能基线报告
- [ ] 安全扫描报告（bandit、pip-audit）

---

### 📚 阶段四：文档与交付任务

#### 4.1 API文档完善 (0.5天)
- [ ] **OpenAPI文档增强**
  ```python
  @router.post(
      "",
      response_model=StandardResponse[ProjectResponse],
      status_code=201,
      summary="创建新项目",
      description="创建一个新的广告投放项目，需要管理员权限",
      responses={
          201: {"description": "项目创建成功"},
          400: {"description": "请求参数验证失败"},
          403: {"description": "权限不足"},
          500: {"description": "服务器内部错误"}
      }
  )
  ```

- [ ] **示例文档生成**
  - [ ] 请求示例（cURL、JavaScript）
  - [ ] 响应示例（成功、错误）
  - [ ] 错误码说明文档

#### 4.2 使用指南编写 (0.5天)
- [ ] **README更新**
  ```markdown
  ## 项目管理API

  ### 获取项目列表
  ```bash
  curl -X GET "http://localhost:8000/api/v1/projects?page=1&page_size=20" \
       -H "Authorization: Bearer YOUR_TOKEN"
  ```

  ### 创建新项目
  ```bash
  curl -X POST "http://localhost:8000/api/v1/projects" \
       -H "Content-Type: application/json" \
       -H "Authorization: Bearer YOUR_TOKEN" \
       -d '{
         "name": "新项目",
         "description": "项目描述",
         "client_id": 1,
         "budget": "10000.00"
       }'
  ```
  ```

- [ ] **最佳实践文档**
  - [ ] 错误处理指南
  - [ ] 分页使用建议
  - [ ] 权限检查说明
  - [ ] 性能优化建议

#### 4.3 部署准备 (0.5天)
- [ ] **健康检查确认**
  ```python
  @router.get("/healthz", tags=["health"])
  async def health_check():
      return success_response(
          data={"status": "healthy", "timestamp": datetime.utcnow()},
          message="服务健康"
      )

  @router.get("/readyz", tags=["health"])
  async def readiness_check(db: Session = Depends(get_db)):
      try:
          db.execute("SELECT 1")
          return success_response(
              data={"status": "ready", "database": "connected"},
              message="服务就绪"
          )
      except Exception:
          return error_response(
              code="DATABASE_UNAVAILABLE",
              message="数据库连接失败",
              status_code=503
          )
  ```

- [ ] **Docker配置验证**
  - [ ] Dockerfile优化
  - [ ] 健康检查配置
  - [ ] 环境变量文档

#### 4.4 最终质量检查 (0.5天)
- [ ] **代码质量门禁**
  ```bash
  # 代码格式检查
  black --check backend/
  isort --check-only backend/

  # 静态分析
  flake8 backend/
  mypy backend/

  # 安全扫描
  bandit -r backend/
  pip-audit
  ```

- [ ] **集成测试验证**
  - [ ] 完整业务流程测试
  - [ ] 多服务协作测试
  - [ ] 数据一致性检查

#### 阶段四交付检查
- [ ] 完整的API文档（OpenAPI）
- [ ] 使用示例和最佳实践
- [ ] 部署配置和检查清单
- [ ] 质量门禁报告
- [ ] 发布说明文档

---

## 🚀 Claude协作开发指南

### 使用Claude的最佳实践

#### 1. 阶段开始时
- **明确阶段目标**: 告诉Claude当前处于哪个阶段（设计/实现/测试/交付）
- **提供上下文**: 分享相关的业务需求和技术约束
- **设定预期结果**: 明确阶段结束时需要交付什么

#### 2. 开发过程中
- **迭代开发**: 按照子任务逐一完成，及时反馈问题
- **代码审查**: 让Claude检查代码质量和规范遵循情况
- **测试驱动**: 先写测试，再实现功能，确保质量

#### 3. 阶段结束时
- **交付检查**: 使用提供的检查清单验证完整性
- **文档同步**: 确保文档与代码实现保持一致
- **下阶段准备**: 为下一阶段准备好必要的输入

### Claude提示词模板

#### 设计阶段提示词
```
我正在开发AI广告代投系统的[模块名]功能，当前处于需求与设计阶段。

业务背景：[描述业务场景]
核心需求：[列出主要需求]
技术约束：FastAPI + Pydantic v2 + PostgreSQL + RLS

请帮我：
1. 分析业务需求，定义API端点清单
2. 设计请求/响应Schema（使用Pydantic v2）
3. 定义错误码和权限矩阵
4. 输出设计文档和业务流程图
```

#### 实现阶段提示词
```
我正在实现[模块名]的API接口，已有设计方案。

设计文档：[附上设计文档链接]
端点清单：[列出要实现的端点]
数据库模型：[描述表结构]

请按照以下要求实现：
1. 创建Pydantic模型（ConfigDict(from_attributes=True)）
2. 实现Service层业务逻辑
3. 实现FastAPI路由（含权限控制）
4. 使用统一响应格式（success_response/error_response）
5. 添加异常处理和审计日志

注意事项：
- 严格遵循项目代码规范
- 所有接口都需要JWT认证
- 实现RLS数据隔离
- 添加适当的类型注解
```

#### 测试阶段提示词
```
我需要为[模块名]API编写完整的测试套件。

已实现接口：[列出API端点]
测试要求：单元测试+集成测试+权限测试，覆盖率≥70%

请帮我：
1. 编写Service层单元测试
2. 编写API集成测试（含分页和错误场景）
3. 编写权限矩阵测试
4. 性能基线测试
5. 生成覆盖率报告

测试环境：pytest + TestClient + 覆盖率检查
```

#### 交付阶段提示词
```
我需要完成[模块名]的交付准备工作。

已完成：设计→实现→测试阶段
当前状态：[描述当前状态]

请帮我：
1. 完善OpenAPI文档和示例
2. 更新README使用指南
3. 准备部署配置和健康检查
4. 执行最终质量门禁检查
5. 生成发布说明文档

质量要求：
- 代码格式化检查通过
- 静态分析无问题
- 安全扫描通过
- 覆盖率达到要求
```

---

## 📊 进度跟踪模板

### 阶段进度检查表

```
## 项目开发进度跟踪

### 阶段一：需求与设计 (目标：2-3天)
- [x] 业务需求分析 (0.5天)
- [x] API端点设计 (1天)
- [x] 数据模型设计 (0.5天)
- [x] 权限矩阵设计 (0.5天)
- [x] 设计文档评审

实际用时：2.5天 | 进度：100%

### 阶段二：代码实现 (目标：3-5天)
- [x] 环境准备 (0.5天)
- [x] Pydantic模型 (1天)
- [x] Service层实现 (1.5天)
- [x] 路由层实现 (1天)
- [x] 异常处理 (0.5天)
- [x] 代码评审

实际用时：4.5天 | 进度：100%

### 阶段三：测试验证 (目标：2-3天)
- [x] 单元测试 (1天)
- [x] API集成测试 (1天)
- [x] 权限测试 (0.5天)
- [x] 性能安全测试 (0.5天)
- [x] 覆盖率报告 (0.5天)

实际用时：3天 | 进度：100%

### 阶段四：文档与交付 (目标：1-2天)
- [x] API文档完善 (0.5天)
- [x] 使用指南 (0.5天)
- [x] 部署准备 (0.5天)
- [x] 最终检查 (0.5天)

实际用时：2天 | 进度：100%

## 总体进度
预计用时：8-13天 | 实际用时：12天 | 效率：92%
```

---

**文档版本**: v2.1
**创建时间**: 2025-11-12
**适用项目**: AI广告代投系统接口开发
**维护责任人**: 开发团队
**下次更新**: 重大功能变更时