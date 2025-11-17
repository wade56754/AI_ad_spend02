# AI广告代投系统

> **项目版本**: v2.3
> **最后更新**: 2025-11-12
> **技术栈**: FastAPI + PostgreSQL + Redis + Python

---

## 📋 项目概述

AI广告代投系统是一个基于FastAPI的现代化广告投放管理平台，提供完整的广告账户管理、数据监控、财务对账、数据分析等功能。

### 核心功能

#### 📊 核心功能模块

##### 日报管理系统（已实现）
- ✅ **日报创建和管理** - 投手每日提交广告投放数据
- ✅ **审核工作流** - 数据员审核确认，支持通过/驳回
- ✅ **批量导入导出** - 支持Excel文件导入导出
- ✅ **数据统计分析** - 实时统计CPA、ROAS等关键指标
- ✅ **审计日志** - 完整的操作记录追踪

##### 项目管理模块（已实现）
- ✅ **项目CRUD管理** - 完整的项目创建、查询、更新、删除
- ✅ **成员管理** - 灵活的团队成员分配和权限控制
- ✅ **费用记录** - 项目成本追踪和费用管理
- ✅ **统计分析** - 项目数据统计和绩效分析
- ✅ **权限控制** - 基于角色的细粒度访问控制

##### 充值管理模块（已实现）
- ✅ **充值申请管理** - 创建、查询、更新充值申请
- ✅ **双重审核机制** - 数据审核 + 财务审批的完整流程
- ✅ **打款凭证管理** - 支付凭证上传和管理
- ✅ **统计分析报表** - 多维度充值数据分析
- ✅ **资金流程控制** - 完整的资金流转管理

#### 🔧 系统功能
- 📈 **数据监控** - 实时广告投放数据监控
- 💰 **财务对账** - 自动化对账系统
- 📊 **数据分析** - CPL、ROI等关键指标分析
- 🔒 **权限管理** - 基于角色的访问控制

---

## 📊 系统架构

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│             │       │             │       │             │
│  前端 (Next.js)│◄──────┤  后端 (FastAPI) │◄──────┤  数据库 (PostgreSQL) │
│             │       │             │       │             │
│ - 用户界面    │       │ - RESTful API   │       │ - 业务数据       │
│ - 业务逻辑    │       │ - 业务逻辑       │       │ - 数据持久化     │
│ - 权限控制    │       │ - 身份验证       │       │ - 数据关系       │
└─────────────┘       └─────────────┘       └─────────────┘
                                    │
                                    │
                          ┌─────────────┐
                          │             │
                          │  Redis      │
                          │             │
                          │ - 缓存服务     │
                          │ - 任务队列     │
                          │ - 会话存储     │
                          └─────────────┘
```

---

## 📚 开发规范和文档

### 核心规范文档（必读）

> 完整文档地图与权威链接请访问：`docs/DOCUMENTATION_INDEX.md`
1. **[.project-rules.md](./.project-rules.md)** ⭐ - 项目开发核心规范（最高优先级）
   - 技术栈约定、角色权限、开发规范总则
   - 所有规则冲突以此文档为准

2. **[CLAUDE.md](./CLAUDE.md)** - AI助手开发规范
   - AI助手强制性约束和开发流程
   - 典型错误防范清单

3. **[docs/API_RULEBOOK.md](./docs/API_RULEBOOK.md)** - API规则索引（定义以 SoT 为准；实践见 `docs/dev/API_RULEBOOK.md`）
   - 统一响应格式、权限校验、性能指标

4. **[docs/DOCUMENTATION_INDEX.md](./docs/DOCUMENTATION_INDEX.md)** - 文档索引与导航（SoT 与模块文档入口）
   - 前端开发规范、UI设计指南、接口开发流程等

### 规则优先级

```
Level 1: .project-rules.md (总纲和仲裁标准) ⭐
    ↓
Level 2: 领域规范 (API_RULEBOOK.md, FRONTEND_DEVELOPMENT_RULES.md, CLAUDE.md)
    ↓
Level 3: 执行指南 (AI_MODULE_DEVELOPMENT_WORKFLOW.md, UI_DESIGN_GUIDE.md)
    ↓
