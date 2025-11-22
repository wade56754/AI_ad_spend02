# AI广告代投系统

[![Version](https://img.shields.io/badge/version-3.0-blue.svg)](https://github.com/wade56754/AI_ad_spend02)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-orange.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15+-black.svg)](https://nextjs.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🚀 项目简介

AI广告代投系统是一个专为Facebook广告代理商设计的智能化广告投放管理平台。通过AI技术和自动化流程,帮助代理商提升投放效率、优化ROI、降低运营成本。

### 核心特性

- 🤖 **AI智能监控** - 账户异常检测、性能预警、寿命预测
- 📊 **自动化对账** - 精准的财务对账和差异分析
- 👥 **多角色协作** - 投手、运营、财务、管理员协同工作
- 🔒 **安全权限控制** - 基于RLS的数据隔离和权限管理
- 📈 **实时数据监控** - 消耗、转化、ROI等关键指标实时追踪
- 💰 **智能充值管理** - 自动化充值申请和审批流程

### 核心功能模块

#### 日报管理系统（已实现）
- ✅ **日报创建和管理** - 投手每日提交广告投放数据
- ✅ **审核工作流** - 数据员审核确认，支持通过/驳回
- ✅ **批量导入导出** - 支持Excel文件导入导出
- ✅ **数据统计分析** - 实时统计CPA、ROAS等关键指标
- ✅ **审计日志** - 完整的操作记录追踪

#### 项目管理模块（已实现）
- ✅ **项目CRUD管理** - 完整的项目创建、查询、更新、删除
- ✅ **成员管理** - 灵活的团队成员分配和权限控制
- ✅ **费用记录** - 项目成本追踪和费用管理
- ✅ **统计分析** - 项目数据统计和绩效分析
- ✅ **权限控制** - 基于角色的细粒度访问控制

#### 充值管理模块（已实现）
- ✅ **充值申请管理** - 创建、查询、更新充值申请
- ✅ **双重审核机制** - 数据审核 + 财务审批的完整流程
- ✅ **打款凭证管理** - 支付凭证上传和管理
- ✅ **统计分析报表** - 多维度充值数据分析
- ✅ **资金流程控制** - 完整的资金流转管理

## 📚 文档中心

完整的文档请访问 **[📖 DOCS_README.md](./DOCS_README.md)** - 完整的5层文档体系

### 快速链接

- 📋 [MASTER_SPEC.md](./MASTER_SPEC.md) - 系统根规范（最高优先级SoT）
- 📖 [系统架构文档](./docs/1.overview/SYSTEM_OVERVIEW.md)
- 🗄️ [数据库设计](./docs/2.sot/DATA_SCHEMA.md)
- 🔄 [状态机设计](./docs/2.sot/STATE_MACHINE.md)
- 📋 [项目开发规则](./docs/1.overview/PROJECT_RULES.md) - AI协作开发必读
- 🚀 [快速开始指南](#快速开始)

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI + Pydantic v2
- **数据库**: PostgreSQL (Supabase)
- **ORM**: SQLAlchemy 2.0
- **缓存**: Redis
- **认证**: JWT + OAuth2

### 前端
- **框架**: Next.js 15 (App Router)
- **语言**: TypeScript
- **样式**: Tailwind CSS
- **组件**: shadcn/ui
- **状态管理**: Zustand

### 基础设施
- **容器化**: Docker + Docker Compose
- **监控**: Prometheus + Grafana
- **日志**: ELK Stack
- **CI/CD**: GitHub Actions

## 🚀 快速开始

### 环境要求

- Node.js 18+
- Python 3.11+
- Docker Desktop
- PostgreSQL 15+
- Redis 7+

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/wade56754/AI_ad_spend02.git
cd AI_ad_spend02
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置必要的环境变量
```

3. **安装依赖**
```bash
# 后端依赖
pip install -r requirements.txt

# 前端依赖
cd frontend && npm install
cd ..
```

4. **启动数据库**
```bash
docker-compose up -d postgres redis
```

5. **运行数据库迁移**
```bash
cd backend
alembic upgrade head
cd ..
```

6. **启动服务**
```bash
# 启动后端 (新终端)
cd backend
uvicorn main:app --reload --port 8000

# 启动前端 (新终端)
cd frontend
npm run dev
```

7. **访问应用**
- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 📂 项目结构

```
AI_ad_spend02/
├── backend/                # 后端服务
│   ├── app/               # 应用主目录
│   ├── tests/             # 测试文件
│   └── alembic/           # 数据库迁移
├── frontend/              # 前端应用
│   ├── app/              # Next.js App目录
│   ├── components/       # React组件
│   └── lib/              # 工具函数
├── docs/                  # 文档中心（5层架构）
│   ├── 1.overview/       # Tier 1: 系统全局视图
│   ├── 2.sot/            # Tier 2: 真相来源文档（11个SoT）
│   ├── 3.dev-guides/     # Tier 3: 开发指南
│   ├── 4.ui-ux/          # Tier 4: UI/UX文档
│   ├── 5.ops/            # Tier 5: 运维文档
│   └── archive/          # 历史文档归档
├── .claude/              # Claude Code项目规则
│   └── rule/             # AI开发规则集
├── MASTER_SPEC.md        # 系统根规范（P0优先级）
├── DOCS_README.md        # 文档中心完整索引
├── scripts/              # 脚本工具
├── tests/                # 集成测试
└── docker-compose.yml    # Docker编排
```

## 🎯 角色权限

| 角色 | 权限范围 | 主要功能 |
|------|----------|----------|
| **admin** | 全部权限 | 系统管理、用户管理、全部数据访问 |
| **finance** | 财务相关 | 查看报表、财务对账、充值审批 |
| **data_operator** | 数据管理 | 审核日报、数据导入、统计分析 |
| **account_manager** | 账户管理 | 管理所属项目、查看团队数据 |
| **media_buyer** | 投手操作 | 创建/编辑日报、查看个人数据 |

## 🧪 测试

```bash
# 运行后端测试
pytest

# 运行前端测试
npm test

# 运行E2E测试
npm run test:e2e

# 查看测试覆盖率
pytest --cov=backend/app
```

## 🚢 部署

### Docker部署

```bash
# 构建镜像
docker build -t ai-ad-spend .

# 使用docker-compose部署
docker-compose up -d
```

### Kubernetes部署

```bash
# 应用配置
kubectl apply -f k8s/

# 查看部署状态
kubectl get pods -n ai-ad-spend
```

详细部署文档请参考 [部署指南](./docs/5.ops/README.md)

## 🤝 贡献指南

我们欢迎所有形式的贡献！请阅读 [贡献指南](CONTRIBUTING.md) 了解如何参与项目开发。

### 开发流程

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范

#### 后端代码规范
- 遵循 PEP 8 Python代码规范
- 使用 Black + isort 进行代码格式化
- 编写单元测试，确保测试覆盖率

#### 前端代码规范
- TypeScript严格模式，禁止any类型
- 优先使用 shadcn/ui 组件
- 必须通过 ESLint 和 TypeScript 检查
- 提交前检查: `npm run lint` 和 `npm run type-check` 必须0错误

#### AI协作开发
- 严格遵循 [PROJECT_RULES.md](./docs/1.overview/PROJECT_RULES.md) 中定义的所有规则
- 所有代码生成必须基于 [docs/2.sot/](./docs/2.sot/) 下的SoT文档
- 开发前必读 [MASTER_SPEC.md](./MASTER_SPEC.md) 了解系统架构原则

## 📊 项目状态

- ✅ Phase 0: 基础架构搭建 (完成)
- ✅ Phase 1: 核心功能开发 (完成)
- 🚧 Phase 2: AI功能集成 (进行中)
- ⏳ Phase 3: 性能优化 (计划中)

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 联系我们

- 📧 Email: support@ai-ad-spend.com
- 💬 Discord: [加入我们的社区](https://discord.gg/ai-ad-spend)
- 🐛 Issues: [GitHub Issues](https://github.com/wade56754/AI_ad_spend02/issues)

---

**更新日志**:

### v4.0.0 (2025-11-22)
- 🎯 重构：完成文档体系重构为5层分级架构
- 📚 新增：MASTER_SPEC.md 系统根规范（P0优先级）
- 📖 优化：11个SoT文档统一归档至 docs/2.sot/
- 🗂️ 归档：历史文档版本统一归档至 docs/archive/
- ✨ 新增：DOCS_README.md 完整文档索引

### v3.0.0 (2024-11-18)
- 🎯 重构：创建项目规则总纲 (.claude/PROJECT_RULES.md)
- 📚 重构：重新组织文档结构 (保留核心文档，新建6大板块)
- ✨ 新增：AI自检清单和开发强制规范
- 📖 完善：各板块README索引文档

### v2.3.0 (2024-11-12)
- ✨ 新增：完整的充值管理系统
- ✨ 新增：双重审核机制（数据审核+财务审批）
- ✨ 新增：打款凭证管理功能
- ✨ 新增：充值统计分析报表
- 🔧 优化：权限控制和RLS策略

---

<p align="center">
  Made with ❤️ by AI Ad Spend Team
</p>
