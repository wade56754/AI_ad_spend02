# AI广告代投系统文档中心

> **版本**: v2.1
> **更新日期**: 2025-11-11

欢迎来到AI广告代投系统的文档中心。这里包含了系统的完整技术文档、开发指南、部署说明和项目管理资料。

## 📑 文档架构

```
docs/
├── core/                     # 核心系统文档
│   ├── SYSTEM_OVERVIEW.md   # 系统架构概览
│   ├── DATA_SCHEMA.md       # 数据库设计
│   ├── STATE_MACHINE.md     # 状态机规范
│   └── AI_AD_SYSTEM_MAIN_DOCUMENT.md  # 主技术文档
│
├── development/              # 开发指南
│   ├── BACKEND_API_GUIDE.md        # 后端API开发
│   ├── FRONTEND_GUIDE.md           # 前端开发
│   ├── DEVELOPMENT_ENVIRONMENT_SETUP.md  # 环境配置
│   └── DEVELOPMENT_STANDARDS.md    # 开发规范
│
├── deployment/               # 运维部署
│   ├── DEPLOYMENT_GUIDE.md         # 部署指南
│   ├── MONITORING_OPS.md           # 监控运维
│   ├── SECURITY_CONFIG.md          # 安全配置
│   └── TESTING_STRATEGY.md         # 测试策略
│
├── project-management/       # 项目管理
│   ├── TASK_ROADMAP.md             # 任务路线图
│   └── DOCUMENTATION_INDEX.md      # 文档索引
│
├── scripts/                  # 脚本工具
│   ├── create_partitioned_tables.sql
│   ├── fix_database_schema.sql
│   └── optimize_rls_policies.sql
│
└── archive/                  # 归档文档
    └── [历史版本文档]
```

## 🎯 快速导航

