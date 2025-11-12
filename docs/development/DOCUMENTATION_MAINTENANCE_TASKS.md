# 文档维护任务清单

## 📚 文档体系概览

### 文档结构层次
```
docs/
├── development/           # 开发文档
│   ├── 接口开发流程文档
│   ├── 代码质量检查任务
│   ├── 测试实施任务清单
│   └── 部署发布任务列表
├── api/                  # API文档
│   ├── v1/              # 版本化API文档
│   └── openapi/         # OpenAPI规范
├── user/                # 用户文档
├── deployment/          # 部署文档
└── maintenance/         # 维护文档
```

### 文档类型分类
- **开发文档**: 技术规范、开发指南、最佳实践
- **API文档**: 接口规范、使用示例、错误码说明
- **用户文档**: 使用手册、常见问题、操作指南
- **运维文档**: 部署指南、监控配置、故障处理
- **维护文档**: 版本更新、变更记录、维护流程

---

## 🎯 阶段一：文档规划与架构

### 任务1.1：文档架构设计
**时间预估**: 1天
**负责角色**: 技术写作工程师 + 架构师

#### 文档架构要求
- [ ] 文档分类体系设计
- [ ] 导航结构规划
- [ ] 版本管理策略
- [ ] 搜索优化方案
- [ ] 多媒体支持规划

#### 文档架构配置
```yaml
# mkdocs.yml
site_name: AI广告代投系统文档
site_description: 智能化广告投放管理平台技术文档
site_author: 开发团队
site_url: https://docs.your-domain.com

# 文档导航结构
nav:
  - 首页: index.md
  - 快速开始:
    - 环境搭建: quickstart/setup.md
    - 第一个项目: quickstart/first-project.md
    - 基础概念: quickstart/concepts.md
  - 开发指南:
    - 接口开发: development/interface-development.md
    - 代码规范: development/coding-standards.md
    - 测试指南: development/testing-guide.md
    - API设计: development/api-design.md
  - API文档:
    - 概览: api/overview.md
    - 认证: api/authentication.md
    - 错误码: api/error-codes.md
    - 接口列表: api/endpoints.md
  - 部署运维:
    - 部署指南: deployment/deployment-guide.md
    - 监控配置: deployment/monitoring.md
    - 故障处理: deployment/troubleshooting.md
  - 用户手册:
    - 项目管理: user/project-management.md
    - 数据报表: user/reports.md
    - 常见问题: user/faq.md

# 主题配置
theme:
  name: material
  language: zh
  features:
    - navigation.instant
    - navigation.tracking
    - navigation.tabs
    - navigation.tabs.sticky
    - navigation.sections
    - navigation.expand
    - navigation.indexes
    - search.highlight
    - search.share

# 插件配置
plugins:
  - search:
      lang:
        - zh
        - en
  - minify:
      minify_html: true
  - git-revision-date-localized
  - awesome-pages

# Markdown扩展
markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.tabbed:
      alternate_style: true
  - tables
  - footnotes
```

#### Claude提示词
```
请设计AI广告代投系统的文档架构：

文档类型：
- 开发文档（技术规范、开发指南）
- API文档（接口规范、使用示例）
- 用户文档（使用手册、操作指南）
- 运维文档（部署指南、故障处理）
- 维护文档（版本更新、变更记录）

设计要求：
1. 清晰的分类体系
2. 直观的导航结构
3. 版本管理策略
4. 搜索优化方案
5. 多媒体内容支持

请生成：
1. 文档架构设计方案
2. 目录结构规划
3. 导航菜单配置
4. 搜索优化策略
5. 版本控制方案
```

### 任务1.2：文档标准制定
**时间预估**: 1天
**负责角色**: 技术写作工程师

#### 文档标准要求
- [ ] 文档格式规范
- [ ] 写作风格指南
- [ ] 术语词汇表
- [ ] 图表制作标准
- [ ] 版本控制规范

#### 文档写作规范
```markdown
# 文档写作规范

## 1. 文档结构标准

### 标题层级
```markdown
# 一级标题（文档标题）
## 二级标题（章节标题）
### 三级标题（小节标题）
#### 四级标题（子小节）
##### 五级标题（详细内容）
```

### 文档模板
```markdown
# {文档标题}

## 概述
> **适用场景**: {使用场景描述}
> **目标读者**: {目标读者群体}
> **前置条件**: {阅读本文档的前置条件}

---

## 基础概念
{基本概念解释}

## 使用指南
{详细使用说明}

## 示例代码
```python
# 示例代码
def example_function():
    pass
```

## 常见问题
{FAQ内容}

