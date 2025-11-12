# 接口文档索引 v2.1

本页汇总与接口开发相关的规范、指南与任务清单，按照"设计 → 实现 → 测试 → 交付"的完整工作流组织，支持Claude协作开发的分阶段实施。

## 🚀 快速导航（Claude协作开发）

### 核心工作流程文档
- **[接口开发任务流程总览](./INTERFACE_DEVELOPMENT_WORKFLOW.md)** - 四阶段完整开发流程（设计→实现→测试→交付）
- **[分阶段任务清单模板](./PHASE_BASED_TASK_TEMPLATES.md)** - 可复用的阶段任务模板，含检查清单
- **[Claude开发路线图](./CLAUDE_DEVELOPMENT_ROADMAP.md)** - Claude协作开发指南和提示词模板

### 技术规范文档
- **[后端API开发指南](./BACKEND_API_GUIDE.md)** - FastAPI + Pydantic v2 完整开发规范
- **[代码质量任务清单](./CODE_QUALITY_TASKS.md)** - 代码规范、质量门禁、安全扫描
- **[测试实施任务清单](./TESTING_IMPLEMENTATION_TASKS.md)** - 单元测试、集成测试、覆盖率要求

### 部署运维文档
- **[部署发布任务清单](./DEPLOYMENT_RELEASE_TASKS.md)** - 部署配置、健康检查、监控告警

### 历史参考文档
- 接口设计模板 - `docs/development/INTERFACE_DESIGN_TEMPLATE.md`
- 接口开发检查清单 - `docs/development/INTERFACE_DEVELOPMENT_CHECKLIST.md`
- 接口测试指南 - `docs/development/INTERFACE_TESTING_GUIDELINES.md`
- 接口文档工作流 - `docs/development/INTERFACE_DOCUMENTATION_WORKFLOW.md`

## 🎯 Claude协作开发流程

### 四阶段开发模式
**阶段一：需求与设计** (2-3天)
1. 使用 [接口开发任务流程总览](./INTERFACE_DEVELOPMENT_WORKFLOW.md) 了解阶段目标
2. 复制 [分阶段任务清单模板](./PHASE_BASED_TASK_TEMPLATES.md) 的阶段一模板
3. 按照模板完成业务分析、接口设计、数据建模、权限设计

**阶段二：代码实现** (3-5天)
1. 参考后端API开发指南进行编码
2. 使用代码质量任务清单进行质量检查
3. 按照阶段二模板完成环境准备、模型实现、服务层、路由层

**阶段三：测试验证** (2-3天)
1. 使用测试实施任务清单指导测试编写
2. 按照阶段三模板完成单元测试、集成测试、权限测试
3. 确保覆盖率≥70%，性能基线达标

**阶段四：文档与交付** (1-2天)
1. 完善API文档和使用指南
2. 使用部署发布任务清单准备上线
3. 按照阶段四模板完成最终质量检查

## 📋 技术规范要点

### API设计规范
- **版本与路由**: 统一 `/api/v1`，资源名用复数（`/projects`、`/ad-accounts`）
- **认证方式**: `Authorization: Bearer <token>`（JWT）
- **权限控制**: 基于角色的访问控制（5个角色）
- **数据隔离**: RLS行级安全策略

### 响应格式标准
```python
# 成功响应
{
  "success": true,
  "data": {...},
  "message": "操作成功",
  "code": "SUCCESS",
  "request_id": "uuid",
  "timestamp": "2025-11-12T10:30:00Z"
}

# 分页响应
{
  "success": true,
  "data": {
    "items": [...],
    "meta": {
      "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 100,
        "total_pages": 5
      }
    }
  }
}
```

### Pydantic v2 规范
- **配置**: `ConfigDict(from_attributes=True)`
- **验证**: 使用 `model_validate(..., from_attributes=True)`
- **禁用**: 不再使用 `from_orm` 方法

### 错误处理规范
- **系统错误**: `SYS_xxx` 格式
- **业务错误**: `BIZ_xxx` 格式
- **安全错误**: `SEC_xxx` 格式
- **HTTP映射**: 统一错误响应体，401/403等状态码

### 健康检查规范
- `/healthz` - 服务存活探针
- `/readyz` - 服务就绪探针（含数据库检查）
- `/api/v1/health` - API健康状态（兼容旧版 `/api/health`）

## 🔧 开发质量门禁

### 代码质量要求
- **格式化**: Black + isort
- **静态检查**: flake8 + mypy
- **安全扫描**: bandit + pip-audit
- **类型检查**: mypy strict模式

### 测试覆盖要求
- **总覆盖率**: ≥70%
- **核心功能**: 100%覆盖率
- **分支覆盖率**: ≥80%

### 性能基线
- **健康检查**: P95 < 100ms
- **列表接口**: P95 < 300ms
- **详情接口**: P95 < 100ms

## 📚 文档导航

### 新手快速开始
1. **阅读顺序**:
   - 接口开发任务流程总览 → 分阶段任务清单模板 → Claude开发路线图
2. **开始第一个模块**:
   - 复制阶段一模板 → 完成设计 → 进入阶段二实现

### 进阶开发者
1. **深入了解**: 后端API开发指南 → 代码质量任务清单
2. **测试优化**: 测试实施任务清单 → 性能基线设定

### 运维部署
1. **部署准备**: 部署发布任务清单 → 健康检查配置
2. **监控运维**: 监控告警配置 → 故障处理流程

## 🎯 使用建议

### 团队协作
- **项目经理**: 使用阶段一模板进行需求分析和设计
- **后端开发**: 使用阶段二模板进行代码实现
- **测试工程师**: 使用阶段三模板进行测试验证
- **运维工程师**: 使用阶段四模板进行部署准备

### Claude协作
- **提示词**: 使用Claude开发路线图中的提示词模板
- **分阶段执行**: 严格按照四阶段流程，每个阶段完成后再进入下一阶段
- **质量保证**: 每个阶段都使用对应的检查清单验证交付质量

### 持续改进
- **经验积累**: 在项目总体跟踪模板中记录经验教训
- **流程优化**: 根据实际使用情况优化任务模板
- **知识分享**: 定期更新文档和最佳实践

