# AI广告代投系统 - 项目导航指南

> **项目名称**: AI广告代投系统
> **版本**: v2.1
> **更新日期**: 2025-11-11
> **文档类型**: 项目入口和导航中心

本指南为AI广告代投系统提供完整的项目概览、文档导航和快速启动指南，帮助不同角色的团队成员快速了解和参与项目。

---

## 🎯 项目概览

### 项目简介
AI广告代投系统是一个智能化的广告投放管理平台，专为Facebook广告代理商设计，通过AI技术提升投放效率、降低成本、优化ROI。

### 核心价值
- **效率提升**: 自动化日报处理，节省90%人工时间
- **成本控制**: 精准的对账系统，避免财务损失
- **智能决策**: AI驱动的账户寿命预测和异常检测
- **风险管控**: 实时监控和预警，及时发现问题

### 技术亮点
- **现代化架构**: FastAPI + Next.js + PostgreSQL
- **安全可靠**: RLS权限控制 + JWT认证 + 审计日志
- **高性能**: Redis缓存 + 数据库优化 + 异步处理
- **可扩展**: 微服务架构 + Docker容器化 + CI/CD

### 目标用户
- **广告代理商**: 多项目管理、客户关系维护
- **投手**: 日常广告投放、数据录入、报表提交
- **户管**: 账户分配、日报审核、数据管理
- **财务**: 充值审批、对账管理、财务分析
- **管理者**: 整体监控、ROI分析、团队管理

### 核心功能
- 📊 **智能项目管理**: 项目生命周期管理，ROI分析
- 👥 **多角色协作**: 投手、户管、财务、管理员协同工作
- 🔒 **安全权限控制**: 基于RLS的数据隔离和权限管理
- 🤖 **AI智能监控**: 账户异常检测、性能预警、寿命预测
- 💰 **自动对账系统**: 精准的财务对账和差异分析
- 📈 **实时数据监控**: 消耗、转化、ROI等关键指标监控

---

## 📚 文档导航体系

### 🏗️ 核心文档索引

#### 主技术文档
- **[AI广告代投系统开发文档_优化版v2.1.md](./AI广告代投系统开发文档_优化版v2.1.md)** - 完整的技术架构和开发规范

#### 系统架构文档
- **[SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md)** - 系统架构概览、业务模式、权限矩阵
- **[DATA_SCHEMA.md](./DATA_SCHEMA.md)** - 数据库设计、RLS策略、表结构定义
- **[STATE_MACHINE.md](./STATE_MACHINE.md)** - 状态机定义、业务流程、权限控制

### 💻 开发文档
- **[BACKEND_API_GUIDE.md](./BACKEND_API_GUIDE.md)** - 后端API开发指南、接口规范
- **[FRONTEND_GUIDE.md](./FRONTEND_GUIDE.md)** - 前端开发指南、组件库使用
- **[DEVELOPMENT_ENVIRONMENT_SETUP.md](./DEVELOPMENT_ENVIRONMENT_SETUP.md)** - 开发环境配置、工具链

### 🔧 运维文档
- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - 部署指南、Docker配置、CI/CD
- **[MONITORING_OPS.md](./MONITORING_OPS.md)** - 监控运维、告警系统、故障处理
- **[SECURITY_CONFIG.md](./SECURITY_CONFIG.md)** - 安全配置、权限策略、漏洞管理
- **[TESTING_STRATEGY.md](./TESTING_STRATEGY.md)** - 测试策略、质量保证、自动化

### 📋 角色阅读路径

