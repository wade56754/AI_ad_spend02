# 开发指南

## 📌 概述

本目录包含AI广告代投系统的开发指南，帮助开发人员快速上手并遵循统一的开发规范。

## 📂 文档结构

```
development/
├── README.md                 # 开发指南索引（本文件）
├── setup.md                  # 环境搭建指南
├── coding-standards.md       # 编码规范
├── best-practices.md         # 最佳实践
├── database-guide.md         # 数据库开发指南
├── frontend-guide.md         # 前端开发指南
├── backend-guide.md          # 后端开发指南
└── git-workflow.md           # Git工作流程
```

## 🚀 快速开始

### 1. 环境要求

- **Python** 3.11+
- **Node.js** 18+
- **PostgreSQL** 15+
- **Redis** 7+
- **Docker** 20+

### 2. 开发工具推荐

- **IDE**: VSCode / PyCharm
- **API测试**: Postman / Insomnia
- **数据库工具**: DBeaver / pgAdmin
- **Git客户端**: GitKraken / SourceTree

### 3. 项目初始化

```bash
# 克隆项目
git clone https://github.com/wade56754/AI_ad_spend02.git
cd AI_ad_spend02

# 安装依赖
pip install -r requirements.txt
cd frontend && npm install

# 配置环境
cp .env.example .env
# 编辑 .env 文件
```

## 🏗️ 技术架构

### 后端技术栈
- **框架**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0
- **验证**: Pydantic v2
- **认证**: JWT + OAuth2
- **异步**: asyncio + aiohttp
- **任务队列**: Celery + Redis

### 前端技术栈
- **框架**: Next.js 15
- **语言**: TypeScript
- **样式**: Tailwind CSS
- **组件库**: shadcn/ui
- **状态管理**: Zustand
- **数据获取**: SWR / React Query

## 📋 开发规范概览

### Python编码规范
```python
# 使用类型注解
def calculate_roi(spend: float, revenue: float) -> float:
    """计算投资回报率。

    Args:
        spend: 广告花费
        revenue: 收入

    Returns:
        ROI百分比
    """
    if spend == 0:
        return 0.0
    return (revenue - spend) / spend * 100
```

### TypeScript编码规范
```typescript
// 使用接口定义类型
interface Project {
  id: string;
  name: string;
  status: 'active' | 'paused' | 'completed';
  createdAt: Date;
}

// 使用枚举定义常量
enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  OPERATOR = 'operator',
}
```

## 🔧 开发流程

### 1. 功能开发流程
```mermaid
graph LR
    A[需求分析] --> B[设计评审]
    B --> C[编码实现]
    C --> D[单元测试]
    D --> E[代码审查]
    E --> F[集成测试]
    F --> G[部署上线]
```

### 2. 分支管理策略
- `main` - 生产环境分支
- `develop` - 开发环境分支
- `feature/*` - 功能开发分支
- `hotfix/*` - 紧急修复分支
- `release/*` - 发布分支

### 3. 提交规范
```bash
# 提交格式
<type>(<scope>): <subject>

# 示例
feat(api): 添加项目创建接口
fix(auth): 修复JWT过期问题
docs(readme): 更新安装说明
style(frontend): 格式化代码
refactor(db): 优化查询性能
test(api): 添加单元测试
chore(deps): 更新依赖包
```

## 🧪 测试要求

### 测试覆盖率
- 单元测试: ≥80%
- 集成测试: 核心流程100%
- E2E测试: 关键用户路径

### 测试命令
```bash
# 后端测试
pytest
pytest --cov=backend/app

# 前端测试
npm test
npm run test:coverage

# E2E测试
npm run test:e2e
```

## 📚 学习资源

### 官方文档
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [Next.js文档](https://nextjs.org/docs)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [Tailwind CSS文档](https://tailwindcss.com/docs)

### 内部文档
- [系统架构设计](../core/SYSTEM_OVERVIEW.md)
- [数据库设计](../core/DATA_SCHEMA.md)
- [API文档](../api/README.md)

## 🐛 调试技巧

### 后端调试
```python
# 使用debugpy进行远程调试
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()

# 使用logging记录日志
import logging
logger = logging.getLogger(__name__)
logger.debug("调试信息")
```

### 前端调试
```typescript
// 使用console进行调试
console.log('调试信息', data);
console.table(arrayData);
console.time('性能测试');
// ... 代码
console.timeEnd('性能测试');

// 使用React DevTools
// 安装浏览器扩展进行组件调试
```

## 🔒 安全注意事项

1. **永远不要**将敏感信息硬编码
2. **始终**验证用户输入
3. **使用**参数化查询防止SQL注入
4. **实现**适当的错误处理
5. **记录**所有安全相关事件

## 📞 获取帮助

- **技术问题**: 查看 [FAQ](../guides/faq.md)
- **Bug报告**: 提交 [GitHub Issue](https://github.com/wade56754/AI_ad_spend02/issues)
- **代码审查**: 创建 Pull Request
- **团队讨论**: Slack频道 #dev-team

---

*最后更新: 2024-11-18*