### 新手入门
1. **[系统概述](core/SYSTEM_OVERVIEW.md)** - 了解系统整体架构和业务模式
2. **[开发环境配置](development/DEVELOPMENT_ENVIRONMENT_SETUP.md)** - 搭建本地开发环境
3. **[快速开始](../README.md#-快速开始)** - 一键启动项目

### 开发人员
- **后端开发**: [API开发指南](development/BACKEND_API_GUIDE.md) → [数据库设计](core/DATA_SCHEMA.md)
- **前端开发**: [前端开发指南](development/FRONTEND_GUIDE.md) → [开发规范](development/DEVELOPMENT_STANDARDS.md)
- **全栈开发**: [主技术文档](core/AI_AD_SYSTEM_MAIN_DOCUMENT.md) → [状态机规范](core/STATE_MACHINE.md)

### 运维人员
1. **[部署指南](deployment/DEPLOYMENT_GUIDE.md)** - 生产环境部署
2. **[监控运维](deployment/MONITORING_OPS.md)** - 系统监控和告警
3. **[安全配置](deployment/SECURITY_CONFIG.md)** - 安全策略配置

### 项目管理
1. **[任务路线图](project-management/TASK_ROADMAP.md)** - 开发进度跟踪
2. **[文档索引](project-management/DOCUMENTATION_INDEX.md)** - 查找特定文档
3. **[测试策略](deployment/TESTING_STRATEGY.md)** - 质量保证流程

## 🔍 文档说明

### 核心系统文档
- **SYSTEM_OVERVIEW.md**: 系统的整体架构、业务模式、角色权限矩阵
- **DATA_SCHEMA.md**: 完整的数据库设计、表结构、RLS安全策略
- **STATE_MACHINE.md**: 5大核心业务流程的状态机设计
- **AI_AD_SYSTEM_MAIN_DOCUMENT.md**: 最完整的技术文档（77KB）

### 开发指南
- **BACKEND_API_GUIDE.md**: FastAPI后端开发规范和最佳实践
- **FRONTEND_GUIDE.md**: Next.js前端开发指南，包含组件库使用
- **DEVELOPMENT_ENVIRONMENT_SETUP.md**: 详细的开发环境配置步骤
- **DEVELOPMENT_STANDARDS.md**: 代码规范、Git提交规范、开发流程

### 运维部署
- **DEPLOYMENT_GUIDE.md**: Docker部署、Nginx配置、SSL证书
- **MONITORING_OPS.md**: Prometheus+Grafana监控配置
- **SECURITY_CONFIG.md**: 安全配置、漏洞防护、审计日志
- **TESTING_STRATEGY.md**: 测试策略、自动化测试、质量门禁

### 脚本工具
- **create_partitioned_tables.sql**: 创建分区表，优化大数据量查询
- **fix_database_schema.sql**: 修复数据库schema问题
- **optimize_rls_policies.sql**: 优化RLS策略性能

## 📚 文档阅读建议

### 按角色阅读

#### 👨‍💻 后端开发者
1. [开发环境配置](development/DEVELOPMENT_ENVIRONMENT_SETUP.md) - 搭建环境
2. [API开发指南](development/BACKEND_API_GUIDE.md) - 了解接口规范
3. [数据库设计](core/DATA_SCHEMA.md) - 理解数据模型
4. [状态机规范](core/STATE_MACHINE.md) - 掌握业务逻辑

#### 👨‍🎨 前端开发者
1. [开发环境配置](development/DEVELOPMENT_ENVIRONMENT_SETUP.md) - 搭建环境
2. [前端开发指南](development/FRONTEND_GUIDE.md) - 了解技术栈
3. [开发规范](development/DEVELOPMENT_STANDARDS.md) - 遵循编码规范
4. [系统概述](core/SYSTEM_OVERVIEW.md) - 理解业务流程

#### 🔧 运维工程师
1. [部署指南](deployment/DEPLOYMENT_GUIDE.md) - 学习部署流程
2. [监控运维](deployment/MONITORING_OPS.md) - 配置监控系统
3. [安全配置](deployment/SECURITY_CONFIG.md) - 实施安全策略
4. [测试策略](deployment/TESTING_STRATEGY.md) - 建立测试流程

#### 📊 项目经理
1. [系统概述](core/SYSTEM_OVERVIEW.md) - 了解项目全貌
2. [任务路线图](project-management/TASK_ROADMAP.md) - 跟踪开发进度
3. [主技术文档](core/AI_AD_SYSTEM_MAIN_DOCUMENT.md) - 深入技术细节

### 按学习路径

#### 初学者路径
1. 了解项目背景 → [系统概述](core/SYSTEM_OVERVIEW.md)
2. 搭建开发环境 → [环境配置](development/DEVELOPMENT_ENVIRONMENT_SETUP.md)
3. 快速上手 → [README快速开始](../README.md#-快速开始)

#### 进阶开发者
1. 深入技术架构 → [主技术文档](core/AI_AD_SYSTEM_MAIN_DOCUMENT.md)
2. 掌握业务逻辑 → [状态机规范](core/STATE_MACHINE.md)
3. 提升代码质量 → [开发规范](development/DEVELOPMENT_STANDARDS.md)

#### 架构师/高级工程师
1. 系统设计 → [系统概述](core/SYSTEM_OVERVIEW.md)
2. 数据架构 → [数据库设计](core/DATA_SCHEMA.md)
3. 部署架构 → [部署指南](deployment/DEPLOYMENT_GUIDE.md)

## 💡 使用提示

1. **文档搜索**: 使用 `Ctrl+F` 在文档内搜索关键词
2. **代码示例**: 所有代码示例都经过测试，可直接使用
3. **Mermaid图表**: 图表可以使用 Mermaid Live Editor 在线编辑
4. **版本控制**: 所有文档都有版本号和更新日期
5. **反馈建议**: 发现问题请提交 GitHub Issue

## 📌 重要提醒

- ⚠️ 生产环境部署前请务必阅读[安全配置](deployment/SECURITY_CONFIG.md)
- 🔒 所有API调用都需要正确的JWT认证
- 📊 数据库操作需要遵循RLS权限策略
- 🚀 部署前请完成所有测试用例
- 📝 代码提交请遵循[开发规范](development/DEVELOPMENT_STANDARDS.md)

## 🔗 相关链接

- **GitHub仓库**: https://github.com/your-org/ai-ad-spend
- **项目管理**: https://project.yourdomain.com
- **监控面板**: https://monitor.yourdomain.com
- **API文档**: http://localhost:8000/docs (开发环境)

---

**文档维护**: 技术架构团队
**更新频率**: 随项目进展同步更新
**最后更新**: 2025-11-11