#### 👥 项目管理者
**推荐阅读路径**:
1. [项目概览](#-项目概览) → 了解项目价值和技术亮点
2. [SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md) → 掌握业务模式和权限体系
3. [开发阶段规划](#-项目管理指南) → 了解开发进度和里程碑
4. [验收标准](#-验收标准) → 确认交付质量

**重点关注**: 业务价值、开发进度、验收标准、ROI指标

#### 💻 后端开发者
**推荐阅读路径**:
1. [开发环境配置](#-快速开始) → 搭建开发环境
2. [BACKEND_API_GUIDE.md](./BACKEND_API_GUIDE.md) → API开发规范和最佳实践
3. [DATA_SCHEMA.md](./DATA_SCHEMA.md) → 数据库设计和RLS策略
4. [STATE_MACHINE.md](./STATE_MACHINE.md) → 状态机实现和业务逻辑
5. [主技术文档](./AI广告代投系统开发文档_优化版v2.1.md) → 完整技术规范

**重点关注**: API规范、数据库设计、状态机、安全配置

#### 🎨 前端开发者
**推荐阅读路径**:
1. [开发环境配置](#-快速开始) → 搭建前端开发环境
2. [FRONTEND_GUIDE.md](./FRONTEND_GUIDE.md) → 前端开发规范和组件使用
3. [BACKEND_API_GUIDE.md](./BACKEND_API_GUIDE.md) → API接口规范和调用方式
4. [主技术文档](./AI广告代投系统开发文档_优化版v2.1.md) → 系统架构和接口说明

**重点关注**: 组件库使用、API调用、状态管理、权限控制

#### 🔧 运维工程师
**推荐阅读路径**:
1. [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) → 部署配置和环境管理
2. [MONITORING_OPS.md](./MONITORING_OPS.md) → 监控系统和告警配置
3. [SECURITY_CONFIG.md](./SECURITY_CONFIG.md) → 安全配置和漏洞管理
4. [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) → 测试策略和质量保证

**重点关注**: 部署配置、监控告警、安全防护、备份恢复

---

## 🚀 快速开始

### 系统要求
- **Node.js**: 18.0+
- **Python**: 3.11+
- **Docker**: 4.0+
- **Git**: 2.30+

### 一键启动
```bash
# 克隆项目
git clone <repository-url>
cd ai-ad-spend

# 环境检查
./scripts/check-environment.sh

# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 初始化数据库
./scripts/init-database.sh

# 启动前端
cd frontend && npm run dev

# 启动后端
cd backend && uvicorn app.main:app --reload
```

### 访问地址
- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **Grafana监控**: http://localhost:3001

### 开发环境配置
```bash
# 安装前端依赖
cd frontend && npm install

# 安装后端依赖
cd backend && pip install -r requirements.txt

# 配置环境变量
cp .env.example .env.local
# 编辑 .env.local 添加必要配置

# 数据库迁移
cd backend && alembic upgrade head
```

### 常用开发命令
```bash
# 前端开发
npm run dev          # 开发服务器
npm run build        # 生产构建
npm run test         # 运行测试
npm run lint         # 代码检查

# 后端开发
uvicorn app.main:app --reload  # 开发服务器
pytest -v --disable-warnings     # 运行测试
black app/                    # 代码格式化
isort app/                    # 导入排序

# 数据库操作
alembic upgrade head    # 执行迁移
alembic revision --autogenerate -m "migration message"  # 创建迁移

# Docker操作
docker-compose -f docker-compose.dev.yml up -d    # 启动开发环境
docker-compose -f docker-compose.dev.yml logs -f  # 查看日志
docker-compose -f docker-compose.dev.yml down   # 停止服务
```

---

## 💻 开发者指南

### 技术栈
- **后端**: FastAPI + Pydantic v2 + SQLAlchemy (同步版)
- **前端**: Next.js 14 + TypeScript + Tailwind + shadcn/ui
- **数据库**: PostgreSQL (Supabase托管)
- **缓存**: Redis + RQ
- **监控**: Prometheus + Grafana + Sentry

### 开发规范
- **代码格式化**: Prettier + ESLint (前端), Black + isort (后端)
- **提交规范**: Conventional Commits
- **API规范**: 统一返回格式 + 错误码
- **测试要求**: 单元测试 + 集成测试 + E2E测试

### 核心开发流程
1. **创建功能分支** → 编写代码 → 提交PR
2. **代码审查** → 自动化测试 → 部署到测试环境
3. **QA测试** → 验收 → 合并到主分支
4. **自动化部署** → 监控确认 → 功能上线

### 分支管理
- `main`: 主分支，生产环境代码
- `develop`: 开发分支，集成测试
- `feature/*`: 功能分支，新功能开发
- `hotfix/*`: 热修复分支，紧急修复

### API开发标准
```python
# 统一响应格式
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
    "message": "参数验证失败"
  },
  "request_id": "uuid",
  "timestamp": "2025-11-11T10:30:00Z"
}
```

---

## 🔧 运维管理

### 部署环境
- **开发环境**: 本地开发，热重载
- **测试环境**: 自动部署，数据脱敏
- **预生产环境**: 生产数据镜像，完整测试
- **生产环境**: 蓝绿部署，零停机

### 监控指标
- **应用指标**: 响应时间、错误率、吞吐量
- **业务指标**: 消耗、转化、ROI、账户状态
- **基础设施**: CPU、内存、磁盘、网络
- **安全指标**: 登录失败、异常访问、攻击检测

### 备份策略
- **数据库**: 每日全量备份 + 实时增量备份
- **配置文件**: 版本控制管理
- **日志文件**: 集中收集和长期存储
- **代码**: Git仓库 + 多地备份

### 故障处理
1. **监控告警** → 自动通知相关人员
2. **快速诊断** → 定位问题根因
3. **紧急修复** → 实施临时解决方案
4. **根本解决** -> 彻底修复问题并预防

---

## 👥 项目管理指南

### 项目状态
- **当前版本**: v2.1 (2025-11-11)
- **开发阶段**: P0核心功能开发中
- **预计上线**: 3个月内

### 核心业务流程
```
甲方签约付款 → 创建项目 → 申请渠道账户 → 分配账户给投手
      ↓
投手投放广告 → 每日提交日报 → 数据员审核 → 确认粉数
      ↓
提交充值申请 → 数据员审核需求 → 财务审批 → 财务打款
      ↓
代理商充值 → 月底财务对账 → 项目盈利分析 → AI优化建议
```

### 开发阶段规划

#### P0阶段：核心业务功能（3-4周）
- ✅ 用户认证和权限系统
- ✅ 项目管理和渠道管理
- ✅ 广告账户管理
- ✅ 日报提交流程
- ✅ 充值申请流程

#### P1阶段：财务和数据（2-3周）
- 🔄 财务对账系统
- 🔄 成本分析模块
- 🔄 数据导入工具
- 🔄 基础报表功能

#### P2阶段：AI和自动化（2-3周）
- ⏳ AI异常检测
- ⏳ 账户寿命预测
- ⏳ 自动化通知
- ⏳ 高级报表功能

### 验收标准
- ✅ **核心流程完整**：日报、充值、对账端到端可跑通
- ✅ **安全控制严格**：所有操作都有权限验证和审计日志
- ✅ **API响应统一**：所有接口都遵循统一的响应格式
- ✅ **监控覆盖全面**：关键业务指标都有监控和告警
- ✅ **部署自动化**：支持一键部署和回滚

### 团队协作
- **架构团队**: 技术架构、核心模块、代码审查
- **开发团队**: 前端、后端、数据库、AI模块
- **测试团队**: 功能测试、性能测试、安全测试
- **运维团队**: 部署、监控、备份、故障处理
- **产品团队**: 需求分析、用户体验、项目协调

---

## 📞 技术支持

### 文档反馈
- **技术问题**: 提交GitHub Issue
- **文档更新**: 联系架构团队
- **紧急故障**: 联系运维负责人

### 联系方式
- **技术架构师**: architect@company.com
- **开发团队负责人**: dev-team@company.com
- **运维负责人**: ops-team@company.com
- **产品负责人**: product@company.com

### 相关资源
- **代码仓库**: https://github.com/your-org/ai-ad-spend
- **项目管理**: https://project.yourdomain.com
- **监控面板**: https://monitor.yourdomain.com
- **文档中心**: https://docs.yourdomain.com

---

## 🤖 AI助手开发规范

### 项目规则记忆
为了确保代码的一致性和质量，AI助手必须遵循存储在 [`.project-rules.md`](./.project-rules.md) 中的所有项目规范。

### 核心开发原则

1. **严格遵循技术栈规范**
   - 后端：FastAPI + Pydantic v2 + SQLAlchemy (同步版)
   - 前端：Next.js 15 + TypeScript + Tailwind + shadcn/ui
   - 数据库：PostgreSQL + RLS权限控制
   - 缓存：Redis + RQ异步队列

2. **代码规范要求**
   - Python必须使用类型注解和文档字符串
   - TypeScript必须有严格的类型定义
   - 遵循统一的代码格式化（Black/isort/Prettier）
   - 所有API必须有适当的错误处理和日志

3. **安全要求**
   - 所有API端点都需要JWT认证
   - 实现基于角色的权限控制（5个角色）
   - 敏感数据必须加密存储
   - 遵循RLS数据隔离原则

4. **API响应格式**
   ```python
   # 成功响应（必须格式）
   {
     "success": true,
     "data": {...},
     "message": "操作成功",
     "code": "SUCCESS",
     "request_id": "uuid",
     "timestamp": "2025-11-11T10:30:00Z"
   }
   ```

5. **数据库设计原则**
   - 表名使用复数形式（users, projects）
   - 必须包含created_at和updated_at字段
   - 外键必须创建索引
   - 大表必须考虑分区

6. **测试要求**
   - 单元测试覆盖率 > 80%
   - 所有API必须有集成测试
   - 关键业务流程需要E2E测试

7. **Git提交规范**
   ```
   <type>(<scope>): <subject>

   type: feat, fix, docs, style, refactor, perf, test, chore
   ```

### 开发检查清单
在编写或修改代码前，AI助手必须：
- [ ] 查阅 [`.project-rules.md`](./.project-rules.md) 确认规范
- [ ] 检查是否遵循统一的命名规范
- [ ] 确认是否包含适当的错误处理
- [ ] 验证是否实现了必要的权限控制
- [ ] 检查是否添加了必要的日志记录

### 重要提醒
- **禁止**硬编码敏感信息（使用环境变量）
- **必须**使用依赖注入而非直接实例化
- **必须**处理所有可能的异常情况
- **禁止**在生产环境输出调试信息
- **必须**遵循项目的目录结构和文件命名规范

### 常见问题
1. **Q**: 如何处理权限验证？
   **A**: 使用 `require_role` 装饰器，传入允许的角色列表

2. **Q**: 如何实现分页？
   **A**: 使用 `page` 和 `size` 参数，返回 `PaginatedResponse`

3. **Q**: 如何处理数据库事务？
   **A**: 使用 `db.begin()` 上下文管理器

4. **Q**: 如何添加审计日志？
   **A**: 使用 `audit_log` 服务记录关键操作

---

**文档版本**: v2.1
**最后更新**: 2025-11-11
**下次审查**: 功能重大变更时
**维护责任人**: 项目架构团队