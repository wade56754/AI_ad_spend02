# 前后端集成文档

> **文档集版本**: v1.0
> **最后更新**: 2025-12-10
> **文档类型**: 集成指南合集

---

## 📚 文档导航

本目录包含前后端打通的完整集成方案，包括：

### 1. [前后端打通完整方案](./FRONTEND_BACKEND_INTEGRATION.md)
**FRONTEND_BACKEND_INTEGRATION.md**

**适合人群**: 前后端开发人员
**阅读时间**: 30-40分钟

**内容概览**:
- ✅ 当前状态分析 (前后端配置、已启用模块、集成状态)
- ✅ CORS配置说明 (跨域配置、请求头、预检请求)
- ✅ 认证流程说明 (登录、Token管理、用户信息)
- ✅ API调用示例 (基础调用、各模块示例、React Query)
- ✅ 环境变量配置 (后端、前端配置项)
- ✅ 常见问题排查 (CORS、401、422、Network等)

**何时阅读**:
- 第一次开发前端页面时
- 遇到API调用问题时
- 需要了解认证机制时
- 排查集成问题时

---

### 2. [快速启动指南](./QUICK_START.md)
**QUICK_START.md**

**适合人群**: 所有开发人员、新成员
**阅读时间**: 15-20分钟
**实践时间**: 15-20分钟

**内容概览**:
- ✅ 环境准备 (系统要求、环境检查、项目克隆)
- ✅ 后端启动 (虚拟环境、依赖安装、配置、迁移、启动)
- ✅ 前端启动 (依赖安装、环境变量、启动)
- ✅ 数据库初始化 (连接、表结构、测试数据)
- ✅ 首次登录 (注册、登录、验证)
- ✅ 验证集成 (API调用、页面功能、CRUD操作)
- ✅ 常见问题 (启动失败、CORS、登录、API调用)

**何时阅读**:
- 第一次搭建开发环境时
- 新成员入职时
- 遇到启动问题时
- 需要快速验证环境时

---

### 3. [API对接清单](./API_INTEGRATION_CHECKLIST.md)
**API_INTEGRATION_CHECKLIST.md**

**适合人群**: 前端开发人员
**阅读时间**: 20-30分钟
**参考时间**: 持续参考

**内容概览**:
- ✅ 清单说明 (优先级、状态、使用方法)
- ✅ 认证模块 (注册、登录、Token、用户信息)
- ✅ 项目管理 (CRUD、统计、成员)
- ✅ 日报管理 (CRUD、审核、统计、导入导出)
- ✅ 充值管理 (CRUD、审核流程、统计)
- ✅ 供应商管理 (CRUD、账户、统计)
- ✅ 结算管理 (CRUD、审核、统计)
- ✅ 对账管理 (CRUD、差异处理)
- ✅ 报表中心 (仪表盘、专项报表、趋势)
- ✅ 其他模块 (广告账户、渠道、账本、转移、导入)
- ✅ 开发优先级建议 (分阶段实施)
- ✅ 前端技术建议 (React Query示例)

**何时阅读**:
- 规划开发任务时
- 实现具体功能时
- 需要参考API端点时
- 查看实现状态时

---

## 🚀 快速开始

### 对于新成员

**建议阅读顺序**:

1. **第一步**: 阅读 [快速启动指南](./QUICK_START.md) (15分钟)
   - 搭建开发环境
   - 启动前后端服务
   - 完成首次登录

2. **第二步**: 浏览 [前后端打通完整方案](./FRONTEND_BACKEND_INTEGRATION.md) (30分钟)
   - 了解系统架构
   - 理解认证机制
   - 学习API调用方式

3. **第三步**: 参考 [API对接清单](./API_INTEGRATION_CHECKLIST.md) (20分钟)
   - 查看可用API
   - 了解功能模块
   - 规划开发任务

4. **第四步**: 开始开发
   - 选择优先级最高的任务
   - 参考清单中的示例代码
   - 遇到问题查阅完整方案

**预计总时间**: 1-2小时

---

### 对于有经验的开发者

**快速参考**:

1. **环境搭建**: [QUICK_START.md](./QUICK_START.md) 第2-3节
2. **认证流程**: [FRONTEND_BACKEND_INTEGRATION.md](./FRONTEND_BACKEND_INTEGRATION.md) 第3节
3. **API调用**: [FRONTEND_BACKEND_INTEGRATION.md](./FRONTEND_BACKEND_INTEGRATION.md) 第4节
4. **API端点**: [API_INTEGRATION_CHECKLIST.md](./API_INTEGRATION_CHECKLIST.md) 第2-10节

---

## 📋 开发检查清单

### 开发前

