# AI广告代投系统 - 文档中心

> 📅 **最后更新**: 2025-11-12
> 📋 **版本**: v2.1
> 👥 **维护者**: 开发团队

---

## 📚 文档导航

### 🏠 快速开始
| 文档 | 描述 | 更新日期 |
|------|------|----------|
| [README.md](../README.md) | 项目概述和快速入门 | - |
| [CLAUDE.md](../CLAUDE.md) | Claude AI 开发规范和规则 | - |
| [系统概览](core/SYSTEM_OVERVIEW.md) | 系统架构和核心概念 | - |

### 🗄️ 数据库相关
| 文档 | 描述 | 版本 | 状态 |
|------|------|------|------|
| [数据库设计 v2.3](core/DATA_SCHEMA_v2_3.md) | 完整数据库设计文档 | v2.3 | ✅ 当前版本 |
| [数据库优化总结](core/DATABASE_OPTIMIZATION_v3.3_SUMMARY.md) | 性能优化和改进记录 | v3.3 | ✅ 已完成 |
| [数据库修复报告](core/DATABASE_FIX_VALIDATION_REPORT.md) | 问题修复和验证报告 | v3.4 | ✅ 已验证 |
| [数据库脚本说明](../scripts/database/README.md) | 数据库初始化和维护脚本 | - | ✅ 可用 |
| [Supabase VSCode设置](SUPABASE_VSCODE_SETUP.md) | 开发环境配置指南 | - | ✅ 最新 |

### 🚀 部署运维
| 文档 | 描述 | 状态 |
|------|------|------|
| [部署指南](deployment/DEPLOYMENT_GUIDE.md) | 生产环境部署流程 | 📝 待更新 |
| [安全配置](deployment/SECURITY_CONFIG.md) | 安全策略和配置 | 📝 待更新 |
| [监控运维](deployment/MONITORING_OPS.md) | 系统监控和维护 | 📝 待更新 |
| [测试策略](deployment/TESTING_STRATEGY.md) | 测试流程和规范 | 📝 待更新 |

### 💻 开发指南
| 文档 | 描述 | 状态 |
|------|------|------|
| [开发规范](development/DEVELOPMENT_STANDARDS.md) | 代码规范和最佳实践 | ✅ 当前 |
| [后端API指南](development/BACKEND_API_GUIDE.md) | API开发规范和示例 | ✅ 当前 |
| [前端开发指南](development/FRONTEND_GUIDE.md) | 前端框架和组件开发 | 📝 待更新 |
| [开发环境设置](development/DEVELOPMENT_ENVIRONMENT_SETUP.md) | 本地开发环境搭建 | ✅ 当前 |

### 📋 项目管理
| 文档 | 描述 | 状态 |
|------|------|------|
| [任务路线图](project-management/TASK_ROADMAP.md) | 开发计划和里程碑 | 📝 待更新 |
| [需求文档](requirements/) | 业务需求和功能规格 | 📁 归档 |

### 🔧 工具和脚本
| 文档 | 描述 | 位置 |
|------|------|------|
| 数据库脚本 | SQL执行和维护 | `../scripts/database/` |
| 数据迁移脚本 | 版本迁移工具 | `../scripts/migration/` |
| 测试脚本 | 自动化测试 | `../scripts/test/` |

---

## 🏷️ 文档状态说明

- ✅ **已完成** - 文档是最新的且已经验证
- 📝 **待更新** - 文档需要更新以反映最新变化
- 🔨 **构建中** - 文档正在编写中
- 📁 **归档** - 历史文档，仅供参考

---

## 🔍 快速查找

### 按主题查找

**想了解数据库？**
1. 先读 [数据库设计 v2.3](core/DATA_SCHEMA_v2_3.md)
2. 查看 [数据库优化总结](core/DATABASE_OPTIMIZATION_v3.3_SUMMARY.md)
3. 使用 [数据库脚本](../scripts/database/)

**需要部署系统？**
1. 阅读 [部署指南](deployment/DEPLOYMENT_GUIDE.md)
2. 配置 [安全设置](deployment/SECURITY_CONFIG.md)
3. 设置 [监控](deployment/MONITORING_OPS.md)

**开始开发？**
1. 查看 [开发规范](development/DEVELOPMENT_STANDARDS.md)
2. 搭建 [开发环境](development/DEVELOPMENT_ENVIRONMENT_SETUP.md)
3. 学习 [API开发](development/BACKEND_API_GUIDE.md)

### 按角色查找

**数据库管理员**
- [数据库设计 v2.3](core/DATA_SCHEMA_v2_3.md)
- [数据库修复报告](core/DATABASE_FIX_VALIDATION_REPORT.md)
- [数据库脚本](../scripts/database/README.md)

**后端开发**
- [后端API指南](development/BACKEND_API_GUIDE.md)
- [开发规范](development/DEVELOPMENT_STANDARDS.md)
- [状态机文档](core/STATE_MACHINE.md)

**前端开发**
- [前端开发指南](development/FRONTEND_GUIDE.md)
- [系统概览](core/SYSTEM_OVERVIEW.md)

**运维工程师**
- [部署指南](deployment/DEPLOYMENT_GUIDE.md)
- [监控运维](deployment/MONITORING_OPS.md)
- [安全配置](deployment/SECURITY_CONFIG.md)

---

## 📝 文档贡献指南

### 编写规范
1. 使用 Markdown 格式
2. 标题层级清晰（H1-H6）
3. 代码块标明语言类型
4. 包含更新日期和版本号

### 提交流程
1. 创建新文档或修改现有文档
2. 更新本文档索引（如有新文档）
3. 提交 Pull Request
4. 经过代码审查后合并

### 文档模板
```markdown
# 文档标题

> 📅 **最后更新**: YYYY-MM-DD
> 📋 **版本**: v1.0
> 👥 **维护者**: 维护者名称

## 概述
简要描述文档内容

## 目录
1. 章节1
2. 章节2

## 详细内容
...

## 参考资料
- [相关文档](链接)
```

---

## 📞 联系方式

如有文档相关问题，请联系：
- 📧 Email: dev@aiad.com
- 💬 项目讨论组: [内部链接]
- 🐛 问题反馈: [GitHub Issues](链接)

---

**提示**: 使用 `Ctrl+F` 在页面内快速搜索关键词。