Level 4: 参考文档 (技术文档、部署指南)
```

**规则冲突时**: 以高优先级文档为准

### 快速查找
- 🔰 新手入门: [.project-rules.md](./.project-rules.md) + [CLAUDE.md](./CLAUDE.md)
- 💻 后端开发: [docs/API_RULEBOOK.md](./docs/API_RULEBOOK.md) + [docs/rule/AI_MODULE_DEVELOPMENT_WORKFLOW.md](./docs/rule/AI_MODULE_DEVELOPMENT_WORKFLOW.md)
- 🎨 前端开发: [docs/dev/FRONTEND_RULES.md](./docs/dev/FRONTEND_RULES.md) + [docs/rule/UI_DESIGN_GUIDE.md](./docs/rule/UI_DESIGN_GUIDE.md)
- 🤖 AI助手: [CLAUDE.md](./CLAUDE.md) + [docs/rule/AI_MODULE_DEVELOPMENT_WORKFLOW.md](./docs/rule/AI_MODULE_DEVELOPMENT_WORKFLOW.md)

---

## 🚀 快速开始

### 环境要求
- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Node.js 16+ (前端)

### 1. 克隆项目
```bash
git clone https://github.com/your-org/ai_ad_spend02.git
cd ai_ad_spend02
```

### 2. 后端启动
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要配置

# 数据库迁移
cd backend
alembic upgrade head

# 启动服务
uvicorn main:app --reload
```

### 3. 前端开发（重要）
```bash
# 进入前端目录
cd frontend

# 安装依赖
pnpm install

# 开发服务器（使用Turbo）
pnpm dev

# 代码质量检查（必须通过）
pnpm lint          # ESLint检查
pnpm type-check    # TypeScript类型检查

# 生产构建
pnpm build
```

### 4. 访问系统
- **前端应用**: http://localhost:3000
- **API服务**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/healthz

### ⚠️ 前端开发核心要求
- **必须遵循**: [前端开发规则总纲](docs/dev/FRONTEND_RULES.md) 中的所有强制性规范
- **页面结构**: 必须使用 `AppLayout + PageHeader` 标准结构
- **组件使用**: 优先使用 shadcn/ui 组件，禁止裸HTML标签
- **类型安全**: 严格的TypeScript类型检查，禁止any类型
- **代码质量**: 提交前必须通过 `pnpm lint` 和 `pnpm type-check`

---

## 📚 文档中心

### 📖 开发文档
- [接口开发流程总览](docs/development/INTERFACE_DEVELOPMENT_WORKFLOW.md) - 四阶段开发流程
- [分阶段任务模板](docs/development/PHASE_BASED_TASK_TEMPLATES.md) - 可复用的开发模板
- [Claude协作开发指南](docs/development/CLAUDE_COLLABORATION_GUIDE.md) - AI辅助开发指南
- [后端API开发规范](docs/development/BACKEND_API_GUIDE.md) - 完整的API开发规范
- [日报管理API文档](docs/development/DAILY_REPORT_API_README.md) - 日报模块使用指南
- [项目管理API文档](docs/development/PROJECT_API_README.md) - 项目模块使用指南
- [充值管理API文档](docs/development/TOPUP_API_README.md) - 充值模块使用指南

### 🎨 前端开发规范（重要）
- [前端开发规则总纲](docs/rule/FRONTEND_DEVELOPMENT_RULES.md) - **强制性的前端开发规范**
- [项目开发规则索引](docs/rule/PROJECT_DEV_RULES.md) - 前端开发入口和快速查找指南
- [UI设计与开发指南](docs/rule/UI_DESIGN_GUIDE.md) - 组件使用规范和设计标准
- [页面模板指南](docs/rule/UI_LIST_PAGE_TEMPLATE.md) - **AppLayout + PageHeader 标准结构**

### 🔧 部署运维
- [部署指南](docs/deployment/DEPLOYMENT_GUIDE.md) - 生产环境部署（含“已实现 vs 规划”标注）
- [监控运维](docs/deployment/MONITORING_OPS.md) - 监控与告警（部分为规划能力）
- [安全配置](docs/deployment/SECURITY_CONFIG.md) - 安全基线（RLS 为未来方案，当前未启用）

### 📋 任务清单
- [代码质量任务](docs/development/CODE_QUALITY_TASKS.md) - 代码规范和质量门禁
- [测试实施任务](docs/development/TESTING_IMPLEMENTATION_TASKS.md) - 测试策略和规范

---

## 🛠️ 技术栈

### 后端技术
- **框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0 (同步)
- **数据验证**: Pydantic v2
- **认证**: JWT (15分钟访问令牌)
- **缓存**: Redis
- **任务队列**: RQ (Redis Queue)

### 前端技术
- **框架**: Next.js 16.0.2 + App Router
- **语言**: TypeScript 5.x (严格模式)
- **UI库**: React 18.x + shadcn/ui
- **样式**: Tailwind CSS 3.x
- **状态管理**: Zustand + React Hooks
- **数据获取**: SWR 2.x
- **表单处理**: React Hook Form 7.x
- **图表**: Recharts 2.x
- **构建工具**: Turbo (Next.js内置)