- [ ] 已阅读快速启动指南
- [ ] 后端服务运行正常 (http://localhost:8000/healthz)
- [ ] 前端服务运行正常 (http://localhost:3000)
- [ ] 数据库连接正常
- [ ] 已创建测试账号
- [ ] 能够正常登录

### 开发中

- [ ] 查看API端点定义 (API对接清单)
- [ ] 使用统一的API客户端 (`lib/api.ts`)
- [ ] 使用React Query管理状态
- [ ] 处理Loading状态
- [ ] 处理错误状态
- [ ] 添加表单验证
- [ ] 添加确认提示

### 开发后

- [ ] 功能测试通过
- [ ] 错误处理完善
- [ ] 用户体验良好
- [ ] 代码review通过
- [ ] 更新API对接清单状态

---

## 🔗 相关文档

### SoT (真相源) 文档

- [STATE_MACHINE.md](../2.sot/STATE_MACHINE.md) v2.6 - 状态机定义
- [DATA_SCHEMA.md](../2.sot/DATA_SCHEMA.md) v5.2 - 数据模型
- [API_SOT.md](../2.sot/API_SOT.md) v9.0 - API规范
- [ERROR_CODES_SOT.md](../2.sot/ERROR_CODES_SOT.md) v2.1 - 错误码
- [BUSINESS_RULES.md](../2.sot/BUSINESS_RULES.md) v3.2 - 业务规则

### 开发指南

- [API_DEVELOPMENT_FLOW.md](../3.dev-guides/API_DEVELOPMENT_FLOW.md) - API开发流程
- [FRONTEND_DEVELOPMENT_RULES.md](../3.dev-guides/FRONTEND_DEVELOPMENT_RULES.md) - 前端开发规范
- [TESTING_STRATEGY.md](../3.dev-guides/TESTING_STRATEGY.md) - 测试策略

### 架构文档

- [SYSTEM_CONTEXT_VIEW.md](../4.architecture/SYSTEM_CONTEXT_VIEW.md) - 系统上下文
- [DATA_FLOW_VIEW.md](../4.architecture/DATA_FLOW_VIEW.md) - 数据流
- [SERVICE_COMPONENT_VIEW.md](../4.architecture/SERVICE_COMPONENT_VIEW.md) - 服务组件

---

## 💡 常见场景指南

### 场景1: 实现新的CRUD页面

**参考文档**:
1. [API对接清单](./API_INTEGRATION_CHECKLIST.md) - 查找API端点
2. [前后端打通完整方案](./FRONTEND_BACKEND_INTEGRATION.md) 第4.2节 - 参考项目管理示例

**步骤**:
1. 创建React Query hooks
2. 创建列表页面组件
3. 创建详情页面组件
4. 创建表单组件
5. 实现增删改查功能

**示例代码**: API对接清单附录B

---

### 场景2: 处理认证问题

**参考文档**:
1. [前后端打通完整方案](./FRONTEND_BACKEND_INTEGRATION.md) 第3节 - 认证流程
2. [前后端打通完整方案](./FRONTEND_BACKEND_INTEGRATION.md) 第6.2节 - 401错误处理

**常见问题**:
- Token未传递 → 检查localStorage
- Token过期 → 实现刷新机制
- Token无效 → 重新登录

---

### 场景3: 处理CORS问题

**参考文档**:
1. [前后端打通完整方案](./FRONTEND_BACKEND_INTEGRATION.md) 第2节 - CORS配置
2. [快速启动指南](./QUICK_START.md) 第7.3节 - CORS错误

**解决步骤**:
1. 检查后端CORS配置
2. 检查环境变量
3. 重启后端服务
4. 清除浏览器缓存

---

### 场景4: 调试API调用

**参考文档**:
1. [前后端打通完整方案](./FRONTEND_BACKEND_INTEGRATION.md) 第6.6节 - 调试技巧

**调试工具**:
- 浏览器开发工具 (Network标签)
- FastAPI文档 (http://localhost:8000/docs)
- Console日志
- React DevTools

---

## 📊 集成状态概览

### 后端API实现状态

| 模块 | 端点数 | 实现状态 | 前端集成 |
|------|--------|----------|----------|
| 认证 | 12 | ✅ 100% | 🟡 50% |
| 项目管理 | 8 | ✅ 100% | 🟡 30% |
| 日报管理 | 12 | ✅ 100% | 🟡 40% |
| 充值管理 | 10 | ✅ 100% | 🟡 30% |
| 供应商管理 | 8 | ✅ 100% | ❌ 0% |
| 结算管理 | 10 | ✅ 100% | ❌ 0% |
| 对账管理 | 6 | ✅ 100% | ❌ 0% |
| 报表中心 | 8 | ✅ 100% | 🟡 20% |
| 其他模块 | 15 | ✅ 100% | ❌ 0% |

**说明**:
- ✅ 已实现: 后端API已完成
- 🟡 部分实现: 前端部分页面已集成
- ❌ 未实现: 前端尚未集成

### 优先级开发建议

**Week 1-2**: 完成P0核心功能
- 认证模块 → 100%
- 项目管理 → 100%
- 日报管理 → 100%
- 充值管理 → 100%
- 仪表盘 → 100%

**Week 3-4**: 完成P1重要功能
- 供应商管理 → 100%
- 结算管理 → 100%
- 对账管理 → 100%
- 报表中心 → 100%

**Week 5-6**: 完成P2常规功能
- 其他模块 → 100%
- 功能完善
- 性能优化
- 测试文档

---

## 🛠️ 开发工具链

### 必备工具

1. **VSCode** (推荐)
   - 扩展: Python, ESLint, Prettier, React DevTools
2. **Postman** 或 **Insomnia** (API测试)
3. **Git** (版本控制)
4. **Node.js** 18+ (前端运行时)
5. **Python** 3.11+ (后端运行时)

### 可选工具

1. **DBeaver** (数据库管理)
2. **Redis Desktop Manager** (Redis管理)
3. **Docker Desktop** (容器管理)

---

## 📞 获取帮助

### 文档问题

如果文档有不清楚的地方：
1. 提交 GitHub Issue
2. 联系文档维护者
3. 查看其他相关文档

### 技术问题

如果遇到技术问题：
1. 查看常见问题排查 (各文档第6节)
2. 检查后端日志
3. 检查浏览器控制台
4. 访问FastAPI文档 (http://localhost:8000/docs)
5. 联系技术支持

---

## 📝 文档维护

### 更新记录

| 版本 | 日期 | 更新内容 | 维护者 |
|------|------|----------|--------|
| v1.0 | 2025-12-10 | 初始版本 | AI Development Team |

### 贡献指南

欢迎贡献文档改进：
1. Fork项目
2. 创建特性分支
3. 提交改进
4. 发起Pull Request

---

**文档维护者**: AI Development Team
**最后更新**: 2025-12-10
**下一次审核**: 2025-12-24