## 参考资料
{相关链接和资源}
```

## 2. 写作风格规范

### 语言要求
- 使用简洁明了的中文表达
- 避免使用过于技术化的术语
- 保持段落简短，重点突出
- 使用主动语态，避免被动语态

### 格式要求
- 代码块使用语法高亮
- 重点内容使用**粗体**或*斜体*标注
- 列表使用有序或无序列表
- 表格要有表头和对齐

### 术语规范
- 技术术语要保持一致性
- 首次出现的术语要给出解释
- 使用标准的翻译，避免自创词汇
```

#### Claude提示词
```
请制定项目文档标准：

标准类型：
- 文档格式规范
- 写作风格指南
- 术语词汇表
- 图表制作标准
- 版本控制规范

要求：
1. 统一的文档模板
2. 一致的写作风格
3. 标准的术语使用
4. 清晰的图表规范
5. 规范的版本管理

请生成：
1. 文档写作规范
2. 模板文件示例
3. 术语词汇表
4. 图表制作指南
5. 版本控制流程
```

---

## 🔧 阶段二：文档内容创建

### 任务2.1：API文档生成
**时间预估**: 2天
**负责角色**: 后端工程师 + 技术写作工程师

#### API文档要求
- [ ] 自动生成OpenAPI规范
- [ ] 接口详细信息
- [ ] 请求/响应示例
- [ ] 错误码说明
- [ ] 认证方式说明

#### API文档生成脚本
```python
# scripts/generate_api_docs.py
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

class APIDocGenerator:
    """API文档生成器"""

    def __init__(self, app, output_dir: Path):
        self.app = app
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_openapi_spec(self):
        """生成OpenAPI规范"""
        openapi_spec = self.app.openapi()

        # 添加项目信息
        openapi_spec["info"].update({
            "description": "AI广告代投系统API接口文档",
            "version": "v1.0.0",
            "contact": {
                "name": "开发团队",
                "email": "dev-team@company.com"
            }
        })

        # 生成JSON格式
        with open(self.output_dir / "openapi.json", "w", encoding="utf-8") as f:
            json.dump(openapi_spec, f, indent=2, ensure_ascii=False)

        return openapi_spec

    def generate_markdown_docs(self, openapi_spec: Dict[str, Any]):
        """生成Markdown格式文档"""
        # 生成API概览
        self.generate_api_overview(openapi_spec)

        # 生成认证文档
        self.generate_auth_docs(openapi_spec)

        # 生成错误码文档
        self.generate_error_codes_docs(openapi_spec)

        # 生成接口详情文档
        self.generate_endpoint_docs(openapi_spec)

    def generate_api_overview(self, openapi_spec: Dict[str, Any]):
        """生成API概览文档"""
        content = f"""# API接口文档

## 概览

**API版本**: {openapi_spec['info']['version']}
**基础URL**: https://api.your-domain.com
**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 基本信息

### 认证方式
本API使用JWT Bearer Token认证。在请求头中添加：
```
Authorization: Bearer <your_token>
```

### 响应格式

所有API响应都遵循统一的格式：

#### 成功响应
```json
{{
  "success": true,
  "data": {{ ... }},
  "message": "操作成功",
  "code": "SUCCESS",
  "request_id": "uuid",
  "timestamp": "2025-11-12T10:30:00Z"
}}
```

#### 错误响应
```json
{{
  "success": false,
  "error": {{
    "code": "ERROR_CODE",
    "message": "错误描述"
  }},
  "request_id": "uuid",
  "timestamp": "2025-11-12T10:30:00Z"
}}
```

### 通用错误码

| 错误码 | HTTP状态码 | 描述 |
|--------|------------|------|
| SUCCESS | 200 | 操作成功 |
| VALIDATION_ERROR | 400 | 参数验证失败 |
| UNAUTHORIZED | 401 | 未授权访问 |
| FORBIDDEN | 403 | 权限不足 |
| NOT_FOUND | 404 | 资源不存在 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

## 接口列表

{self._generate_endpoint_summary(openapi_spec)}
"""

        with open(self.output_dir / "api-overview.md", "w", encoding="utf-8") as f:
            f.write(content)

    def generate_auth_docs(self, openapi_spec: Dict[str, Any]):
        """生成认证文档"""
        content = """# API认证指南

## 认证概述

AI广告代投系统API使用JWT（JSON Web Token）进行身份认证。

## 获取Token

### 请求
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

### 响应
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 900
  }
}
```

## 使用Token

在API请求的Header中添加Authorization字段：

```bash
GET /api/v1/projects
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Token刷新

Access Token有效期为15分钟，过期后需要使用refresh_token刷新：

```bash
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## 权限控制

系统支持以下角色：

| 角色 | 权限描述 |
|------|----------|
| admin | 系统管理员，拥有所有权限 |
| finance | 财务人员，可管理充值和对账 |
| data_operator | 数据操作员，可管理数据 |
| account_manager | 账户管理员，可管理项目和账户 |
| media_buyer | 投手，可管理广告投放 |

## 注意事项

