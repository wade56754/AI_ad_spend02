# AI 代码质量保障助手 - 使用指南

> **版本**: v1.0
> **状态**: Production Ready
> **定位**: 独立的 AI 编程质量保障助手，重点关注代码质量提升和安全性

---

## 目录

- [快速开始](#快速开始)
- [核心功能](#核心功能)
- [命令参考](#命令参考)
- [使用示例](#使用示例)
- [MCP 工具集成](#mcp-工具集成)
- [3 层约束模型](#3-层约束模型)
- [FAQ](#faq)
- [故障排除](#故障排除)

---

## 快速开始

### 安装

AI 代码质量保障助手已集成到项目中，无需额外安装。确保您的 `.claude/skills/` 目录包含 `ai-code-quality-assistant/` 文件夹即可。

### 第一次使用

```bash
# 检查代码质量
/code-quality check backend/services/user_service.py

# 设计架构
/code-quality design 设计一个高并发的订单系统

# 审查代码
/code-quality review frontend/src/components/UserCard.tsx
```

---

## 核心功能

### 1. 代码质量检查

使用 3 层约束模型检查代码：

- **Layer 1 (MUST)**: 安全约束 - SQL注入、XSS、硬编码密钥、不安全加密
- **Layer 2 (SHOULD)**: 行为约束 - 可读性、错误处理、性能意识、可测试性
- **Layer 3 (MAY)**: 任务约束 - 文档完整性、扩展性、兼容性

**特点**:
- ✅ 5 类安全问题自动检测
- ✅ 详细的问题定位和修复建议
- ✅ 按风险等级排序（Critical > High > Medium > Low）

---

### 2. 架构设计建议

使用 **sequential-thinking** MCP 工具进行深度推理：

- **问题分解**: 将复杂问题拆解为可管理的子问题
- **方案探索**: 列举可能的解决方案（方案 A vs B vs C）
- **权衡分析**: 评估每个方案的优缺点（性能、复杂度、成本）
- **决策验证**: 验证选择的方案是否满足所有约束
- **风险识别**: 识别潜在风险和缓解策略

**特点**:
- ✅ 多步推理（5+ 步）
- ✅ 方案对比和权衡
- ✅ 架构图和代码示例
- ✅ 风险识别和缓解策略

---

### 3. 最新技术集成

使用 **context7** MCP 工具获取最新框架/库文档：

- 确保使用最新 API 和最佳实践
- 避免使用过时的技术模式
- 提供版本兼容性建议

**特点**:
- ✅ 自动解析库名称
- ✅ 获取最新版本文档
- ✅ 提供关键 API 和最佳实践
- ✅ 包含代码示例

---

### 4. 问题诊断与修复

深度分析代码问题根因：

- 多种修复方案及对比
- 修复优先级建议
- 潜在风险提示

**特点**:
- ✅ 根因分析
- ✅ 多种修复方案
- ✅ 优先级排序
- ✅ 风险提示

---

### 5. 代码生成增强

生成符合项目规范和质量标准的代码：

- 自动应用 SoT 标注格式
- 确保与代码工厂输出兼容
- 符合 CLAUDE.md v3.4 规范

**特点**:
- ✅ SoT 标注格式
- ✅ 3 层约束自动应用
- ✅ 单元测试示例
- ✅ 文档和注释

---

## 命令参考

### 主命令

```bash
/code-quality <子命令> [参数]
```

### 子命令列表

#### 1. `check` - 代码质量检查

**用法**:
```bash
/code-quality check <文件路径>
```

**示例**:
```bash
/code-quality check backend/services/user_service.py
/code-quality check frontend/src/components/UserCard.tsx
```

**输出**: 质量检查报告，包含安全问题、行为问题、改进建议

---

#### 2. `review` - 代码审查

**用法**:
```bash
/code-quality review <文件路径>
```

**示例**:
```bash
/code-quality review backend/routers/authentication.py
```

**输出**: 代码审查报告，包含代码风格、最佳实践、重构建议

---

#### 3. `design` - 架构设计

**用法**:
```bash
/code-quality design <设计需求>
```

**示例**:
```bash
/code-quality design 设计一个高并发的订单系统，需要处理每秒 10000+ 请求
/code-quality design 实现一个用户认证系统，支持 JWT 和 OAuth2
```

**输出**: 架构设计方案，包含深度推理过程、方案对比、架构图、代码示例

---

#### 4. `diagnose` - 问题诊断

**用法**:
```bash
/code-quality diagnose <问题描述>
```

**示例**:
```bash
/code-quality diagnose 为什么数据库查询这么慢？
/code-quality diagnose 内存使用率持续上升，可能的原因是什么？
```

**输出**: 问题诊断报告，包含根因分析、修复方案、优先级排序

---

#### 5. `gen` - 代码生成（质量增强）

**用法**:
```bash
/code-quality gen <代码需求>
```

**示例**:
```bash
/code-quality gen 生成一个用户认证 API，使用 FastAPI
/code-quality gen 创建一个 React 组件，用于显示用户列表
```

**输出**: 高质量代码，包含 SoT 标注、安全检查、单元测试、文档

---

### 自动触发

当检测到以下关键词时自动触发：

```yaml
触发关键词:
  - "帮我设计一个..."
  - "审查这段代码..."
  - "如何优化..."
  - "这段代码有什么问题..."
  - "检查代码质量..."
  - "生成一个高质量的..."
```

**示例**:
```
用户: "帮我设计一个高并发的支付系统"
→ 自动触发 /code-quality design
```

---

## 使用示例

### 示例 1: 代码质量检查

**输入**:
```bash
/code-quality check backend/services/user_service.py
```

**输出**:
```markdown
## 🔍 代码质量检查报告

### 📊 总体评估
- **质量等级**: 良好
- **总体评分**: 78/100

### 🔴 Layer 1: 安全约束（MUST）

#### ❌ 发现问题
**1. 硬编码 API 密钥（第 42 行）**
- **风险等级**: Critical
- **问题代码**: `API_KEY = "sk-1234567890abcdef"`
- **修复建议**: 使用环境变量
  ```python
  import os
  API_KEY = os.getenv("API_KEY")
  ```

### 🟡 Layer 2: 行为约束（SHOULD）

#### ⚠️ 发现问题
**1. 缺少错误处理（函数 getUserData，第 58 行）**
- **建议**: 添加 try-catch 块
  ```python
  try:
      user = session.query(User).filter(User.id == user_id).first()
      if not user:
          raise HTTPException(404, "User not found")
      return user
  except SQLAlchemyError as e:
      logger.error(f"Database error: {e}")
      raise HTTPException(500, "Database error")
  ```

### 🛠️ 修复优先级
1. [Critical] 移除硬编码 API 密钥
2. [High] 添加错误处理
3. [Medium] 优化 N+1 查询
```

---

### 示例 2: 架构设计

**输入**:
```bash
/code-quality design 设计一个高并发的订单系统，需要处理每秒 10000+ 请求
```

**输出**:
```markdown
## 🏗️ 架构设计方案

### 🤔 深度推理过程（Sequential Thinking）

**1. 问题分析**
- 高并发写入（订单创建）
- 高并发读取（订单查询）
- 数据一致性要求

**2. 方案探索**

**方案 A: 消息队列 + 异步处理**
- 优点: 削峰填谷、解耦、高吞吐
- 缺点: 延迟高、复杂度高

**方案 B: 数据库分片 + 读写分离**
- 优点: 扩展性强、读写分离
- 缺点: 数据一致性难、运维复杂

**方案 C: 缓存层 + CDN**
- 优点: 低延迟、成本低
- 缺点: 缓存失效复杂

**3. 权衡分析**

| 维度 | 方案 A | 方案 B | 方案 C |
|------|-------|-------|-------|
| 并发能力 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 响应延迟 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 数据一致性 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |

**4. 最终选择**: 组合方案 A+C

### 💻 架构方案

```
Client → API Gateway (FastAPI)
         ├──→ [查询] → Redis Cache → PostgreSQL (从库)
         └──→ [写入] → RabbitMQ → Worker Pool → PostgreSQL (主库)
```

### ✅ 质量保障
- 查询延迟: < 50ms (缓存命中)
- 写入吞吐: > 10000 QPS
- 可用性: 99.95%
```

---

### 示例 3: 问题诊断

**输入**:
```bash
/code-quality diagnose 为什么数据库查询这么慢？
```

**输出**:
```markdown
## 🔍 问题诊断报告

### 📋 问题描述
数据库查询响应时间过长（> 1秒）

### 🤔 根因分析

**可能原因 1: N+1 查询问题**
- **症状**: 循环中多次查询数据库
- **检测方法**: 查看 SQL 日志
- **示例**:
  ```python
  users = session.query(User).all()
  for user in users:
      print(user.orders)  # 每个 user 触发一次查询
  ```

**可能原因 2: 缺少索引**
- **症状**: WHERE 子句字段未建索引
- **检测方法**: EXPLAIN 查询计划
- **示例**: `EXPLAIN SELECT * FROM users WHERE email = 'test@example.com'`

**可能原因 3: 查询返回过多数据**
- **症状**: SELECT * 返回大量字段
- **检测方法**: 查看返回行数和字段数

### 🛠️ 修复方案

**方案 1: 使用 joinedload（针对 N+1 问题）**
```python
from sqlalchemy.orm import joinedload
users = session.query(User).options(joinedload(User.orders)).all()
```

**方案 2: 添加索引（针对缺少索引）**
```sql
CREATE INDEX idx_users_email ON users(email);
```

**方案 3: 限制返回字段和行数**
```python
users = session.query(User.id, User.name).limit(100).all()
```

### 📊 优先级排序
1. [High] 检查并修复 N+1 查询
2. [High] 添加缺失的索引
3. [Medium] 优化查询字段和行数
```

---

## MCP 工具集成

### sequential-thinking

**用途**: 复杂问题的多步推理

**触发条件**:
- 架构设计（需要权衡多个方案）
- 复杂问题诊断（需要排查根因）
- 技术选型（需要对比评估）
- 性能优化（需要分析瓶颈）

**工作流程**:
```
1. 问题分解
2. 方案探索
3. 权衡分析
4. 决策验证
5. 风险识别
```

**配置**:
```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

---

### context7

**用途**: 获取最新框架/库文档

**触发条件**:
- 用户明确提到特定库/框架（如 "Next.js 14"、"FastAPI"）
- 涉及较新的技术（API 可能已变更）
- 需要确保最佳实践

**工作流程**:
```
1. 解析库名称
2. 调用 resolve-library-id 获取库 ID
3. 调用 get-library-docs 获取文档
4. 提取关键 API 和最佳实践
```

**配置**:
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"]
    }
  }
}
```

---

## 3 层约束模型

### Layer 1: 安全约束（MUST，不可违反）

| 安全类别 | 检查项 | 违反处理 |
|---------|--------|---------|
| SQL 注入 | 拼接 SQL 字符串 | 立即拒绝 |
| XSS 防护 | 未转义 HTML 输出 | 立即拒绝 |
| 硬编码密钥 | 密钥/密码/token | 立即拒绝 |
| 不安全加密 | MD5/SHA1 哈希密码 | 立即拒绝 |
| 命令注入 | 拼接 shell 命令 | 立即拒绝 |

**详细规则**: 参见 `constraints/layer1-security.md`

---

### Layer 2: 行为约束（SHOULD，强烈推荐）

| 行为类别 | 检查项 | 违反处理 |
|---------|--------|---------|
| 代码可读性 | 清晰命名、适当注释 | 警告 + 建议 |
| 错误处理 | try-catch、错误消息、日志 | 警告 + 建议 |
| 性能意识 | 避免 N+1 查询、缓存 | 警告 + 建议 |
| 可测试性 | 依赖注入、单元测试 | 警告 + 建议 |

**详细规则**: 参见 `constraints/layer2-behavior.md`

---

### Layer 3: 任务约束（MAY，根据场景决定）

| 任务类别 | 检查项 | 违反处理 |
|---------|--------|---------|
| 文档完整性 | docstring、README、使用示例 | 提示 |
| 扩展性 | 设计模式、配置分离 | 提示 |
| 兼容性 | 版本要求、跨平台处理 | 提示 |

**详细规则**: 参见 `constraints/layer3-task.md`

---

## FAQ

### Q1: 如何判断是否需要使用 sequential-thinking？

**A**: 当任务涉及以下场景时，会自动使用 sequential-thinking：

- 架构设计（需要权衡多个方案）
- 复杂问题诊断（需要排查根因）
- 技术选型（需要对比评估）
- 性能优化（需要分析瓶颈）

如果您不确定，可以在命令中明确指出：
```bash
/code-quality design 设计一个高并发系统，请使用深度推理
```

---

### Q2: 如何获取特定框架的最新文档？

**A**: 只需在命令中提到框架名称和版本，context7 会自动获取：

```bash
/code-quality gen 使用 Next.js 14 的 App Router 实现 SSR
```

支持的框架包括：Next.js, React, FastAPI, Django, Flask 等。

---

### Q3: 如何禁用某一层约束？

**A**: 默认情况下，所有 3 层约束都会检查。如果您只想检查安全约束：

```bash
/code-quality check --layer=1 backend/services/user_service.py
```

如果您只想检查安全和行为约束：
```bash
/code-quality check --layer=1,2 backend/services/user_service.py
```

---

### Q4: 如何与代码工厂集成？

**A**: 当前版本作为独立 Skill 使用。未来版本将支持以下集成方式：

- **选项 A**: 增强 ai-ad-code-verifier（作为 Layer 7）
- **选项 B**: 新增 QUALITY_FLOW 流程类型
- **选项 C**: 作为代码工厂的可选增强（quality_mode=strict）

---

### Q5: 如何处理误报？

**A**: 如果您认为某个检查结果是误报，可以：

1. 在代码中添加注释说明：
   ```python
   # QUALITY_ASSISTANT_IGNORE: false positive
   API_KEY = "public-key-12345"  # 公开的 API 密钥，非敏感信息
   ```

2. 或者在命令中忽略特定规则：
   ```bash
   /code-quality check --ignore=hardcoded-key backend/services/user_service.py
   ```

---

## 故障排除

### 问题 1: MCP 工具调用失败

**症状**:
```
Error: Failed to call sequential-thinking MCP tool
```

**解决方法**:

1. 检查 MCP 服务器是否配置正确：
   ```bash
   # 查看 .mcp.json
   cat .mcp.json
   ```

2. 确保 MCP 服务器已安装：
   ```bash
   npx -y @modelcontextprotocol/server-sequential-thinking --version
   npx -y @context7/mcp-server --version
   ```

3. 如果仍然失败，会降级到基础模式（不使用 MCP 工具）

---

### 问题 2: 约束检查误报

**症状**: 合法代码被标记为不安全

**解决方法**:

1. 使用 `# QUALITY_ASSISTANT_IGNORE` 注释忽略特定行
2. 使用 `--ignore` 参数忽略特定规则
3. 向我们反馈误报案例，帮助改进检查规则

---

### 问题 3: 性能问题

**症状**: 质量检查耗时过长（> 30 秒）

**解决方法**:

1. 使用 `--quick` 模式（仅检查 Layer 1）：
   ```bash
   /code-quality check --quick backend/services/user_service.py
   ```

2. 限制检查范围：
   ```bash
   /code-quality check --lines=1-100 backend/services/user_service.py
   ```

3. 如果文件过大（> 1000 行），考虑拆分文件

---

## 联系与反馈

- **维护者**: wade
- **项目**: AI_ad_spend02
- **文档**: 参见 SKILL.md, CHANGELOG.md
- **示例**: 参见 examples/ 目录

---

**版本**: v1.0
**最后更新**: 2025-12-22
**状态**: Production Ready
