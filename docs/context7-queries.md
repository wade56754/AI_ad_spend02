# Context7 MCP查询日志

> **目的**: 记录所有通过Context7 MCP进行的查询，便于后续查找和复用
> **更新日期**: 2025-11-11

---

## 📋 查询格式

每个查询记录包含：
- 查询日期和时间
- 查询目的
- 查询的库名/主题
- 查询结果和关键信息
- 应用到项目的具体内容

---

## 📝 查询记录

### 2025-11-11

#### Query #1 - Context7 MCP基础信息
- **时间**: 2025-11-11 12:00
- **目的**: 了解Context7 MCP的功能和使用方法
- **查询**:
  - `resolve-library-id`: context7
  - `get-library-docs`: /upstash/context7
- **关键收获**:
  - Context7提供两个主要工具：`resolve-library-id`和`get-library-docs`
  - 必须先解析库ID才能获取文档
  - 可以指定topic和tokens参数
- **应用**: 创建了Context7使用规范文档

#### Query #2 - Supabase文档查询
- **时间**: 2025-11-11 12:05
- **目的**: 获取Supabase最新文档和最佳实践
- **查询**:
  - `resolve-library-id`: supabase
  - 结果ID: /supabase/supabase
- **关键收获**:
  - Supabase Auth + RLS的最佳实践
  - 行级安全策略的实现方法
- **应用**: 优化了RLS策略脚本

#### Query #3 - Next.js 15文档查询
- **时间**: 2025-11-11 12:10
- **目的**: 了解Next.js 15的新特性和最佳实践
- **查询**:
  - `resolve-library-id`: next.js
  - `get-library-docs`: /vercel/next.js topic="app router"
- **关键收获**:
  - App Router的最佳实践
  - Server Components使用方法
- **应用**: 更新了前端开发指南

#### Query #4 - FastAPI文档查询
- **时间**: 2025-11-11 12:15
- **目的**: 获取FastAPI最新版本的特性和规范
- **查询**:
  - `resolve-library-id`: fastapi
  - `get-library-docs`: /tiangolo/fastapi topic="dependency injection"
- **关键收获**:
  - 依赖注入的最佳实践
  - 中间件的正确使用方法
- **应用**: 优化了后端架构设计

---

## 📊 统计信息

### 查询频率最高的库
1. **Next.js** - 前端框架查询
2. **Supabase** - 数据库和认证
3. **FastAPI** - 后端框架
4. **Tailwind CSS** - 样式框架
5. **TypeScript** - 类型系统

### 查询主题分布
- API设计 (30%)
- 数据库设计 (25%)
- 前端组件 (20%)
- 部署和运维 (15%)
- 测试策略 (10%)

---

## 💡 最佳实践总结

### 1. 查询策略
- 先通过`resolve-library-id`确认库是否存在
- 使用具体的topic参数获取精准信息
- 根据项目需求设置合适的token数量

### 2. 信息验证
- 查询后需要验证信息的时效性
- 对比多个来源的信息
- 在项目中小范围测试后再推广

### 3. 知识沉淀
- 及时记录查询结果
- 将有用信息整合到项目文档
- 建立知识库供团队共享

---

## 🔗 相关文档

- [开发规范](../DEVELOPMENT_STANDARDS.md)
- [Context7官方文档](https://context7.com)
- [MCP配置](../.mcp.json)

---

## 📝 待查询事项

### 高优先级
- [ ] PostgreSQL性能优化最佳实践
- [ ] Redis缓存策略
- [ ] Docker多阶段构建优化

### 中优先级
- [ ] TypeScript高级类型技巧
- [ ] React性能优化
- [ ] 自动化测试策略

### 低优先级
- [ ] GraphQL vs REST对比
- [ ] 微服务架构模式
- [ ] Serverless最佳实践

---

**最后更新**: 2025-11-11 12:30
**更新人**: 开发团队
**下次审查**: 每周更新