1. 请妥善保管Token，避免泄露
2. Token过期后需要重新获取
3. 长时间不活动会自动退出登录
4. 建议在客户端实现Token自动刷新机制
"""

        with open(self.output_dir / "authentication.md", "w", encoding="utf-8") as f:
            f.write(content)

    def _generate_endpoint_summary(self, openapi_spec: Dict[str, Any]) -> str:
        """生成接口摘要表格"""
        summary = []
        summary.append("| 方法 | 端点 | 描述 | 权限要求 |")
        summary.append("|------|------|------|----------|")

        for path, path_item in openapi_spec.get("paths", {}).items():
            for method, operation in path_item.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    desc = operation.get("summary", operation.get("description", ""))
                    auth_req = operation.get("security", [])
                    permission = "需要认证" if auth_req else "公开接口"

                    summary.append(f"| {method.upper()} | {path} | {desc} | {permission} |")

        return "\n".join(summary)

# 使用示例
if __name__ == "__main__":
    from backend.main import app

    generator = APIDocGenerator(app, Path("docs/api"))
    openapi_spec = generator.generate_openapi_spec()
    generator.generate_markdown_docs(openapi_spec)

    print("✅ API文档生成完成")
```

#### Claude提示词
```
请生成API文档：

API要求：
- 基于OpenAPI 3.0规范
- 包含完整的接口信息
- 提供请求/响应示例
- 说明认证方式和权限要求
- 包含错误码说明

生成内容：
1. OpenAPI JSON规范文件
2. API概览文档
3. 认证指南
4. 错误码说明
5. 接口详细文档

请确保：
- 文档格式规范统一
- 示例代码可执行
- 错误说明准确
- 权限要求明确
```

### 任务2.2：用户手册编写
**时间预估**: 3天
**负责角色**: 产品经理 + 技术写作工程师

#### 用户手册要求
- [ ] 功能使用指南
- [ ] 操作流程说明
- [ ] 常见问题解答
- [ ] 最佳实践建议
- [ ] 故障排除指南

#### 用户手册模板
```markdown
# {功能模块}用户手册

## 功能概述

{功能模块的基本介绍和主要用途}

## 使用场景

{适用的业务场景和用户群体}

## 操作指南

### 基础操作

{详细的使用步骤，配有截图或示例}

### 高级功能

{进阶功能的使用方法}

## 常见问题

### Q1: {常见问题1}
**A**: {详细解答}

### Q2: {常见问题2}
**A**: {详细解答}

## 最佳实践

{使用建议和优化技巧}

## 注意事项

{使用限制和注意事项}
```

#### Claude提示词
```
请编写{功能模块}的用户手册：

功能信息：
- 功能描述：{功能描述}
- 目标用户：{目标用户群体}
- 主要操作：{主要操作流程}
- 常见问题：{常见问题列表}

手册要求：
1. 详细的操作步骤
2. 清晰的截图说明
3. 常见问题解答
4. 最佳实践建议
5. 注意事项提醒

请生成：
1. 功能概述部分
2. 操作指南部分
3. FAQ部分
4. 最佳实践部分
5. 注意事项部分
```

---

## 🔄 阶段三：文档维护与更新

### 任务3.1：文档同步维护
**时间预估**: 持续执行
**检查频率**: 每次代码更新

#### 同步检查清单
- [ ] API文档与代码同步
- [ ] 配置文档与实际配置同步
- [ ] 部署文档与实际流程同步
- [ ] 版本信息及时更新
- [ ] 链接有效性检查

#### 文档同步脚本
```python
# scripts/sync_docs.py
import ast
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple
import requests

class DocumentationSyncer:
    """文档同步器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.docs_dir = project_root / "docs"
        self.backend_dir = project_root / "backend"

    def check_api_sync(self) -> Dict[str, bool]:
        """检查API文档同步状态"""
        # 获取实际API路由
        actual_routes = self._extract_api_routes()

        # 检查文档中的API
        documented_routes = self._extract_documented_routes()

        # 比较差异
        missing_in_docs = set(actual_routes) - set(documented_routes)
        missing_in_code = set(documented_routes) - set(actual_routes)

        return {
            "sync_complete": len(missing_in_docs) == 0 and len(missing_in_code) == 0,
            "missing_in_docs": list(missing_in_docs),
            "missing_in_code": list(missing_in_code),
            "total_actual": len(actual_routes),
            "total_documented": len(documented_routes)
        }

    def _extract_api_routes(self) -> List[str]:
        """从代码中提取API路由"""
        routes = []

        # 扫描路由文件
        for route_file in self.backend_dir.glob("routers/*.py"):
            with open(route_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 提取路由定义
            pattern = r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
            matches = re.findall(pattern, content)

            for method, path in matches:
                routes.append(f"{method.upper()} {path}")

        return sorted(routes)

    def _extract_documented_routes(self) -> List[str]:
        """从文档中提取已记录的API路由"""
        routes = []

        # 扫描API文档
        for doc_file in self.docs_dir.glob("**/*.md"):
            with open(doc_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 提取API端点
            pattern = r'^\|\s*(GET|POST|PUT|DELETE|PATCH)\s*\|\s*([^\|]+)\s*\|'
            matches = re.findall(pattern, content, re.MULTILINE)

            for method, path in matches:
                routes.append(f"{method.upper()} {path.strip()}")

        return sorted(routes)

    def check_link_validity(self) -> List[Tuple[str, str, str]]:
        """检查文档链接有效性"""
        broken_links = []

        for doc_file in self.docs_dir.rglob("*.md"):
            with open(doc_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 提取Markdown链接
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            matches = re.findall(link_pattern, content)

            for text, link in matches:
                if link.startswith("http"):
                    # 外部链接
                    if not self._check_external_link(link):
                        broken_links.append((str(doc_file.relative_to(self.docs_dir)), text, link))
                elif not link.startswith("#"):
                    # 内部链接
                    if not self._check_internal_link(link, doc_file.parent):
                        broken_links.append((str(doc_file.relative_to(self.docs_dir)), text, link))

        return broken_links

    def _check_external_link(self, url: str) -> bool:
        """检查外部链接有效性"""
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            return response.status_code < 400
        except:
            return False

    def _check_internal_link(self, link: str, base_path: Path) -> bool:
        """检查内部链接有效性"""
        target_path = base_path / link
        return target_path.exists()

    def check_config_sync(self) -> Dict[str, bool]:
        """检查配置文档同步"""
        config_checks = {}

        # 检查环境变量文档
        env_vars_in_code = self._extract_env_vars()
        env_vars_in_docs = self._extract_documented_env_vars()

        config_checks["env_vars_sync"] = set(env_vars_in_code) <= set(env_vars_in_docs)

        return config_checks

    def _extract_env_vars(self) -> List[str]:
        """从代码中提取环境变量"""
        env_vars = set()

        for py_file in self.backend_dir.rglob("*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 提取环境变量使用
            pattern = r'os\.environ\.get\(["\']([^"\']+)["\']'
            matches = re.findall(pattern, content)
            env_vars.update(matches)

            # 提取pydantic环境变量
            pattern = r'\w+\s*:\s*str\s*=\s*Field\([^)]*env=["\']([^"\']+)["\']'
            matches = re.findall(pattern, content)
            env_vars.update(matches)

        return sorted(list(env_vars))

    def _extract_documented_env_vars(self) -> List[str]:
        """从文档中提取环境变量"""
        env_vars = set()

        for doc_file in self.docs_dir.rglob("*.md"):
            with open(doc_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 提取环境变量文档
            pattern = r'`([A-Z_]+)`'
            matches = re.findall(pattern, content)
            env_vars.update(matches)

        return sorted(list(env_vars))

    def generate_sync_report(self) -> str:
        """生成同步报告"""
        api_sync = self.check_api_sync()
        broken_links = self.check_link_validity()
        config_sync = self.check_config_sync()

        report = f"""# 文档同步检查报告

## 检查时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## API文档同步状态
- **同步状态**: {'✅ 正常' if api_sync['sync_complete'] else '❌ 异常'}
- **实际API数量**: {api_sync['total_actual']}
- **文档记录数量**: {api_sync['total_documented']}

{'' if api_sync['sync_complete'] else f"""
### 缺失的API文档
{chr(10).join(f'- {route}' for route in api_sync['missing_in_docs'])}

### 文档中多余的API
{chr(10).join(f'- {route}' for route in api_sync['missing_in_code'])}
"""}

## 链接有效性检查
- **总链接数**: {len(broken_links)}
- **损坏链接数**: {len(broken_links)}

{'' if not broken_links else f"""
### 损坏链接详情
{chr(10).join(f'- **{file}**: [{text}]({link})' for file, text, link in broken_links)}
"""}

## 配置文档同步
- **环境变量同步**: {'✅ 正常' if config_sync.get('env_vars_sync', False) else '❌ 异常'}

## 改进建议
1. 及时更新API文档，确保与代码同步
2. 修复所有损坏的文档链接
3. 完善环境变量配置文档
4. 建立文档更新的自动化流程
"""

        return report

# 使用示例
if __name__ == "__main__":
    syncer = DocumentationSyncer(Path("."))
    report = syncer.generate_sync_report()

    with open("docs_sync_report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print("✅ 文档同步报告已生成")
```

#### Claude提示词
```
请检查文档同步状态：

检查范围：
- API文档与代码同步
- 配置文档与实际配置同步
- 文档链接有效性
- 版本信息准确性

同步要求：
1. API接口完全文档化
2. 配置参数详细说明
3. 所有链接有效可访问
4. 版本信息及时更新

请生成：
1. 同步状态检查报告
2. 差异问题清单
3. 修复建议方案
4. 自动化同步流程
```

### 任务3.2：版本管理
**时间预估**: 持续执行
**检查频率**: 每次版本发布

#### 版本管理清单
- [ ] 版本号规范管理
- [ ] 变更记录维护
- [ ] 历史版本归档
- [ ] 版本兼容性说明
- [ ] 升级指南编写

#### 变更记录模板
```markdown
# 变更记录

## [v2.1.0] - 2025-11-12

### 新增
- 🎨 新增项目成本分析功能
- 🔒 增强权限控制机制
- 📊 添加实时数据监控面板

### 改进
- ⚡ 优化API响应速度，提升30%
- 🛠️ 重构用户管理模块，提升稳定性
- 📱 改进移动端适配

### 修复
- 🐛 修复项目创建时的权限验证问题
- 🔧 解决数据库连接池泄漏问题
- 📝 修正报表数据计算错误

### 安全
- 🔒 更新依赖包，修复安全漏洞
- 🛡️ 加强输入验证，防止注入攻击
- 🔐 改进JWT Token安全策略

### 文档
- 📖 更新API文档，添加新接口说明
- 📚 完善部署指南
- ❓ 增加常见问题解答

---

## [v2.0.0] - 2025-10-15

### 重大更新
- 🚀 全新的AI异常检测功能
- 🔄 重构数据模型，提升性能
- 🎨 全新的用户界面设计

[更多历史版本...]
```

#### Claude提示词
```
请维护版本变更记录：

版本信息：
- 当前版本：v2.1.0
- 发布日期：2025-11-12
- 变更类型：{变更类型}

变更内容：
{具体变更内容}

记录要求：
1. 按照标准格式记录
2. 分类清晰（新增/改进/修复/安全）
3. 详细的变更说明
4. 影响范围评估
5. 升级注意事项

请生成：
1. 版本变更记录
2. 升级指南
3. 兼容性说明
4. 回滚方案
```

---

## 📊 阶段四：文档质量与优化

### 任务4.1：文档质量评估
**时间预估**: 1天
**检查频率**: 每月

#### 质量评估清单
- [ ] 内容准确性检查
- [ ] 结构完整性验证
- [ ] 用户友好性评估
- [ ] 搜索效果优化
- [ ] 可读性改进

#### 文档质量评估脚本
```python
# scripts/doc_quality_checker.py
import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter

class DocumentationQualityChecker:
    """文档质量检查器"""

    def __init__(self, docs_dir: Path):
        self.docs_dir = docs_dir

    def check_document_quality(self) -> Dict[str, any]:
        """检查文档质量"""
        doc_files = list(self.docs_dir.rglob("*.md"))

        quality_metrics = {
            "total_documents": len(doc_files),
            "content_analysis": self._analyze_content(doc_files),
            "structure_analysis": self._analyze_structure(doc_files),
            "readability_analysis": self._analyze_readability(doc_files),
            "search_optimization": self._check_search_optimization(doc_files)
        }

        return quality_metrics

    def _analyze_content(self, doc_files: List[Path]) -> Dict[str, any]:
        """分析文档内容质量"""
        total_words = 0
        total_code_blocks = 0
        total_images = 0
        total_links = 0

        for doc_file in doc_files:
            with open(doc_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 统计字数
            words = len(re.findall(r'\w+', content))
            total_words += words

            # 统计代码块
            code_blocks = len(re.findall(r'```', content)) // 2
            total_code_blocks += code_blocks

            # 统计图片
            images = len(re.findall(r'!\[.*?\]\(.*?\)', content))
            total_images += images

            # 统计链接
            links = len(re.findall(r'\[.*?\]\(.*?\)', content))
            total_links += links

        return {
            "total_words": total_words,
            "avg_words_per_doc": total_words / len(doc_files) if doc_files else 0,
            "total_code_blocks": total_code_blocks,
            "total_images": total_images,
            "total_links": total_links,
            "content_density": total_words / (total_code_blocks + 1)  # 内容与代码的比例
        }

    def _analyze_structure(self, doc_files: List[Path]) -> Dict[str, any]:
        """分析文档结构"""
        structure_metrics = {
            "has_table_of_contents": 0,
            "has_sections": 0,
            "avg_section_depth": 0,
            "has_code_examples": 0,
            "has_faqs": 0
        }

        total_sections = 0
        total_depth = 0

        for doc_file in doc_files:
            with open(doc_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查目录
            if re.search(r'(## 目录|## 目录|## TOC)', content, re.IGNORECASE):
                structure_metrics["has_table_of_contents"] += 1

            # 检查章节
            sections = re.findall(r'^#{1,6}\s+', content, re.MULTILINE)
            if sections:
                structure_metrics["has_sections"] += 1
                total_sections += len(sections)

                # 计算平均深度
                depths = [len(section.split()[0]) - 1 for section in sections]
                total_depth += sum(depths)

            # 检查代码示例
            if '```' in content:
                structure_metrics["has_code_examples"] += 1

            # 检查FAQ
            if re.search(r'(## 常见问题|## FAQ|## Q&A)', content, re.IGNORECASE):
                structure_metrics["has_faqs"] += 1

        structure_metrics["avg_section_depth"] = total_depth / total_sections if total_sections > 0 else 0

        return structure_metrics

    def _analyze_readability(self, doc_files: List[Path]) -> Dict[str, any]:
        """分析可读性"""
        readability_metrics = {
            "avg_sentence_length": 0,
            "avg_paragraph_length": 0,
            "heading_consistency": 0,
            "terminology_consistency": self._check_terminology_consistency(doc_files)
        }

        total_sentences = 0
        total_sentence_words = 0
        total_paragraphs = 0
        total_paragraph_words = 0

        for doc_file in doc_files:
            with open(doc_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 移除代码块
            content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)

            # 分析句子
            sentences = re.split(r'[。！？]', content)
            for sentence in sentences:
                if sentence.strip():
                    words = len(re.findall(r'\w+', sentence))
                    if words > 0:
                        total_sentences += 1
                        total_sentence_words += words

            # 分析段落
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            for paragraph in paragraphs:
                if not paragraph.startswith('#'):  # 排除标题
                    words = len(re.findall(r'\w+', paragraph))
                    if words > 0:
                        total_paragraphs += 1
                        total_paragraph_words += words

        readability_metrics["avg_sentence_length"] = total_sentence_words / total_sentences if total_sentences > 0 else 0
        readability_metrics["avg_paragraph_length"] = total_paragraph_words / total_paragraphs if total_paragraphs > 0 else 0

        return readability_metrics

    def _check_terminology_consistency(self, doc_files: List[Path]) -> Dict[str, any]:
        """检查术语一致性"""
        term_counter = Counter()

        for doc_file in doc_files:
            with open(doc_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 提取技术术语
            technical_terms = re.findall(r'\b[A-Z][a-zA-Z]+\b', content)
            term_counter.update(technical_terms)

        # 找出可能的变体
        inconsistent_terms = []
        common_terms = term_counter.most_common(20)

        for term, count in common_terms:
            if count > 1:
                # 检查是否有大小写变体
                variants = [t for t in term_counter.keys() if t.lower() == term.lower() and t != term]
                if variants:
                    inconsistent_terms.append((term, variants))

        return {
            "total_unique_terms": len(term_counter),
            "most_common_terms": common_terms[:10],
            "inconsistent_terms": inconsistent_terms
        }

    def _check_search_optimization(self, doc_files: List[Path]) -> Dict[str, any]:
        """检查搜索优化"""
        optimization_metrics = {
            "documents_with_keywords": 0,
            "avg_keywords_per_doc": 0,
            "documents_with_meta": 0,
            "heading_optimization": 0
        }

        total_keywords = 0

        for doc_file in doc_files:
            with open(doc_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查关键词
            keywords = re.findall(r'(keywords|标签):\s*(.+)', content, re.IGNORECASE)
            if keywords:
                optimization_metrics["documents_with_keywords"] += 1
                total_keywords += len(keywords[0][1].split(',')) if keywords[0][1] else 0

            # 检查元数据
            if re.search(r'(description|描述):', content, re.IGNORECASE):
                optimization_metrics["documents_with_meta"] += 1

            # 检查标题优化
            headings = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
            if headings:
                # 检查是否包含关键词
                optimized_headings = sum(1 for h in headings if len(h.split()) <= 10)  # 简洁的标题
                optimization_metrics["heading_optimization"] += optimized_headings

        optimization_metrics["avg_keywords_per_doc"] = total_keywords / len(doc_files) if doc_files else 0

        return optimization_metrics

    def generate_quality_report(self) -> str:
        """生成质量报告"""
        quality_data = self.check_document_quality()

        report = f"""# 文档质量评估报告

## 评估时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 总体概况
- **文档总数**: {quality_data['total_documents']}
- **内容质量评分**: {self._calculate_content_score(quality_data['content_analysis'])}/10
- **结构质量评分**: {self._calculate_structure_score(quality_data['structure_analysis'])}/10
- **可读性评分**: {self._calculate_readability_score(quality_data['readability_analysis'])}/10

## 内容分析
- **总字数**: {quality_data['content_analysis']['total_words']:,}
- **平均每文档字数**: {quality_data['content_analysis']['avg_words_per_doc']:.0f}
- **代码块数量**: {quality_data['content_analysis']['total_code_blocks']}
- **图片数量**: {quality_data['content_analysis']['total_images']}
- **链接数量**: {quality_data['content_analysis']['total_links']}

## 结构分析
- **有目录的文档**: {quality_data['structure_analysis']['has_table_of_contents']}/{quality_data['total_documents']}
- **有章节的文档**: {quality_data['structure_analysis']['has_sections']}/{quality_data['total_documents']}
- **平均章节深度**: {quality_data['structure_analysis']['avg_section_depth']:.1f}
- **有代码示例的文档**: {quality_data['structure_analysis']['has_code_examples']}/{quality_data['total_documents']}

## 可读性分析
- **平均句子长度**: {quality_data['readability_analysis']['avg_sentence_length']:.1f} 词
- **平均段落长度**: {quality_data['readability_analysis']['avg_paragraph_length']:.1f} 词
- **术语一致性**: {'✅ 良好' if not quality_data['readability_analysis']['terminology_consistency']['inconsistent_terms'] else '⚠️ 需改进'}

## 搜索优化
- **有关键词的文档**: {quality_data['search_optimization']['documents_with_keywords']}/{quality_data['total_documents']}
- **平均关键词数**: {quality_data['search_optimization']['avg_keywords_per_doc']:.1f}

## 改进建议
{self._generate_improvement_suggestions(quality_data)}
"""

        return report

    def _calculate_content_score(self, content_data: Dict[str, any]) -> float:
        """计算内容质量评分"""
        score = 0

        # 字数评分
        if content_data["avg_words_per_doc"] >= 500:
            score += 3
        elif content_data["avg_words_per_doc"] >= 300:
            score += 2
        else:
            score += 1

        # 代码示例评分
        if content_data["total_code_blocks"] > 50:
            score += 3
        elif content_data["total_code_blocks"] > 20:
            score += 2
        else:
            score += 1

        # 媒体内容评分
        if content_data["total_images"] > 20:
            score += 2
        elif content_data["total_images"] > 10:
            score += 1

        # 链接质量评分
        if content_data["total_links"] > 100:
            score += 2
        elif content_data["total_links"] > 50:
            score += 1

        return min(score, 10)

    def _generate_improvement_suggestions(self, quality_data: Dict[str, any]) -> str:
        """生成改进建议"""
        suggestions = []

        # 内容改进建议
        if quality_data['content_analysis']['avg_words_per_doc'] < 300:
            suggestions.append("1. 增加文档内容深度，每篇文档至少300字")

        if quality_data['structure_analysis']['has_table_of_contents'] < quality_data['total_documents'] * 0.8:
            suggestions.append("2. 为长文档添加目录，提高导航性")

        if quality_data['search_optimization']['documents_with_keywords'] < quality_data['total_documents'] * 0.5:
            suggestions.append("3. 为文档添加关键词标签，优化搜索效果")

        readability = quality_data['readability_analysis']
        if readability['avg_sentence_length'] > 25:
            suggestions.append("4. 缩短句子长度，提高可读性")

        if readability['avg_paragraph_length'] > 100:
            suggestions.append("5. 分割长段落，提升阅读体验")

        return "\n".join(suggestions) if suggestions else "文档质量良好，继续保持"

# 使用示例
if __name__ == "__main__":
    checker = DocumentationQualityChecker(Path("docs"))
    report = checker.generate_quality_report()

    with open("docs_quality_report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print("✅ 文档质量报告已生成")
```

#### Claude提示词
```
请评估文档质量：

评估维度：
- 内容质量（完整性、准确性、深度）
- 结构质量（组织性、导航性、一致性）
- 可读性（语言表达、术语使用）
- 搜索优化（关键词、元数据）

评估要求：
1. 量化质量指标
2. 识别改进空间
3. 提供优化建议
4. 制定提升计划

请生成：
1. 质量评估报告
2. 问题分析清单
3. 改进建议方案
4. 质量提升计划
```

---

## 🚀 阶段五：自动化与工具

### 任务5.1：文档自动化工具
**时间预估**: 2天
**负责角色**: 开发工程师

#### 自动化工具清单
- [ ] 文档自动生成工具
- [ ] 文档同步检查工具
- [ ] 文档质量检查工具
- [ ] 文档发布自动化
- [ ] 文档监控告警

#### CI/CD文档流水线
```yaml
# .github/workflows/docs.yml
name: Documentation Pipeline

on:
  push:
    branches: [main, develop]
    paths:
      - "docs/**"
      - "backend/**"
  pull_request:
    branches: [main]
    paths:
      - "docs/**"

jobs:
  build-docs:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-docs.txt

    - name: Generate API documentation
      run: |
        python scripts/generate_api_docs.py

    - name: Check documentation sync
      run: |
        python scripts/sync_docs.py

    - name: Check documentation quality
      run: |
        python scripts/doc_quality_checker.py

    - name: Build documentation site
      run: |
        mkdocs build

    - name: Deploy to GitHub Pages
      if: github.ref == 'refs/heads/main'
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./site

    - name: Notify documentation updates
      if: github.ref == 'refs/heads/main'
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        text: "📚 文档已更新: https://your-domain.com/docs/"
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

#### Claude提示词
```
请开发文档自动化工具：

工具类型：
- 文档自动生成
- 文档同步检查
- 文档质量评估
- 文档发布部署
- 文档监控告警

功能要求：
1. 自动提取API信息生成文档
2. 检查文档与代码同步状态
3. 评估文档质量并生成报告
4. 自动部署到文档站点
5. 监控文档变更并发送通知

请开发：
1. 文档生成脚本
2. 同步检查工具
3. 质量评估工具
4. 自动化流水线
5. 监控告警系统
```

### 任务5.2：用户反馈收集
**时间预估**: 1天
**负责角色**: 产品经理

#### 反馈收集机制
- [ ] 文档评分系统
- [ ] 意见反馈表单
- [ ] 用户调研问卷
- [ ] 使用情况分析
- [ ] 反馈处理流程

#### 反馈收集工具
```html
<!-- docs/feedback.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文档反馈</title>
    <style>
        .feedback-form {
            max-width: 600px;
            margin: 20px auto;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }
        .rating {
            margin: 10px 0;
        }
        .rating button {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            margin: 0 5px;
        }
        .rating button:hover {
            color: gold;
        }
    </style>
</head>
<body>
    <div class="feedback-form">
        <h2>文档反馈</h2>
        <form id="feedbackForm">
            <div class="rating">
                <label>文档评分：</label>
                <button type="button" onclick="setRating(1)">⭐</button>
                <button type="button" onclick="setRating(2)">⭐</button>
                <button type="button" onclick="setRating(3)">⭐</button>
                <button type="button" onclick="setRating(4)">⭐</button>
                <button type="button" onclick="setRating(5)">⭐</button>
                <input type="hidden" id="rating" name="rating" value="0">
            </div>

            <div>
                <label for="page">当前页面：</label>
                <input type="text" id="page" name="page" readonly>
            </div>

            <div>
                <label for="category">反馈类型：</label>
                <select id="category" name="category">
                    <option value="content">内容问题</option>
                    <option value="format">格式问题</option>
                    <option value="suggestion">改进建议</option>
                    <option value="other">其他</option>
                </select>
            </div>

            <div>
                <label for="feedback">详细反馈：</label>
                <textarea id="feedback" name="feedback" rows="5" cols="50"></textarea>
            </div>

            <div>
                <label for="email">联系邮箱（可选）：</label>
                <input type="email" id="email" name="email">
            </div>

            <button type="submit">提交反馈</button>
        </form>

        <div id="result"></div>
    </div>

    <script>
        // 自动获取当前页面
        document.getElementById('page').value = document.referrer || window.location.href;

        function setRating(rating) {
            document.getElementById('rating').value = rating;

            // 更新星星显示
            const stars = document.querySelectorAll('.rating button');
            stars.forEach((star, index) => {
                if (index < rating) {
                    star.style.color = 'gold';
                } else {
                    star.style.color = '#ccc';
                }
            });
        }

        document.getElementById('feedbackForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const data = Object.fromEntries(formData);

            try {
                const response = await fetch('/api/feedback', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    document.getElementById('result').innerHTML =
                        '<p style="color: green;">✅ 感谢您的反馈！</p>';
                    this.reset();
                } else {
                    throw new Error('提交失败');
                }
            } catch (error) {
                document.getElementById('result').innerHTML =
                    '<p style="color: red;">❌ 提交失败，请稍后重试</p>';
            }
        });
    </script>
</body>
</html>
```

#### Claude提示词
```
请设计文档反馈收集系统：

收集需求：
- 文档评分功能
- 反馈分类收集
- 用户联系信息
- 自动页面识别
- 反馈统计分析

功能要求：
1. 简单易用的反馈表单
2. 自动识别用户当前页面
3. 支持多种反馈类型
4. 反馈数据统计分析
5. 反馈处理流程管理

请设计：
1. 反馈收集界面
2. 数据存储方案
3. 统计分析功能
4. 反馈处理流程
5. 用户体验优化
```

---

## 📋 文档维护检查清单

### 日常维护
- [ ] API文档与代码同步检查
- [ ] 链接有效性验证
- [ ] 用户反馈及时处理
- [ ] 版本信息更新
- [ ] 搜索效果监控

### 周期维护
- [ ] 文档质量评估
- [ ] 术语一致性检查
- [ ] 用户使用分析
- [ ] 文档结构优化
- [ ] 内容更新补充

### 版本发布维护
- [ ] 变更记录更新
- [ ] 版本兼容性检查
- [ ] 升级指南编写
- [ ] 历史版本归档
- [ ] 发布通知发布

---

**文档版本**: v1.0
**最后更新**: 2025-11-12
**适用范围**: 所有文档维护工作
**维护责任人**: 技术写作团队