### 开发工具
#### 后端开发工具
- **代码格式化**: Black + isort
- **静态检查**: flake8 + mypy
- **测试框架**: pytest
- **API文档**: OpenAPI/Swagger
- **数据库迁移**: Alembic

#### 前端开发工具
- **代码格式化**: Prettier + ESLint
- **类型检查**: TypeScript (严格模式)
- **测试框架**: Jest + Testing Library
- **构建工具**: Next.js (内置Turbo)
- **包管理器**: pnpm

### 安全特性
- **权限控制**: 服务层 RBAC（5个角色）；数据库 RLS 为未来方案（当前未启用）
- **SQL注入防护**: ORM参数化查询
- **XSS防护**: 输入验证和输出编码
- **审计日志**: 完整的操作记录

---

## 🎯 角色权限

| 角色 | 权限范围 | 主要功能 |
|------|----------|----------|
| **admin** | 全部权限 | 系统管理、用户管理、全部数据访问 |
| **finance** | 财务相关 | 查看报表、财务对账、充值审批 |
| **data_operator** | 数据管理 | 审核日报、数据导入、统计分析 |
| **account_manager** | 账户管理 | 管理所属项目、查看团队数据 |
| **media_buyer** | 投手操作 | 创建/编辑日报、查看个人数据 |

---

## 📊 API端点

### 核心模块
- `/api/v1/topups` - 充值管理 **(新实现)**
- `/api/v1/projects` - 项目管理 **(已实现)**
- `/api/v1/ad-accounts` - 广告账户
- `/api/v1/daily-reports` - 日报管理 **(已实现)**
- `/api/v1/channels` - 渠道管理

### 系统端点
- `/healthz` - 健康检查
- `/readyz` - 就绪检查（含数据库）
- `/api/v1/health` - API状态

---

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
pytest -v

# 运行带覆盖率的测试
pytest --cov=backend --cov-report=html

# 运行特定模块测试
pytest tests/test_daily_report_*.py -v
```

### 测试覆盖率要求
- 总覆盖率 ≥ 70%
- 核心功能 100% 覆盖
- 分支覆盖率 ≥ 80%

---

## 📦 部署

### Docker部署
```bash
# 构建镜像
docker build -t ai-ad-spend .

# 运行容器
docker run -p 8000:8000 ai-ad-spend
```

### 生产环境
```bash
# 使用Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

### 代码规范
#### 后端代码规范
- 遵循 PEP 8 Python代码规范
- 使用 Black + isort 进行代码格式化
- 编写单元测试，确保测试覆盖率

#### 前端代码规范（强制要求）
- **严格遵循**: [前端开发规则总纲](docs/rule/FRONTEND_DEVELOPMENT_RULES.md)
- **页面结构**: 必须使用 AppLayout + PageHeader 标准布局
- **组件使用**: 优先使用 shadcn/ui，禁止裸HTML标签
- **类型安全**: TypeScript严格模式，禁止any类型
- **代码质量**: 必须通过 ESLint 和 TypeScript 检查
- **提交前检查**: `pnpm lint` 和 `pnpm type-check` 必须0错误

---

## 📞 支持

- **问题反馈**: [GitHub Issues](https://github.com/your-org/ai_ad_spend02/issues)
- **技术支持**: tech-support@your-domain.com
- **文档反馈**: docs@your-domain.com

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

---

**更新日志**:

### v2.3.0 (2025-11-12)
- ✨ 新增：完整的充值管理系统
- ✨ 新增：双重审核机制（数据审核+财务审批）
- ✨ 新增：打款凭证管理功能
- ✨ 新增：充值统计分析报表
- ✨ 新增：资金流程控制
- 🔧 优化：权限控制和RLS策略

### v2.2.0 (2025-11-12)
- ✨ 新增：完整的项目管理系统
- ✨ 新增：项目成员管理功能
- ✨ 新增：项目费用记录功能
- ✨ 新增：项目统计分析功能
- 🔧 优化：RLS权限策略
- 📚 完善：API文档和使用指南

### v2.1.0 (2025-11-12)
- ✨ 新增：完整的日报管理系统
- ✨ 新增：四阶段接口开发流程
- ✨ 新增：Claude协作开发指南
- 🔧 优化：统一响应格式
- 🔧 优化：错误处理机制
- 🔧 优化：权限控制系统

### v2.0.0 (2025-01-15)
- 🚀 重构：系统架构升级
- 🚀 重构：数据库设计优化
- 🚀 新增：RBAC权限系统
- 🚀 新增：审计日志功能

---

**开发团队**: AI广告代投系统开发团队
**最后更新**: 2025-11-12